"""核验无头调用中 Bash 能否真正执行并回传输出。

要回答的问题只有一条。在 `claude -p` 的无人值守调用里，把 Bash 放进工具列表之后，
模型发出的命令是否真的被执行，输出是否随 tool_result 回到会话中。若不能，
实验中「能否运行测试」这一个因子就不成立。

脚本会搭建一个一次性工作区，含一个带缺陷的实现与一条失败测试，
然后用若干组参数各调用一次，把原始 stream 与逐次判定写入 RECORD。

用法
    ./.venv/Scripts/python.exe harness/probe_bash.py
环境变量一律白名单注入，鉴权串只从 settings.json 读取后注入子进程，不打印不落盘。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parents[1]
RECORD = PROJ / "RECORD"
MODEL = "deepseek-v4-pro"
EFFORT = "high"
TIMEOUT_S = 180

PROMPT = "在当前工作目录下运行 python -m pytest，把命令的原始输出完整贴回来，不要总结。"
PROMPT_SCOPE = ("依次在当前工作目录下运行两条命令，先 echo probe-echo，再 python -m pytest。"
                "把两条命令的输出分别贴回来。若某条命令无法运行，原样说明原因。")
TOOLS = "Read,Glob,Grep,Edit,Write,Bash"
RESTRICT = ["--allowedTools", "Bash(python -m pytest:*)"]

# 只测受审批约束的配置。bypassPermissions 会关闭审批闸门并放开任意命令，
# 不在本次核验范围内，若确需使用须由用户单独确认。
CONFIGS: list[tuple[str, list[str], str]] = [
    ("A_acceptEdits", ["--tools", TOOLS, "--permission-mode", "acceptEdits"], PROMPT),
    ("B_allowedTools", ["--tools", TOOLS, "--permission-mode", "acceptEdits",
                        *RESTRICT], PROMPT),
    ("C_scope", ["--tools", TOOLS, "--permission-mode", "acceptEdits",
                 *RESTRICT], PROMPT_SCOPE),
    ("D_scope_space", ["--tools", TOOLS, "--permission-mode", "acceptEdits",
                       "--allowedTools", "Bash(python -m pytest *)"], PROMPT_SCOPE),
    ("E_scope_prefix", ["--tools", TOOLS, "--permission-mode", "acceptEdits",
                        "--allowedTools", "Bash(python:*)"], PROMPT_SCOPE),
    ("F_manual_scope", ["--tools", TOOLS, "--permission-mode", "manual",
                        *RESTRICT], PROMPT_SCOPE),
]

BUGGY_CALC = '''"""统计工具。"""


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2]
'''

FAILING_TEST = '''from calc import median


def test_median_odd_length():
    assert median([3, 1, 2]) == 2


def test_median_even_length():
    assert median([1, 2, 3, 4]) == 2.5
'''


def resolve_claude_bin() -> Path:
    """定位原生 claude.exe。不能用给 Git Bash 用的 sh 脚本，也不能用 .cmd。"""
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules"
        / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe",
        Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"
        / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    found = shutil.which("claude.exe")
    if found:
        return Path(found)
    raise FileNotFoundError("未找到 claude.exe")


def read_anthropic_env() -> dict[str, str]:
    """从 settings.json 取鉴权与端点。只返回 ANTHROPIC_ 开头的键。"""
    path = Path.home() / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    env = data.get("env", {})
    return {k: str(v) for k, v in env.items() if k.startswith("ANTHROPIC_")}


def build_env(venv_scripts: Path, anthropic: dict[str, str]) -> dict[str, str]:
    """白名单构造子进程环境。鉴权串只在此处注入一次，不进任何产物。"""
    npm_dir = Path(os.environ.get("APPDATA", "")) / "npm"
    path_parts = [
        str(venv_scripts),
        str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"),
        os.environ.get("SystemRoot", r"C:\Windows"),
        str(npm_dir),
    ]
    env = {
        "PATH": os.pathsep.join(path_parts),
        "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
        "SystemDrive": os.environ.get("SystemDrive", "C:"),
        "COMSPEC": os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "USERPROFILE": os.environ.get("USERPROFILE", ""),
        "APPDATA": os.environ.get("APPDATA", ""),
        "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
        "HOMEDRIVE": os.environ.get("HOMEDRIVE", "C:"),
        "HOMEPATH": os.environ.get("HOMEPATH", ""),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "GIT_CONFIG_NOSYSTEM": "0",
    }
    env.update(anthropic)
    return env


def build_workspace(root: Path) -> tuple[Path, Path]:
    """搭一次性工作区。返回工作区目录与 venv 的 Scripts 目录。"""
    ws = root / "ws"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "calc.py").write_text(BUGGY_CALC, encoding="utf-8", newline="\n")
    (ws / "test_calc.py").write_text(FAILING_TEST, encoding="utf-8", newline="\n")

    venv = root / "venv"
    subprocess.run(["uv", "venv", str(venv)], check=True, capture_output=True)
    py = venv / "Scripts" / "python.exe"
    subprocess.run(["uv", "pip", "install", "--python", str(py), "pytest"],
                   check=True, capture_output=True)
    return ws, venv / "Scripts"


def run_once(claude_bin: Path, ws: Path, env: dict[str, str],
             extra: list[str], prompt: str) -> dict:
    """跑一次无头调用，回收原始 stream 与退出信息。"""
    argv = [str(claude_bin), "-p", prompt,
            "--model", MODEL, "--effort", EFFORT,
            "--safe-mode",
            "--output-format", "stream-json", "--verbose",
            *extra]
    started = time.time()
    timed_out = False
    proc = subprocess.Popen(argv, cwd=str(ws), env=env,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        out, err = proc.communicate()
    return {
        "argv": argv[1:],
        "退出码": proc.returncode,
        "超时": timed_out,
        "耗时秒": round(time.time() - started, 1),
        "stdout原文": out.decode("utf-8", errors="replace"),
        "stderr原文": err.decode("utf-8", errors="replace"),
    }


def flatten(content) -> str:
    """把 tool_result 的 content 压成纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", block.get("content", ""))))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return json.dumps(content, ensure_ascii=False)


DENY_MARKERS = ("requires approval", "permission denied", "not allowed",
                "have not granted", "haven't granted", "requested permissions",
                "不允许", "需要批准", "被拒绝")
RUN_MARKERS = ("test session starts", "collected ", "passed", "failed", "probe-echo")


def parse_stream(raw: str) -> dict:
    """从 stream-json 里抽出工具调用、工具结果与末行汇总。"""
    bash_calls: list[dict] = []
    results: list[dict] = []
    summary: dict = {}
    n_lines = 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        n_lines += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = obj.get("type")
        if kind == "assistant":
            for block in obj.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    bash_calls.append({"工具": block.get("name"),
                                       "入参": block.get("input"),
                                       "id": block.get("id")})
        elif kind == "user":
            for block in obj.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results.append({"id": block.get("tool_use_id"),
                                    "is_error": block.get("is_error", False),
                                    "内容": flatten(block.get("content"))})
        elif kind == "result":
            summary = {"成本USD": obj.get("total_cost_usd"),
                       "num_turns": obj.get("num_turns"),
                       "duration_ms": obj.get("duration_ms"),
                       "is_error": obj.get("is_error"),
                       "最终回答": obj.get("result")}
    tool_hist: dict[str, int] = {}
    for call in bash_calls:
        tool_hist[call["工具"]] = tool_hist.get(call["工具"], 0) + 1
    return {"行数": n_lines, "工具调用直方图": tool_hist,
            "调用明细": bash_calls, "工具结果": results, "汇总": summary}


def judge_calls(parsed: dict) -> dict:
    """逐条命令判定，按 id 把 tool_use 与 tool_result 配对。

    判定不能依据 is_error。pytest 因测试失败而退出码非零时 is_error 同样为真，
    此时命令是执行成功的。被拒与执行成功只能从结果正文区分。
    """
    results = {r["id"]: r for r in parsed["工具结果"]}
    rows = []
    for call in parsed["调用明细"]:
        if call["工具"] != "Bash":
            continue
        cmd = (call.get("入参") or {}).get("command", "")
        res = results.get(call["id"])
        if res is None:
            rows.append({"命令": cmd, "判定": "无结果回传",
                         "is_error": None, "结果摘要": ""})
            continue
        text = res["内容"] or ""
        low = text.lower()
        if any(m in low for m in DENY_MARKERS):
            verdict = "被拒"
        elif text.strip():
            verdict = "已执行，退出码非零" if res["is_error"] else "已执行"
        else:
            verdict = "结果为空"
        rows.append({"命令": cmd, "判定": verdict, "is_error": res["is_error"],
                     "结果摘要": text[:300].replace("\n", " ")})

    n_exec = sum(1 for r in rows if r["判定"].startswith("已执行"))
    n_deny = sum(1 for r in rows if r["判定"] == "被拒")
    if not rows:
        overall = "未发出 Bash 调用"
    elif n_deny and not n_exec:
        overall = "全部被拒"
    elif n_exec and not n_deny:
        overall = "命令可执行"
    else:
        overall = f"部分可执行，执行 {n_exec} 条，被拒 {n_deny} 条"
    return {"总体": overall, "逐条": rows}


def main() -> None:
    RECORD.mkdir(exist_ok=True)
    claude_bin = resolve_claude_bin()
    anthropic = read_anthropic_env()

    root = Path(tempfile.mkdtemp(prefix="nlp-probe-"))
    ws, venv_scripts = build_workspace(root)
    env = build_env(venv_scripts, anthropic)

    version = subprocess.run([str(claude_bin), "--version"],
                             capture_output=True, text=True).stdout.strip()

    record: dict = {
        "时间": datetime.now().isoformat(timespec="seconds"),
        "可执行文件": str(claude_bin),
        "CLI版本": version,
        "模型": MODEL,
        "effort": EFFORT,
        "工作区": str(ws),
        "提示词": PROMPT,
        "超时秒": TIMEOUT_S,
        "各配置": {},
    }

    for name, extra, prompt in CONFIGS:
        print(f"[{name}] 调用中 ...", flush=True)
        res = run_once(claude_bin, ws, env, extra, prompt)
        raw = res.pop("stdout原文")
        parsed = parse_stream(raw)
        verdict = judge_calls(parsed)
        raw_path = RECORD / "probe_bash" / f"{name}.stream.jsonl"
        raw_path.parent.mkdir(exist_ok=True)
        raw_path.write_text(raw, encoding="utf-8", newline="\n")
        record["各配置"][name] = {
            "提示词": prompt,
            "额外参数": extra,
            **res,
            "判定": verdict["总体"],
            "判定明细": verdict["逐条"],
            "解析": parsed,
            "原始流向": str(raw_path.relative_to(PROJ)),
        }
        print(f"[{name}] 判定 {verdict['总体']}  退出码 {res['退出码']}  "
              f"耗时 {res['耗时秒']} 秒", flush=True)

    RECORD.mkdir(exist_ok=True)
    out = RECORD / "probe_bash.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2),
                   encoding="utf-8", newline="\n")
    print(f"\n原始记录写入 {out}")
    print(f"一次性工作区保留在 {root}")


if __name__ == "__main__":
    main()
