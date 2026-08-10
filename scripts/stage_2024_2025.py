#!/usr/bin/env python3
"""Stage the newly-downloaded 2024 + 2025 Chemistry 9701 PDFs into raw/ with clean names.

Source folders (Downloads):
  * "Chemistry (9701)_20260810_111845"  -> 2025 (June s25 / March m25 / November w25) + ERs
  * "Chemistry (9701)_20260810_111755"  -> 2024 (June s24 / March m24 / November w24) + ERs

Naming target:
  QP  -> raw/papers/9701_<season>_qp_<NN>.pdf
  MS  -> raw/papers/9701_<season>_ms_<NN>.pdf
  ER  -> raw/reports/9701_<year>_<season>_er.pdf
"""
import os
import re
import shutil
import sys

REPO = "/Users/tsinglan-school/Desktop/题库"
PAPERS_DIR = os.path.join(REPO, "raw", "papers")
REPORTS_DIR = os.path.join(REPO, "raw", "reports")

SOURCES = {
    # (source_dir, season, year)
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111755", "s24", 2024),
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111755", "m24", 2024),
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111755", "w24", 2024),
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111845", "s25", 2025),
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111845", "m25", 2025),
    ("/Users/tsinglan-school/Downloads/Chemistry (9701)_20260810_111845", "w25", 2025),
}

SEASON_LABEL = {"s24": "June 2024", "m24": "March 2024", "w24": "November 2024",
                "s25": "June 2025", "m25": "March 2025", "w25": "November 2025"}


def season_from_name(name):
    """Return season token for a filename, or None."""
    low = name.lower()
    for token in ["june", "march", "november"]:
        if token in low:
            for year in ["2024", "2025"]:
                if year in name:
                    season = {"june": "s", "march": "m", "november": "w"}[token] + year[2:]
                    return season
    return None


def main():
    os.makedirs(PAPERS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    copied = []  # (season, kind, paper_label, src_rel)
    skipped = []

    for src_dir, _season, _year in SOURCES:
        for fname in sorted(os.listdir(src_dir)):
            full = os.path.join(src_dir, fname)
            if not os.path.isfile(full) or not fname.lower().endswith(".pdf"):
                continue

            season = season_from_name(fname)
            if season is None:
                skipped.append((fname, "no season matched"))
                continue

            low = fname.lower()
            if "question" in low:
                kind = "qp"
            elif "mark scheme" in low:
                kind = "ms"
            elif "examiner report" in low:
                kind = "er"
            else:
                skipped.append((fname, "unknown kind"))
                continue

            year = int("20" + season[1:3])

            if kind == "er":
                dest = os.path.join(REPORTS_DIR, f"9701_{year}_{season}_er.pdf")
            else:
                # paper number: last 2-digit number in filename (e.g. ... 11.pdf)
                nums = re.findall(r"\d{2}", fname)
                if not nums:
                    skipped.append((fname, "no paper number"))
                    continue
                paper = nums[-1]
                dest = os.path.join(PAPERS_DIR, f"9701_{season}_{kind}_{paper}.pdf")

            if os.path.exists(dest):
                skipped.append((fname, f"already exists -> {os.path.relpath(dest, REPO)}"))
                continue

            shutil.copy2(full, dest)
            copied.append((season, kind, os.path.relpath(dest, REPO)))

    # Report
    from collections import defaultdict, Counter
    per_season = defaultdict(Counter)
    for season, kind, _ in copied:
        per_season[season][kind] += 1

    print("=== STAGED (copied) ===")
    for season in ["s24", "m24", "w24", "s25", "m25", "w25"]:
        c = per_season.get(season, Counter())
        print(f"  {season} ({SEASON_LABEL[season]}): qp={c['qp']} ms={c['ms']} er={c['er']}")
    print(f"\n  TOTAL copied: {len(copied)}")

    if skipped:
        print("\n=== SKIPPED ===")
        for name, reason in skipped:
            print(f"  {name!r}: {reason}")
    else:
        print("\nNo skips.")


if __name__ == "__main__":
    sys.exit(main())
