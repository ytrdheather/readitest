# -*- coding: utf-8 -*-
"""
어법 포인트 7종 추가 — 본문에 나오는데 담을 칸이 없던 것들. 원장 지시 2026-09-07.

  python db/011_add_grammar_points.py --apply

**INSERT 뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
`is_candidate = true` 로 넣는다 — 원장이 목록을 보고 확정한다.

## 왜 늘리나 — 방향이 바뀌었다

어제까지는 **좁히는** 쪽으로 갔다. 학교별 학습지 범위를 재서 「이 학교는 여기까지」로
가르려 했다. 원장이 정정했다:

> 「That 쓰임의 모든 것들은 당연히 나올 거라고 봐야 하고. 다른 학교에서 안 나온다고
>  하더라도 반드시 알아야 하는 중2 문법이니 정리해서 넣는 게 좋아.」
> 「우리 지역의 영어 시험은 생각보다 범위가 꽤나 넓더라고. 학습지 준 것뿐만 아니라
>  그냥 의례 지난 학기나 지난 달에 배운 것도 나와~ 라는 주의라서.」

**학습지 범위는 그 학교가 무엇을 강조했는지를 말할 뿐, 무엇이 안 나오는지를 말하지
않는다.** 그러니 태깅은 본문에 나오는 문법을 **다 덮어야** 하고, 학교별 범위는 그
위에서 우선순위를 매기는 데 쓴다. 좁히기는 나중 일이다.

## 근거는 전부 5·6과 본문에 있다

코드를 늘리는 것이 부담이라는 판단은 그대로다(31 → 38). 그래서 **본문에서 실제로
관측되는 것만** 넣는다. 아래 evidence 는 전부 확정된 body_text 에서 뽑았다.
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

SRC = "원장 지시 2026-09-07. 근거: data/stage0/comparisons/L5_학교별_문법범위.md"

ROWS = [
    {"code": "REL_OBJECT", "category": "관계사",
     "label_ko": "목적격 관계대명사 (생략 · 목적어 중복 · whom · 전치사+관계대명사)",
     "note": "L5 단원 문법. REL_PRON_VS_ADV(관계대명사 vs 관계부사)와 다른 현상이라 "
             "지금까지 담을 칸이 없어 그쪽으로 갔다. 본문 근거 4곳: "
             "'The place that we are going to visit' · 'the green tree (that) you see' · "
             "'gum that people drop' · 'people (that) he meets'. " + SRC},
    {"code": "THAT_USAGE", "category": "접속",
     "label_ko": "that 의 쓰임 구별 (지시대명사 · 지시형용사 · 접속사 · 관계대명사)",
     "note": "원장: 「that 쓰임의 모든 것은 당연히 나올 거라고 봐야 하고, 다른 학교에서 "
             "안 나와도 반드시 알아야 하는 중2 문법」. Street Art in London 한 편에 "
             "관계대명사 that 4곳 + 명사절 접속사 that 2곳('telling us that nature is…' · "
             "'They think (that) he wants')이 함께 나온다 — 쓰임 구별을 묻기에 맞춤인 지문이다. "
             "실제로 태장중이 이 문항을 냈다(L5 Exercise A 7번). " + SRC},
    {"code": "VERB_USED_TO", "category": "동사",
     "label_ko": "used to / be used to / get used to",
     "note": "본문 'Poor workers used to live in this area'. 태장중은 이것만 별도 "
             "워크시트(5-2)로 다섯 갈래 전부 다룬다(used to+동사원형 / There used to be / "
             "be used to+-ing / 부정·의문문 / get used to). VERB_MODAL_USAGE 는 "
             "have to·must 라 다르다 — 지금 'used to live' 가 거기 붙어 있다. " + SRC},
    {"code": "SVOO_DATIVE", "category": "문형",
     "label_ko": "4형식 (수여동사 + 간접목적어 + 직접목적어) · 3형식 전환",
     "note": "본문 'they will give you a clue'(4형식) · 'they give great pleasure to many "
             "people'(3형식 전환). 앞의 것은 지금 태그가 아예 없고, 뒤의 것은 "
             "VERB_PREP_COLLOCATION 으로 갔다. " + SRC},
    {"code": "SVOC_OBJ_COMPLEMENT", "category": "문형",
     "label_ko": "5형식 (동사 + 목적어 + 목적격보어)",
     "note": "본문 'it makes cities colorful and lively'(make+O+형용사) · "
             "'he wants us to take better care'(want+O+to부정사). 앞의 것은 지금 "
             "MOD_ADJ_VS_ADV 로 가 있는데 핵심은 문형이다. " + SRC},
    {"code": "NONFIN_TO_ROLE", "category": "준동사",
     "label_ko": "to부정사 용법 (명사적 · 형용사적 · 부사적)",
     "note": "본문 'we are going to see some well-known street artworks'(목적) · "
             "'in Finsbury Park to see a painting'(목적) — 둘 다 지금 태그가 없다. "
             "NONFIN_TO_VS_GERUND 는 to 냐 -ing 냐를 묻는 것이라 다른 축이다. " + SRC},
    {"code": "PERCEPTION_VERB_OC", "category": "문형",
     "label_ko": "지각동사 + 목적어 + -ing / 동사원형",
     "note": "L6 단원 문법. 본문 'Dr. Schofield heard people shouting for Korean "
             "independence'. SENSE_VERB_ADJ 는 감각동사 + 형용사 보어라 다른 현상이다. " + SRC},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()
    have = {g["code"] for g in r.get("/grammar_point?select=code")}
    todo = [x for x in ROWS if x["code"] not in have]

    print("=" * 74)
    print(f" 어법 포인트 추가 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: INSERT 만. DELETE / DROP / TRUNCATE 없음.")
    print(f"  마스터 {len(have)}종 → {len(have) + len(todo)}종\n")
    for x in ROWS:
        mark = "새로" if x["code"] in {t["code"] for t in todo} else "이미 있음"
        print(f"  [{mark:8}] {x['code']:22} [{x['category']}] {x['label_ko']}")

    if not todo:
        print("\n  추가할 것이 없습니다")
        return 0
    if not a.apply:
        print(f"\n  {len(todo)}종 추가. 실제로 넣으려면 --apply")
        return 0

    r.insert("grammar_point", [dict(x, is_candidate=True) for x in todo])
    print(f"\n  {len(todo)}종 추가 완료 (is_candidate=true — 원장 확정 대기)")
    print("  마스터 총", len(r.get("/grammar_point?select=code")), "종")
    return 0


if __name__ == "__main__":
    sys.exit(main())
