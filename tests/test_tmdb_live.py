import os

import pytest

from movie_cover_tagger.models import ParsedMovieName
from movie_cover_tagger.tmdb import TMDbClient


@pytest.mark.skipif(not os.getenv("TMDB_BEARER_TOKEN"), reason="TMDB_BEARER_TOKEN not set")
def test_live_tmdb_smoke(tmp_path):
    parsed = ParsedMovieName(tmp_path / "Inception.2010.mp4", 2010, ("Inception",))

    metadata = TMDbClient(os.environ["TMDB_BEARER_TOKEN"]).search_best(parsed)

    assert metadata is not None
    assert metadata.poster_path
    assert metadata.year == 2010
