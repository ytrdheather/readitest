# -*- coding: utf-8 -*-
"""
동형 모의고사 JSON → 시험지 PDF · 정답지 PDF, result/readitude/ 에.

  python tools/build_mock_pdf.py                 # data/generated/mock/*.json 전부
  python tools/build_mock_pdf.py --school 영덕중

    result/readitude/영덕중2 동형모의고사 1세트.pdf
    result/readitude/영덕중2 동형모의고사 1세트 정답지.pdf

이름은 자체 드릴과 같은 꼴 — 학교 뒤에 학년. 과는 안 붙는다: 동형은 5·6과를
한 시험지에 섞는다 (시험 범위가 네 학교 다 5·6과).

시험지와 정답지는 다른 파일이다 — build_drill_pdf.py 와 같은 이유.
렌더는 render_mock_exam.build, PDF 변환은 build_drill_pdf.to_pdf (Chrome) 를 그대로 쓴다.
"""
import argparse
import glob
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.render_mock_exam import build                              # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MOCK = os.path.join(ROOT, "data", "generated", "mock")
OUT = os.path.join(ROOT, "result", "readitude")
GRADE = "2"      # 동형은 중2 5·6과 대비


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--school", action="append")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(MOCK, "*세트.json")))
    if a.school:
        files = [f for f in files if any(os.path.basename(f).startswith(s) for s in a.school)]
    if not files:
        raise SystemExit("세트 JSON 이 없습니다: " + MOCK)

    chrome = find_chrome()
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="mockpdf_")
    os.makedirs(a.out, exist_ok=True)
    try:
        for f in files:
            d = json.load(io.open(f, encoding="utf-8"))
            base = f"{d['school']}{GRADE} 동형모의고사 {d['set_no']}세트"
            # 줄바꿈·고쳐쓰기는 parse() 가 원본으로 덮어써 이미 해결된 기록이다
            bad = [p for p in d["diagnostics"]["problems"]
                   if "줄바꿈" not in p and "고쳐 썼다" not in p]
            for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
                html = os.path.join(tmp, f"{base}{suffix}.html")
                pdf = os.path.join(a.out, f"{base}{suffix}.pdf")
                io.open(html, "w", encoding="utf-8").write(build(d, logo, part))
                to_pdf(chrome, html, pdf)
            flag = f"   ⚠ {' / '.join(bad)}" if bad else ""
            print(f"  {base}  선택 {len(d['items'])} · 서술 {len(d['essays'])} · "
                  f"{d['diagnostics']['total_points']}점{flag}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  → {a.out}")
    print("  시험지와 정답지는 다른 파일입니다. 정답지는 강사만 가지십시오.")


if __name__ == "__main__":
    sys.exit(main())
