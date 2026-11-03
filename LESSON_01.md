# 第 1 课：从官方名单到全国学校目录

这一版的目标是安全地展示全国普通高等学校目录，而不是猜测每所学校的校址。代码的数据流是：**教育部 XLS → 生成脚本 → `institutions.csv` → 搜索网页**。

## 1. 生成脚本

打开 `scripts/build_moe_catalog.py`。

- `EXPECTED_COUNT = 2_952` 是保护线。生成出来的学校数不等于教育部公告数时，程序立刻报错。
- `pd.read_excel(..., header=2, engine="xlrd")` 跳过 XLS 前两行标题，从第三行的表头开始读取。
- 原始表把“北京市（92所）”这类省份标题和学校行放在同一张表。循环遇到省份标题时，把它保存到 `current_province`；遇到学校行时，把当前省份写入学校记录。
- `catalog.to_csv(..., encoding="utf-8-sig")` 输出 UTF-8 with BOM CSV，让 Windows Excel 打开中文时不乱码。

这一步不调用地理编码服务，也不猜测坐标，所以 2,952 所学校都能被安全收录。

## 2. 读取目录

打开 `app.py`。

`PROJECT_ROOT = Path(__file__).parent` 表示项目文件夹。`INSTITUTIONS_FILE` 再拼接到 `data/institutions.csv`，所以无论从哪里执行启动命令，程序都能找到目录。

`load_institutions` 做三项检查：字段完整、总数为 2,952、教育部学校标识码不重复。`@st.cache_data` 会缓存已读取的表，让每次点筛选控件时不必重复读取大 CSV。

## 3. 筛选函数

`filter_institutions` 有四个输入：完整表、选中的省份、搜索文字和办学层次列表。

- 如果选择“全部省份”，`province_matches` 会是全为 `True` 的一列；否则只保留目标省份。
- `str.contains(..., regex=False)` 按普通文字查学校名。`regex=False` 防止用户输入 `[`、`?` 之类字符时意外触发正则表达式。
- `&` 表示同时满足省份、名称和办学层次三个条件。

## 4. 为什么地图没有学校点

`make_china_map` 只设置中国中心坐标和缩放等级，并没有循环添加标记。教育部清单给出了学校所在地（城市），但没有校区级 WGS84 坐标。把城市中心当作校址会把用户带到错误位置，因此代码明确不这样做。

## 5. 页面控件

`st.selectbox` 创建省份下拉框，`st.text_input` 创建名称搜索框，`st.multiselect` 创建本科/专科筛选框。筛选结果一边通过 `st.dataframe` 显示，另一边保留无标记全国底图。

点击搜索结果中的学校卡片后，页面显示其教育部标识码、所在地、办学层次和主管部门。`find_openstreetmap_location` 只为这一次点击请求一个公开地图结果，并用缓存避免反复查询；它不会批量查询 2,952 所学校。

`make_selected_school_map` 把该次查询的结果画成临时地图。这个标记没有写入 CSV，因此不是项目确认的校址；查询失败时，“在 OpenStreetMap 中检索学校”链接仍可供手动检索。

## 6. 自动测试

`tests/test_app.py` 验证：

1. 目录确实有 2,952 所；
2. 每所学校的教育部标识码唯一；
3. “湖北省 + 武汉大学”能够筛到武汉大学；
4. 没有勾选办学层次时不会返回学校；
5. Streamlit 页面可正常渲染。

运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```
