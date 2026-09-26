# -*- coding: utf-8 -*-
"""특급기출 본책 한 권에서 단원별 쪽 구간을 찾는다.

  python tools/teukgeup_lessons.py "Z:/…/특급기출 … 1-1(25)본책.pdf"

2학기 것은 원장이 단원별로 잘라 줬지만(「… 5과 추출.pdf」) **1학기 본책은 한 권에
네 단원이 다 들어 있다.** 그대로 extract_teukgeup 에 넣으면 책 전체를 한 단원으로
긁는다 — 2026-09-26 에 실제로 그랬다. 여기서 구간을 찾아 `--pages A-B` 로 넘긴다.

단원 제목이 쪽마다 머리글로 박혀 있어서 그것으로 찾는다. 앞쪽 목차(2~5쪽)는
네 제목이 한 쪽에 다 나오므로 **연속 구간만** 단원으로 본다.
"""
import re
import sys

import fitz

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def lesson_ranges(path, min_run=5):
    doc = fitz.open(path)
    texts = [p.get_text() for p in doc]
    titles = {}
    for t in texts:
        for m in re.finditer(r"Lesson\s*(\d)\s+([^\n]{3,50})", t):
            titles.setdefault(int(m.group(1)), m.group(2).strip())
    out = {}
    for L, name in sorted(titles.items()):
        hit = [i for i, t in enumerate(texts, 1) if name in t]
        runs, cur = [], []
        for i in hit:
            if cur and i - cur[-1] > 4:
                runs.append(cur); cur = []
            cur.append(i)
        if cur:
            runs.append(cur)
        runs = [r for r in runs if len(r) >= min_run]
        if runs:
            longest = max(runs, key=len)
            out[L] = (longest[0], longest[-1], name)
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit("사용: python tools/teukgeup_lessons.py <본책.pdf>")
    for L, (lo, hi, name) in lesson_ranges(sys.argv[1]).items():
        print(f"  Lesson {L}  {lo:>3}~{hi:<3}쪽   {name}")
        print(f"      --pages {lo}-{hi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
