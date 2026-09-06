# -*- coding: utf-8 -*-
"""
남은 후보 어법 포인트 7종 정식 승인. 원장 승인 2026-09-06.

  python db/007_approve_remaining_points.py --apply

**UPDATE 7건뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).

## 이 7종은 어떻게 놓쳤나

`master_candidates.json` 에는 5개만 적혀 있었다. 그런데 DB 를 보니 `is_candidate=true`
가 10종이었다. 파일에 기록되지 않은 채 시드·인제스트로 들어간 것이 7종 더 있었던 것이다.

클로드는 원장에게 「후보는 3개」라고 답했는데, **파일만 보고 DB 를 안 봤다.**
마스터의 상태를 묻는 질문에는 마스터를 봐야 한다. 재발을 막으려고
`tools/check_schema.py` 가 후보 코드 수를 항상 찍도록 했다.

## 승인 근거

넷은 2026-1 기말 4개교 기출에서 직접 확인된다. 그리고 **이미 오늘 넣은
`school_grammar_map` 28행에 쓰이고 있었다** — 정식 승인 없는 코드를 정식처럼 쓰던 셈이다.

셋은 이번 기출에는 없고 지문 태그에서만 쓰인다. `VERB_PERFECT` 와 같은 이유로
승인한다 — 기출 표본이 **1회차뿐**이라 「이번에 안 나왔다」로 「안 나온다」를
판정할 수 없다 (원장: 「결과적으로 언젠간 다룬다」).
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

BASE = "2026-09-06 원장 정식 승인. "
EVIDENCE = "1회차 표본만으로 판정하지 않는다 (원장 「결과적으로 언젠간 다룬다」). "

CODES = {
    "NOUN_CLAUSE_IF":   BASE + "근거: 청명중 문항 25 · 태장중 문항 18 (조건절 if 와 구별). "
                               "school_grammar_map 2행에서 사용 중이었다.",
    "NOUN_CLAUSE_THAT": BASE + "근거: 영일중 문항 21 (Remember that ~). "
                               "school_grammar_map 1행에서 사용 중이었다.",
    "REL_POSSESSIVE":   BASE + "근거: 영일중 문항 12 · 21 (whose). "
                               "school_grammar_map 1행에서 사용 중이었다.",
    "VERB_MODAL_USAGE": BASE + "근거: 영덕중 문항 6 · 영일중 문항 11 · 태장중 문항 3. "
                               "school_grammar_map 3행에서 사용 중이었다.",
    "MOD_POSTPOSITIVE": BASE + "2026-1 기말 4개교에는 없었으나 지문 태그에서 사용 중. " + EVIDENCE,
    "PRON_INDEFINITE":  BASE + "2026-1 기말 4개교에는 없었으나 지문 태그에서 사용 중. " + EVIDENCE,
    "SENSE_VERB_ADJ":   BASE + "2026-1 기말 4개교에는 없었으나 지문 태그에서 사용 중. " + EVIDENCE,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    rows = {g["code"]: g for g in r.get("/grammar_point?select=code,label_ko,is_candidate,note")}
    used = {m["grammar_point_code"] for m in r.get("/school_grammar_map?select=grammar_point_code")}
    tagged = {t["grammar_point_code"] for t in r.get("/passage_tag?select=grammar_point_code")}

    print("=" * 74)
    print(f" 남은 후보 어법 포인트 승인 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print("  실행 SQL: UPDATE. DELETE / DROP / TRUNCATE 없음.\n")

    todo = []
    for code in CODES:
        g = rows.get(code)
        if not g:
            print(f"  X {code} 가 마스터에 없습니다 — 아무것도 쓰지 않고 중단")
            return 1
        where = " · ".join(filter(None, [
            "school_grammar_map" if code in used else "",
            "지문 태그" if code in tagged else ""])) or "미사용"
        print(f"  [{'후보' if g['is_candidate'] else '정식'}] {code:20} {g['label_ko']:28} {where}")
        if g["is_candidate"]:
            todo.append(code)

    print(f"\n  승격 대상 {len(todo)}종")
    if not a.apply:
        print("  실제로 쓰려면 --apply")
        return 0

    for code in todo:
        note = rows[code].get("note") or ""
        r.patch("grammar_point", f"code=eq.{code}",
                {"is_candidate": False, "note": (note + " · " if note else "") + CODES[code]})

    left = [g["code"] for g in r.get("/grammar_point?select=code,is_candidate")
            if g["is_candidate"]]
    print(f"\n  {len(todo)}종 승격 완료 · 후보로 남은 것 {len(left)}종 {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
