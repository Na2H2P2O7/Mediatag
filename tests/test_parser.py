from pathlib import Path

from mediatag.parser import clean_filename_part, parse_movie_filename


def test_parse_english_release_name():
    parsed = parse_movie_filename(Path("Overheard.3.2014.BluRay.1080p.x265.10bit.2Audio-SSDSSE.mp4"))

    assert parsed.year == 2014
    assert "Overheard 3" in parsed.candidates


def test_parse_chinese_release_name_with_site_noise():
    parsed = parse_movie_filename(
        Path("【高清影视之家发布 www.HDBTHD.com】窃听风云3[国粤多音轨+中文字幕].Overheard.3.2014.1080p.WEB-DL.mp4")
    )

    assert parsed.year == 2014
    assert parsed.candidates[0].startswith("窃听风云3")
    assert "Overheard 3" in parsed.candidates


def test_parse_parenthesized_year():
    parsed = parse_movie_filename(Path("火遮眼 (2025)-BD-1080p.H264.AAC.2AUDIO.CHS.mp4"))

    assert parsed.year == 2025
    assert parsed.candidates[0] == "火遮眼"


def test_clean_filename_removes_illegal_chars():
    assert clean_filename_part('2025 A:B/C*D?"E<>|') == "2025 ABCDE"
