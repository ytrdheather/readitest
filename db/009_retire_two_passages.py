# -*- coding: utf-8 -*-
"""
대표 문형이 붙어 있던 지문 2개를 DB 에서 물러나게 한다. 원장 지시 2026-09-06.

  python db/009_retire_two_passages.py --apply

**UPDATE 만 한다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
행을 지우지 않는 이유: 무엇이 있었는지가 남아야 나중에 「이 지문 왜 두 벌이냐」에
답할 수 있다. `_retired/` 폴더와 같은 취급이다.

  transcription_status  confirmed → disputed
  title                 'L5 대화-1' → 'L5 대화-1 (물러남 2026-09-06)'

제목까지 바꾸는 이유: 새 레코드가 같은 제목을 쓴다. 그대로 두면 `--passage` 로
찾을 때 둘이 같이 잡히고, 어느 것이 현행인지 화면에서 구별되지 않는다.

새 본문은 `db/008_ingest_passages.py --apply` 가 넣는다 — 해시가 다르므로
중복으로 걸리지 않는다.
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

TITLES = ["L5 대화-1", "L5 대화-4"]
NOTE = ("2026-09-06 물러남. 대화 끝에 자습서 대표 문형이 붙어 있었다 — 원장 설명 "
        "「~ 라는 것은 거기에 장소 이름을 넣으라는 표식이야」. 지문이 아니라 옆단 "
        "표제 문형이라 본문에서 떼고 key_expressions 로 옮겼다. 확정된 body_text 는 "
        "고치지 않는다는 원칙(설계원칙 7)에 따라 새 레코드를 만들었다.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    rows = [p for p in r.get("/passage?select=id,title,body_text,transcription_status")
            if p["title"] in TITLES]
    print("=" * 74)
    print(f" 지문 2개 물러나게 하기 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE. DELETE / DROP / TRUNCATE 없음.\n")

    todo = []
    for p in rows:
        has = "~" in p["body_text"]
        print(f"  {p['title']:14} status={p['transcription_status']:10} "
              f"대표문형 남아있음={has}")
        if has and p["transcription_status"] != "disputed":
            todo.append(p)

    if not todo:
        print("\n  물러나게 할 행이 없습니다 (이미 처리됐거나 대상이 아님)")
        return 0
    print(f"\n  대상 {len(todo)}행")
    if not a.apply:
        print("  실제로 쓰려면 --apply")
        return 0

    for p in todo:
        r.patch("passage", f"id=eq.{p['id']}", {
            "transcription_status": "disputed",
            "title": f"{p['title']} (물러남 2026-09-06)",
            "transcription_note": NOTE,
        })
    print(f"\n  {len(todo)}행 disputed 로 표시 완료")
    print("  이어서:  python db/008_ingest_passages.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
