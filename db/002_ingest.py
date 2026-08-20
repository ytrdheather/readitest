# -*- coding: utf-8 -*-
"""
0단계 JSON → Supabase 인제스트.

  python db/002_ingest.py                      # 기본 = 검증만. 네트워크도 안 쓴다
  python db/002_ingest.py --apply              # 실제 적재 (없는 것만 추가)
  python db/002_ingest.py --apply --allow-new-codes
                                               # 마스터 후보 코드까지 함께 적재
  python db/002_ingest.py --apply --reset      # ★ DELETE 포함. 아래 경고 참조

──────────────────────────────────────────────────────────────────────
파괴적 동작 고지 (CLAUDE.md 작업규칙 4)

  --reset 은 이 스크립트가 적재하는 지문·시험에 딸린 행을 DELETE 한 뒤 다시 넣습니다.
  대상: passage_tag / passage_logic / predicted_item_site / item(→option·check 연쇄)
        / passage_variant / exam_observation  중 해당 passage_id·exam_id 의 것만.
  마스터 테이블(grammar_point 등)과 school·textbook 은 건드리지 않습니다.
  --reset 없이는 DELETE 가 한 번도 실행되지 않습니다.
──────────────────────────────────────────────────────────────────────

검증(--dry-run)에서 잡는 것 — 전부 네트워크 없이:
  · body_text 의 sha256 이 기록값과 일치하는가        (설계원칙 7: 확정 후 불변)
  · 태그 스팬이 body_text[start:end] == surface 인가   (span 어긋남 = 조용한 재앙)
  · span_end > span_start (스키마 check 제약)
  · 쓰인 코드가 001_schema.sql 시드에 있는가
  · 정답 선지가 정확히 1개인가 / answer_key 와 일치하는가
  · passage_logic 문장번호가 1..N 빠짐없이 있는가
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S0 = os.path.join(ROOT, "data", "stage0")
SCHEMA_SQL = os.path.join(ROOT, "db", "001_schema.sql")

TEXTBOOK = {"publisher": "동아", "author": "윤정미",
            "curriculum_version": "2022개정", "grade": 2}

problems, notes = [], []


def fail(msg):
    problems.append(msg)


def note(msg):
    notes.append(msg)


def jload(*rel):
    with open(os.path.join(S0, *rel), encoding="utf-8") as f:
        return json.load(f)


def norm_school(name):
    """'영덕중학교' → '영덕중'. school 테이블 시드가 짧은 이름이다."""
    return name[:-2] if name.endswith("중학교") else name


# ═══════════════════════════════════════════════════════════════════
#  마스터 코드 — 001_schema.sql 을 그대로 읽는다 (DB 없이 검증하려고)
# ═══════════════════════════════════════════════════════════════════

def load_master_codes():
    sql = open(SCHEMA_SQL, encoding="utf-8").read()
    out = {}
    for table in ("grammar_point", "modification_type", "question_type", "reject_reason"):
        m = re.search(rf"insert into {table} \(.*?\) values(.*?)on conflict", sql, re.S)
        out[table] = set(re.findall(r"^\s*\('([A-Z0-9_\-]+)'", m.group(1), re.M)) if m else set()
    return out


MASTER = load_master_codes()
CAND = jload("master_candidates.json")
CAND_GP = {c["code"] for c in CAND["grammar_point"]}
CAND_QT = {c["code"] for c in CAND["question_type"]}


def known(table, code, where, allow_new):
    if code is None:
        return True
    if code in MASTER[table]:
        return True
    cand = CAND_GP if table == "grammar_point" else CAND_QT if table == "question_type" else set()
    if code in cand:
        if allow_new:
            return True
        note(f"후보코드 {code} 사용 — {where} (--allow-new-codes 없으면 건너뜀)")
        return False
    fail(f"미등록 {table} 코드 '{code}' — {where}")
    return False


# ═══════════════════════════════════════════════════════════════════
#  적재 계획 만들기
# ═══════════════════════════════════════════════════════════════════

class Plan:
    def __init__(self, allow_new):
        self.allow_new = allow_new
        self.passages = []       # (key, row, extras)
        self.exams = []
        self.variants = []
        self.tags = []
        self.logic = []
        self.sites = []
        self.items = []
        self.maps = []
        self.observations = []


def check_passage(src, body, sha_recorded, where):
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if sha != sha_recorded:
        fail(f"sha256 불일치 — {where}\n      기록 {sha_recorded}\n      실측 {sha}")
    return sha


def build_plan(allow_new):
    p = Plan(allow_new)

    # ── 지문 1: 2025-2 중간 영덕중 배부프린트 ────────────────────────
    a = jload("passages", "영덕중2_2025-2-중간_5과학습지3_p2.json")
    sha_a = check_passage(a, a["body_text"], a["body_text_sha256"], a["passage_id"])
    p.passages.append({
        "_key": a["passage_id"],
        "kind": "handout_external",
        "title": "goose (5과 학습지 3)",
        "textbook_unit": "Lesson 5",
        "source_detail": a["source_detail"],
        "body_text": a["body_text"],
        "body_text_sha256": sha_a,
        "word_count": a["word_count"],
        "transcription_status": a["transcription"]["status"],
        "transcription_note": a["transcription"]["note"],
        "has_handwriting": a["transcription"]["has_handwriting"],
        "scan_file": a["scan_file"],
        "scan_page": a["scan_page"],
    })

    # 태깅 A
    t = jload("tags", "영덕중2_2025-2-중간_5과학습지3_p2.tags.json")
    if t["body_text_sha256"] != sha_a:
        fail(f"태깅 파일 해시가 지문과 다름 — {t['passage_id']}")
    emph = {(e["start"], e["end"]) for e in a["emphasis_spans"]}
    for tag in t["tags"]:
        _add_tag(p, a["passage_id"], a["body_text"], tag, emph, allow_new)

    # ── 지문 2: 2026-1 기말 L4 impulse buying ──────────────────────
    b = jload("passages", "영덕중2_2026-1-기말_L4_impulse-buying.json")
    sha_b = check_passage(b, b["body_text"], b["body_text_sha256"], b["passage_id"])
    p.passages.append({
        "_key": b["passage_id"],
        "kind": b["kind"],
        "title": b["title"],
        "textbook_unit": b["textbook_unit"],
        "source_detail": b["source_detail"],
        "body_text": b["body_text"],
        "body_text_sha256": sha_b,
        "word_count": b["word_count"],
        "transcription_status": b["transcription"]["status"],
        "transcription_note": b["transcription"]["note"],
        "has_handwriting": b["transcription"]["has_handwriting"],
    })

    tb = jload("tags", "영덕중2_2026-1-기말_L4_impulse-buying.tags.json")
    if tb["body_text_sha256"] != sha_b:
        fail(f"태깅 파일 해시가 지문과 다름 — {tb['passage_id']}")
    tag_by_no = {}
    for tag in tb["tags"]:
        row = _add_tag(p, b["passage_id"], b["body_text"], tag, set(), allow_new)
        if row:
            tag_by_no[tag["tag_no"]] = row
            # 예상 출제 지점 = 태그 × 적용 가능 변형
            for i, mod in enumerate(tag.get("applicable_modifications", [])):
                if known("modification_type", mod, f"태그 {tag['tag_no']}", allow_new):
                    p.sites.append({
                        "_passage": b["passage_id"], "_tag_no": tag["tag_no"],
                        "modification_type_code": mod,
                        "rendered_wrong_form": tag.get("exam_wrong_form"),
                        # 기출에서 실제 오류가 삽입된 지점 > 밑줄만 그어진 지점 > 나머지
                        "priority": (20 if tag.get("exam_wrong_form")
                                     else 10 if tag.get("exam_underlined") else 0) - i,
                    })

    # 태깅 B
    lg = jload("logic", "영덕중2_2026-1-기말_L4_impulse-buying.logic.json")
    if lg["body_text_sha256"] != sha_b:
        fail("논리태깅 파일 해시가 지문과 다름")
    nos = [s["sentence_no"] for s in lg["sentences"]]
    if sorted(nos) != list(range(1, len(nos) + 1)):
        fail(f"passage_logic 문장번호가 1..N 연속이 아님: {sorted(nos)}")
    for s in lg["sentences"]:
        p.logic.append({
            "_passage": b["passage_id"], "sentence_no": s["sentence_no"],
            "role": s["role"], "signal": s["signal"],
            "is_blank_candidate": s["is_blank_candidate"], "note": s["text"],
        })

    # ── 시험 ────────────────────────────────────────────────────────
    cmp4 = jload("comparisons", "4개교_2026-1기말_대조.json")
    for e in cmp4["exams"]:
        p.exams.append({
            "_key": f"{e['school']}_2026-1-기말",
            "_school": e["school"], "grade": 2, "year": 2026, "semester": 1,
            "sitting": "기말", "exam_date": e["date"],
            "mc_count": e["mc"], "essay_count": e["essay"],
            "total_score": 100, "page_count": e["pages"],
        })
    p.exams.append({
        "_key": "영덕중_2025-2-중간", "_school": "영덕중", "grade": 2,
        "year": 2025, "semester": 2, "sitting": "중간", "exam_date": "2025-09-30",
        "mc_count": 20, "essay_count": 2, "total_score": 100, "page_count": 5,
    })

    # ── 관측 ────────────────────────────────────────────────────────
    pred = jload("comparisons", "영덕중2_2026-1-기말_예측대조.json")
    dist = {it["point"]: it["score"] for it in pred["actual_grammar_items"]}
    for school in ("영덕중", "영일중", "청명중", "태장중"):
        obs = {
            "_exam": f"{school}_2026-1-기말",
            "textbook_passage_hit_rate": 1.0,   # 4개교 전부 7/7
            "note": cmp4["textbook_passage_coverage"]["conclusion"],
        }
        if school == "영덕중":
            obs["grammar_score_share"] = pred["grammar_score_share"]
            obs["grammar_distribution"] = {
                "items": pred["actual_grammar_items"],
                "by_point_score": dist,
                "grammar_score_total": pred["grammar_score_total"],
                "textbook_dependency": pred["textbook_dependency"],
            }
        p.observations.append(obs)

    cmp1 = jload("comparisons", "영덕중2_2025-2-중간_5과학습지3_p2.compare.json")
    p.observations.append({
        "_exam": "영덕중_2025-2-중간",
        "handout_passage_hit_rate": 1.0,   # 배부 지문이 논술형 1로 출제됨
        "note": ("표본 1지문. 커버리지 %.2f / 과잉률 %.2f. %s"
                 % (cmp1["metrics"]["coverage"], cmp1["metrics"]["excess_ratio"],
                    cmp1["caveats"][0])),
    })

    # ── 학교별 변형본 + 어법 매핑 ────────────────────────────────────
    ws = jload("worksheets", "영덕중2_2025-2-중간_5과학습지3.json")
    variant_body = a["body_text"]
    for ch in cmp1["passage_diff"]["changes"]:
        if ch["배부"] not in variant_body:
            fail(f"변형본 생성 실패 — 배부본에 없는 문자열: {ch['배부']!r}")
        variant_body = variant_body.replace(ch["배부"], ch["시험"], 1)
    p.variants.append({
        "_passage": a["passage_id"], "_school": norm_school(ws["header"]["school"]),
        "_exam": "영덕중_2025-2-중간",
        "body_text": variant_body,
        "body_text_sha256": hashlib.sha256(variant_body.encode("utf-8")).hexdigest(),
        "handout_ref": f"{ws['header']['lesson']} / 학습지 {ws['header']['worksheet_no']}",
        "diff_note": json.dumps(
            {"note": "canonical=배부본, variant=시험 출제본. 교사가 5곳을 변형했다.",
             "changes": cmp1["passage_diff"]["changes"]}, ensure_ascii=False),
        "planted_points": [m["grammar_point_code"] for m in ws["map_seed"]],
    })
    for m in ws["map_seed"]:
        if known("grammar_point", m["grammar_point_code"], "worksheet map_seed", allow_new):
            p.maps.append({
                "_school": norm_school(m["school"]), "grade": m["grade"],
                "textbook_unit": m["textbook_unit"],
                "grammar_point_code": m["grammar_point_code"],
                "is_extension": m["is_extension"],
                "_exam": "영덕중_2025-2-중간",
                "confidence": m["confidence"],
                "note": f"{m['point_label']} · 근거: {m['evidence']} · {m['note']}",
            })

    # ── 문항 ────────────────────────────────────────────────────────
    for fname in ("영덕중2_2026-1-기말_L4_impulse-buying.items.json",
                  "impulse-buying_전유형세트.items.json"):
        _add_items(p, jload("items", fname), sha_b, fname, allow_new)

    return p


def _add_tag(p, passage_key, body, tag, emph, allow_new):
    where = f"{passage_key} 태그 {tag['tag_no']}"
    s, e = tag["span_start"], tag["span_end"]
    if e <= s:
        fail(f"span_end <= span_start — {where}")
        return None
    if body[s:e] != tag["surface"]:
        fail(f"스팬 불일치 — {where}\n      기대 {tag['surface']!r}\n      실제 {body[s:e]!r}")
        return None
    if not known("grammar_point", tag["grammar_point_code"], where, allow_new):
        return None
    row = {
        "_passage": passage_key, "_tag_no": tag["tag_no"],
        "grammar_point_code": tag["grammar_point_code"],
        "span_start": s, "span_end": e, "surface": tag["surface"],
        "rationale": tag["rationale"], "confidence": tag["confidence"],
        "teacher_emphasis": tag.get("teacher_emphasis") or (s, e) in emph,
        "status": "approved",   # 0단계에서 원장 대조로 검증된 태깅
    }
    p.tags.append(row)
    return row


def _add_items(p, doc, sha, fname, allow_new):
    if doc["body_text_sha256"] != sha:
        fail(f"문항 파일 해시가 지문과 다름 — {fname}")
    secs = doc.get("review_seconds_per_item")
    recorded = secs.get("recorded") if isinstance(secs, dict) else None
    for it in doc["items"]:
        where = f"{fname} {it['local_id']}"
        qt = it["question_type_code"]
        if not known("question_type", qt, where, allow_new):
            continue
        if not known("grammar_point", it.get("grammar_point_code"), where, allow_new):
            continue
        # 정답 선지 검증
        ans = [o for o in it["options"] if o["is_answer"]]
        if it["options"]:
            if len(ans) != 1:
                fail(f"정답 선지가 {len(ans)}개 — {where}")
                continue
            if not it["answer_key"].startswith(ans[0]["label"]):
                fail(f"answer_key({it['answer_key']}) 와 정답 선지({ans[0]['label']}) 불일치 — {where}")
                continue
        for o in it["options"]:
            known("grammar_point", o.get("violates_point_code"), where, allow_new)
            known("modification_type", o.get("via_modification"), where, allow_new)

        rv = it["review"]
        approved = rv["verdict"] == "approved"
        if rv.get("reject_reason"):
            known("reject_reason", rv["reject_reason"], where, allow_new)

        p.items.append({
            "_passage": doc["passage_id"], "_local": it["local_id"], "_set": doc["item_set_id"],
            "question_type_code": qt,
            "grammar_point_code": it.get("grammar_point_code"),
            "stem": it["stem"],
            "answer_key": it["answer_key"],
            "explanation": it["explanation"],
            "difficulty": it["difficulty"],
            "option_lang": it["option_lang"],
            "status": "approved" if approved else "rejected",
            "approved_at": doc["generated_at"] if approved else None,
            "_options": it["options"],
            "_check": {
                "check_type": "director_review",
                "passed": approved,
                "reject_reason": rv.get("reject_reason"),
                "review_seconds": recorded,
                "detail": {
                    "review_mode": doc["review_mode"],
                    "review_seconds_range": secs,
                    "verbatim": rv.get("verbatim"),
                    "condition": rv.get("condition"),
                    "condition_status": rv.get("condition_status"),
                    "note": rv.get("note"),
                    "self_flagged": it.get("self_flagged"),
                    "source_sheet": doc["source_sheet"],
                },
            },
        })


# ═══════════════════════════════════════════════════════════════════
#  Supabase REST
# ═══════════════════════════════════════════════════════════════════

class Rest:
    def __init__(self):
        env = {}
        with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
        self.url = env["SUPABASE_URL"].rstrip("/") + "/rest/v1"
        self.key = env["SUPABASE_SERVICE_ROLE_KEY"]

    def _call(self, method, path, body=None, prefer=None):
        h = {"apikey": self.key, "Authorization": f"Bearer {self.key}",
             "Content-Type": "application/json", "Accept": "application/json"}
        if prefer:
            h["Prefer"] = prefer
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else []
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise SystemExit(f"\n  X  {method} {path} → HTTP {e.code}\n     {detail}")

    def get(self, path):
        return self._call("GET", path)

    def insert(self, table, rows, on_conflict=None):
        if not rows:
            return []
        path = f"/{table}"
        prefer = "return=representation"
        if on_conflict:
            path += f"?on_conflict={on_conflict}"
            prefer += ",resolution=merge-duplicates"
        return self._call("POST", path, rows, prefer)

    def delete(self, table, query):
        return self._call("DELETE", f"/{table}?{query}", prefer="return=representation")


def strip_(row):
    return {k: v for k, v in row.items() if not k.startswith("_")}


def q(v):
    return urllib.parse.quote(str(v), safe="")


# ═══════════════════════════════════════════════════════════════════
#  적재
# ═══════════════════════════════════════════════════════════════════

def apply_plan(p, reset, allow_new):
    api = Rest()
    print("\n[적재 시작]")

    # 0. 마스터 후보 코드
    if allow_new:
        gp = [{k: v for k, v in c.items() if k in
               ("code", "category", "label_ko", "is_candidate", "note")}
              for c in CAND["grammar_point"]]
        api.insert("grammar_point", gp, on_conflict="code")
        qt = [{k: v for k, v in c.items() if k in
               ("code", "label_ko", "option_lang", "value_approved", "review_tier",
                "tier_reason", "note")} for c in CAND["question_type"]]
        api.insert("question_type", qt, on_conflict="code")
        print(f"  마스터 후보코드     grammar_point {len(gp)} · question_type {len(qt)}")

    # 1. textbook / school
    tb = api.insert("textbook", [TEXTBOOK],
                    on_conflict="publisher,author,curriculum_version,grade")
    textbook_id = tb[0]["id"] if tb else api.get(
        f"/textbook?publisher=eq.{q(TEXTBOOK['publisher'])}"
        f"&author=eq.{q(TEXTBOOK['author'])}&grade=eq.2")[0]["id"]
    schools = {s["name"]: s["id"] for s in api.get("/school?select=id,name")}
    print(f"  textbook / school    id 확보 · 학교 {len(schools)}개")

    # 2. exam
    exam_id = {}
    for e in p.exams:
        row = strip_(e)
        row["school_id"] = schools[e["_school"]]
        row["textbook_id"] = textbook_id
        got = api.insert("exam", [row], on_conflict="school_id,grade,year,semester,sitting")
        exam_id[e["_key"]] = got[0]["id"]
    print(f"  exam                 {len(exam_id)}건")

    # 3. passage
    passage_id = {}
    for pg in p.passages:
        row = strip_(pg)
        row["textbook_id"] = textbook_id
        got = api.insert("passage", [row], on_conflict="body_text_sha256")
        passage_id[pg["_key"]] = got[0]["id"]
    print(f"  passage              {len(passage_id)}건")

    # 4. --reset: 자식 행 삭제
    if reset:
        print("\n  ! DELETE 실행 (--reset)")
        for pid in passage_id.values():
            for t in ("item", "predicted_item_site", "passage_tag",
                      "passage_logic", "passage_variant"):
                n = len(api.delete(t, f"passage_id=eq.{pid}"))
                if n:
                    print(f"      {t:22} {n}행 삭제")
        for eid in exam_id.values():
            n = len(api.delete("exam_observation", f"exam_id=eq.{eid}"))
            if n:
                print(f"      exam_observation       {n}행 삭제")
        print()

    def empty(table, pid):
        return not api.get(f"/{table}?passage_id=eq.{pid}&select=id&limit=1")

    # 5. passage_variant
    for v in p.variants:
        pid = passage_id[v["_passage"]]
        row = strip_(v)
        row["passage_id"] = pid
        row["school_id"] = schools[v["_school"]]
        row["exam_id"] = exam_id[v["_exam"]]
        api.insert("passage_variant", [row], on_conflict="passage_id,school_id")
    print(f"  passage_variant      {len(p.variants)}건")

    # 6. passage_tag  (자연키가 없어 '이미 있으면 건너뜀')
    tag_id = {}
    for pkey, pid in passage_id.items():
        rows = [t for t in p.tags if t["_passage"] == pkey]
        if not rows:
            continue
        if not empty("passage_tag", pid):
            print(f"  passage_tag          {pkey}: 이미 있음 → 건너뜀 (--reset 로 재적재)")
            for r in api.get(f"/passage_tag?passage_id=eq.{pid}&select=id,span_start,span_end"):
                tag_id[(pkey, r["span_start"], r["span_end"])] = r["id"]
            continue
        got = api.insert("passage_tag", [dict(strip_(t), passage_id=pid) for t in rows])
        for r in got:
            tag_id[(pkey, r["span_start"], r["span_end"])] = r["id"]
        print(f"  passage_tag          {pkey}: {len(got)}건")

    # 7. passage_logic
    for pkey, pid in passage_id.items():
        rows = [l for l in p.logic if l["_passage"] == pkey]
        if rows:
            api.insert("passage_logic", [dict(strip_(l), passage_id=pid) for l in rows],
                       on_conflict="passage_id,sentence_no")
            print(f"  passage_logic        {pkey}: {len(rows)}건")

    # 8. predicted_item_site
    tag_no_to_span = {(t["_passage"], t["_tag_no"]): (t["span_start"], t["span_end"])
                      for t in p.tags}
    for pkey, pid in passage_id.items():
        rows = [s for s in p.sites if s["_passage"] == pkey]
        if not rows or not empty("predicted_item_site", pid):
            if rows:
                print(f"  predicted_item_site  {pkey}: 이미 있음 → 건너뜀")
            continue
        out = []
        for s in rows:
            span = tag_no_to_span.get((pkey, s["_tag_no"]))
            out.append(dict(strip_(s), passage_id=pid,
                            passage_tag_id=tag_id.get((pkey,) + span) if span else None))
        api.insert("predicted_item_site", out)
        print(f"  predicted_item_site  {pkey}: {len(out)}건")

    # 9. item / item_option / item_check
    for pkey, pid in passage_id.items():
        rows = [i for i in p.items if i["_passage"] == pkey]
        if not rows:
            continue
        if not empty("item", pid):
            print(f"  item                 {pkey}: 이미 있음 → 건너뜀 (--reset 로 재적재)")
            continue
        tiers = {r["code"]: r["review_tier"]
                 for r in api.get("/question_type?select=code,review_tier")}
        got = api.insert("item", [dict(strip_(i), passage_id=pid,
                                       review_tier=tiers.get(i["question_type_code"], "fast"))
                                  for i in rows])
        opts, checks = [], []
        for src, made in zip(rows, got):
            for o in src["_options"]:
                opts.append(dict(o, item_id=made["id"]))
            checks.append(dict(src["_check"], item_id=made["id"]))
        api.insert("item_option", opts)
        api.insert("item_check", checks)
        print(f"  item                 {pkey}: {len(got)}건 · 선지 {len(opts)} · 검수 {len(checks)}")

    # 10. school_grammar_map  (unique 제약이 없어 직접 중복 확인)
    added = 0
    for m in p.maps:
        row = strip_(m)
        row.update(school_id=schools[m["_school"]], textbook_id=textbook_id,
                   evidence_exam_id=exam_id[m["_exam"]])
        dup = api.get(
            f"/school_grammar_map?select=id"
            f"&school_id=eq.{row['school_id']}&grade=eq.{row['grade']}"
            f"&textbook_id=eq.{row['textbook_id']}"
            f"&textbook_unit=eq.{q(row['textbook_unit'])}"
            f"&grammar_point_code=eq.{row['grammar_point_code']}&limit=1")
        if dup:
            continue
        api.insert("school_grammar_map", [row])
        added += 1
    print(f"  school_grammar_map   {added}건 추가 (계획 {len(p.maps)})")

    # 11. exam_observation
    for o in p.observations:
        row = strip_(o)
        row["exam_id"] = exam_id[o["_exam"]]
        api.insert("exam_observation", [row], on_conflict="exam_id")
    print(f"  exam_observation     {len(p.observations)}건")

    print("\n[적재 완료]")


# ═══════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 적재 (기본은 검증만)")
    ap.add_argument("--reset", action="store_true",
                    help="★ 대상 지문·시험의 자식 행을 DELETE 후 재적재")
    ap.add_argument("--allow-new-codes", action="store_true",
                    help="master_candidates.json 의 후보 코드까지 적재")
    args = ap.parse_args()

    print("=" * 68)
    print(" 0단계 JSON 인제스트  —  " + ("적재 모드" if args.apply else "검증만 (DRY RUN)"))
    print("=" * 68)

    p = build_plan(args.allow_new_codes)

    counts = [("passage", p.passages), ("exam", p.exams), ("passage_variant", p.variants),
              ("passage_tag", p.tags), ("passage_logic", p.logic),
              ("predicted_item_site", p.sites), ("item", p.items),
              ("school_grammar_map", p.maps), ("exam_observation", p.observations)]
    print("\n[적재 계획]")
    for name, rows in counts:
        print(f"  {name:22} {len(rows):>4}행")
    print(f"  {'item_option':22} {sum(len(i['_options']) for i in p.items):>4}행")
    print(f"  {'item_check':22} {len(p.items):>4}행")

    print("\n[문항 상태]")
    for st in ("approved", "rejected"):
        n = sum(1 for i in p.items if i["status"] == st)
        print(f"  {st:22} {n:>4}건")

    if notes:
        print("\n[주의]")
        for m in dict.fromkeys(notes):
            print("  ·", m)

    if problems:
        print("\n[검증 실패]")
        for m in problems:
            print("  X", m)
        print("\n  → 고치기 전에는 적재하지 않습니다.")
        return 1

    print("\n  O 검증 통과 — 해시·스팬·코드·정답 전부 일치")

    if not args.apply:
        print("\n  실제 적재:  python db/002_ingest.py --apply"
              + ("" if args.allow_new_codes else " --allow-new-codes"))
        return 0

    if args.reset:
        print("\n  ! --reset: DELETE 가 실행됩니다 (대상 지문·시험의 자식 행만).")
    apply_plan(p, args.reset, args.allow_new_codes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
