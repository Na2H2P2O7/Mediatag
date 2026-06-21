from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import requests

from .config import TMDbCredentials
from .models import MovieMetadata, ParsedMovieName
from .parser import has_han


TMDB_API = "https://api.themoviedb.org/3"

NO_ORIGINAL_TITLE_LANGUAGES = {
    "zh",
    "cn",
    "yue",
    "ja",
    "ko",
    "th",
    "vi",
    "id",
    "ms",
}

NO_ORIGINAL_TITLE_COUNTRIES = {
    "CN",
    "HK",
    "MO",
    "TW",
    "SG",
    "MY",
    "JP",
    "KR",
    "TH",
}

POSTER_LANGUAGE_BY_COUNTRY = {
    "CN": ("zh", "cn", "yue", None, "en"),
    "HK": ("zh", "cn", "yue", None, "en"),
    "MO": ("zh", "cn", "yue", None, "en"),
    "TW": ("zh", "cn", "yue", None, "en"),
    "SG": ("zh", "cn", "en", None),
    "MY": ("zh", "cn", "ms", "en", None),
    "JP": ("ja", None, "en"),
    "KR": ("ko", None, "en"),
    "TH": ("th", None, "en"),
    "US": ("en", None),
    "GB": ("en", None),
    "AU": ("en", None),
    "CA": ("en", None),
    "IE": ("en", None),
    "NZ": ("en", None),
}

POSTER_LANGUAGE_BY_ORIGINAL_LANGUAGE = {
    "zh": ("zh", "cn", "yue", None, "en"),
    "cn": ("zh", "cn", "yue", None, "en"),
    "yue": ("zh", "cn", "yue", None, "en"),
    "ja": ("ja", None, "en"),
    "ko": ("ko", None, "en"),
    "th": ("th", None, "en"),
    "en": ("en", None),
}


class TMDbError(RuntimeError):
    pass


@dataclass(frozen=True)
class TMDbClient:
    credentials: TMDbCredentials | str
    timeout: int = 20

    def __post_init__(self) -> None:
        if isinstance(self.credentials, str):
            object.__setattr__(
                self,
                "credentials",
                TMDbCredentials(bearer_token=self.credentials),
            )

    def _get(self, path: str, params: dict[str, object] | None = None) -> dict:
        credentials = self.credentials
        assert isinstance(credentials, TMDbCredentials)
        request_params = dict(params or {})
        headers = {"Accept": "application/json"}
        if credentials.bearer_token:
            headers["Authorization"] = f"Bearer {credentials.bearer_token}"
        elif credentials.api_key:
            request_params["api_key"] = credentials.api_key
        else:
            raise TMDbError("Missing TMDb credentials. Set TMDB_BEARER_TOKEN or TMDB_API_KEY.")

        response = requests.get(
            f"{TMDB_API}{path}",
            headers=headers,
            params=request_params,
            timeout=self.timeout,
        )
        if response.status_code == 401:
            raise TMDbError("TMDb authentication failed. Check TMDB_BEARER_TOKEN or TMDB_API_KEY.")
        response.raise_for_status()
        return response.json()

    def search_best(self, parsed: ParsedMovieName) -> MovieMetadata | None:
        for candidate in parsed.candidates:
            result = self._search_candidate(candidate, parsed.year, "zh-CN", use_year_filter=True)
            if result:
                return result
            if not has_han(candidate):
                result = self._search_candidate(candidate, parsed.year, "en-US", use_year_filter=True)
                if result:
                    return result
        for candidate in parsed.candidates:
            result = self._search_candidate(candidate, parsed.year, "zh-CN", use_year_filter=False)
            if result:
                return result
            if not has_han(candidate):
                result = self._search_candidate(candidate, parsed.year, "en-US", use_year_filter=False)
                if result:
                    return result
        return None

    def _search_candidate(
        self,
        query: str,
        year: int | None,
        language: str,
        use_year_filter: bool,
    ) -> MovieMetadata | None:
        params: dict[str, object] = {
            "query": query,
            "include_adult": "false",
            "language": language,
            "page": 1,
        }
        if year and use_year_filter:
            params["year"] = year
            params["primary_release_year"] = year

        data = self._get("/search/movie", params)
        results = data.get("results") or []
        if not results:
            return None

        ranked = sorted(
            results,
            key=lambda item: self._score(item, query, year),
            reverse=True,
        )
        best = ranked[0]
        confidence = self._score(best, query, year)
        if confidence < 0.55 or not best.get("poster_path"):
            return None

        details = self._get(
            f"/movie/{best['id']}",
            {
                "language": "zh-CN",
                "append_to_response": "translations,images",
                "include_image_language": "en,null,zh,cn,yue,ja,ko,th,ms",
            },
        )
        movie_year = _year_from_date(details.get("release_date")) or year
        if not movie_year:
            return None

        chinese_title = (details.get("title") or best.get("title") or "").strip()
        original_title = (details.get("original_title") or best.get("original_title") or "").strip()
        english_title = self._english_title(details) or original_title
        original_language = (details.get("original_language") or best.get("original_language") or "").strip()
        production_countries = [
            str(country.get("iso_3166_1") or "").strip()
            for country in details.get("production_countries", [])
        ]
        poster_path = _select_poster_path(
            details,
            fallback=best["poster_path"],
            original_language=original_language,
            production_countries=production_countries,
        )
        display_title = _format_display_title(
            movie_year,
            chinese_title,
            english_title,
            original_language=original_language,
            production_countries=production_countries,
        )

        return MovieMetadata(
            tmdb_id=int(best["id"]),
            year=int(movie_year),
            chinese_title=chinese_title or english_title,
            original_title=english_title,
            display_title=display_title,
            poster_path=poster_path,
            confidence=confidence,
        )

    def poster_url(self, poster_path: str, size: str = "w780") -> str:
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"

    @staticmethod
    def _score(item: dict, query: str, year: int | None) -> float:
        title_bits = {
            str(item.get("title") or "").casefold(),
            str(item.get("original_title") or "").casefold(),
        }
        q = query.casefold()
        score = 0.25
        if q in title_bits:
            score += 0.45
        elif any(q in bit or bit in q for bit in title_bits if bit):
            score += 0.25
        if year and _year_from_date(item.get("release_date")) == year:
            score += 0.25
        if item.get("poster_path"):
            score += 0.1
        popularity = float(item.get("popularity") or 0)
        score += min(popularity / 1000, 0.05)
        return min(score, 1.0)

    @staticmethod
    def _english_title(details: dict) -> str | None:
        translations = details.get("translations", {}).get("translations", [])
        for item in translations:
            if item.get("iso_639_1") == "en":
                title = (item.get("data") or {}).get("title")
                if title:
                    return str(title).strip()
        return None


def _year_from_date(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value).year
    except ValueError:
        return None


def _format_display_title(
    year: int,
    chinese_title: str,
    english_title: str,
    original_language: str = "",
    production_countries: list[str] | tuple[str, ...] = (),
) -> str:
    chinese_title = chinese_title.strip()
    english_title = english_title.strip()
    if (
        chinese_title
        and english_title
        and chinese_title.casefold() != english_title.casefold()
        and _should_append_original_title(original_language, production_countries)
    ):
        return f"{year} {chinese_title} {english_title}"
    return f"{year} {chinese_title or english_title}"


def _should_append_original_title(
    original_language: str,
    production_countries: list[str] | tuple[str, ...],
) -> bool:
    language = original_language.strip().lower()
    countries = {country.strip().upper() for country in production_countries if country}
    if language in NO_ORIGINAL_TITLE_LANGUAGES:
        return False
    if countries & NO_ORIGINAL_TITLE_COUNTRIES:
        return False
    return True


def _select_poster_path(
    details: dict,
    fallback: str,
    original_language: str,
    production_countries: list[str] | tuple[str, ...],
) -> str:
    posters = details.get("images", {}).get("posters") or []
    if not posters:
        return details.get("poster_path") or fallback

    language_priority = _poster_language_priority(original_language, production_countries)
    priority_index = {language: index for index, language in enumerate(language_priority)}

    def score(poster: dict) -> tuple[int, float, float]:
        language = poster.get("iso_639_1")
        priority = priority_index.get(language, len(language_priority))
        vote_average = float(poster.get("vote_average") or 0)
        vote_count = float(poster.get("vote_count") or 0)
        return (-priority, vote_average, vote_count)

    selected = max(posters, key=score)
    return selected.get("file_path") or details.get("poster_path") or fallback


def _poster_language_priority(
    original_language: str,
    production_countries: list[str] | tuple[str, ...],
) -> tuple[str | None, ...]:
    for country in production_countries:
        country_key = country.strip().upper()
        if country_key in POSTER_LANGUAGE_BY_COUNTRY:
            return POSTER_LANGUAGE_BY_COUNTRY[country_key]
    language_key = original_language.strip().lower()
    if language_key in POSTER_LANGUAGE_BY_ORIGINAL_LANGUAGE:
        return POSTER_LANGUAGE_BY_ORIGINAL_LANGUAGE[language_key]
    return (None, "en", "zh")
