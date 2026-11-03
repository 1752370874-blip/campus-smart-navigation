"""全国学校目录和页面的自动测试。"""

from pathlib import Path

from app import EXPECTED_INSTITUTION_COUNT, filter_institutions, load_institutions
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parents[1]


def test_catalogue_matches_official_count() -> None:
    institutions = load_institutions(ROOT / "data" / "institutions.csv")
    assert len(institutions) == EXPECTED_INSTITUTION_COUNT


def test_catalogue_has_unique_moe_ids() -> None:
    institutions = load_institutions(ROOT / "data" / "institutions.csv")
    assert institutions["moe_id"].is_unique


def test_filter_finds_wuhan_university() -> None:
    institutions = load_institutions(ROOT / "data" / "institutions.csv")
    levels = list(institutions["education_level"].unique())
    results = filter_institutions(institutions, "湖北省", "武汉大学", levels)
    assert results["name"].tolist() == ["武汉大学"]


def test_filtering_to_no_levels_returns_no_rows() -> None:
    institutions = load_institutions(ROOT / "data" / "institutions.csv")
    assert filter_institutions(institutions, "全部省份", "", []).empty


def test_streamlit_page_renders_without_an_exception() -> None:
    page = AppTest.from_file(ROOT / "app.py")
    page.run(timeout=15)
    assert not page.exception
