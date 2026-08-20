# -*- coding: utf-8 -*-
"""
인제스트 사후 검증 — DB에 실제로 들어간 값을 기준으로 본다.

002_ingest.py 의 검증은 JSON 파일을 봤다. 이건 DB를 본다. 둘은 다른 질문이다:
전송 중 잘렸거나, 컬럼이 밀렸거나, 나중에 누가 body_text 를 손대면 여기서만 잡힌다.

보는 것:
  1. sha256(body_text) 가 body_text_sha256 과 같은가       ← 설계원칙 7
  2. body_text[span_start:span_end] == surface 인가        ← span 어긋남
  3. 문항마다 정답 선지가 정확히 1개인가 (서술형 제외)
  4. 문항마다 검수 기록이 있는가
  5. 예상 출제 지점이 태그에 연결돼 있는가
  6. RLS — 공개 키로 미승인 문항이 보이는가                ← 설계원칙 8
"""
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = {}
with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
URL = env["SUPABASE_URL"].rstrip("/") + "/rest/v1"
SECRET = env["SUPABASE_SERVICE_ROLE_KEY"]
ANON = env["SUPABASE_ANON_KEY"]

fails = []


def get(path, key=SECRET):
    req = urllib.request.Request(
        URL + path, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


print("=" * 66)
print(" 인제스트 사후 검증  (DB 실제 값 기준)")
print("=" * 66)

# ── 1·2. 해시와 스팬 ────────────────────────────────────────────────
passages = get("/passage?select=id,title,body_text,body_text_sha256,word_count")
tags = get("/passage_tag?select=id,passage_id,span_start,span_end,surface,grammar_point_code")
by_id = {p["id"]: p for p in passages}

print(f"\n[지문 {len(passages)}개]")
for p in passages:
    sha = hashlib.sha256(p["body_text"].encode("utf-8")).hexdigest()
    ok = check(sha == p["body_text_sha256"],
               f"sha256 불일치 — {p['title']}: DB기록 {p['body_text_sha256'][:12]} / 실측 {sha[:12]}")
    mine = [t for t in tags if t["passage_id"] == p["id"]]
    bad = [t for t in mine if p["body_text"][t["span_start"]:t["span_end"]] != t["surface"]]
    for t in bad:
        fails.append(f"스팬 불일치 — {p['title']} [{t['span_start']}:{t['span_end']}] "
                     f"기대 {t['surface']!r} / 실제 {p['body_text'][t['span_start']:t['span_end']]!r}")
    mark = "O" if ok and not bad else "X"
    print(f"  {mark}  {p['title'][:38]:40} {p['word_count']:>4}단어  태그 {len(mine):>2}개"
          f"{'' if not bad else f'  스팬오류 {len(bad)}'}")

# ── 3·4. 문항 ──────────────────────────────────────────────────────
items = get("/item?select=id,question_type_code,status,stem,answer_key")
options = get("/item_option?select=item_id,label,is_answer")
checks = get("/item_check?select=item_id,passed,reject_reason,review_seconds")

opt_by_item, chk_by_item = {}, {}
for o in options:
    opt_by_item.setdefault(o["item_id"], []).append(o)
for c in checks:
    chk_by_item.setdefault(c["item_id"], []).append(c)

print(f"\n[문항 {len(items)}개 · 선지 {len(options)} · 검수 {len(checks)}]")
for it in items:
    os_ = opt_by_item.get(it["id"], [])
    if os_:
        n = sum(1 for o in os_ if o["is_answer"])
        check(n == 1, f"정답 선지 {n}개 — {it['stem'][:30]}…")
    check(it["id"] in chk_by_item, f"검수 기록 없음 — {it['stem'][:30]}…")

by_status = {}
for it in items:
    by_status[it["status"]] = by_status.get(it["status"], 0) + 1
for st, n in sorted(by_status.items()):
    print(f"  {st:12} {n:>3}건")

rej = [c for c in checks if c["passed"] is False]
print(f"  반려 사유    {[c['reject_reason'] for c in rej]}")
secs = [c["review_seconds"] for c in checks if c["review_seconds"]]
if secs:
    print(f"  검수 시간    {len(secs)}건 기록 · 평균 {sum(secs)//len(secs)}초 "
          f"(게이트 60초 — 1차는 유형검수 이전이라 초과가 정상)")
print(f"  시간 미기록  {len(checks) - len(secs)}건  ← 2차 유형검수. gate_speed 여전히 미측정")

# ── 5. 예상 출제 지점 ───────────────────────────────────────────────
sites = get("/predicted_item_site?select=id,passage_tag_id,modification_type_code,"
            "rendered_wrong_form,priority")
orphan = [s for s in sites if not s["passage_tag_id"]]
check(not orphan, f"태그에 연결 안 된 예상 지점 {len(orphan)}건")
top = sorted(sites, key=lambda s: -s["priority"])[:5]
print(f"\n[예상 출제 지점 {len(sites)}개 · 태그 미연결 {len(orphan)}]")
for s in top:
    print(f"  우선순위 {s['priority']:>3}  {s['modification_type_code']:26} "
          f"{s['rendered_wrong_form'] or ''}")

# ── 6. RLS ─────────────────────────────────────────────────────────
print("\n[RLS — 공개 키로 조회]")
for table in ("item", "item_option", "passage"):
    try:
        rows = get(f"/{table}?select=id&limit=5", key=ANON)
        ok = check(len(rows) == 0, f"공개 키에 {table} {len(rows)}행 노출됨")
        print(f"  {'O' if ok else 'X'}  {table:14} {len(rows)}행 보임  "
              f"{'(정상 — 로그인 안 한 쪽엔 아무것도 안 보임)' if not rows else '★ 노출!'}")
    except urllib.error.HTTPError as e:
        print(f"  O  {table:14} HTTP {e.code} 차단됨")

print("\n" + "=" * 66)
if fails:
    print(f" 결과: 문제 {len(fails)}건")
    for m in fails:
        print("  X", m)
else:
    print(" 결과: 이상 없음")
print("=" * 66)
sys.exit(1 if fails else 0)
