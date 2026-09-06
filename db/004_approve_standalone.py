# -*- coding: utf-8 -*-
"""
`T-GRAMMAR-STANDALONE`(어법 — 단문 나열형) 반려를 뒤집는다. 원장 승인 2026-09-06.

  python db/004_approve_standalone.py          # 보기만
  python db/004_approve_standalone.py --apply

**UPDATE 한 건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

## 왜 뒤집는가

2026-08-09 에 `DETACHED_FROM_PASSAGE`(지문 비연계 — 훈련 가치 없음)로 반려했다.
그 판단의 근거는 **훈련 가치**였고, 「이 유형이 출제되지 않는다」는 관측이 아니었다.
그런데 지금까지 그것을 「안 나온다」처럼 취급해 왔다.

2026-09-06 4개교 96문항 전수 분류 결과:

    청명중  문항 9 · 15 · 24 · 25   20점 (100점 중 20%)
    영덕중  문항 3 · 8               8점
    태장중  문항 3                   4점
    영일중  —                        0점

원장 판단: 「저런 유형의 문제 꽤나 자주 나온다.」 시험지 한 회차가 아니라 **여러 해를
본 사람의 관측**이고, 우리 표본(4개교 1회차)은 그것과 어긋나지 않는다.

## 클로드가 틀렸던 지점

「반려는 유지하고 드릴로만 만들자」고 권했다. 유형 반려와 출제 빈도를 구분한 데까지는
맞았지만, **빈도를 모르면서 「문항으로는 안 만들어도 된다」고 판단한 것**이 틀렸다.
학교 대비 자료에서 20점짜리 유형을 문항으로 안 만들 이유는 없다.

기록으로 남기는 이유: 같은 실수를 반복하지 않으려면 「무엇을 몰랐는지」가 남아야 한다.
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

CODE = "T-GRAMMAR-STANDALONE"
NOTE = ("2026-08-09 DETACHED_FROM_PASSAGE 로 반려 → 2026-09-06 원장 승인으로 뒤집음. "
        "반려 근거는 '훈련 가치'였지 '출제되지 않는다'가 아니었는데 후자처럼 취급해 왔다. "
        "4개교 2026-1 기말 전수 분류: 청명 20점(문항 9·15·24·25) · 영덕 8점(3·8) · "
        "태장 4점(3) · 영일 0점. 원장 관측 「저런 유형의 문제 꽤나 자주 나온다」. "
        "근거: data/stage0/comparisons/4개교_2026-1기말_문항분석.md §3")


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
    print(f" {CODE} 반려 해제 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE 1건. DELETE / DROP / TRUNCATE 없음.\n")
    print(f"  현재  value_approved={row['value_approved']}  "
          f"tier_reason={row['tier_reason']!r}")
    print(f"  변경  value_approved=True   tier_reason='정오 판정만 — 선지가 독립 문장이라 연속 판정'")

    if row["value_approved"] is True:
        print("\n  이미 승인 상태입니다 — 할 일 없음")
        return 0
    if not a.apply:
        print("\n  실제로 쓰려면 --apply")
        return 0

    r.patch("question_type", f"code=eq.{CODE}", {
        "value_approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        # 검수 티어는 fast 그대로다. 선지가 독립 문장이라 한 줄씩 정오만 보면 되고,
        # 이건 §7.1.3 의 「78%가 20~30초」쪽에 해당한다.
        "tier_reason": "정오 판정만 — 선지가 독립 문장이라 연속 판정",
        "note": NOTE,
    })
    print("\n  적용 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
