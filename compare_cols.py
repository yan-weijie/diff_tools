# -*- coding: utf-8 -*-
"""
对比两个 Excel 文件的列名差异。
- 仅读取表头（nrows=0），快速且省内存
- 输出：各自全部列名 / 仅A有列 / 仅B有列 / 共有列顺序差异
- 结果同时打印到控制台并写入 _cols_diff.txt
- 自动检测并安装缺失依赖 pandas / openpyxl
用法：
    python demo/compare_cols.py
    或指定文件：
    python demo/compare_cols.py 文件1.xlsx 文件2.xlsx
"""
import sys
import os
import subprocess
import traceback
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


def build_report(c1, c2):
    """根据两份列名列表构造报告文本行。"""
    lines = []
    lines.append(f"===== 文件A列名 (共 {len(c1)} 列) =====")
    for i, c in enumerate(c1, 1):
        lines.append(f"{i:3d}. {c}")

    lines.append("")
    lines.append(f"===== 文件B列名 (共 {len(c2)} 列) =====")
    for i, c in enumerate(c2, 1):
        lines.append(f"{i:3d}. {c}")

    s1, s2 = set(c1), set(c2)
    only_a = [c for c in c1 if c not in s2]
    only_b = [c for c in c2 if c not in s1]

    lines.append("")
    lines.append(f"===== 仅文件A存在 ({len(only_a)} 项) =====")
    for c in only_a:
        lines.append(f" - {c}")

    lines.append("")
    lines.append(f"===== 仅文件B存在 ({len(only_b)} 项) =====")
    for c in only_b:
        lines.append(f" - {c}")

    lines.append("")
    lines.append("===== 共有列顺序差异 =====")
    common_a = [c for c in c1 if c in s2]
    common_b = [c for c in c2 if c in s1]
    if common_a == common_b:
        lines.append("共有列顺序完全一致")
    else:
        for i, (a, b) in enumerate(zip(common_a, common_b), 1):
            flag = "" if a == b else "  <-- 差异"
            lines.append(f"{i:3d}. A={a} | B={b}{flag}")

    return lines, only_a, only_b


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

    # 仅读取表头
    df1 = pd.read_excel(f1, nrows=0)
    df2 = pd.read_excel(f2, nrows=0)
    c1 = list(df1.columns)
    c2 = list(df2.columns)
    print(f"[规模] A 列数: {len(c1)}")
    print(f"[规模] B 列数: {len(c2)}")

    # 构造报告
    lines, only_a, only_b = build_report(c1, c2)
    print(f"[差异] 仅 A 有列: {len(only_a)}")
    print(f"[差异] 仅 B 有列: {len(only_b)}")

    # 输出文件
    out_path = Path(__file__).resolve().parent / "_cols_diff.txt"
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    print(f"\n[完成] 结果已写入: {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        print(err)
        # 异常信息同样落盘，便于排查
        fallback = Path(__file__).resolve().parent / "_cols_diff.txt"
        try:
            with open(fallback, "w", encoding="utf-8") as fp:
                fp.write(err)
        except Exception:
            pass
        sys.exit(99)