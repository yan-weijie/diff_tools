# -*- coding: utf-8 -*-
"""
对比 new_data.json ($.data.list) 与 old_data.json ($.data.dataList) 的数据差异
new_data 使用驼峰命名, old_data 使用下划线命名
以 skuId + storeId 作为联合主键进行匹配
输出结果为 HTML 文件
"""
import json
import os
import html as html_mod

# 字段映射: new_data(camelCase) -> old_data(snake_case)
FIELD_MAP = {
    "skuId": "sku_id",
    "dt": "dt",
    "skuType": "sku_type",
    "skuName": "sku_name",
    "deptName0": "dept_name0",
    "deptName1": "dept_name1",
    "deptName2": "dept_name2",
    "deptName3": "dept_name3",
    "cname1": "cname1",
    "cname2": "cname2",
    "cname3": "cname3",
    "brandId": "brand_id",
    "brandName": "brand_name",
    "brandLevel": "brand_level",
    "goodsLevel": "goods_level",
    "shopId": "shop_id",
    "shopName": "shop_name",
    "storeId": "store_id",
    "storeName": "store_name",
    "salerErp": "saler_erp",
    "salerName": "saler_name",
    "gmvBand": "gmv_band",
    "salesBand": "sales_band",
    "pvBand": "pv_band",
    "gmv": "gmv",
    "sales": "sales",
    "pv": "pv",
    "dealPrice": "deal_price",
    "oneItemMinPrice": "one_item_min_price",
    "oneItemMinPriceSku": "one_item_min_price_sku",
    "oppMinPrice": "opp_min_price",
    "oppMinPriceUrl": "opp_min_price_url",
    "insiteValidSpuCount": "insite_valid_spu_count",
    "pricestar": "pricestar",
    "oppSkuCnt": "opp_sku_cnt",
    "scopeType": "scope_type",
    "allPriceTagDesc": "all_price_tag_desc",
    "updateTime": "update_time",
    "last30DaysSv": "last_30_days_sv",
    "operAccount": "oper_account",
    "operName": "oper_name",
    "oppMinPriceSku": "opp_min_price_sku",
    "oppMinPriceOppid": "opp_min_price_oppid",
    "oppName": "opp_name",
    "star": "star",
    "score": "score",
    "scopeTypeNum": "scope_type_num",
    "allPriceTag": "all_price_tag",
    "subSkuType": "sub_sku_type",
    "skuInfo": "sku_info",
    "dealPriceJson": "deal_price_json",
    "oneItemCnt": "one_item_cnt",
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


def esc(val, field_name=""):
    """HTML转义，None显示为null，dealPriceJson字段展示完整可视化JSON"""
    if val is None:
        return '<span style="color:#999">null</span>'
    s = str(val)
    # dealPriceJson 字段特殊处理：展示完整内容 + 格式化JSON
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


def get_type_name(val):
    """获取值的数据类型名称"""
    if val is None:
        return "null"
    t = type(val).__name__
    type_map = {"str": "string", "int": "int", "float": "float", "bool": "bool", "list": "list", "dict": "dict"}
    return type_map.get(t, t)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_file = os.path.join(base_dir, "new_data.json")
    old_file = os.path.join(base_dir, "old_data.json")

    with open(new_file, "r", encoding="utf-8") as f:
        new_data = json.load(f)
    with open(old_file, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    new_list = new_data["data"]["list"]
    old_list = old_data["data"]["dataList"]

    def build_key_new(item):
        return (str(item["skuId"]), str(item["storeId"]))

    def build_key_old(item):
        return (str(item["sku_id"]), str(item["store_id"]))

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

    # 构建HTML
    rows = []
    diff_count = 0
    for key in sorted(common_keys):
        new_item = new_dict[key]
        old_item = old_dict[key]
        has_diff = False
        field_rows = []
        for new_field, old_field in FIELD_MAP.items():
            if new_field not in new_item or old_field not in old_item:
                continue
            new_val = new_item.get(new_field)
            old_val = old_item.get(old_field)
            is_same = compare_values(new_val, old_val)
            cls = "" if is_same else ' class="diff"'
            flag = "一致" if is_same else "差异"
            if not is_same:
                has_diff = True
            field_rows.append(
                f"<tr{cls}><td>{new_field}</td><td>{esc(new_val, new_field)}</td><td>{get_type_name(new_val)}</td>"
                f"<td>{old_field}</td><td>{esc(old_val, old_field)}</td><td>{get_type_name(old_val)}</td><td>{flag}</td></tr>"
            )
        if has_diff:
            diff_count += 1
        rows.append((key, field_rows))

    # 生成HTML内容
    output_file = os.path.join(base_dir, "demo", "diff_result.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE.format(
            total_new=len(new_list),
            total_old=len(old_list),
            new_dedup=len(new_dict),
            old_dedup=len(old_dict),
            only_new=len(only_in_new),
            only_old=len(only_in_old),
            common=len(common_keys),
            diff_count=diff_count,
            tables=build_tables(rows, only_in_new, new_dict, only_in_old, old_dict),
        ))
    print(f"对比结果已输出到: {output_file}")


def build_tables(rows, only_in_new, new_dict, only_in_old, old_dict):
    parts = []
    # 仅存在于new
    if only_in_new:
        parts.append("<h2>仅存在于 new_data 中的记录</h2><ul>")
        for key in sorted(only_in_new):
            item = new_dict[key]
            parts.append(f"<li>skuId={key[0]}, storeId={key[1]}, skuName={esc(item.get('skuName'))}</li>")
        parts.append("</ul>")
    # 仅存在于old
    if only_in_old:
        parts.append("<h2>仅存在于 old_data 中的记录</h2><ul>")
        for key in sorted(only_in_old):
            item = old_dict[key]
            parts.append(f"<li>sku_id={key[0]}, store_id={key[1]}, sku_name={esc(item.get('sku_name'))}</li>")
        parts.append("</ul>")
    # 共有记录对比
    for key, field_rows in rows:
        parts.append(f'<details><summary>skuId={key[0]} | storeId={key[1]}</summary>')
        parts.append("<table><thead><tr><th>new_data字段</th><th>new值</th><th>new类型</th>"
                     "<th>old_data字段</th><th>old值</th><th>old类型</th><th>结果</th></tr></thead><tbody>")
        parts.append("\n".join(field_rows))
        parts.append("</tbody></table></details>")
    return "\n".join(parts)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>JSON数据对比结果</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; background: #f5f5f5; }}
h1 {{ color: #333; }}
.summary {{ background: #fff; padding: 15px; border-radius: 6px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
.summary span {{ margin-right: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-size: 13px; }}
th {{ background: #4a90d9; color: #fff; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
tr.diff {{ background: #ffe0e0 !important; font-weight: bold; }}
h3 {{ margin-top: 25px; color: #4a90d9; }}
pre.json-view {{ background: #f0f4f8; border: 1px solid #ccc; border-radius: 4px; padding: 8px; margin: 0; font-size: 12px; white-space: pre-wrap; word-break: break-all; max-width: 500px; }}
details {{ margin-bottom: 10px; border: 1px solid #ddd; border-radius: 6px; background: #fff; }}
details summary {{ cursor: pointer; padding: 10px 15px; font-weight: bold; font-size: 14px; color: #4a90d9; background: #f7f9fc; border-radius: 6px; }}
details summary:hover {{ background: #eaf1fb; }}
details[open] summary {{ border-bottom: 1px solid #ddd; border-radius: 6px 6px 0 0; }}
details table {{ margin: 0; box-shadow: none; }}
</style></head><body>
<h1>JSON 数据对比结果</h1>
<div class="summary">
<p><span>new_data.list 记录数: <b>{total_new}</b></span>
<span>old_data.dataList 记录数: <b>{total_old}</b></span></p>
<p><span>联合主键去重 new: <b>{new_dedup}</b></span>
<span>联合主键去重 old: <b>{old_dedup}</b></span></p>
<p><span>仅存在于 new: <b>{only_new}</b></span>
<span>仅存在于 old: <b>{only_old}</b></span>
<span>共有可比较: <b>{common}</b></span></p>
<p style="color:red;">存在字段差异的记录: <b>{diff_count}/{common}</b></p>
</div>
{tables}
</body></html>"""


if __name__ == "__main__":
    main()