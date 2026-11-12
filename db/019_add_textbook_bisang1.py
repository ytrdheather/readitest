# -*- coding: utf-8 -*-
"""
비상(황종배) 2022개정 중1 교과서 행을 넣는다 — 청명중1 5과 지문을 008 이 받으려면 필요하다.

  python db/019_add_textbook_bisang1.py            # 미리보기
  python db/019_add_textbook_bisang1.py --apply

**INSERT 하나뿐이다. DELETE · DROP · TRUNCATE · UPDATE 없음** (CLAUDE.md 규칙 4).
이미 있으면 아무것도 안 한다.

주의: `015_readiplan_prep.py` 3-b 는 「grade 1 교과서 지문 중 textbook_id 가 동아 중2 인 것」만
동아 중1 로 옮긴다. 비상 지문은 처음부터 이 행으로 들어가므로 015 를 다시 돌려도 안 건드린다.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pipeline.supabase import Rest  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROW = {"publisher": "비상", "author": "황종배", "curriculum_version": "2022개정", "grade": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()
    print("  실행 SQL: INSERT 1행. DELETE / DROP / TRUNCATE 없음.")
    have = [t for t in r.get("/textbook?select=id,publisher,author,curriculum_version,grade")
            if (t["publisher"], t["author"], t["curriculum_version"], t["grade"])
            == (ROW["publisher"], ROW["author"], ROW["curriculum_version"], ROW["grade"])]
    if have:
        print(f"  이미 있음 {have[0]['id']}")
        return
    if not a.apply:
        print(f"  넣을 것: {ROW}  (--apply 로 실제 적용)")
        return
    print("  넣음", r.insert("textbook", [ROW])[0]["id"])


if __name__ == "__main__":
    main()
