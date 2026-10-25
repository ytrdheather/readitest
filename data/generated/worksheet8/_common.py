# -*- coding: utf-8 -*-
"""worksheet8 데이터 스크립트가 같이 쓰는 조립 함수. 각 make_*.py 는 표만 적고 이것을 부른다."""
import json, os, re

_flip = lambda s, a, b: re.sub(a, b, s)


def build(out, unit, school, grade, S, PREP, WS1, WS2, WS4, WS5, WS6, WS7, WS8):
    n = len(S)
    assert n == len(WS1) == len(WS2) == len(WS4) == len(WS5) == len(WS7) == len(WS8), \
        [len(x) for x in (S, WS1, WS2, WS4, WS5, WS7, WS8)]
    d = {
     "unit": unit, "school": school, "grade": grade,
     "sentences": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(S, 1)],
     "prep": [dict(zip(("word", "pos", "ko", "def", "example", "example_ko"), p)) for p in PREP],
     "ws1": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(WS1, 1)],
     "ws2": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(WS2, 1)],
     # ③ 은 ② 를 뒤집는다 — 영어 굵게 → 빈칸, 우리말 빈칸 → 굵게
     "ws3": [{"no": i, "ko": _flip(k, r"\{\{(.+?)\}\}", r"**\1**"), "en": _flip(e, r"\*\*(.+?)\*\*", r"{{\1}}")}
             for i, (e, k) in enumerate(WS2, 1)],
     "ws4": [{"no": i, "en": e, "answer": a} for i, (e, a) in enumerate(WS4, 1)],
     "ws5": [{"no": i, "en": e, "answer": a} for i, (e, a) in enumerate(WS5, 1)],
     "ws6": WS6,
     "ws7": [{"no": i, "en": e, "answer": S[i - 1][0]} for i, e in enumerate(WS7, 1)],
     "ws8": [{"no": i, "keywords": k, "frame": f, "answer": S[i - 1][0]} for i, (k, f) in enumerate(WS8, 1)],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(out)
    return d
