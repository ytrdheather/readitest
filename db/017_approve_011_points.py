# -*- coding: utf-8 -*-
"""
011(2026-09-07) 로 후보로 넣은 어법 포인트 중 남은 6종 정식 승인. 원장 2026-10-03 「승인해라」.

  python db/017_approve_011_points.py            # 미리보기
  python db/017_approve_011_points.py --apply

**UPDATE 6건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

7종 중 `NONFIN_TO_ROLE` 은 016 에서 먼저 올렸다. 9/7 에 넣은 뒤 태깅·드릴·동형이 전부 이
코드를 써 왔는데 DB 에는 후보로 남아 있었다 — 승인은 했지만 반영이 안 된 상태였다.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.env import load_env                                    # noqa: E402
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CODES = ["REL_OBJECT", "THAT_USAGE", "VERB_USED_TO",
         "SVOO_DATIVE", "SVOC_OBJ_COMPLEMENT", "PERCEPTION_VERB_OC"]
WHY = "2026-10-03 원장 승인 「승인해라」 — 011(2026-09-07) 후보 7종. DB 반영은 017"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest(load_env())

    rows = {g["code"]: g for g in r.get("/grammar_point?select=code,label_ko,is_candidate,note")}
    print("=" * 74)
    print(f" 017 011 후보 어법 포인트 승인 — {'실제 적용' if a.apply else '미리보기 (쓰지 않음)'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE. DELETE / DROP / TRUNCATE 없음.\n")

    todo = []
    for code in CODES:
        g = rows.get(code)
        if not g:
            print(f"  X {code} 가 마스터에 없습니다 — 아무것도 쓰지 않고 중단")
            return 1
        print(f"  [{'후보' if g['is_candidate'] else '정식'}] {code:22} {g['label_ko']}")
        if g["is_candidate"]:
            todo.append(code)

    print(f"\n  승격 대상 {len(todo)}종")
    if not a.apply:
        print("  [미리보기] 실제로 쓰려면 --apply")
        return 0
    for code in todo:
        note = rows[code].get("note") or ""
        r.patch("grammar_point", f"code=eq.{code}",
                {"is_candidate": False, "note": (note + " · " if note else "") + WHY})
    left = [g["code"] for g in r.get("/grammar_point?select=code,is_candidate") if g["is_candidate"]]
    print(f"\n  {len(todo)}종 승격 완료 · 후보로 남은 것 {len(left)}종 {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
