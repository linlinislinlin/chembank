#!/usr/bin/env python3
"""压缩 quiz-app/site 里的题目截图，让 GitHub Pages 部署能顺利上传。

背景：
  题图是 240 dpi 截图（宽 ~1700 px，单张最大几百 KB），整站 assets 会涨到 350 MB 以上，
  Pages 的部署步骤会超时（Deploy to GitHub Pages: Timeout reached, aborting）。
  这些图只用于网页显示（卡片宽度 ~700-900 px），降到 1000 px 宽 + 调色板压缩肉眼几乎无差别。

用法：
    python3 quiz-app/optimize_assets.py            # 原地压缩（可反复执行，幂等）
    python3 quiz-app/optimize_assets.py --dry-run  # 只报告当前体积

规则：
  * 宽度 > 1000 px 才缩放；
  * 几乎纯灰的图转 8-bit 灰度（文字扫描件），彩色图量化到 48 色（保留火焰/指示剂等颜色）；
  * 压缩后反而更大的文件保持原样。
"""
from __future__ import annotations

import argparse
import io
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

SITE = Path(__file__).resolve().parent / "site"
MAX_W = 1000
COLORS = 48
GRAY_TOL = 10          # 最大通道差 <= 10 视为灰度图
MIN_BYTES = 30 * 1024  # 小于 30 KB 的图基本已优化，跳过


def optimize(path_str: str) -> tuple[int, int]:
    path = Path(path_str)
    before = path.stat().st_size
    if before < MIN_BYTES:
        return before, before
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            arr = np.asarray(im)
            spread = int(arr.max(axis=2).astype(np.int16).max() -
                         arr.min(axis=2).astype(np.int16).min())
            is_gray = spread <= GRAY_TOL
            if im.width > MAX_W:
                im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
            out = (im.convert("L") if is_gray else
                   im.quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE))
            buf = io.BytesIO()
            out.save(buf, "PNG", optimize=True)
        data = buf.getvalue()
        if len(data) >= before:
            return before, before
        path.write_bytes(data)
        return before, len(data)
    except Exception as exc:  # 坏图不阻塞整批
        print(f"  ! {path.name}: {exc}")
        return before, before


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files: list[str] = sorted(str(p) for p in (SITE / "assets").rglob("*.png"))
    sol = SITE / "solution-images"
    if sol.is_dir():
        files += sorted(str(p) for p in sol.rglob("*.png"))
    print(f"待处理 PNG：{len(files)}")

    if args.dry_run:
        print(f"当前体积：{sum(os.path.getsize(f) for f in files) / 1e6:.1f} MB")
        return 0

    before = after = 0
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        for i, (b, a) in enumerate(pool.map(optimize, files, chunksize=32), 1):
            before += b
            after += a
            if i % 500 == 0:
                print(f"  {i}/{len(files)}  {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB")
    print(f"完成：{before / 1e6:.1f} MB -> {after / 1e6:.1f} MB "
          f"（省 {100 * (1 - after / max(before, 1)):.0f}%）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
