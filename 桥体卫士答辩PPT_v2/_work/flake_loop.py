# -*- coding: utf-8 -*-
"""flake_loop.py —— 复现 test_mobile_layout 的竞态（核验员报告 ❌-1）。

跑法：python flake_loop.py [轮数]
每轮跑 tests/test_mobile_layout.py -q，记录红/绿与失败的用例，最后给统计。
"""
import subprocess
import sys

PY = r"C:\Users\CX\AppData\Local\Programs\Python\Python314\python.exe"
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 8

red = 0
fails = []
for i in range(1, RUNS + 1):
    r = subprocess.run([PY, "-X", "utf8", "-m", "pytest", "tests/test_mobile_layout.py", "-q"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (r.stdout or "").strip().splitlines()
    summary = tail[-1] if tail else "(no output)"
    ok = r.returncode == 0
    if not ok:
        red += 1
        for ln in tail:
            if "FAILED" in ln or "AssertionError" in ln:
                fails.append(ln.strip()[:160])
    print(f"round {i:02d}: rc={r.returncode} {'GREEN' if ok else 'RED  '}  {summary[:90]}")

print(f"\n{RUNS} 轮: 绿 {RUNS - red} / 红 {red}  (失败率 {red / RUNS:.0%})")
for f in fails[:10]:
    print("  ", f)
