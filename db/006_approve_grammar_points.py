# -*- coding: utf-8 -*-
"""
후보 어법 포인트 3종 정식 승인 (`is_candidate` true → false). 원장 승인 2026-09-06.

  python db/006_approve_grammar_points.py --apply

**UPDATE 3건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

## 무엇이 후보였나

마스터 31종에 **담을 칸이 없어서** 0단계 작업 중 새로 만든 코드들이다.
`is_candidate = true` 는 「임시로 쓰고 있으나 정식 승인은 안 받았다」는 표시다.

    VERB_PERFECT           현재완료 — 기존 코드에 완료시제 항목이 아예 없었다.
                           VERB_TENSE(시제 일치)는 절 간 일치 문제라 다른 축이다.
    VERB_PREP_COLLOCATION  동사+전치사 결합 (help A with B). 변형 EI_PREP_DELETE 가
                           겨냥하는 포인트인데 대응 코드가 없었다.
    PREP_USAGE             일반 전치사 용법. 전치사 계열 코드가 CONJ_VS_PREP 하나뿐이었고
                           그건 다른 현상이다.

## 원장의 승인 근거

`PREP_USAGE` · `VERB_PREP_COLLOCATION` 은 기출에서 바로 확인된다
(청명 문항 5 · 영일 문항 15 · 영덕 문항 16 ⓖ).

`VERB_PERFECT` 는 2026-1 기말 4개교 96문항에 **직접은 안 나왔다.** 그런데 원장이
승인한 근거가 이것이다: 「**결과적으로 언젠간 다룬다.**」

이건 우리 표본이 못 보는 것을 본 판단이다. 우리가 가진 기출은 **한 회차뿐**이고,
어법 포인트는 학년 전체에 걸쳐 순환한다. 「이번 회차에 안 나왔다」를 「안 나온다」로
읽으면 안 된다 — 오늘 유형 3건(T-WORD-ORDER · T-GRAMMAR-STANDALONE · T-FORM-CHOICE)에서
같은 실수를 이미 세 번 했다. 표본이 1회차라는 사실을 판단에 먼저 넣어야 한다.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CODES = {
    "VERB_PERFECT": ("2026-09-06 원장 정식 승인. 기출 1회차(4개교 96문항)에는 직접 나오지 "
                     "않았으나 원장 판단 「결과적으로 언젠간 다룬다」 — 어법 포인트는 학년 "
                     "전체에 걸쳐 순환하므로 1회차 표본으로 '안 나온다'를 판정할 수 없다."),
    "VERB_PREP_COLLOCATION": ("2026-09-06 원장 정식 승인. 근거: 영덕중 2026-1 기말 문항 16 ⓖ "
                              "(EI_PREP_DELETE 변형이 겨냥하는 포인트)."),
    "PREP_USAGE": ("2026-09-06 원장 정식 승인. 근거: 청명중 2026-1 기말 문항 5(전치사 4곳 빈칸) · "
                   "영일중 문항 15. school_grammar_map 에 이미 2행 사용 중이었다."),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    rows = {g["code"]: g for g in r.get("/grammar_point?select=code,label_ko,is_candidate")}
    print("=" * 74)
    print(f" 후보 어법 포인트 정식 승인 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE 3건. DELETE / DROP / TRUNCATE 없음.\n")

    todo = []
    for code in CODES:
        g = rows.get(code)
        if not g:
            print(f"  X {code} 가 마스터에 없습니다 — 중단")
            return 1
        state = "후보" if g["is_candidate"] else "이미 정식"
        print(f"  [{state:6}] {code:24} {g['label_ko']}")
        if g["is_candidate"]:
            todo.append(code)

    print(f"\n  승격 대상 {len(todo)}종")
    if not a.apply:
        print("  실제로 쓰려면 --apply")
        return 0

    for code in todo:
        note = (rows[code].get("note") or "")
        r.patch("grammar_point", f"code=eq.{code}",
                {"is_candidate": False,
                 "note": (note + " · " if note else "") + CODES[code]})
    print(f"\n  {len(todo)}종 정식 승격 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
