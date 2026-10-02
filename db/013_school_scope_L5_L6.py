# -*- coding: utf-8 -*-
"""
5·6과 학교별 출제 범위를 `school_grammar_map` 에 넣는다 — 배부물 근거.

  python db/013_school_scope_L5_L6.py            # 무엇이 들어가는지 보기만
  python db/013_school_scope_L5_L6.py --apply

**INSERT 만 한다. DELETE · UPDATE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
이미 같은 (학교 · 학년 · 단원 · 코드) 행이 있으면 건너뛴다.

## 왜 지금 넣는가

기존 28행은 전부 **2026-1 기말 기출 96문항**에서 나온 것이다 — 즉 **끝난 시험**의
관측이다. 이번 시험 범위인 5·6과는 아직 한 행도 없었다.

시험이 9월 29일~10월 1일(영일·청명·태장)과 10월 둘째 주(영덕)다. 배부물을 다 읽은
지금이 넣을 때다.

## 근거는 전부 **배부물 실물**이다

기출이 아니라 학교가 이번 학기에 **나눠 준 종이**다. 기획서 §5.5.15 의 원칙 —
「본문과 학습지에 나오는 문법 포인트는 모두 출제 범위로 본다」 — 를 그대로 따른다.

`confidence` 는 `high`. 학교가 직접 인쇄해 돌린 것이라 「가르쳤다」는 사실 자체는
확실하다. 다만 **시험에 나온다는 보장은 아니므로** `note` 에 근거 쪽수를 남겨,
시험 뒤에 맞았는지 되짚을 수 있게 한다.

## 관측되지 않은 것은 넣지 않는다

영덕 L5 · 청명 L5·L6 · 태장 L6 · 영일 L6 배부물은 아직 없다. **없다고 적지 않고,
그냥 넣지 않는다.** 「관측되지 않음 ≠ 없음」(§5.5.15).
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

# (학교, 단원, 코드, 근거)
ROWS = [
    # ── 영일중 L5 · 배부물 10쪽 전부 읽음 (2026-09-07) ──
    ("영일중", "Lesson 5", "REL_OBJECT",
     "배부물 3·4쪽 「Grammar Help! Lesson 5 (P.94) 목적격 관계대명사」 + 5쪽 연습 B 10문항. "
     "범위: 생략 · 목적어 중복 · something/all/최상급→that · 전치사+관계대명사 · whom"),
    ("영일중", "Lesson 5", "REL_POSSESSIVE",
     "배부물 5쪽 연습 B 에 whose 문항 포함. 교과서 5·6과 본문에는 whose 가 없는데도 "
     "가르친다 — 2026-1 기말에서 영일이 소유격을 낸 것과 이어진다"),
    ("영일중", "Lesson 5", "VERB_USED_TO",
     "배부물 8쪽 「used to / be used to」 개념 + 연습 6문항. "
     "범위: used to+동사원형 · 의문문 · be used to+-ing · be used to+동사원형(수동)"),
    ("영일중", "Lesson 5", "PREP_USAGE",
     "배부물 5쪽 연습 C 「관계사절 안의 전치사 자리」 8문항 (the music we listened to)"),

    # ── 태장중 L5 · 배부물 8쪽 전부 읽음 (2026-09-07) ──
    ("태장중", "Lesson 5", "REL_OBJECT",
     "배부물 3쪽 「Worksheet 5-2 Grammar 목적격 관계대명사」 + 4·5쪽 Exercise A 8문항. "
     "범위: 생략 · [명사+S+V] 판별법 · 목적어 중복 · whom · that 쓰임 구별. "
     "전치사+관계대명사는 안 다룸"),
    ("태장중", "Lesson 5", "VERB_USED_TO",
     "배부물 4·5쪽 개념 + 6쪽 Exercise B 8문항. "
     "범위: used to+동사원형 · There used to be · be used to+-ing · 부정·의문문 · get used to"),

    # ── 영덕중 L6 · 배부물 15쪽 전부 읽음 (2026-09-07) ──
    ("영덕중", "Lesson 6", "SVOC_OBJ_COMPLEMENT",
     "배부물 3쪽 「지각동사 see, hear + 목적어 + 목적격보어(-ing/동사원형)」 개념, "
     "4·6쪽 그림 묘사 연습, 7쪽 교사 자작 워크시트, 8쪽 Exercise A 8문항"),
    ("영덕중", "Lesson 6", "SO_SUCH_TOO_ENOUGH",
     "배부물 3쪽 「so+형용사/부사+that+S+V」 및 「~that+S+can't+동사원형」 개념, "
     "4·5·6쪽 연습, 7쪽 교사 자작 워크시트 B, 9쪽 Exercise B 8문항. "
     "문법 6쪽 중 4쪽이 이것 — 지각동사와 같은 비중이다"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 넣는다")
    a = ap.parse_args()

    rest = Rest(load_env())
    schools = {s["name"]: s["id"] for s in rest.get("/school?select=id,name")}
    books = rest.get("/textbook?select=id,publisher,author,grade")
    book = next((b["id"] for b in books
                 if b["publisher"] == "동아" and b["author"] == "윤정미" and b["grade"] == 2), None)
    if book is None:
        raise SystemExit("동아 윤정미 중2 교과서 레코드를 못 찾았습니다")

    # 근거 시험까지 키에 넣는다 (2026-10-02). 이 스크립트의 행은 배부물 근거라 시험이 없으므로
    # 기출 근거 행과 겹쳐도 별개 관측으로 본다.
    have = {(r["school_id"], r["textbook_unit"], r["grammar_point_code"])
            for r in rest.get("/school_grammar_map?select=school_id,textbook_unit,grammar_point_code,"
                              "evidence_exam_id")
            if r["evidence_exam_id"] is None}

    print("=" * 74)
    print(" 5·6과 학교별 출제 범위 — 배부물 근거")
    print("=" * 74)
    print("  INSERT 만 합니다. 기존 행은 건드리지 않습니다.\n")

    new = []
    for school, unit, code, why in ROWS:
        sid = schools.get(school)
        if sid is None:
            raise SystemExit(f"학교 레코드가 없습니다: {school}")
        mark = "건너뜀 (이미 있음)" if (sid, unit, code) in have else "넣음"
        print(f"  {school} · {unit} · {code:24} {mark}")
        print(f"      {why[:96]}")
        if mark == "넣음":
            new.append({"school_id": sid, "grade": 2, "textbook_id": book,
                        "textbook_unit": unit, "grammar_point_code": code,
                        "confidence": "high",
                        "note": why + " · 배부물 전수 판독 2026-09-07 · "
                                      "is_extension(교과서 범위 초과 여부)은 원장 판단 필요"})
                        # updated_by 는 uuid(auth 사용자)라 비워 둔다 — 근거는 note 에 있다

    print(f"\n  넣을 행 {len(new)} / {len(ROWS)}")
    if not new:
        return 0
    if not a.apply:
        print("  [미리보기] 실제로 넣으려면 --apply")
        return 0

    rest.insert("school_grammar_map", new)
    total = len(rest.get("/school_grammar_map?select=id"))
    print(f"  넣었습니다. school_grammar_map 총 {total} 행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
