"""阶段一的提示词渲染。五份二轮提示词共用同一份失败信息，只差一行。

用法
    python harness/phase1_prompts.py --block <失败信息文件> --outdir <目录>

产出 round1.txt 与 c1.txt 至 c5.txt。脚本自带一条断言，渲染后逐行比较，
除第一行外必须完全相同。任一条件若多带一行说明文字，此处即报错。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROUND1 = "工作区里有测试未通过。请修复，使全部测试通过。"

# 五条反馈逐字取自 REQUIRE.md，不得改写。
FEEDBACK: list[tuple[str, str]] = [
    ("c1_纯继续", "这是当前测试失败信息，请继续修复。"),
    ("c2_中性反馈", "测试仍未通过，请继续检查。"),
    ("c3_方法指引", "测试仍未通过，请先阅读错误日志，并做最小必要修改。"),
    ("c4_负面反馈", "我对刚才的修改很不满意，请继续修复。"),
    ("c5_负面反馈加方法指引", "我对刚才的修改很不满意，请先阅读错误日志，并做最小必要修改。"),
]

HEADER = "以下是当前测试失败信息。"


def render(lead: str, block: str) -> str:
    return f"{lead}\n\n{HEADER}\n\n{block}\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    block = Path(args.block).read_text(encoding="utf-8").strip()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "round1.txt").write_text(render(ROUND1, block),
                                       encoding="utf-8", newline="\n")

    texts = {}
    for name, feedback in FEEDBACK:
        text = render(feedback, block)
        (outdir / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
        texts[name] = text.splitlines()

    names = list(texts)
    base = texts[names[0]]
    for name in names[1:]:
        lines = texts[name]
        assert len(lines) == len(base), f"{name} 行数与首份不同"
        diff = [i for i, (x, y) in enumerate(zip(base, lines)) if x != y]
        assert diff == [0], f"{name} 与首份的差异行不是唯一的第一行，而是 {diff}"
        assert base[0] != lines[0], f"{name} 的反馈行与首份相同"

    print(f"五份提示词渲染完成，逐行比较只差第 1 行，失败信息行数 {len(base) - 2}")
    for name, _ in FEEDBACK:
        print(f"  {name}")


if __name__ == "__main__":
    main()
