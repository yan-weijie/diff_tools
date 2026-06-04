# -*- coding: utf-8 -*-
"""
JSON 数据对比 - 后端 API 服务
启动: python demo/server/app.py
端口: http://localhost:5000
"""
import io
import json
import re
import csv
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===== 字段映射: new_data(camelCase) -> old_data(snake_case) =====
FIELD_MAP = {
    "skuId": "sku_id", "dt": "dt", "skuType": "sku_type", "skuName": "sku_name",
    "deptName0": "dept_name0", "deptName1": "dept_name1", "deptName2": "dept_name2",
    "deptName3": "dept_name3", "cname1": "cname1", "cname2": "cname2", "cname3": "cname3",
    "brandId": "brand_id", "brandName": "brand_name", "brandLevel": "brand_level",
    "goodsLevel": "goods_level", "shopId": "shop_id", "shopName": "shop_name",
    "storeId": "store_id", "storeName": "store_name", "salerErp": "saler_erp",
    "salerName": "saler_name", "gmvBand": "gmv_band", "salesBand": "sales_band",
    "pvBand": "pv_band", "gmv": "gmv", "sales": "sales", "pv": "pv",
    "dealPrice": "deal_price", "oneItemMinPrice": "one_item_min_price",
    "oneItemMinPriceSku": "one_item_min_price_sku", "oppMinPrice": "opp_min_price",
    "oppMinPriceUrl": "opp_min_price_url", "insiteValidSpuCount": "insite_valid_spu_count",
    "pricestar": "pricestar", "oppSkuCnt": "opp_sku_cnt", "scopeType": "scope_type",
    "allPriceTagDesc": "all_price_tag_desc", "updateTime": "update_time",
    "last30DaysSv": "last_30_days_sv", "operAccount": "oper_account", "operName": "oper_name",
    "oppMinPriceSku": "opp_min_price_sku", "oppMinPriceOppid": "opp_min_price_oppid",
    "oppName": "opp_name", "star": "star", "score": "score",
    "scopeTypeNum": "scope_type_num", "allPriceTag": "all_price_tag",
    "subSkuType": "sub_sku_type", "skuInfo": "sku_info",
    "dealPriceJson": "deal_price_json", "oneItemCnt": "one_item_cnt",
    "status": "status", "tags": "tags",
}

# ===== 通用工具 =====
def camel_to_snake(s):
    return re.sub(r'([A-Z])', lambda m: '_' + m.group(1).lower(), s)


def snake_to_camel(s):
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def normalize_value(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip()
    return val


def compare_values(new_val, old_val):
    nv, ov = normalize_value(new_val), normalize_value(old_val)
    if nv is None and ov is None:
        return True
    if nv is None or ov is None:
        return False
    try:
        return float(nv) == float(ov)
    except (ValueError, TypeError):
        pass
    return str(nv) == str(ov)


def get_type_name(val):
    if val is None:
        return "null"
    name = type(val).__name__
    return {"str": "string", "int": "int", "float": "float",
            "bool": "bool", "list": "array", "dict": "object"}.get(name, name)


def extract_by_path(data, path):
    if not path or not path.strip() or path.strip() == "$":
        return data
    p = path.strip().lstrip("$").lstrip(".")
    tokens = re.findall(r'[^\.\[\]]+|\[\d+\]', p)
    obj = data
    for token in tokens:
        if not token:
            continue
        m = re.match(r'^\[(\d+)\]$', token)
        if m:
            obj = obj[int(m.group(1))]
        else:
            obj = obj[token]
    return obj


def find_old_field(new_field, old_obj):
    """根据新字段名在旧对象中查找对应字段（映射表 -> 直接 -> snake/camel 互转）"""
    if new_field in FIELD_MAP and FIELD_MAP[new_field] in old_obj:
        return FIELD_MAP[new_field]
    if new_field in old_obj:
        return new_field
    snake = camel_to_snake(new_field)
    if snake in old_obj:
        return snake
    camel = snake_to_camel(new_field)
    if camel in old_obj:
        return camel
    return None


def expand_json_ignore_fields(fields):
    aliases = set()
    for field in fields:
        aliases.add(field)
        aliases.add(camel_to_snake(field))
        aliases.add(snake_to_camel(field))
        if field in FIELD_MAP:
            aliases.add(FIELD_MAP[field])
        for new_field, old_field in FIELD_MAP.items():
            if field == old_field:
                aliases.add(new_field)
    return aliases


def build_key(item, primary_keys=None):
    """构造记录主键。
    - primary_keys: 用户指定的主键字段列表（如 ["skuId", "storeId"]），
      支持自动 camel↔snake 互转匹配（即输入 skuId 也能匹配到 sku_id）。
    - 若未指定或全部字段都取不到值，回退到默认 skuId+storeId 联合主键；
      仍取不到则返回 '__single__'，用于支持单对象对比场景。
    """
    if not isinstance(item, dict):
        return "__single__"

    def get_field(obj, field):
        """从 obj 中按 field 名取值，自动尝试 camel/snake 互转"""
        if field in obj:
            return obj[field]
        snake = camel_to_snake(field)
        if snake in obj:
            return obj[snake]
        camel = snake_to_camel(field)
        if camel in obj:
            return obj[camel]
        return None

    if primary_keys:
        vals = [get_field(item, k) for k in primary_keys]
        if any(v is not None for v in vals):
            return "_".join("" if v is None else str(v) for v in vals)

    # 默认主键
    sku = item.get("skuId", item.get("sku_id"))
    store = item.get("storeId", item.get("store_id"))
    if sku is None and store is None:
        return "__single__"
    return f"{sku}_{store}"


def parse_separated(value):
    """Parse comma/plus/space separated text or list values."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [s.strip() for s in re.split(r"[,+\s]+", str(value or "")) if s.strip()]


def parse_excel_column_aliases(text):
    """Parse B-to-A column aliases, e.g. '点击量=曝光量'."""
    aliases = {}
    for raw in re.split(r"[\n,;]+", str(text or "")):
        line = raw.strip()
        if not line:
            continue
        if "=" in line:
            left, right = line.split("=", 1)
        elif "->" in line:
            left, right = line.split("->", 1)
        elif ":" in line:
            left, right = line.split(":", 1)
        else:
            continue
        b_col, a_col = left.strip(), right.strip()
        if b_col and a_col:
            aliases[b_col] = a_col
    return aliases


def compare_excel_frames(df_a, df_b, key_cols, time_col="", ignore_cols=None, column_aliases=None):
    """Compare two Excel data frames using compare_lbs_excel.py's core flow."""
    ignore_cols = set(ignore_cols or [])
    if column_aliases:
        df_b = df_b.rename(columns={k: v for k, v in column_aliases.items() if k in df_b.columns})

    missing = [col for col in key_cols if col not in df_a.columns or col not in df_b.columns]
    if missing:
        raise ValueError("缺少主键列: " + ", ".join(missing))

    if time_col and time_col in df_a.columns:
        df_a = df_a.sort_values(time_col).drop_duplicates(key_cols, keep="last").reset_index(drop=True)
    if time_col and time_col in df_b.columns:
        df_b = df_b.sort_values(time_col).drop_duplicates(key_cols, keep="last").reset_index(drop=True)

    only_a = (
        df_a.merge(df_b[key_cols], on=key_cols, how="left", indicator=True)
        .query('_merge=="left_only"')
        .drop(columns=["_merge"])
    )
    only_b = (
        df_b.merge(df_a[key_cols], on=key_cols, how="left", indicator=True)
        .query('_merge=="left_only"')
        .drop(columns=["_merge"])
    )
    common = df_a.merge(df_b, on=key_cols, suffixes=("_A", "_B"))

    cmp_cols = [
        c for c in df_a.columns
        if c not in key_cols and c not in ignore_cols and c in df_b.columns
    ]
    diff_records = []
    for _, row in common.iterrows():
        field_diffs = []
        for col in cmp_cols:
            va, vb = row.get(f"{col}_A", ""), row.get(f"{col}_B", "")
            if str(va) != str(vb):
                field_diffs.append({"field": col, "a": va, "b": vb})
        if field_diffs:
            key_values = {k: row[k] for k in key_cols}
            diff_records.append({
                "key": " / ".join(str(key_values[k]) for k in key_cols),
                "keyValues": key_values,
                "diffCount": len(field_diffs),
                "diffs": field_diffs,
                "detail": " ; ".join(
                    f"{d['field']}: A=[{d['a']}] | B=[{d['b']}]" for d in field_diffs
                ),
            })

    return {
        "totalA": len(df_a),
        "totalB": len(df_b),
        "onlyA": only_a.to_dict(orient="records"),
        "onlyB": only_b.to_dict(orient="records"),
        "commonCount": len(common),
        "diffCount": len(diff_records),
        "diffRecords": diff_records,
        "keyColumns": key_cols,
        "compareColumns": cmp_cols,
        "ignoredColumns": sorted(ignore_cols),
    }


def excel_result_to_workbook(result):
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("缺少 pandas/openpyxl 依赖，请先安装后再导出 Excel") from exc

    summary_df = pd.DataFrame([
        {"项目": "文件A行数", "值": result.get("totalA", 0)},
        {"项目": "文件B行数", "值": result.get("totalB", 0)},
        {"项目": "仅A有主键数", "值": len(result.get("onlyA", []))},
        {"项目": "仅B有主键数", "值": len(result.get("onlyB", []))},
        {"项目": "共同主键数", "值": result.get("commonCount", 0)},
        {"项目": "字段有差异的主键数", "值": result.get("diffCount", 0)},
    ])
    diff_df = pd.DataFrame([
        {
            **rec.get("keyValues", {}),
            "差异列数": rec.get("diffCount", 0),
            "差异详情": rec.get("detail", ""),
        }
        for rec in result.get("diffRecords", [])
    ])
    if diff_df.empty:
        diff_df = pd.DataFrame([{"结论": "共同主键的所有字段值完全一致"}])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(result.get("onlyA", [])).to_excel(writer, sheet_name="仅文件A有", index=False)
        pd.DataFrame(result.get("onlyB", [])).to_excel(writer, sheet_name="仅文件B有", index=False)
        diff_df.to_excel(writer, sheet_name="字段值差异", index=False)
        summary_df.to_excel(writer, sheet_name="摘要", index=False)
    output.seek(0)
    return output


# ===== API: 格式化 / 校验 =====
@app.route("/api/format", methods=["POST"])
def format_json():
    raw = (request.json or {}).get("text", "")
    try:
        obj = json.loads(raw)
        return jsonify({"ok": True, "formatted": json.dumps(obj, ensure_ascii=False, indent=2)})
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"第{e.lineno}行第{e.colno}列 - {e.msg}"})


@app.route("/api/validate", methods=["POST"])
def validate_json():
    raw = (request.json or {}).get("text", "")
    try:
        json.loads(raw)
        return jsonify({"ok": True, "message": "JSON格式正确"})
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"第{e.lineno}行第{e.colno}列 - {e.msg}"})


# ===== API: 对比 =====
@app.route("/api/compare", methods=["POST"])
def compare_json():
    data = request.json or {}
    new_text = data.get("new_json", "")
    old_text = data.get("old_json", "")
    new_path = data.get("new_path", "$.data.list")
    old_path = data.get("old_path", "$.data.dataList")
    # 主键/忽略字段：支持字符串（逗号/加号/空格分隔）或数组
    primary_keys = parse_separated(data.get("primary_keys", data.get("primary_key", "")))
    ignore_fields = expand_json_ignore_fields(parse_separated(data.get("ignore_fields", "")))

    try:
        new_data = json.loads(new_text)
        old_data = json.loads(old_text)
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"JSON解析失败: {str(e)}"})

    try:
        new_list = extract_by_path(new_data, new_path)
        old_list = extract_by_path(old_data, old_path)
    except (KeyError, TypeError, IndexError) as e:
        return jsonify({"ok": False, "error": f"路径提取失败: {str(e)}"})

    if not isinstance(new_list, list) or not isinstance(old_list, list):
        # 允许提取结果是单个对象，自动包装为单元素列表进行对比
        if isinstance(new_list, dict) and isinstance(old_list, dict):
            new_list = [new_list]
            old_list = [old_list]
        elif isinstance(new_list, dict) and isinstance(old_list, list):
            new_list = [new_list]
        elif isinstance(new_list, list) and isinstance(old_list, dict):
            old_list = [old_list]
        else:
            return jsonify({
                "ok": False,
                "error": "JsonPath 提取结果必须是数组或对象，当前为：%s / %s"
                         % (type(new_list).__name__, type(old_list).__name__),
            })

    return jsonify({"ok": True, "result": build_compare_result(new_list, old_list, primary_keys, ignore_fields)})


@app.route("/api/compare-excel", methods=["POST"])
def compare_excel():
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")
    if not file_a or not file_b:
        return jsonify({"ok": False, "error": "请上传文件A和文件B"})

    key_cols = parse_separated(request.form.get("key_columns", "商品编码,门店ID"))
    if not key_cols:
        return jsonify({"ok": False, "error": "请至少配置一个主键列"})

    time_col = (request.form.get("time_column") or "时间").strip()
    ignore_cols = parse_separated(request.form.get("ignore_columns", ""))
    aliases = parse_excel_column_aliases(request.form.get("column_aliases", ""))

    try:
        import pandas as pd
    except ImportError:
        return jsonify({"ok": False, "error": "缺少 pandas/openpyxl 依赖，请先安装后再使用 Excel 对比"})

    try:
        df_a = pd.read_excel(file_a, dtype=str).fillna("")
        df_b = pd.read_excel(file_b, dtype=str).fillna("")
        result = compare_excel_frames(
            df_a,
            df_b,
            key_cols=key_cols,
            time_col=time_col,
            ignore_cols=ignore_cols,
            column_aliases=aliases,
        )
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Excel 对比失败: {e}"})

    return jsonify({"ok": True, "result": result})


def build_compare_result(new_list, old_list, primary_keys=None, ignore_fields=None):
    ignore_fields = set(ignore_fields or [])
    new_dict = {build_key(it, primary_keys): it for it in new_list}
    old_dict = {build_key(it, primary_keys): it for it in old_list}

    only_in_new = [{"key": k, "record": new_dict[k]} for k in new_dict if k not in old_dict]
    only_in_old = [{"key": k, "record": old_dict[k]} for k in old_dict if k not in new_dict]
    common_keys = [k for k in new_dict if k in old_dict]

    comparisons = []
    diff_count = 0
    for key in sorted(common_keys):
        ni, oi = new_dict[key], old_dict[key]
        fields = []
        has_diff = False
        seen_old_fields = set()
        # 以 new 字段为驱动
        for nf, nv in ni.items():
            of = find_old_field(nf, oi)
            if nf in ignore_fields or (of and of in ignore_fields):
                if of:
                    seen_old_fields.add(of)
                continue
            ov = oi.get(of) if of else None
            same = of is not None and compare_values(nv, ov)
            if not same:
                has_diff = True
            if of:
                seen_old_fields.add(of)
            fields.append({
                "newField": nf, "newVal": nv, "newType": get_type_name(nv),
                "oldField": of or "(缺失)", "oldVal": ov, "oldType": get_type_name(ov) if of else "-",
                "same": same,
            })
        # 补充：旧字段中尚未对应的
        for of, ov in oi.items():
            if of in seen_old_fields or of in ignore_fields:
                continue
            fields.append({
                "newField": "(缺失)", "newVal": None, "newType": "-",
                "oldField": of, "oldVal": ov, "oldType": get_type_name(ov),
                "same": False,
            })
            has_diff = True
        if has_diff:
            diff_count += 1
        comparisons.append({"key": key, "hasDiff": has_diff, "fields": fields})

    return {
        "totalNew": len(new_list),
        "totalOld": len(old_list),
        "onlyInNew": only_in_new,
        "onlyInOld": only_in_old,
        "commonCount": len(common_keys),
        "diffCount": diff_count,
        "comparisons": comparisons,
    }


# ===== API: 导出 CSV =====
@app.route("/api/export", methods=["POST"])
def export_csv():
    payload = request.json or {}
    result = payload.get("result")
    if not result:
        return jsonify({"ok": False, "error": "缺少对比结果"}), 400

    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM for Excel
    writer = csv.writer(buf)
    writer.writerow(["主键", "新字段", "新值", "新类型", "旧字段", "旧值", "旧类型", "是否一致"])
    for comp in result.get("comparisons", []):
        for f in comp.get("fields", []):
            writer.writerow([
                comp["key"], f["newField"], f["newVal"], f["newType"],
                f["oldField"], f["oldVal"], f["oldType"],
                "一致" if f["same"] else "差异",
            ])
    for item in result.get("onlyInNew", []):
        writer.writerow([item["key"], "仅新存在", json.dumps(item["record"], ensure_ascii=False), "-", "-", "-", "-", "差异"])
    for item in result.get("onlyInOld", []):
        writer.writerow([item["key"], "-", "-", "-", "仅旧存在", json.dumps(item["record"], ensure_ascii=False), "-", "差异"])

    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=compare-result.csv"},
    )


@app.route("/api/export-excel-result", methods=["POST"])
def export_excel_result():
    payload = request.json or {}
    result = payload.get("result")
    if not result:
        return jsonify({"ok": False, "error": "缺少 Excel 对比结果"}), 400

    try:
        output = excel_result_to_workbook(result)
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=excel-compare-result.xlsx"},
    )


if __name__ == "__main__":
    print("JSON 对比 API 服务: http://localhost:5000")
    app.run(host="0.0.0.0", port=5001, debug=True)
