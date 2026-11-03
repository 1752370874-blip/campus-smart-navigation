# 全国普通高等学校地图目录

[![Test](https://github.com/1752370874-blip/campus-smart-navigation/actions/workflows/test.yml/badge.svg)](https://github.com/1752370874-blip/campus-smart-navigation/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

这是一个独立的 Python + Streamlit 项目。它收录教育部截至 2026 年 6 月 17 日公布的 **2,952 所普通高等学校**（本科与高职），支持按省份、名称和办学层次检索，并提供无标记的全国底图。

## 当前边界

本项目**不显示任何校内地点标记、校址坐标或路线**。教育部名单提供学校名称、所在地和办学层次，但不提供经过核验的校址或校内路网。将城市中心或未经核验的第三方坐标画成“校园地图”会产生误导，因此本版只提供目录和全国底图。

搜索学校后，点击出现的学校卡片，应用会按需查询 OpenStreetMap 并在页面内打开临时地图。地图结果不会保存为本项目的校址标注；未查到时可使用 OpenStreetMap 搜索链接手动检索。

## 数据来源

目录由教育部《全国普通高等学校名单》附件生成，统计截止日期为 2026-06-17。教育部说明该名单不含港澳台地区学校。

- 官方公告：[全国高等学校名单](https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/t20260618_1441074.html)
- 目录文件：[data/institutions.csv](data/institutions.csv)
- 生成脚本：[scripts/build_moe_catalog.py](scripts/build_moe_catalog.py)

## 运行

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

如果 Python 没有加入 PATH，创建好虚拟环境后可直接使用：

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
```

测试会确认目录恰为 2,952 所、教育部学校标识码不重复、学校筛选正确，且 Streamlit 页面可以渲染。

## 更新教育部目录

1. 下载新的教育部普通高等学校 XLS 附件到 `work/`。
2. 在 `scripts/build_moe_catalog.py` 更新来源日期、链接和预期学校数量。
3. 运行：

   ```powershell
   .\.venv\Scripts\python.exe scripts\build_moe_catalog.py <附件.xls> data\institutions.csv
   ```

4. 运行测试，确认新目录完整。

## 后续的校园地图计划

只有满足以下条件的校区才应加入地图点位或路线：

1. 有学校授权的 GIS/地图数据，或可以复查的精确校址坐标；
2. 坐标系明确为 WGS84，或已记录可靠的坐标转换；
3. 校内地点经过审核，且不包含宿舍房间、门禁、安防等敏感位置；
4. 路线服务基于授权或经过审核的可步行路网。

## 仓库与发布

- 仓库：<https://github.com/1752370874-blip/campus-smart-navigation>
- 每次 push 或 PR 都会自动执行 [`.github/workflows/test.yml`](.github/workflows/test.yml)：在 Python 3.12 上安装依赖并运行 pytest。

```bash
git clone https://github.com/1752370874-blip/campus-smart-navigation.git
```

## 许可证

代码以 [MIT](LICENSE) 协议发布。学校目录数据来自教育部公开发布的名单，使用时请保留来源与统计截止日期。
