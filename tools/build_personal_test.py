# -*- coding: utf-8 -*-
"""
동형 모의고사 채점 결과 → 학생별 「오답 다시 풀기」 시험지 PDF + 정답지 PDF.

  python tools/build_personal_test.py <채점결과.json>            # → result/personal_test/

채점결과 JSON (학생 이름이 들어 있으니 **저장소 밖에** 둔다 — CLAUDE.md 규칙 3):

  {"students": [
     {"name": "홍길동", "set": "중1_영덕중_4세트", "wrong": [14, 15, 20]},
     ...]}

  · `set` 은 data/generated/mock/ 의 세트 JSON 이름
  · `wrong` 은 감점된 번호 — 선택형·서술형 구분 없이 원래 문항 번호. 서술형은 한 칸만
    틀려도 문항 통째로 다시 낸다
  · 서술형이 1번부터 다시 세는 세트는 `"wrong_essay": [4]` 로 서술형 번호를 따로 준다
    (그러면 `wrong` 은 선택형 번호만)
  · 틀린 문항이 없는 학생은 건너뛴다

시험지 모양은 동형 시험지 그대로 (render_mock_exam.build 를 그대로 쓴다):
문항 번호는 원래 번호를 지키고, 자료(지문)는 그 자료를 쓰는 문항 앞에 다시 싣는다.
제목에 학생 이름과 원래 세트 이름(학년 포함 — 디자인 지침 2)을 넣는다.
"""
import argparse
import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.build_mock_pdf import MOCK, school_lessons                 # noqa: E402
from tools.pdf_pages import stamp_file                                # noqa: E402
from tools.render_mock_exam import build                              # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = os.path.join(ROOT, "result", "personal_test")


def set_title(set_name, d):
    """build_mock_pdf 와 같은 이름 — `영덕중1 5·6과 동형모의고사 4세트`."""
    import glob
    grade = "1" if set_name.startswith("중1_") else "2"
    lessons = ([int(c) for c in d["range"]] if d.get("range")
               else school_lessons(sorted(glob.glob(os.path.join(MOCK, "*세트.json"))),
                                   set_name.rsplit("_", 1)[0]))
    lesson = (" " + "·".join(map(str, lessons)) + "과") if grade == "1" and lessons else ""
    return f"{d['school']}{grade}{lesson} 동형모의고사 {d['set_no']}세트"


def wrong_only(d, wrong, wrong_essay=None):
    """wrong_essay 를 주면 wrong 은 선택형 번호만, wrong_essay 는 서술형 번호만 —
    서술형이 1번부터 다시 세는 세트(중1 7세트)에서는 번호만으로 가를 수 없다 (2026-10-06)."""
    w = set(wrong)
    we = w if wrong_essay is None else set(wrong_essay)
    out = copy.deepcopy(d)
    out["items"] = [it for it in d["items"] if it["no"] in w]
    out["essays"] = [e for e in d["essays"] if e["no"] in we]
    missing = (w | we) - {it["no"] for it in out["items"]} - {e["no"] for e in out["essays"]}
    if wrong_essay is not None:
        missing = (w - {it["no"] for it in out["items"]}) | (we - {e["no"] for e in out["essays"]})
    if missing:
        raise SystemExit(f"세트에 없는 번호: {sorted(missing)}")
    pts = sum(it["points"] for it in out["items"]) + sum(e["points"] for e in out["essays"])
    out["spec"] = {**d["spec"], "total_points": pts}
    # 「구조 검사에서 걸린 것」 은 세트를 만들 때의 내부 기록 — 학생별 오답지에는 뜻이 없다
    out["diagnostics"] = {**d["diagnostics"], "problems": []}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_json")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)      # Chrome 은 상대 경로를 제 작업 폴더 기준으로 읽는다

    res = json.load(io.open(a.result_json, encoding="utf-8"))
    chrome = find_chrome()
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="personal_")
    os.makedirs(a.out, exist_ok=True)
    try:
        for s in res["students"]:
            if not s.get("wrong") and not s.get("wrong_essay"):
                print(f"  {s['name']}  — 틀린 문항 없음, 건너뜀")
                continue
            d = json.load(io.open(os.path.join(MOCK, s["set"] + ".json"), encoding="utf-8"))
            base = set_title(s["set"], d)
            title = f"{s['name']} · {base} 오답 다시 풀기"
            sub = wrong_only(d, s.get("wrong", []), s.get("wrong_essay"))
            # 시험지와 정답지는 다른 파일 — build_mock_pdf 와 같은 이유 (정답지는 강사만)
            for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
                html = os.path.join(tmp, "p.html")
                pdf = os.path.join(a.out, re.sub(r'[\\/:*?"<>|]', "_", title) + suffix + ".pdf")
                io.open(html, "w", encoding="utf-8").write(build(sub, logo, part, title=title))
                to_pdf(chrome, html, pdf)
                stamp_file(pdf)              # 아래 가운데 쪽수 — 디자인 지침 1
            print(f"  {title}  ({len(s['wrong'])}문항: {', '.join(map(str, s['wrong']))})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  → {a.out}")


if __name__ == "__main__":
    sys.exit(main())
