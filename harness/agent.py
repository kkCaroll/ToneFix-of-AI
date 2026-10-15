"""无头驱动 claude CLI 的共用件。

鉴权串只从 settings.json 读出后注入子进程环境，不打印也不写入任何产物。
本模块是正式脚手架的雏形，后者落地后由 harness 下的完整实现取代。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

CLI_NAME = "claude.exe"
NPM_REL = (Path("npm") / "node_modules" / "@anthropic-ai" / "claude-code"
           / "bin" / "claude.exe")
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_TIMEOUT_S = 180


def resolve_claude_bin() -> Path:
    """定位原生 claude.exe。给 Git Bash 的 sh 脚本与 .cmd 都不能用。"""
    bases = [os.environ.get("APPDATA"), str(Path.home() / "AppData" / "Roaming")]
    for base in bases:
        if base:
            candidate = Path(base) / NPM_REL
            if candidate.is_file():
                return candidate
    found = shutil.which(CLI_NAME)
    if found:
        return Path(found)
    raise FileNotFoundError(f"未找到 {CLI_NAME}")


def read_anthropic_env() -> dict[str, str]:
    """只取 settings.json 里 ANTHROPIC_ 开头的键。"""
    path = Path.home() / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: str(v) for k, v in data.get("env", {}).items()
            if k.startswith("ANTHROPIC_")}


def build_env(path_prefix: tuple[str, ...] = ()) -> dict[str, str]:
    """白名单构造子进程环境。多余变量一律不继承，避免某一臂被残留变量带偏。"""
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    parts = list(path_prefix)
    parts += [str(Path(system_root) / "System32"), system_root,
              str(Path(os.environ.get("APPDATA", "")) / "npm")]
    keep = ("SystemRoot", "SystemDrive", "COMSPEC", "TEMP", "TMP", "USERPROFILE",
            "APPDATA", "LOCALAPPDATA", "HOMEDRIVE", "HOMEPATH", "PATHEXT",
            "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE")
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env["PATH"] = os.pathsep.join(parts)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(read_anthropic_env())
    return env


def run_once(claude_bin: Path, cwd: Path, env: dict[str, str], prompt: str,
             extra_args: tuple[str, ...] = (), model: str = DEFAULT_MODEL,
             effort: str = "high",
             timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    """跑一次无头调用。一次调用即本实验定义的一轮。"""
    argv = [str(claude_bin), "-p", prompt,
            "--model", model, "--effort", effort,
            "--safe-mode",
            "--output-format", "stream-json", "--verbose",
            *extra_args]
    started = time.time()
    timed_out = False
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        out, err = proc.communicate()
    return {"argv": argv[1:],
            "退出码": proc.returncode,
            "超时": timed_out,
            "耗时秒": round(time.time() - started, 1),
            "stdout原文": out.decode("utf-8", errors="replace"),
            "stderr原文": err.decode("utf-8", errors="replace")}


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


def parse_stream(raw: str) -> dict:
    """从 stream-json 抽出工具调用、工具结果与末行汇总。

    注意 is_error 不可用作被拒的判据。命令因测试失败而退出码非零时它同样为真。
    """
    calls: list[dict] = []
    results: list[dict] = []
    summary: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = obj.get("type")
        if kind == "assistant":
            for block in obj.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append({"工具": block.get("name"),
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

    histogram: dict[str, int] = {}
    for call in calls:
        histogram[call["工具"]] = histogram.get(call["工具"], 0) + 1
    return {"工具调用直方图": histogram, "调用明细": calls,
            "工具结果": results, "汇总": summary}


def bash_commands(parsed: dict) -> list[str]:
    """抽出所有 Bash 调用的命令原文，保留原样供人工复核。"""
    out = []
    for call in parsed["调用明细"]:
        if call["工具"] == "Bash":
            out.append(str((call.get("入参") or {}).get("command", "")))
    return out


def write_json(path: Path, data) -> None:
    """产物写出只有一个出口，行尾显式 LF。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8", newline="\n")
