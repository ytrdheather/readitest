# -*- coding: utf-8 -*-
"""
낡은 태그를 물러나게 한다 (재태깅 전에 돌린다). 원장 승인 2026-09-07.

  python db/012_retire_tags.py            # 무엇이 바뀌는지 보기만
  python db/012_retire_tags.py --apply

**UPDATE 만 한다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

## 왜 지우지 않는가

지우면 「무엇이 있었는지」가 사라진다. 새 코드 7종(§5.5.16)이 생긴 뒤 태깅이
어떻게 달라졌는지는 나중에 품질을 되짚을 때 쓰는 정보다.

`passage_tag.status` 를 `rejected` 로 바꾸고 `rationale` 앞에 이유를 붙인다.
커버리지·과잉률을 셀 때는 `rejected` 를 빼고 세면 된다.

## 검수를 거친 태그는 건드리지 않는다

`status='approved'` 인 38개(goose · impulse)에는 문항과 예상 출제 지점이
걸려 있다(`on delete cascade`). 이건 재태깅 대상이 아니고 여기서도 제외한다.
`pipeline/run.py` 도 같은 규칙으로 그 지문을 잠근다.
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

MARK = ("[2026-09-07 물러남 — 어법 포인트 7종 추가(기획서 §5.5.16) 전에 붙은 태그다. "
        "REL_OBJECT · THAT_USAGE · VERB_USED_TO · SVOO_DATIVE · SVOC_OBJ_COMPLEMENT · "
        "NONFIN_TO_ROLE · PERCEPTION_VERB_OC 를 담을 칸이 없어 가장 가까운 코드로 갔다.] ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    pgs = {p["id"]: p["title"] for p in r.get("/passage?select=id,title")}
    tags = r.get("/passage_tag?select=id,passage_id,status,grammar_point_code,rationale")
    pend = [t for t in tags if t["status"] == "pending"]
    appr = [t for t in tags if t["status"] == "approved"]
    done = [t for t in tags if t["status"] == "rejected"]

    print("=" * 74)
    print(f" 낡은 태그 물러나게 하기 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE. DELETE / DROP / TRUNCATE 없음.\n")
    print(f"  pending  {len(pend):>4}  ← 이번에 물러남")
    print(f"  approved {len(appr):>4}  ← 검수를 거쳤고 문항이 참조한다. 건드리지 않음")
    print(f"  rejected {len(done):>4}  ← 이미 물러난 것")

    from collections import Counter
    c = Counter(pgs.get(t["passage_id"], "?") for t in pend)
    print(f"\n  대상 지문 {len(c)}개")
    for title, n in sorted(c.items()):
        print(f"     {title[:42]:44} {n:>3}개")

    if not pend:
        print("\n  물러나게 할 태그가 없습니다")
        return 0
    if not a.apply:
        print("\n  실제로 쓰려면 --apply")
        return 0

    for i in range(0, len(pend), 100):
        for t in pend[i:i + 100]:
            r.patch("passage_tag", f"id=eq.{t['id']}",
                    {"status": "rejected",
                     "rationale": MARK + (t.get("rationale") or "")})
        print(f"     …{min(i + 100, len(pend))}/{len(pend)}")
    left = [t for t in r.get("/passage_tag?select=status") if t["status"] == "pending"]
    print(f"\n  {len(pend)}개 물러남 · 남은 pending {len(left)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
