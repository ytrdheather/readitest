# -*- coding: utf-8 -*-
"""
영덕중2 2026-2 중간 시험일 + `NONFIN_TO_ROLE` 정식 승인. 원장 2026-10-03.

  python db/016_yeongdeok_date_to_role.py            # 미리보기
  python db/016_yeongdeok_date_to_role.py --apply

**UPDATE 2건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

1. `exam` 영덕중2 2026-2 중간의 `exam_date` — 015 에서 「10월 둘째 주」라 비워 뒀다.
   원장: 「10월 7일이다」. **비어 있을 때만** 채운다 (다른 날짜가 이미 있으면 멈춘다).
2. `grammar_point.NONFIN_TO_ROLE` 의 `is_candidate` → false.
   원장: 「이미 승인했는데」. 2026-09-07 `011` 로 7종을 후보로 넣은 뒤 승인은 했으나
   DB 에 반영되지 않았던 것이다. 이번에는 원장이 말한 이 코드 하나만 올린다 —
   나머지 6종(011 의 동기들)은 원장 확인 없이 같이 올리지 않는다.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.env import load_env                                    # noqa: E402
from pipeline.supabase import Rest, q                                # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DATE = "2026-10-07"
CODE = "NONFIN_TO_ROLE"
WHY = "2026-10-03 원장 「이미 승인했는데」 — 011(2026-09-07) 후보 7종 중 하나. DB 반영은 016"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest(load_env())

    print("=" * 74)
    print(f" 016 — {'실제 적용' if a.apply else '미리보기 (쓰지 않음)'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE 2건. DELETE / DROP / TRUNCATE 없음.\n")

    sid = next(s["id"] for s in r.get("/school?select=id,name") if s["name"] == "영덕중")
    ex = r.get(f"/exam?select=id,exam_date&school_id=eq.{sid}&grade=eq.2&year=eq.2026"
               f"&semester=eq.2&sitting=eq.{q('중간')}")
    if len(ex) != 1:
        raise SystemExit(f"영덕중2 2026-2 중간 행이 {len(ex)}개 — 015 를 먼저 돌릴 것")
    cur = ex[0]["exam_date"]
    if cur not in (None, DATE):
        raise SystemExit(f"이미 다른 날짜가 있습니다 ({cur}) — 덮어쓰지 않고 멈춤")
    print(f"[1] 영덕중2 2026-2 중간 exam_date  {cur or '비어 있음'} → {DATE}"
          f"  {'(이미 같음)' if cur == DATE else ''}")

    g = r.get(f"/grammar_point?select=code,is_candidate,note&code=eq.{CODE}")
    if not g:
        raise SystemExit(f"{CODE} 가 마스터에 없습니다")
    g = g[0]
    print(f"[2] {CODE}  {'후보' if g['is_candidate'] else '정식'} → 정식")

    if not a.apply:
        print("\n  [미리보기] 실제로 쓰려면 --apply")
        return 0
    if cur is None:
        r.patch("exam", f"id=eq.{ex[0]['id']}&exam_date=is.null", {"exam_date": DATE})
    if g["is_candidate"]:
        note = g.get("note") or ""
        r.patch("grammar_point", f"code=eq.{CODE}",
                {"is_candidate": False, "note": (note + " · " if note else "") + WHY})
    left = [x["code"] for x in r.get("/grammar_point?select=code,is_candidate") if x["is_candidate"]]
    print(f"\n  완료. 후보로 남은 어법 포인트 {len(left)}종 {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
