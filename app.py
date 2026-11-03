"""全国普通高等学校地图目录。

运行：.venv\\Scripts\\streamlit.exe run app.py
本版展示教育部学校目录与无标记全国底图；不展示校内地点、校址点或路线。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium


PROJECT_ROOT = Path(__file__).parent
INSTITUTIONS_FILE = PROJECT_ROOT / "data" / "institutions.csv"
CHINA_CENTER = (35.86166, 104.195397)
EXPECTED_INSTITUTION_COUNT = 2_952
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "CampusNavigationPrototype/1.0"


@st.cache_data
def load_institutions(path: Path) -> pd.DataFrame:
    """读取教育部普通高等学校目录，并校验它没有被意外截断。"""
    institutions = pd.read_csv(path, dtype={"moe_id": str})
    required_columns = {
        "moe_id", "name", "province", "city", "authority", "education_level",
        "notes", "source_date", "source_url",
    }
    missing_columns = required_columns - set(institutions.columns)
    if missing_columns:
        raise ValueError(f"学校目录缺少字段：{', '.join(sorted(missing_columns))}")
    if len(institutions) != EXPECTED_INSTITUTION_COUNT:
        raise ValueError(f"学校目录应有 {EXPECTED_INSTITUTION_COUNT} 所，实际为 {len(institutions)} 所。")
    if institutions["moe_id"].duplicated().any():
        raise ValueError("教育部学校标识码不能重复。")
    return institutions


def filter_institutions(
    institutions: pd.DataFrame, province: str, query: str, levels: list[str]
) -> pd.DataFrame:
    """按省份、学校名称和办学层次筛选全国目录。"""
    province_matches = pd.Series(True, index=institutions.index)
    if province != "全部省份":
        province_matches = institutions["province"] == province
    searchable_text = institutions["name"] + " " + institutions["city"]
    name_matches = searchable_text.str.contains(query.strip(), case=False, regex=False)
    level_matches = institutions["education_level"].isin(levels)
    return institutions[province_matches & name_matches & level_matches].copy()


@st.cache_data(ttl=86_400, show_spinner=False)
def find_openstreetmap_location(name: str, city: str) -> dict[str, Any] | None:
    """按需查找一所学校，避免批量地理编码全部目录。"""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": f"{name}, {city}, 中国", "format": "jsonv2", "limit": 1, "accept-language": "zh"},
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        matches = response.json()
        if not matches:
            return None
        match = matches[0]
        return {
            "latitude": float(match["lat"]),
            "longitude": float(match["lon"]),
            "display_name": str(match.get("display_name", name)),
        }
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None


def make_china_map() -> folium.Map:
    """创建没有学校点位的全国底图，避免把城市级数据误标为校址。"""
    return folium.Map(location=CHINA_CENTER, zoom_start=4, control_scale=True)


def make_selected_school_map(name: str, location: dict[str, Any]) -> folium.Map:
    """只在用户选中学校后显示临时地图标记，不写回学校目录。"""
    latitude = location["latitude"]
    longitude = location["longitude"]
    school_map = folium.Map(location=(latitude, longitude), zoom_start=16, control_scale=True)
    folium.Marker(
        location=(latitude, longitude),
        popup=folium.Popup(f"<b>{name}</b><br>公开地图搜索结果，待人工确认", max_width=260),
        tooltip=name,
    ).add_to(school_map)
    return school_map


def select_school(moe_id: str) -> None:
    """把用户点击的学校保存到当前 Streamlit 会话。"""
    st.session_state.selected_moe_id = moe_id


def main() -> None:
    st.set_page_config(page_title="全国大学地图", page_icon="🗺️", layout="wide")
    st.markdown(
        """<style>
        .hero {padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg, #0b3b75, #087e8b); color: white; margin-bottom: 1rem;}
        .hero h1 {margin: 0; font-size: 2rem;}.hero p {margin: .45rem 0 0; opacity: .92;}
        </style>
        <section class="hero"><h1>🗺️ 全国大学地图</h1><p>搜索一所普通高等学校，点击结果，即可查看对应的公开地图。</p></section>""",
        unsafe_allow_html=True,
    )

    try:
        institutions = load_institutions(INSTITUTIONS_FILE)
    except (OSError, ValueError) as error:
        st.error(f"无法加载学校目录：{error}")
        st.stop()

    st.subheader("搜索大学")
    search_column, province_column, level_column = st.columns([2, 1, 1])
    with search_column:
        query = st.text_input("学校名称或城市", placeholder="例如：北京大学、武汉大学、北京市", label_visibility="visible")
    with province_column:
        province = st.selectbox("省份", ["全部省份", *sorted(institutions["province"].unique())])
    with level_column:
        levels = sorted(institutions["education_level"].unique())
        selected_levels = st.multiselect("办学层次", levels, default=levels)
    st.caption("输入学校名称或城市后，点击出现的学校卡片即可打开地图。数据来源：教育部 2026 年全国普通高等学校名单。")

    results = filter_institutions(institutions, province, query, selected_levels)

    selected_id = st.session_state.get("selected_moe_id")
    if selected_id not in set(results["moe_id"]):
        selected_id = None
        st.session_state.pop("selected_moe_id", None)
    selected = results.loc[results["moe_id"] == selected_id].iloc[0] if selected_id else None

    count_one, count_two, count_three = st.columns(3)
    count_one.metric("普通高等学校", "2,952 所")
    count_two.metric("当前匹配", f"{len(results):,} 所")
    count_three.metric("覆盖地区", "31 个")

    st.subheader("搜索结果")
    if not query and province == "全部省份":
        st.info("先输入学校名或城市，或在左侧选择省份，快速缩小目录范围。")
    elif results.empty:
        st.warning("没有匹配的学校，请调整关键词或筛选条件。")
    elif len(results) > 24:
        st.info(f"找到 {len(results):,} 所学校。请继续输入关键词；下方先展示前 24 所。")

    if not results.empty and (query or province != "全部省份"):
        preview = results.head(24)
        for start in range(0, len(preview), 3):
            columns = st.columns(3)
            for column, (_, school) in zip(columns, preview.iloc[start : start + 3].iterrows()):
                with column:
                    st.button(
                        f"🗺️ {school['name']}\n{school['city']} · {school['education_level']}",
                        key=f"school-{school['moe_id']}",
                        use_container_width=True,
                        on_click=select_school,
                        args=(school["moe_id"],),
                    )

    st.divider()
    first, second = st.columns([3, 2])
    with first:
        if selected is None:
            st.subheader("全国概览")
            st_folium(make_china_map(), height=500, use_container_width=True, returned_objects=[])
        else:
            st.subheader(f"{selected['name']} 地图")
            with st.spinner("正在查找公开地图位置…"):
                location = find_openstreetmap_location(selected["name"], selected["city"])
            if location:
                st_folium(make_selected_school_map(selected["name"], location), height=500, use_container_width=True, returned_objects=[])
                st.caption(f"公开地图搜索结果：{location['display_name']}。该临时标记尚未作为校址数据写入项目。")
            else:
                st.warning("未能从公开地图取得可用位置。请使用右侧的搜索链接手动确认。")
                st_folium(make_china_map(), height=500, use_container_width=True, returned_objects=[])

    with second:
        if selected is None:
            st.subheader("如何使用")
            st.markdown("1. 输入学校名，例如“北京大学”。\n2. 点击出现的学校卡片。\n3. 查看页面左侧切换后的地图。")
            st.caption("地图标记仅在当前查看时显示，不会作为永久校址数据保存。")
            return

        st.subheader("学校信息")
        st.write(f"**所在地：** {selected['city']}")
        st.write(f"**办学层次：** {selected['education_level']}")
        st.write(f"**学校标识码：** {selected['moe_id']}")
        st.write(f"**主管部门：** {selected['authority']}")
        if selected["notes"]:
            st.write(f"**备注：** {selected['notes']}")
        osm_query = quote_plus(f"{selected['name']} {selected['city']}")
        st.link_button("在 OpenStreetMap 中打开检索结果", f"https://www.openstreetmap.org/search?query={osm_query}")
        st.link_button("查看教育部名单来源", selected["source_url"])


if __name__ == "__main__":
    main()
