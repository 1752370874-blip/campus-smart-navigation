"""从教育部 XLS 附件生成全国普通高等学校目录。

用法：
    .venv\\Scripts\\python.exe scripts\\build_moe_catalog.py \
        work\\moe_2026_regular_higher_education.xls data\\institutions.csv
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


EXPECTED_COUNT = 2_952
SOURCE_URL = "https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/t20260618_1441074.html"
SOURCE_DATE = "2026-06-17"


def clean(value: object) -> str:
    """把 Excel 的空单元格和数字单元格转为稳定文本。"""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def build_catalog(source: Path) -> pd.DataFrame:
    """读取附件的分省表格，输出一行一所学校的规范目录。"""
    sheet = pd.read_excel(source, header=2, engine="xlrd")
    expected_columns = {"序号", "学校名称", "学校标识码", "主管部门", "所在地", "办学层次", "备注"}
    if not expected_columns.issubset(sheet.columns):
        raise ValueError("教育部附件表头与预期不一致，请先检查来源文件是否更新。")

    records: list[dict[str, str]] = []
    current_province = ""
    for _, row in sheet.iterrows():
        first_cell = clean(row["序号"])
        school_name = clean(row["学校名称"])
        if first_cell and not school_name and re.search(r"（\d+所）$", first_cell):
            current_province = re.sub(r"（\d+所）$", "", first_cell)
            continue
        if not school_name:
            continue
        if not current_province:
            raise ValueError(f"学校 {school_name} 出现在省份标题之前。")
        records.append({
            "moe_id": clean(row["学校标识码"]),
            "name": school_name,
            "province": current_province,
            "city": clean(row["所在地"]),
            "authority": clean(row["主管部门"]),
            "education_level": clean(row["办学层次"]),
            "notes": clean(row["备注"]),
            "source_date": SOURCE_DATE,
            "source_url": SOURCE_URL,
        })

    catalog = pd.DataFrame(records)
    if len(catalog) != EXPECTED_COUNT:
        raise ValueError(f"目录生成了 {len(catalog)} 所学校，预期应为 {EXPECTED_COUNT} 所。")
    if catalog["moe_id"].duplicated().any():
        raise ValueError("教育部学校标识码重复，停止生成。")
    return catalog


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("请提供来源 XLS 路径和输出 CSV 路径。")
    source, output = map(Path, sys.argv[1:])
    catalog = build_catalog(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"已生成 {len(catalog)} 所学校：{output}")


if __name__ == "__main__":
    main()
