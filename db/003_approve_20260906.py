# -*- coding: utf-8 -*-
"""
2026-09-06 원장 승인 3건 반영.

  python db/003_approve_20260906.py          # 무엇을 쓸지 보여주기만 한다
  python db/003_approve_20260906.py --apply  # 실제로 쓴다

## 실행되는 SQL 종류

**INSERT 와 UPDATE 뿐이다. DELETE · DROP · TRUNCATE 는 없다** (CLAUDE.md 규칙 4).
두 번 돌려도 안전하다 — 이미 있는 행은 건너뛴다.

## 승인 내용 (근거: data/stage0/comparisons/4개교_2026-1기말_문항분석.md)

  1. school_grammar_map 28행 — 4개교 96문항 전수 분류에서 나온 것
  2. modification_type 3종 — 지문 재구성 축
  3. question_type T-WORD-ORDER 승인 — 영덕 2문항 10점

## 코드 이름을 RC_ 가 아니라 RU_ 로 바꾼 이유

제안할 때는 `RC_PASSAGE_MERGE` 였다. 그런데 이 테이블은 **접두사가 category 를
그대로 따른다**: `EI_`→error_injection, `BO_`→blank_out, `CO_`→cosmetic,
`RU_`→reuse. category 의 CHECK 제약은 이 넷뿐이라 새 값을 넣으려면 제약을 갈아야 하고,
그건 승인받은 범위 밖이다. 재구성은 「원문 자산을 다른 형태로 **재사용**」이므로
reuse 로 들어가는 것이 무리가 없다. 규칙을 깨지 않으면서 뜻도 맞는 쪽을 골랐다.

## textbook_unit 을 'Lesson 3-4' 로 둔 이유

2026-1 기말의 출제 범위가 L3~L4 두 단원이다. 어느 포인트가 어느 단원 소속인지는
**교과서 문법 차례와 대조해야** 알 수 있는데 그 근거가 아직 없다. 근거 없이 한 단원에
넣으면 나중에 단원별 예측이 조용히 틀린다. 범위를 그대로 적고 note 에 남긴다.
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

SRC = "4개교 2026-1 기말 96문항 전수 분류 (2026-09-06) · 원장 승인"

# (학교, 포인트, 근거 문항)
MAP_ROWS = [
    ("영덕중", "VOICE_ACTIVE_PASSIVE", "문항 3(단문 나열) · 10(Bicycle 지문)"),
    ("영덕중", "VOICE_PARTICIPLE",     "문항 14 (ice cream cone 빈칸 짝짓기)"),
    ("영덕중", "VERB_MODAL_USAGE",     "문항 6 (will must / don't have to / needs to)"),
    ("영덕중", "IT_CLEFT",             "문항 5 — 비인칭 it vs 대명사 it (교사 자작 날씨 대화)"),
    ("영덕중", "NONFIN_TO_VS_GERUND",  "문항 12 (Whiteout·Webcam to부정사 용법 구별)"),
    ("영덕중", "VERB_TENSE",           "문항 8 — 조건절에 미래시제 (if you will compare)"),
    ("영덕중", "REL_PRON_VS_ADV",      "문항 8 · 20 (who/which · 어순 배열)"),

    ("영일중", "VOICE_ACTIVE_PASSIVE", "문항 2 · 16 (교사 자작 단락, 자동사 수동태 오류 포함)"),
    ("영일중", "VOICE_PARTICIPLE",     "문항 10 · 12 — 감정분사 집중 (boring/surprised/tiring)"),
    ("영일중", "REL_POSSESSIVE",       "문항 12 · 21 (whose)"),
    ("영일중", "VERB_TENSE",           "문항 12 — 조건절에 미래시제 (If you will cook)"),
    ("영일중", "VERB_MODAL_USAGE",     "문항 11 (박물관 안내문 must / don't have to)"),
    ("영일중", "PREP_USAGE",           "문항 15 (by/behind · in/on · to/into)"),
    ("영일중", "NONFIN_TO_VS_GERUND",  "문항 21 (lead to + -ing)"),
    ("영일중", "NOUN_CLAUSE_THAT",     "문항 21 (Remember that ~)"),

    ("청명중", "VOICE_ACTIVE_PASSIVE", "문항 9 · 10 · 15 — 3문항. 이 학교 최다 포인트"),
    ("청명중", "VOICE_PARTICIPLE",     "문항 15 (단문 나열형)"),
    ("청명중", "REL_PRON_VS_ADV",      "문항 24 (단문 나열형, 수일치 결합)"),
    ("청명중", "NOUN_CLAUSE_IF",       "문항 25 (단문 나열형, 조건절 시제 결합)"),
    ("청명중", "NONFIN_TO_VS_GERUND",  "문항 12 (to부정사 용법 구별)"),
    ("청명중", "PREP_USAGE",           "문항 5 (Webcam 지문 빈칸 짝짓기)"),
    ("청명중", "MOD_ADJ_VS_ADV",       "문항 10 (difficult / difficultly)"),

    ("태장중", "VOICE_ACTIVE_PASSIVE", "문항 3(단문 나열) · 15(외부지문 짝짓기)"),
    ("태장중", "VOICE_PARTICIPLE",     "문항 15 (embarrassed / embarrassing)"),
    ("태장중", "REL_PRON_VS_ADV",      "문항 11 (외부지문 빈칸 which)"),
    ("태장중", "NOUN_CLAUSE_IF",       "문항 18 (조건절 if vs 명사절 if 구별)"),
    ("태장중", "VERB_MODAL_USAGE",     "문항 3 (Did she has to)"),
    ("태장중", "VERB_SVA",             "문항 15 (incorrect facts is/are)"),
]

MOD_ROWS = [
    {"code": "RU_PASSAGE_MERGE", "category": "reuse",
     "label_ko": "지문 병합 — 지문 둘 이상을 [A][B] 로 묶어 한 문항군으로",
     "example_before": "Whiteout / Webcam 을 각각 출제",
     "example_after": "[A] Whiteout [B] Webcam 을 나란히 두고 표로 대조시킨 뒤 빈칸 영작",
     "observed_count": 3},
    {"code": "RU_FORMAT_RECAST", "category": "reuse",
     "label_ko": "형식 전환 — 본문을 표·에세이·포스터·광고 문구로 바꿔 제시",
     "example_before": "impulse buying 본문 그대로",
     "example_after": "「올바른 소비 습관 캠페인 포스터」로 재조판하고 취지에 안 맞는 항목 고르기",
     "observed_count": 4},
    {"code": "RU_VOCAB_TRANSPLANT", "category": "reuse",
     "label_ko": "어휘 이식 — 본문 어휘를 교과서 밖 창작 지문에 심어 출제",
     "example_before": "본문의 spend / donation / save",
     "example_after": "창작 지문 「My Money Plan」에 같은 어휘를 넣고 빈칸 짝짓기",
     "observed_count": 2},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 쓴다 (없으면 보기만)")
    a = ap.parse_args()
    r = Rest()

    schools = {s["name"]: s["id"] for s in r.get("/school?select=id,name")}
    # 질의문자열에 한글을 넣지 않는다 — PostgREST 로 가는 URL 은 ascii 여야 한다.
    # 행이 몇 개 안 되므로 받아서 파이썬에서 고른다.
    textbook = next(t["id"] for t in r.get("/textbook?select=id,publisher,author,grade")
                    if t["publisher"] == "동아" and t["author"] == "윤정미" and t["grade"] == 2)
    exams = {e["school_id"]: e["id"]
             for e in r.get("/exam?select=id,school_id,grade,year,semester,sitting")
             if (e["grade"], e["year"], e["semester"], e["sitting"]) == (2, 2026, 1, "기말")}
    points = {p["code"] for p in r.get("/grammar_point?select=code")}

    have = {(m["school_id"], m["grammar_point_code"])
            for m in r.get("/school_grammar_map?select=school_id,grammar_point_code")}
    have_mod = {m["code"] for m in r.get("/modification_type?select=code")}

    print("=" * 74)
    print(f" 2026-09-06 승인 반영 — {'실제 적용' if a.apply else '미리보기 (쓰지 않음)'}")
    print("=" * 74)
    print("  실행 SQL: INSERT · UPDATE 만. DELETE / DROP / TRUNCATE 없음.\n")

    # ── 1. school_grammar_map ──────────────────────────────────
    rows, skipped, bad = [], 0, []
    for school, code, why in MAP_ROWS:
        if code not in points:
            bad.append((school, code))
            continue
        sid = schools[school]
        if (sid, code) in have:
            skipped += 1
            continue
        rows.append({
            "school_id": sid, "grade": 2, "textbook_id": textbook,
            "textbook_unit": "Lesson 3-4",
            "grammar_point_code": code,
            "evidence_exam_id": exams.get(sid),
            "confidence": "high",
            "note": f"{why} · 출제범위 L3~L4 이라 단원 귀속은 미판정 (교과서 문법 차례 대조 필요) · {SRC}",
        })
    if bad:
        print("  X 마스터에 없는 포인트 코드 — 중단합니다")
        for s, c in bad:
            print(f"     {s} {c}")
        return 1
    print(f"[1] school_grammar_map  새로 {len(rows)}행 · 이미 있어 건너뜀 {skipped}행")
    for row in rows:
        name = next(k for k, v in schools.items() if v == row["school_id"])
        print(f"      {name}  {row['grammar_point_code']}")

    # ── 2. modification_type ───────────────────────────────────
    mods = [m for m in MOD_ROWS if m["code"] not in have_mod]
    print(f"\n[2] modification_type  새로 {len(mods)}종 · 이미 있어 건너뜀 "
          f"{len(MOD_ROWS) - len(mods)}종")
    for m in mods:
        print(f"      {m['code']:22} [{m['category']}] {m['label_ko']}")

    # ── 3. T-WORD-ORDER 승인 ───────────────────────────────────
    qt = r.get("/question_type?select=code,value_approved&code=eq.T-WORD-ORDER")
    need_qt = bool(qt) and qt[0]["value_approved"] is not True
    print(f"\n[3] question_type T-WORD-ORDER  "
          f"{'미검수 → 승인' if need_qt else '이미 승인됨 — 건너뜀'}")

    if not a.apply:
        print("\n  실제로 쓰려면 --apply")
        return 0

    if rows:
        r.insert("school_grammar_map", rows)
    if mods:
        r.insert("modification_type", mods)
    if need_qt:
        # 'now()' 를 문자열로 보내면 PostgreSQL 이 timestamptz 로 못 바꾼다.
        # ISO 문자열을 직접 만든다.
        r.patch("question_type", "code=eq.T-WORD-ORDER", {
            "value_approved": True,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "note": ("1차 검수지 Q10. 2026-09-06 승인 — 영덕중 2026-1 기말 문항 4·20 에서 "
                     "2문항 10점으로 실제 출제 확인. 변형 BO_WORD_ORDER 에 대응."),
        })
    print("\n  적용 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
