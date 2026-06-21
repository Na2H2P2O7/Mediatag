from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .models import ParsedMovieName


YEAR_RE = re.compile(r"(?:19|20)\d{2}")
HAN_RE = re.compile(r"[\u3400-\u9fff]")

NOISE_WORDS = {
    "aac",
    "aac2",
    "ac3",
    "bdrip",
    "bd",
    "bluray",
    "chs",
    "cht",
    "dl",
    "dts",
    "h264",
    "h265",
    "hdr",
    "hd",
    "hevc",
    "pandaqt",
    "rip",
    "ssdsse",
    "web",
    "webdl",
    "webrip",
    "x264",
    "x265",
}

QUALITY_RE = re.compile(r"\b(?:480p|720p|1080p|2160p|4k|8k|10bit|12bit)\b", re.I)
BRACKET_RE = re.compile(r"[\[\]【】《》「」『』()（）]")
SITE_RE = re.compile(r"(?:www\.)?[a-z0-9-]+\.(?:com|net|org|cn)", re.I)


def has_han(text: str) -> bool:
    return bool(HAN_RE.search(text))


def normalize_title(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = SITE_RE.sub(" ", text)
    text = re.sub(r"高清影视之家发布|电影|主演|国语音轨|国粤多音轨|中文字幕|中英字幕", " ", text)
    text = BRACKET_RE.sub(" ", text)
    text = re.sub(r"[-_.]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -_.")


def _candidate_from_tokens(tokens: list[str], year_index: int | None) -> str | None:
    if year_index is None:
        useful = tokens
    else:
        useful = tokens[:year_index]
    cleaned: list[str] = []
    for token in useful:
        low = token.lower()
        if not token or low in NOISE_WORDS or QUALITY_RE.fullmatch(token):
            break
        if re.fullmatch(r"\d+audio|\d+ch|\d+", low):
            break
        cleaned.append(token)
    candidate = " ".join(cleaned).strip()
    return candidate if len(candidate) >= 2 else None


def _english_segment_before_year(text: str, year: int | None) -> str | None:
    if year is None:
        return None
    marker = str(year)
    before = text.split(marker, 1)[0]
    chunks = re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[ ._-]+[A-Za-z0-9]+)*", before)
    if not chunks:
        return None
    candidate = normalize_title(chunks[-1])
    tokens = [t for t in candidate.split() if t.lower() not in NOISE_WORDS]
    return " ".join(tokens) if tokens else None


def _han_segments(text: str) -> list[str]:
    segments = re.findall(r"[\u3400-\u9fff][\u3400-\u9fff0-9 ]{0,40}", normalize_title(text))
    return [seg.strip() for seg in segments if len(seg.strip()) >= 2]


def parse_movie_filename(path: str | Path) -> ParsedMovieName:
    path = Path(path)
    stem = path.stem
    normalized = normalize_title(stem)
    year_match = YEAR_RE.search(normalized)
    year = int(year_match.group(0)) if year_match else None

    candidates: list[str] = []
    if year_match:
        before_year = normalized[: year_match.start()].strip()
        after_year = normalized[year_match.end() :].strip()
        candidates.extend(_han_segments(before_year))
        english = _english_segment_before_year(normalized, year)
        if english:
            candidates.append(english)
        if has_han(after_year):
            candidates.extend(_han_segments(after_year))

    tokens = normalized.split()
    year_index = next((i for i, token in enumerate(tokens) if YEAR_RE.fullmatch(token)), None)
    token_candidate = _candidate_from_tokens(tokens, year_index)
    if token_candidate:
        candidates.append(token_candidate)

    if not candidates:
        candidates.append(normalized)

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate = normalize_title(candidate)
        if not candidate:
            continue
        key = candidate.casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)

    return ParsedMovieName(path, year, tuple(deduped))


def clean_filename_part(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
