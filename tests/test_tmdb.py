from mediatag.models import ParsedMovieName
from mediatag.tmdb import TMDbClient
from mediatag.config import TMDbCredentials


def test_tmdb_search_best_with_mocked_requests(monkeypatch, tmp_path):
    calls = []

    class Response:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, headers, params, timeout):
        calls.append((url, params))
        if url.endswith("/search/movie"):
            return Response(
                {
                    "results": [
                        {
                            "id": 42,
                            "title": "盗梦空间",
                            "original_title": "Inception",
                            "release_date": "2010-07-16",
                            "poster_path": "/poster.jpg",
                            "popularity": 100,
                        }
                    ]
                }
            )
        return Response(
            {
                "id": 42,
                "title": "盗梦空间",
                "original_title": "Inception",
                "original_language": "en",
                "release_date": "2010-07-16",
                "poster_path": "/poster.jpg",
                "production_countries": [{"iso_3166_1": "US"}],
                "translations": {
                    "translations": [
                        {"iso_639_1": "en", "data": {"title": "Inception"}},
                    ]
                },
            }
        )

    monkeypatch.setattr("mediatag.tmdb.requests.get", fake_get)
    parsed = ParsedMovieName(tmp_path / "Inception.2010.mp4", 2010, ("Inception",))

    metadata = TMDbClient("token").search_best(parsed)

    assert metadata is not None
    assert metadata.display_title == "2010 盗梦空间 Inception"
    assert calls[0][1]["year"] == 2010


def test_tmdb_does_not_append_original_title_for_hong_kong_movie(monkeypatch, tmp_path):
    class Response:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, headers, params, timeout):
        if url.endswith("/search/movie"):
            return Response(
                {
                    "results": [
                        {
                            "id": 43,
                            "title": "窃听风云",
                            "original_title": "Overheard",
                            "original_language": "cn",
                            "release_date": "2009-07-24",
                            "poster_path": "/overheard.jpg",
                            "popularity": 50,
                        }
                    ]
                }
            )
        return Response(
            {
                "id": 43,
                "title": "窃听风云",
                "original_title": "Overheard",
                "original_language": "cn",
                "release_date": "2009-07-24",
                "poster_path": "/overheard.jpg",
                "production_countries": [{"iso_3166_1": "HK"}],
                "translations": {
                    "translations": [
                        {"iso_639_1": "en", "data": {"title": "Overheard"}},
                    ]
                },
            }
        )

    monkeypatch.setattr("mediatag.tmdb.requests.get", fake_get)
    parsed = ParsedMovieName(tmp_path / "Overheard.2009.mp4", 2009, ("Overheard",))

    metadata = TMDbClient("token").search_best(parsed)

    assert metadata is not None
    assert metadata.display_title == "2009 窃听风云"


def test_tmdb_does_not_append_original_title_for_japanese_movie():
    from mediatag.tmdb import _format_display_title

    assert (
        _format_display_title(
            2001,
            "千与千寻",
            "Spirited Away",
            original_language="ja",
            production_countries=["JP"],
        )
        == "2001 千与千寻"
    )


def test_tmdb_api_key_auth_uses_query_param(monkeypatch):
    seen = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"results": []}

    def fake_get(url, headers, params, timeout):
        seen["headers"] = headers
        seen["params"] = params
        return Response()

    monkeypatch.setattr("mediatag.tmdb.requests.get", fake_get)

    TMDbClient(TMDbCredentials(api_key="abc123"))._get("/search/movie", {"query": "Inception"})

    assert seen["params"]["api_key"] == "abc123"
    assert "Authorization" not in seen["headers"]


def test_tmdb_bearer_auth_uses_authorization_header(monkeypatch):
    seen = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"results": []}

    def fake_get(url, headers, params, timeout):
        seen["headers"] = headers
        seen["params"] = params
        return Response()

    monkeypatch.setattr("mediatag.tmdb.requests.get", fake_get)

    TMDbClient(TMDbCredentials(bearer_token="token123"))._get("/search/movie", {"query": "Inception"})

    assert seen["headers"]["Authorization"] == "Bearer token123"
    assert "api_key" not in seen["params"]
