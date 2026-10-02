# -*- coding: utf-8 -*-
"""
리디플랜 연동 준비 — 조사(docs/리디플랜_연동_데이터조사.md §10)의 1·2·3 (원장 승인 2026-10-02).

  python db/015_readiplan_prep.py            # 무엇이 바뀌는지 보기만 (쓰지 않음)
  python db/015_readiplan_prep.py --apply

**INSERT 와 UPDATE 만 한다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
UPDATE 는 `passage.textbook_id` 한 컬럼뿐이다. `body_text` 는 건드리지 않는다 (설계원칙 7).
여러 번 돌려도 안전하다 — 이미 된 것은 건너뛴다.

## 무엇을 하나 (실행 순서. 중1 시험이 중1 교과서를 참조하므로 3 → 2 → 1)

3. **중1 교과서 행 추가 + 중1 지문 `textbook_id` 정정.**
   `textbook` 에 중2 한 행뿐이라 `008_ingest_passages.py` 가 중1 지문 27개에도 중2 교과서를 붙였다.
   두 학년 모두 L5·L6 이 있어 단원으로 묶으면 섞인다. 지문 파일의 `textbook.grade` 가 1 인 교과서 지문을
   **본문 해시로** DB 행과 짝지어 고친다 (제목으로 짝짓지 않는다).
2. **시험 행 추가** — 중2 2026-2 중간 4건(블루프린트의 날짜), 중1 2025-2 기말 3건(기출 판독 파일).
   방금 끝났거나 다가오는 시험의 구조(문항 수 등)는 아직 관측 전이라 비운다.
1. **`school_grammar_map` 누락 1행 보충.** 영덕 2026-1 기말 12번(to부정사 용법 구별)이 `003` 에서
   (학교, 코드)만으로 중복이 걸러져 버려졌다. 2회째 관측을 버리면 「단골」을 판정할 수 없다.
   이 스크립트와 `002`·`013` 은 이제 **근거 시험까지** 키에 넣는다.
   코드는 원장 결정(2026-10-02)으로 9/6 분류표의 `NONFIN_TO_VS_GERUND` 가 아니라 `NONFIN_TO_ROLE`
   (to부정사 용법 — 명사적·형용사적·부사적)로 넣는다. 12번은 「부사적 vs 명사적」 구별 문항이라
   to부정사와 동명사를 고르는 문항이 아니다. `NONFIN_TO_ROLE` 은 아직 후보(is_candidate) 코드다.
"""
import argparse
import glob
import hashlib
import json
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

PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")
G1 = {"publisher": "동아", "author": "윤정미", "curriculum_version": "2022개정", "grade": 1}

# (학교, 학년, 연도, 학기, 회차, 시험일, 선택, 서술, 총점, 쪽, 교과서 학년, 근거)
EXAMS = [
    ("영일중", 2, 2026, 2, "중간", "2026-09-29", None, None, None, None, 2, "mock_exam_blueprint.json"),
    ("청명중", 2, 2026, 2, "중간", "2026-09-30", None, None, None, None, 2, "mock_exam_blueprint.json"),
    ("태장중", 2, 2026, 2, "중간", "2026-10-01", None, None, None, None, 2, "mock_exam_blueprint.json"),
    # 영덕은 015 때 「10월 둘째 주」라 비웠고, 원장이 10-07 로 알려 016 에서 채웠다.
    ("영덕중", 2, 2026, 2, "중간", "2026-10-07", None, None, None, None, 2, "mock_exam_blueprint.json"),
    ("영덕중", 1, 2025, 2, "기말", "2025-11-17", 17, 4, 100, 5, 1, "comparisons/중1_영덕_2025기말_기출.md"),
    ("영일중", 1, 2025, 2, "기말", "2025-11-17", 20, 4, 100, 5, 1, "comparisons/중1_영일_2025기말_기출.md"),
    ("태장중", 1, 2025, 2, "기말", "2025-11-26", 22, 2, 100, 6, 1, "comparisons/중1_태장_2025기말_기출.md"),
]

# (학교, 코드, 단원, 근거 시험(학년·연도·학기·회차), note)
MAPS = [
    ("영덕중", "NONFIN_TO_ROLE", "Lesson 3-4", (2, 2026, 1, "기말"),
     "문항 12 (to부정사 용법 구별 — 부사적 vs 명사적) · 4개교 2026-1 기말 96문항 전수 분류 (2026-09-06). "
     "9/6 표에는 NONFIN_TO_VS_GERUND 로 승인됐으나 003 이 (학교, 코드) 중복으로 걸러 누락. "
     "2026-10-02 원장 결정으로 NONFIN_TO_ROLE 로 보충 (015)"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 쓴다")
    a = ap.parse_args()
    r = Rest(load_env())

    print("=" * 74)
    print(f" 015 리디플랜 연동 준비 — {'실제 적용' if a.apply else '미리보기 (쓰지 않음)'}")
    print("=" * 74)
    print("  실행 SQL: INSERT · UPDATE(passage.textbook_id) 만. DELETE / DROP / TRUNCATE 없음.\n")

    books = r.get("/textbook?select=id,publisher,author,curriculum_version,grade")

    def book_id(grade):
        return next((b["id"] for b in books
                     if (b["publisher"], b["author"], b["curriculum_version"], b["grade"])
                     == ("동아", "윤정미", "2022개정", grade)), None)

    # ── 3-a. 중1 교과서 ───────────────────────────────────────
    g2 = book_id(2)
    if g2 is None:
        raise SystemExit("동아 윤정미 중2 교과서 레코드를 못 찾았습니다")
    g1 = book_id(1)
    print(f"[3-a] textbook 동아(윤정미) 2022개정 중1  {'이미 있음' if g1 else '넣음'}")
    if g1 is None and a.apply:
        g1 = r.insert("textbook", [G1])[0]["id"]

    # ── 3-b. 중1 지문 textbook_id 정정 (본문 해시로 짝짓기) ────────
    shas = set()
    for f in sorted(glob.glob(os.path.join(PASSAGES, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        tb = d.get("textbook") or {}
        if d.get("source_type") == "교과서" and tb.get("grade") == 1:
            shas.add(hashlib.sha256(d["body_text"].encode("utf-8")).hexdigest())
    pgs = r.get("/passage?select=id,title,textbook_id,body_text_sha256")
    fix = [p for p in pgs if p["body_text_sha256"] in shas and p["textbook_id"] == g2]
    done = [p for p in pgs if p["body_text_sha256"] in shas and g1 and p["textbook_id"] == g1]
    odd = [p["title"] for p in pgs if (p["title"] or "").startswith("중1")
           and p["body_text_sha256"] not in shas]
    print(f"[3-b] passage.textbook_id 중2 → 중1  고칠 것 {len(fix)} · 이미 중1 {len(done)}"
          f"  (중1 교과서 지문 파일 {len(shas)}개 기준)")
    if odd:
        print(f"      ⚠ 제목은 「중1」인데 교과서 지문 파일과 해시가 안 맞는 행 {len(odd)}: {odd} — 건드리지 않음")
    if fix and a.apply:
        ids = ",".join(p["id"] for p in fix)
        got = r.patch("passage", f"id=in.({ids})&textbook_id=eq.{g2}", {"textbook_id": g1})
        print(f"      고쳤습니다 {len(got)}행")

    # ── 2. 시험 ────────────────────────────────────────────
    schools = {s["name"]: s["id"] for s in r.get("/school?select=id,name")}
    key = {(e["school_id"], e["grade"], e["year"], e["semester"], e["sitting"]): e["id"]
           for e in r.get("/exam?select=id,school_id,grade,year,semester,sitting")}
    print("\n[2] exam")
    new_exams = []
    for school, gr, y, sem, sit, date, mc, es, tot, pg, tbg, src in EXAMS:
        sid = schools[school]
        have = (sid, gr, y, sem, sit) in key
        print(f"  {school}{gr} {y}-{sem} {sit}  {date or '날짜 미정':10}  "
              f"{'이미 있음' if have else '넣음'}  ← {src}")
        if not have:
            new_exams.append({"school_id": sid, "grade": gr, "year": y, "semester": sem, "sitting": sit,
                              "exam_date": date, "textbook_id": g1 if tbg == 1 else g2,
                              "mc_count": mc, "essay_count": es, "total_score": tot, "page_count": pg})
    if new_exams and a.apply:
        got = r.insert("exam", new_exams)
        for e in got:
            key[(e["school_id"], e["grade"], e["year"], e["semester"], e["sitting"])] = e["id"]
        print(f"  넣었습니다 {len(got)}행")

    # ── 1. school_grammar_map 누락분 (키 = 학교 · 코드 · 근거 시험) ──────
    points = {p["code"] for p in r.get("/grammar_point?select=code")}
    have = {(m["school_id"], m["grammar_point_code"], m["evidence_exam_id"])
            for m in r.get("/school_grammar_map?select=school_id,grammar_point_code,evidence_exam_id")}
    print("\n[1] school_grammar_map (중복 판정: 학교 · 코드 · 근거 시험)")
    new_maps = []
    for school, code, unit, (gr, y, sem, sit), why in MAPS:
        if code not in points:
            raise SystemExit(f"마스터에 없는 포인트 코드: {code}")
        sid = schools[school]
        eid = key.get((sid, gr, y, sem, sit))
        if eid is None:
            raise SystemExit(f"근거 시험이 DB 에 없습니다: {school}{gr} {y}-{sem} {sit}")
        mark = "이미 있음" if (sid, code, eid) in have else "넣음"
        print(f"  {school} · {code} · {gr}학년 {y}-{sem} {sit}  {mark}")
        if mark == "넣음":
            new_maps.append({"school_id": sid, "grade": gr, "textbook_id": g2, "textbook_unit": unit,
                             "grammar_point_code": code, "evidence_exam_id": eid,
                             "confidence": "high", "note": why})
    if new_maps and a.apply:
        r.insert("school_grammar_map", new_maps)
        print(f"  넣었습니다 {len(new_maps)}행")

    if not a.apply:
        print("\n  [미리보기] 실제로 쓰려면 --apply")
        return 0
    print(f"\n  완료. textbook {len(r.get('/textbook?select=id'))} · exam {len(r.get('/exam?select=id'))}"
          f" · school_grammar_map {len(r.get('/school_grammar_map?select=id'))} 행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
