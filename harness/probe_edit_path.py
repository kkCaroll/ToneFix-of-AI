"""核验模型改代码时走编辑工具还是走 shell。

要回答的问题只有一条。`can_run` 臂的 Bash 权限已证实是全面放开的，
模型若用 sed 或 python -c 直接改文件，工具调用统计会失真，
两臂之间按 git diff 统计的修改规模也不再可比。

做法是给两个缺陷形状各建一个带单次提交的工作区，两个臂各跑两次，
逐次记录工具调用直方图、Bash 命令原文与状态、目标提交的 numstat 与测试结果。

判定口径为 v2。v1 曾用一份宽松的关键词表标记疑似写文件，把普通命令
`python -m pytest -q` 也算了进去，导致六次误判。v2 改用正则匹配真正的写入形态，
并把因工具未启用而未执行的 Bash 调用单独计数。`--rederive` 可以只读已存原始流
重算全部判定，不产生新的调用。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parents[1]
RECORD = PROJ / "RECORD" / "probe_edit_path.json"
MODEL = "deepseek-v4-pro"
REPLICAS = 2
JUDGE_VERSION = "v2"

EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
BASE_TOOLS = "Read,Glob,Grep,Edit,Write"

ARMS: dict[str, tuple[str, ...]] = {
    "no_run": ("--tools", BASE_TOOLS, "--permission-mode", "acceptEdits"),
    "can_run": ("--tools", BASE_TOOLS + ",Bash", "--permission-mode", "acceptEdits",
                "--allowedTools", "Bash(python -m pytest:*)"),
}

# 只匹配真正的写入形态。裸的 `python -` 或 `> ` 一律不匹配，v1 的误判即由此而来。
WRITE_PATTERNS: list[tuple[str, str]] = [
    (r"\bsed\b[^\n|;&]*\s-i", "sed 原地改写"),
    (r"\bperl\b[^\n|;&]*\s-[a-zA-Z]*i", "perl 原地改写"),
    (r"(?<![0-9&])>>?\s*(?!&|\|)(?!/dev/null|\bnul\b)\S", "重定向写入"),
    (r"\btee\b", "tee 写入"),
    (r"\b(set|add)-content\b|\bout-file\b", "PowerShell 写入"),
    (r"\btruncate\b", "truncate"),
    (r"\bgit\s+apply\b|\bpatch\b\s+-p", "补丁应用"),
]
PY_WRITE = re.compile(r"python[0-9.]*\s+(-c|-)\b[^\n]*(\bopen\s*\(|\bwrite\s*\(|\bw\b['\"])",
                      re.IGNORECASE)

TOOL_DISABLED = "no such tool available"
TOOL_DENIED = ("requires approval", "permission denied", "not allowed")

TASKS: dict[str, dict[str, str]] = {
    "median": {
        "calc.py": '"""统计工具。"""\n\n\ndef median(values):\n'
                   '    """返回中位数。"""\n'
                   "    ordered = sorted(values)\n"
                   "    n = len(ordered)\n"
                   "    return ordered[n // 2]\n",
        "test_calc.py": "from calc import median\n\n\n"
                        "def test_median_odd_length():\n"
                        "    assert median([3, 1, 2]) == 2\n\n\n"
                        "def test_median_even_length():\n"
                        "    assert median([1, 2, 3, 4]) == 2.5\n",
    },
    "regex": {
        "textutil.py": '"""文本处理工具。"""\n\nimport re\n\n\n'
                       "def count_keyword(text, keyword):\n"
                       '    """统计关键词出现的次数，不区分大小写。"""\n'
                       "    return len(re.findall(keyword, text))\n",
        "test_textutil.py": "from textutil import count_keyword\n\n\n"
                            "def test_count_keyword_case_insensitive():\n"
                            '    assert count_keyword("Bug bug BUG", "bug") == 3\n',
    },
}

GITIGNORE = "__pycache__/\n.pytest_cache/\n"

PROMPT_TEMPLATE = "工作区里有测试未通过。请修复，使全部测试通过。\n\n以下是失败信息。\n\n{block}"


def ensure_venv(root: Path) -> Path:
    """建立装好 pytest 的探针环境。放在一次性根目录下，不污染项目树。"""
    venv = root / "venv"
    py = venv / "Scripts" / "python.exe"
    if not py.is_file():
        subprocess.run(["uv", "venv", str(venv)], check=True, capture_output=True)
        subprocess.run(["uv", "pip", "install", "--python", str(py), "pytest"],
                       check=True, capture_output=True)
    return py


def run_pytest(py: Path, ws: Path) -> tuple[bool, str]:
    """自己跑测试，不依赖模型是否运行过。判分与失败信息都由脚手架产生。"""
    proc = subprocess.run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=str(ws), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    block = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, block


def git(ws: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                          cwd=str(ws), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.stdout.strip()


def materialize(ws: Path, files: dict[str, str]) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (ws / name).write_text(text, encoding="utf-8", newline="\n")
    (ws / ".gitignore").write_text(GITIGNORE, encoding="utf-8", newline="\n")
    git(ws, "init", "-q", "-b", "main")
    git(ws, "config", "core.autocrlf", "false")
    git(ws, "config", "user.name", "probe")
    git(ws, "config", "user.email", "probe@local")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "起点")


def numstat(ws: Path) -> list[dict]:
    """相对起点提交的逐文件改动。忽略文件不进索引，故缓存与字节码不参与统计。"""
    git(ws, "add", "-A")
    rows = []
    for line in git(ws, "diff", "--cached", "--numstat", "HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        rows.append({"文件": path,
                     "增": int(added) if added.isdigit() else added,
                     "删": int(deleted) if deleted.isdigit() else deleted})
    return rows


def classify_bash(parsed: dict) -> list[dict]:
    """逐条 Bash 调用判定状态。工具未启用与权限被拒是两回事，必须分开记。"""
    results = {r["id"]: r for r in parsed["工具结果"]}
    rows = []
    for call in parsed["调用明细"]:
        if call["工具"] != "Bash":
            continue
        command = str((call.get("入参") or {}).get("command", ""))
        res = results.get(call["id"])
        text = "" if res is None else res["内容"]
        low = text.lower()
        if TOOL_DISABLED in low:
            status = "工具未启用"
        elif any(m in low for m in TOOL_DENIED):
            status = "被拒"
        elif res is None:
            status = "无结果回传"
        else:
            status = "已执行"
        rows.append({"命令": command, "状态": status,
                     "结果摘要": text[:160].replace("\n", " ")})
    return rows


def find_writes(bash_rows: list[dict]) -> list[dict]:
    """只在已执行的调用里找写入形态，并给出命中的理由。"""
    hits = []
    for row in bash_rows:
        if row["状态"] != "已执行":
            continue
        command = row["命令"]
        for pattern, label in WRITE_PATTERNS:
            m = re.search(pattern, command, re.IGNORECASE)
            if m:
                hits.append({"命令": command, "理由": label, "命中": m.group(0)})
                break
        else:
            if PY_WRITE.search(command):
                hits.append({"命令": command, "理由": "python 内联写文件", "命中": "python -c"})
    return hits


def analyze(parsed: dict, diff_rows: list[dict]) -> dict:
    """由原始流与改动明细得到工具画像与判定，实时运行与重算共用同一套逻辑。"""
    hist = parsed["工具调用直方图"]
    n_edit = sum(hist.get(t, 0) for t in EDIT_TOOLS)
    bash_rows = classify_bash(parsed)
    writes = find_writes(bash_rows)
    executed = [r for r in bash_rows if r["状态"] == "已执行"]

    if writes and n_edit:
        verdict = "两种方式都用"
    elif writes:
        verdict = "通过 shell 写文件"
    elif n_edit:
        verdict = "仅用编辑工具"
    elif diff_rows:
        verdict = "有差异但无工具调用记录"
    else:
        verdict = "未修改"

    return {
        "工具调用直方图": hist,
        "编辑类调用数": n_edit,
        "Bash调用明细": bash_rows,
        "Bash已执行数": len(executed),
        "Bash未启用数": sum(1 for r in bash_rows if r["状态"] == "工具未启用"),
        "疑似写文件": writes,
        "判定": verdict,
        "判定口径": JUDGE_VERSION,
    }


def run_episode(claude_bin: Path, py: Path, env: dict, task: str, arm: str,
                replica: int, root: Path) -> dict:
    ws = root / f"{task}_{arm}_r{replica}" / "ws"
    materialize(ws, TASKS[task])
    passed_before, block_before = run_pytest(py, ws)

    prompt = PROMPT_TEMPLATE.format(block=block_before)
    res = agent.run_once(claude_bin, ws, env, prompt, ARMS[arm])
    raw = res.pop("stdout原文")
    parsed = agent.parse_stream(raw)
    raw_path = PROJ / "RECORD" / "probe_edit_path" / f"{task}_{arm}_r{replica}.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(raw, encoding="utf-8", newline="\n")

    rows = numstat(ws)
    passed_after, block_after = run_pytest(py, ws)
    touched_tests = [r["文件"] for r in rows
                     if Path(str(r["文件"])).name.startswith("test_")
                     or str(r["文件"]).endswith("conftest.py")]

    return {
        "任务": task,
        "臂": arm,
        "重复": replica,
        "提示词": prompt,
        "额外参数": list(ARMS[arm]),
        "退出码": res["退出码"],
        "超时": res["超时"],
        "耗时秒": res["耗时秒"],
        "成本USD": parsed["汇总"].get("成本USD"),
        "num_turns": parsed["汇总"].get("num_turns"),
        "改动明细": rows,
        "L_model": sum(r["增"] + r["删"] for r in rows
                       if isinstance(r["增"], int) and isinstance(r["删"], int)),
        "修改文件数": len(rows),
        "触及测试文件": touched_tests,
        "修改前全绿": passed_before,
        "修改后全绿": passed_after,
        "原始流向": str(raw_path.relative_to(PROJ)),
        "修改后测试输出": block_after[:400],
        **analyze(parsed, rows),
    }


def rederive() -> None:
    """只读已存原始流与记录，按当前口径重算全部判定，不产生新的调用。"""
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    for ep in record["episodes"]:
        raw = (PROJ / ep["原始流向"]).read_text(encoding="utf-8")
        parsed = agent.parse_stream(raw)
        ep.update(analyze(parsed, ep["改动明细"]))
        print(f"[{ep['任务']} {ep['臂']} r{ep['重复']}] 重算 → {ep['判定']}"
              f"  编辑类 {ep['编辑类调用数']}  疑似写文件 {len(ep['疑似写文件'])}",
              flush=True)
    record["判定口径"] = JUDGE_VERSION
    record["重算时间"] = datetime.now().isoformat(timespec="seconds")
    agent.write_json(RECORD, record)
    print(f"记录已更新 {RECORD}")


def main() -> None:
    if "--rederive" in sys.argv:
        rederive()
        return

    claude_bin = agent.resolve_claude_bin()
    root = Path(tempfile.mkdtemp(prefix="nlp-editpath-"))
    py = ensure_venv(root)
    env = agent.build_env((str(py.parent),))
    version = subprocess.run([str(claude_bin), "--version"], capture_output=True,
                             text=True).stdout.strip()

    record = {
        "时间": datetime.now().isoformat(timespec="seconds"),
        "CLI版本": version,
        "模型": MODEL,
        "重复次数": REPLICAS,
        "判定口径": JUDGE_VERSION,
        "工作区根": str(root),
        "episodes": [],
    }

    for task in TASKS:
        for replica in range(REPLICAS):
            for arm in ARMS:
                print(f"[{task} r{replica} {arm}] 调用中 ...", flush=True)
                ep = run_episode(claude_bin, py, env, task, arm, replica, root)
                record["episodes"].append(ep)
                agent.write_json(RECORD, record)
                print(f"  → {ep['判定']}  编辑类 {ep['编辑类调用数']}  "
                      f"Bash 已执行 {ep['Bash已执行数']} 未启用 {ep['Bash未启用数']}  "
                      f"L_model {ep['L_model']}  全绿 {ep['修改后全绿']}  "
                      f"{ep['耗时秒']} 秒", flush=True)

    total = sum(e["成本USD"] or 0 for e in record["episodes"])
    record["总成本USD"] = round(total, 4)
    agent.write_json(RECORD, record)
    print(f"\n共 {len(record['episodes'])} 次调用，总成本 {total:.4f} 美元")
    print(f"原始流向 {RECORD}")
    print(f"一次性工作区保留在 {root}")


if __name__ == "__main__":
    main()
