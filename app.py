# -*- coding: utf-8 -*-
"""
JSON数据对比Web服务
本地部署: python demo/app.py
访问: http://localhost:5000
"""
import json
import os
import html as html_mod
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# 字段映射: new_data(camelCase) -> old_data(snake_case)
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
}


def normalize_value(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip()
    return val


def compare_values(new_val, old_val):
    nv = normalize_value(new_val)
    ov = normalize_value(old_val)
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
    t = type(val).__name__
    type_map = {"str": "string", "int": "int", "float": "float", "bool": "bool", "list": "list", "dict": "dict"}
    return type_map.get(t, t)


def esc(val, field_name=""):
    if val is None:
        return '<span style="color:#999">null</span>'
    s = str(val)
    if field_name in ("dealPriceJson", "deal_price_json"):
        try:
            obj = json.loads(s)
            formatted = json.dumps(obj, ensure_ascii=False, indent=2)
            return f'<pre class="json-view">{html_mod.escape(formatted)}</pre>'
        except (json.JSONDecodeError, TypeError):
            return f'<pre class="json-view">{html_mod.escape(s)}</pre>'
    if len(s) > 80:
        s = s[:80] + "..."
    return html_mod.escape(s)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/format", methods=["POST"])
def format_json():
    """格式化JSON"""
    data = request.json
    raw = data.get("text", "")
    try:
        obj = json.loads(raw)
        formatted = json.dumps(obj, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "formatted": formatted})
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"JSON格式错误: {str(e)}"})


@app.route("/api/validate", methods=["POST"])
def validate_json():
    """校验JSON格式"""
    data = request.json
    raw = data.get("text", "")
    try:
        json.loads(raw)
        return jsonify({"ok": True, "message": "JSON格式正确"})
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"JSON格式错误: 第{e.lineno}行第{e.colno}列 - {e.msg}"})


@app.route("/api/compare", methods=["POST"])
def compare_json():
    """对比两个JSON数据"""
    data = request.json
    new_text = data.get("new_json", "")
    old_text = data.get("old_json", "")
    new_path = data.get("new_path", "$.data.list")
    old_path = data.get("old_path", "$.data.dataList")

    try:
        new_data = json.loads(new_text)
        old_data = json.loads(old_text)
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": f"JSON解析失败: {str(e)}"})

    # 根据路径提取数据
    try:
        new_list = extract_by_path(new_data, new_path)
        old_list = extract_by_path(old_data, old_path)
    except (KeyError, TypeError, IndexError) as e:
        return jsonify({"ok": False, "error": f"路径提取失败: {str(e)}"})

    # 生成对比HTML
    result_html = build_compare_html(new_list, old_list)
    return jsonify({"ok": True, "html": result_html})


import re as _re

def extract_by_path(data, path):
    path = path.strip().lstrip("$").lstrip(".")
    tokens = _re.findall(r'[^\.\[\]]+|\[\d+\]', path)
    obj = data
    for token in tokens:
        if not token:
            continue
        idx_m = _re.match(r'^\[(\d+)\]$', token)
        if idx_m:
            obj = obj[int(idx_m.group(1))]
        else:
            obj = obj[token]
    return obj


def build_compare_html(new_list, old_list):
    def build_key_new(item):
        sku = item.get("skuId") or item.get("sku_id")
        store = item.get("storeId") or item.get("store_id")
        return (str(sku), str(store))

    def build_key_old(item):
        sku = item.get("sku_id") or item.get("skuId")
        store = item.get("store_id") or item.get("storeId")
        return (str(sku), str(store))

    new_dict = {}
    for item in new_list:
        new_dict[build_key_new(item)] = item
    old_dict = {}
    for item in old_list:
        old_dict[build_key_old(item)] = item

    new_keys = set(new_dict.keys())
    old_keys = set(old_dict.keys())
    only_in_new = new_keys - old_keys
    only_in_old = old_keys - new_keys
    common_keys = new_keys & old_keys

    parts = []
    diff_count = 0
    parts.append('<div class="summary">')
    parts.append(f'<p><span>new_data: <b>{len(new_list)}</b></span><span>old_data: <b>{len(old_list)}</b></span></p>')
    parts.append(f'<p><span>仅new: <b>{len(only_in_new)}</b></span><span>仅old: <b>{len(only_in_old)}</b></span><span>共有: <b>{len(common_keys)}</b></span></p>')

    if only_in_new:
        parts.append("<h3>仅存在于 new_data</h3><ul>")
        for key in sorted(only_in_new):
            item = new_dict[key]
            name = item.get("skuName") or item.get("sku_name") or ""
            parts.append(f"<li>skuId={key[0]}, storeId={key[1]}, name={html_mod.escape(str(name))}</li>")
        parts.append("</ul>")
    if only_in_old:
        parts.append("<h3>仅存在于 old_data</h3><ul>")
        for key in sorted(only_in_old):
            item = old_dict[key]
            name = item.get("sku_name") or item.get("skuName") or ""
            parts.append(f"<li>sku_id={key[0]}, store_id={key[1]}, name={html_mod.escape(str(name))}</li>")
        parts.append("</ul>")

    for key in sorted(common_keys):
        new_item = new_dict[key]
        old_item = old_dict[key]
        has_diff = False
        field_rows = []
        for nf, of in FIELD_MAP.items():
            if nf not in new_item or of not in old_item:
                continue
            nv = new_item.get(nf)
            ov = old_item.get(of)
            is_same = compare_values(nv, ov)
            cls = "" if is_same else ' class="diff"'
            flag = "一致" if is_same else "差异"
            if not is_same:
                has_diff = True
            field_rows.append(f"<tr{cls}><td>{nf}</td><td>{esc(nv, nf)}</td><td>{get_type_name(nv)}</td><td>{of}</td><td>{esc(ov, of)}</td><td>{get_type_name(ov)}</td><td>{flag}</td></tr>")
        if has_diff:
            diff_count += 1
        parts.append(f'<details><summary>skuId={key[0]} | storeId={key[1]}</summary>')
        parts.append('<table><thead><tr><th>new字段</th><th>new值</th><th>new类型</th><th>old字段</th><th>old值</th><th>old类型</th><th>结果</th></tr></thead><tbody>')
        parts.append("\n".join(field_rows))
        parts.append("</tbody></table></details>")

    parts.insert(3, f'<p style="color:red;">差异记录: <b>{diff_count}/{len(common_keys)}</b></p></div>')
    return "\n".join(parts)


if __name__ == "__main__":
    print("启动JSON对比服务: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

