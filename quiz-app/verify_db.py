#!/usr/bin/env python3
"""Verify the three ChemBank homework tables exist in Supabase (read-only).

Reads credentials from quiz-app/config.js so secrets stay out of the shell.
Exits 0 if all three tables are reachable (HTTP 200), 1 otherwise.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "quiz-app" / "config.js"
BASE = "https://jrobrcaiqtfwuomzycui.supabase.co"


def read_key() -> str:
    text = CONFIG.read_text(encoding="utf-8")
    m = re.search(r'anonKey\s*:\s*"([^"]+)"', text)
    if not m:
        sys.exit("config.js: 找不到 anonKey")
    return m.group(1)


def check_table(key: str, table: str) -> int:
    url = f"{BASE}/rest/v1/{table}?select=id&limit=1"
    r = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "20",
         "-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}", url],
        capture_output=True, text=True,
    )
    code = r.stdout.strip()
    print(f"{table} -> HTTP {code}")
    return 1 if code == "200" else 0


def main() -> int:
    key = read_key()
    results = [check_table(key, t) for t in ("assignments", "students", "answers")]
    ok = all(results)
    print("三张表全部就绪 ✓" if ok else "存在缺失/未就绪的表 ✗")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
