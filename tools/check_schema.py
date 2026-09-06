# -*- coding: utf-8 -*-
"""스키마 생성 확인 — 테이블 존재 여부와 시드 행 수만 본다. 키 값은 출력하지 않는다."""
import json, os, sys, urllib.error, urllib.request
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    env = {}
    with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env

env = load_env()
URL = env["SUPABASE_URL"].rstrip("/")
KEY = env["SUPABASE_SERVICE_ROLE_KEY"]

# (테이블, 최소 행수)
# 마스터는 시드 행수가 하한. 후보 코드가 승인되면 그보다 늘어난다 (002_ingest --allow-new-codes).
# 콘텐츠 테이블은 0이 하한 — 인제스트 전에는 비어 있는 게 정상이다.
TABLES = [
    ("profile", 0), ("grammar_point", 28), ("modification_type", 21),
    ("question_type", 10), ("reject_reason", 9),
    ("textbook", 1), ("school", 4), ("exam", 0),
    ("passage", 0), ("passage_variant", 0), ("passage_tag", 0), ("passage_logic", 0),
    ("predicted_item_site", 0), ("item", 0), ("item_option", 0), ("item_check", 0),
    ("school_grammar_map", 0), ("exam_observation", 0),
]
MASTER = {"grammar_point", "modification_type", "question_type", "reject_reason",
          "textbook", "school"}

def rows(table):
    req = urllib.request.Request(
        f"{URL}/rest/v1/{table}?select=*",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

print("=" * 62)
print(" 스키마 확인")
print("=" * 62)
ok = True
missing = []
for t, expect in TABLES:
    try:
        data = rows(t)
        n = len(data)
        if n < expect:
            print(f"  !  {t:22} {n:>3}행   (최소 {expect}행이어야 함 — 시드 누락)")
            ok = False
        else:
            if t in MASTER:
                tag = "시드" + (f" +{n - expect}" if n > expect else "")
            else:
                tag = "비어있음" if n == 0 else "인제스트됨"
            print(f"  O  {t:22} {n:>3}행   {tag}")
    except urllib.error.HTTPError as e:
        print(f"  X  {t:22} HTTP {e.code}  테이블 없음/접근 불가")
        missing.append(t); ok = False
    except Exception as e:
        print(f"  X  {t:22} {type(e).__name__}")
        missing.append(t); ok = False

print("\n[검수 유형 승인 상태]")
try:
    for q in sorted(rows("question_type"),
                    key=lambda x: ({True: 0, None: 1, False: 2}[x["value_approved"]], x["code"])):
        mark = {True: "승인  ", None: "미검수", False: "반려  "}[q["value_approved"]]
        tier = q["review_tier"]
        print(f"  {mark}  {q['code']:24} {tier:5} {q['label_ko']}")
except Exception as e:
    print("  조회 실패:", type(e).__name__)

# 후보 코드는 **파일이 아니라 DB 가 정답이다.** 2026-09-06 에
# master_candidates.json 만 보고 「후보 3개」라고 답했다가, DB 에는 10종이
# 있는 것을 뒤늦게 발견했다. 파일에 안 적힌 채 시드·인제스트로 들어간
# 것들이었다. 그 뒤로 이 줄을 항상 찍는다.
print("\n[미승인 후보 코드 — 파일 말고 여기가 정답]")
try:
    cand = [g for g in rows("grammar_point") if g.get("is_candidate")]
    if cand:
        print(f"  어법 포인트 후보 {len(cand)}종 — 원장 승인 전")
        for g in sorted(cand, key=lambda x: x["code"]):
            print(f"     {g['code']:24} {g['label_ko']}")
    else:
        print("  없음 — 어법 포인트 전부 정식 승인 상태")
    q = rows("question_type")
    pend = [x for x in q if x["value_approved"] is None]
    print(f"  문항 유형 미검수 {len(pend)}종"
          + (f" — {[x['code'] for x in pend]}" if pend else " (전부 검수됨)"))
except Exception as e:
    print("  조회 실패:", type(e).__name__)

print("\n" + "=" * 62)
print(" 결과:", "스키마 정상" if ok else f"문제 있음 {missing}")
print("=" * 62)
sys.exit(0 if ok else 1)
