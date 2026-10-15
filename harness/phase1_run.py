"""阶段一的单轮驱动器。给定工作区与提示词文件，跑一次无头调用并留证。

阶段三会落地完整脚手架。此处刻意只做一轮，所有中间量直接打印，
便于人工逐项核对真实行为，避免把 CLI 的差异误读成脚手架缺陷。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True, help="工作区目录，模型在此工作")
    ap.add_argument("--prompt", required=True, help="提示词文件")
    ap.add_argument("--out", required=True, help="原始流写出路径")
    ap.add_argument("--tools", required=True)
    ap.add_argument("--allowed", default="", help="额外的 Bash 允许规则，留空则不加")
    ap.add_argument("--permission-mode", default="acceptEdits")
    ap.add_argument("--model", default=agent.DEFAULT_MODEL)
    ap.add_argument("--effort", default="high")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--path-prefix", default="", help="追加到子进程 PATH 最前的目录")
    args = ap.parse_args()

    extra = ["--tools", args.tools, "--permission-mode", args.permission_mode]
    if args.allowed:
        extra += ["--allowedTools", args.allowed]

    prefix = (args.path_prefix,) if args.path_prefix else ()
    claude_bin = agent.resolve_claude_bin()
    env = agent.build_env(prefix)
    prompt = Path(args.prompt).read_text(encoding="utf-8")

    res = agent.run_once(claude_bin, Path(args.ws), env, prompt, tuple(extra),
                         model=args.model, effort=args.effort, timeout_s=args.timeout)

    raw = res["stdout原文"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(raw, encoding="utf-8", newline="\n")

    parsed = agent.parse_stream(raw)
    print(json.dumps({
        "退出码": res["退出码"],
        "超时": res["超时"],
        "耗时秒": res["耗时秒"],
        "成本USD": parsed["汇总"].get("成本USD"),
        "num_turns": parsed["汇总"].get("num_turns"),
        "工具调用直方图": parsed["工具调用直方图"],
        "Bash命令": agent.bash_commands(parsed),
        "文本长度": len(raw),
        "stderr": res["stderr原文"][:300],
    }, ensure_ascii=False, indent=2))
    print(f"原始流 {out}")


if __name__ == "__main__":
    main()
