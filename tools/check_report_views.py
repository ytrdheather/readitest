# -*- coding: utf-8 -*-
"""리디플랜 보고서용 뷰(db/014_report_views.sql) 확인 — **publishable(anon) 키로** 본다.

  python tools/check_report_views.py

리디플랜이 실제로 쓰게 될 키로, 리디플랜이 보게 될 것만 본다.
  · 뷰 2개는 행이 보여야 한다
  · 기반 테이블은 0행이어야 한다 (RLS 그대로)
쓰기 요청은 보내지 않는다 (쓰기가 막혔는지는 014 의 grant 로 판단한다).
키 값은 출력하지 않는다. GET 만 보낸다.
"""
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.env import load_env, require                          # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VIEWS = ["report_school_grammar", "report_exam_schedule"]
BASE = ["school", "exam", "grammar_point", "school_grammar_map", "exam_observation", "item", "passage"]


def get(url, key, path):
    req = urllib.request.Request(url + "/rest/v1" + path, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]


def main():
    url, key = require(load_env(), "SUPABASE_URL", "SUPABASE_ANON_KEY")
    url = url.rstrip("/")
    ok = True
    print("=" * 62)
    print(" 리디플랜 보고서용 뷰 — publishable 키로 확인 (GET 만)")
    print("=" * 62)
    for v in VIEWS:
        code, body = get(url, key, f"/{v}?select=*")
        if code == 200 and body:
            print(f"  O  {v:24} {len(body):>3}행")
        else:
            ok = False
            print(f"  X  {v:24} HTTP {code} " + (f"{len(body)}행" if code == 200 else "— 014 실행 전이거나 grant 누락"))
    for t in BASE:
        code, body = get(url, key, f"/{t}?select=*&limit=1")
        seen = len(body) if code == 200 else 0
        mark = "O" if seen == 0 else "X"
        ok &= seen == 0
        print(f"  {mark}  {t:24} {'0행 (막힘)' if seen == 0 else '보임 — RLS 확인 필요'}")

    code, rows = get(url, key, "/report_school_grammar?select=school_name,grade,grammar_point_code,"
                               "exam_hit_count,exams_observed,last_hit_exam_date"
                               "&exam_hit_count=gt.0&order=school_name,grammar_point_code")
    if code == 200 and rows:
        print("\n[기출 근거가 있는 학교 × 포인트]")
        for r in rows:
            print(f"  {r['school_name']}{r['grade']}  {r['grammar_point_code']:22} "
                  f"{r['exam_hit_count']}/{r['exams_observed']}회  마지막 {r['last_hit_exam_date']}")
    code, rows = get(url, key, "/report_exam_schedule?select=*&order=grade,school_name,year,semester")
    if code == 200 and rows:
        print("\n[시험 일정]")
        for r in rows:
            print(f"  {r['school_name']}{r['grade']}  {r['year']}-{r['semester']} {r['sitting']}  "
                  f"{r['exam_date'] or '날짜 미정'}")

    print("\n 결과:", "정상" if ok else "확인 필요")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
