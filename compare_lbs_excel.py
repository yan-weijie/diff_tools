# -*- coding: utf-8 -*-
"""
对比两个价格星级 LBS 实时数据明细 Excel 文件。
- 唯一键：商品编码 + 店铺ID（同键多行时按时间取最新一条）
- 自动对齐两文件列名差异（旧→新）
- 输出：仅A有 / 仅B有 / 共同主键中字段值差异 三张 sheet 到 差异结果.xlsx
- 自动检测并安装缺失依赖 pandas / openpyxl
用法：
    python demo/compare_lbs_excel.py
    或指定文件：
    python demo/compare_lbs_excel.py 文件1.xlsx 文件2.xlsx
"""
import sys
import os
import subprocess
from pathlib import Path


def ensure_deps():
    need = []
    try:
        import pandas  # noqa: F401
    except ImportError:
        need.append("pandas")
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        need.append("openpyxl")
    if need:
        print(f"[依赖] 缺少 {need}，开始安装 ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-i",
             "https://pypi.tuna.tsinghua.edu.cn/simple"] + need
        )
        print("[依赖] 安装完成")


def main():
    ensure_deps()
    import pandas as pd

    # 默认文件名（位于工作区根目录）
    default_f1 = "价格星级-LBS历史数据明细_20260602183132940384cb_new.xlsx"
    default_f2 = "价格星级LBS商品历史数据明细_2026年05月20日01.xlsx"

    # 允许命令行覆盖
    if len(sys.argv) >= 3:
        f1, f2 = sys.argv[1], sys.argv[2]
    else:
        # 脚本位于 demo/ 下，向上一级即工作区根
        root = Path(__file__).resolve().parent.parent
        f1 = str(root / default_f1)
        f2 = str(root / default_f2)

    print(f"[读取] 文件A: {f1}")
    print(f"[读取] 文件B: {f2}")
    if not (os.path.exists(f1) and os.path.exists(f2)):
        print("[错误] 文件不存在，请检查路径")
        sys.exit(1)

    df1 = pd.read_excel(f1, dtype=str).fillna("")
    df2 = pd.read_excel(f2, dtype=str).fillna("")
    print(f"[规模] A: {len(df1)} 行 / {len(df1.columns)} 列")
    print(f"[规模] B: {len(df2)} 行 / {len(df2.columns)} 列")

    # === 列名对齐：把 文件2(新) 的列名映射回 文件1(旧) 的列名以便对比 ===
    # rename_b_to_a = {
    #     "点击量band": "曝光量band",
    #     "点击量": "曝光量",
    #     "同款最低价": "同品最低价",
    #     "同款最低价sku": "同品最低价sku",
    #     "近30天销量（黄金眼）": "销量",
    #     "近30天销量（商智）": "近30天销量",
    #     "门店名称": "门店",
    # }
    # df2 = df2.rename(columns={k: v for k, v in rename_b_to_a.items() if k in df2.columns})

    # === 主键定义 ===
    key = ["商品编码", "门店ID"]
    for col in key:
        if col not in df1.columns or col not in df2.columns:
            print(f"[错误] 缺少主键列 {col}")
            sys.exit(2)

    # 同键多行：按时间取最新一条
    if "时间" in df1.columns:
        df1 = df1.sort_values("时间").drop_duplicates(key, keep="last").reset_index(drop=True)
    if "时间" in df2.columns:
        df2 = df2.sort_values("时间").drop_duplicates(key, keep="last").reset_index(drop=True)
    print(f"[去重] A 唯一主键: {len(df1)}")
    print(f"[去重] B 唯一主键: {len(df2)}")

    # === 1. 仅A / 仅B ===
    only_a = df1.merge(df2[key], on=key, how="left", indicator=True) \
        .query('_merge=="left_only"').drop(columns=["_merge"])
    only_b = df2.merge(df1[key], on=key, how="left", indicator=True) \
        .query('_merge=="left_only"').drop(columns=["_merge"])
    print(f"[差异] 仅 A 有: {len(only_a)}")
    print(f"[差异] 仅 B 有: {len(only_b)}")

    # === 2. 共同主键的字段差异 ===
    common = df1.merge(df2, on=key, suffixes=("_A", "_B"))
    print(f"[差异] 共同主键: {len(common)}")

    # 找出两边都有的对比列
    cmp_cols = [c for c in df1.columns if c not in key and c in df2.columns]
    diff_records = []
    for _, row in common.iterrows():
        diffs = {}
        for c in cmp_cols:
            va, vb = row.get(f"{c}_A", ""), row.get(f"{c}_B", "")
            if str(va) != str(vb):
                diffs[c] = f"A=[{va}] | B=[{vb}]"
        if diffs:
            rec = {k: row[k] for k in key}
            rec["差异列数"] = len(diffs)
            rec["差异详情"] = " ; ".join(f"{k}: {v}" for k, v in diffs.items())
            diff_records.append(rec)
    diff_df = pd.DataFrame(diff_records)
    print(f"[差异] 共同主键中字段值不一致: {len(diff_df)}")

    # === 3. 输出 ===
    out_path = Path(__file__).resolve().parent / "差异结果2026-06-0205.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        only_a.to_excel(w, sheet_name="仅文件A有", index=False)
        only_b.to_excel(w, sheet_name="仅文件B有", index=False)
        if not diff_df.empty:
            diff_df.to_excel(w, sheet_name="字段值差异", index=False)
        else:
            pd.DataFrame([{"结论": "共同主键的所有字段值完全一致"}]).to_excel(
                w, sheet_name="字段值差异", index=False)
        # 摘要
        pd.DataFrame([
            {"项目": "文件A行数", "值": len(df1)},
            {"项目": "文件B行数", "值": len(df2)},
            {"项目": "仅A有主键数", "值": len(only_a)},
            {"项目": "仅B有主键数", "值": len(only_b)},
            {"项目": "共同主键数", "值": len(common)},
            {"项目": "字段有差异的主键数", "值": len(diff_df)},
        ]).to_excel(w, sheet_name="摘要", index=False)

    print(f"\n[完成] 结果已写入: {out_path}")


if __name__ == "__main__":
    main()