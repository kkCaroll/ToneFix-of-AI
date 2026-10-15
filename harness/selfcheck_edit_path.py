"""自查写入检测器。无需第三方依赖，用系统 Python 直接运行。

一个从不报警的检测器毫无价值，所以先证明它对着真正的写入命令会响，
再证明它对普通命令保持静默。命令串取自本次核验中模型真实发出的形态。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

import probe_edit_path as p  # noqa: E402

SHOULD_WARN = [
    r"sed -i 's/return ordered[n // 2]/x/' calc.py",
    '''python -c "open('calc.py','w').write('x')"''',
    'echo "return 0" > calc.py',
    "cat > calc.py <<EOF",
    'printf "x" >> calc.py',
    r'perl -pi -e "s/a/b/" calc.py',
    "git apply fix.patch",
    "Set-Content -Path calc.py -Value 'x'",
]

SHOULD_PASS = [
    "python -m pytest -q",
    "ls -la",
    "python -m pytest -q 2>&1",
    r'cd "C:\Users\x\ws" && python -m pytest -q',
    "python -m pytest -q > /dev/null",
    "grep -n median calc.py",
    "python -m pytest -q -p no:cacheprovider",
]


def check(commands: list[str], expect_write: bool) -> int:
    failures = 0
    for command in commands:
        rows = [{"命令": command, "状态": "已执行", "结果摘要": ""}]
        hits = p.find_writes(rows)
        fired = bool(hits)
        ok = fired == expect_write
        if not ok:
            failures += 1
        mark = "通过" if ok else "失败"
        reason = f"  命中 {hits[0]['理由']}" if hits else ""
        print(f"  [{mark}] {command!r}{reason}")
    return failures


def main() -> None:
    print("应当报警的写入命令")
    missed = check(SHOULD_WARN, True)
    print("应当保持静默的普通命令")
    false_alarms = check(SHOULD_PASS, False)
    print(f"\n漏检 {missed} 条，误报 {false_alarms} 条")
    if missed or false_alarms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
