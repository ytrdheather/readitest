# -*- coding: utf-8 -*-
"""
`T-FORM-CHOICE`(어법 — 빈칸 어형 짝짓기) 승인. 원장 승인 2026-09-06.

  python db/005_approve_form_choice.py --apply

**UPDATE 한 건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

## 원장 관측이 분류를 교정했다

원장: 「꼭 전체 22~25문항 중에 1개씩 차지하는 문항이다.」

이 말을 듣고 다시 세어 보니 **학교당 정확히 1문항**이다.

    영덕중 14   accepted/accepting/to accept × unexpecting/unexpected × selling/sold
    영일중 21   wasting/waste × whose/who × that/which
    청명중 10   exploded/was exploded × As/On × difficult/difficultly × killed/were killed
    태장중 15   is/are × fooled/fooling × embarrassed/embarrassing

클로드는 처음에 「4개교가 전부, 태장 10·15 / 청명 5·10·18 / 영덕 3·14·20·21 / 영일 21」
이라고 적었다. **형식이 닮았다는 이유로 다른 유형까지 끌어다 붙인 것**이다.

  · 영덕 3   → 독립 문장 나열이므로 `T-GRAMMAR-STANDALONE`
  · 영덕 20  → 어순 배열이므로 `T-WORD-ORDER`
  · 영덕 21 · 청명 18 · 태장 10 → 조합 선택 형식은 같지만 고르는 것이 **어휘**다
  · 청명 5 · 영일 15 → 같은 형식이지만 고르는 것이 **전치사**다

`T-FORM-CHOICE` 는 「같은 낱말의 **어형**을 고르는 것」이다. 세 갈래를 한 코드로 묶으면
드릴을 만들 때 무엇을 연습시키는지가 흐려진다.

## 이 유형이 갖는 특별한 성질 — 세트당 1문항 보장

다른 유형은 학교마다 있고 없고가 갈리는데(서술형은 영일·태장만, 단문 나열형은 영일 0),
**이 유형만은 4개교가 예외 없이, 그것도 딱 하나씩 낸다.**

→ 3층 동형 모의고사를 만들 때 **세트마다 이 유형 1문항이 반드시 들어가야 한다.**
   기획서 §5.5.4 는 「시험 구조는 예측 축이 아니라 관측만」이라 했는데, 그건 문항 수·
   배점 같은 **구조**에 대한 것이었다. 유형의 **보장 출현**은 그와 다른 축이고,
   원장이 여러 해 보아 온 관측이 근거다.
"""
import argparse
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CODE = "T-FORM-CHOICE"
NOTE = ("2026-09-06 원장 승인. 원장 관측 「꼭 전체 22~25문항 중에 1개씩 차지하는 문항이다」 — "
        "4개교 2026-1 기말에서 학교당 정확히 1문항 확인: 영덕 14 · 영일 21 · 청명 10 · 태장 15. "
        "다른 유형과 달리 4개교 예외 없이 출현하므로 동형 모의고사는 세트당 1문항을 보장해야 한다. "
        "범위 주의: 같은 (a)(b)(c) 조합 선택 형식이라도 고르는 것이 어휘(영덕 21·청명 18·태장 10)나 "
        "전치사(청명 5·영일 15)면 이 유형이 아니다. 이 코드는 같은 낱말의 '어형'을 고르는 것. "
        "근거: data/stage0/comparisons/4개교_2026-1기말_문항분석.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    row = r.get(f"/question_type?select=*&code=eq.{CODE}")
    if not row:
        print(f"  X {CODE} 가 없습니다")
        return 1
    row = row[0]

    print("=" * 74)
    print(f" {CODE} 승인 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE 1건. DELETE / DROP / TRUNCATE 없음.\n")
    print(f"  현재  value_approved={row['value_approved']}")
    print(f"  변경  value_approved=True  (검수 티어 {row['review_tier']} 유지)")

    if row["value_approved"] is True:
        print("\n  이미 승인 상태입니다 — 할 일 없음")
        return 0
    if not a.apply:
        print("\n  실제로 쓰려면 --apply")
        return 0

    r.patch("question_type", f"code=eq.{CODE}", {
        "value_approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        # 조합 선택은 선지 하나가 (a)(b)(c) 세 자리를 한꺼번에 담는다. 그래도 판정은
        # 자리별 정오의 연속이라 fast 다 (§7.1.3).
        "tier_reason": "정오 판정만 — 자리별 어형 정오의 연속",
        "note": NOTE,
    })
    print("\n  적용 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
