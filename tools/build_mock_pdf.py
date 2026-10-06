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
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.pdf_pages import stamp_file                                # noqa: E402
from tools.render_mock_exam import build                              # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MOCK = os.path.join(ROOT, "data", "generated", "mock")
OUT = os.path.join(ROOT, "result", "readitude")
GRADE = "2"      # 동형은 중2 5·6과 대비


def school_lessons(files, prefix):
    """같은 학교·학년 세트 파일 전부에서 실은 교과서 지문(P)의 과 번호를 모은다."""
    out = set()
    for g in files:
        if os.path.basename(g).rsplit("_", 1)[0] != prefix:
            continue
        for m in json.load(io.open(g, encoding="utf-8"))["materials"]:
            if m["id"].startswith("P"):
                out.update(int(x) for x in re.findall(r"L(\d)", m["title"]))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--school", action="append")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--set", type=int, action="append",
                    help="이 세트만 — 이미 배부한 세트 PDF 를 다시 덮어쓰지 않게 (2026-10-06)")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(MOCK, "*세트.json")))
    if a.school:
        files = [f for f in files if any(os.path.basename(f).startswith(s) for s in a.school)]
    if a.set:
        files = [f for f in files if any(os.path.basename(f).endswith(f"_{n}세트.json") for n in a.set)]
    if not files:
        raise SystemExit("세트 JSON 이 없습니다: " + MOCK)

    chrome = find_chrome()
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="mockpdf_")
    os.makedirs(a.out, exist_ok=True)
    try:
        for f in files:
            d = json.load(io.open(f, encoding="utf-8"))
            # 학년은 파일명 접두어 '중1_' 로 안다 (make_mock_exam --grade 1). 없으면 중2.
            grade = "1" if os.path.basename(f).startswith("중1_") else GRADE
            # 중1 은 과를 이름에 붙인다 — 실제로 실은 지문(P)의 과에서 읽는다. 「5과」 를 박아 두었더니
            # 5·6·7과 혼합인 영일중1 세트가 「5과」 로 나갔다 (2026-10-04).
            # 세트마다 실은 과가 달라도(영일중1 3세트는 L5·L7 만) 시험 범위는 같으니 학교 전체로 모은다.
            # 세트 파일에 범위(`range`, make_mock_exam 이 남김)가 있으면 그것이 이긴다 — 영덕중1 은
            # 5과 단독(1~3)과 5·6과 합본(4~6)이 한 학교에 같이 있다.
            lessons = ([int(c) for c in d["range"]] if d.get("range")
                       else school_lessons(files, os.path.basename(f).rsplit("_", 1)[0]))
            lesson = (" " + "·".join(map(str, lessons)) + "과") if grade == "1" and lessons else ""
            base = f"{d['school']}{grade}{lesson} 동형모의고사 {d['set_no']}세트"
            # 줄바꿈·고쳐쓰기는 parse() 가 원본으로 덮어써 이미 해결된 기록이다
            # 구조가 깨진 세트(문항 수·배점이 설계와 다름)는 종이로 내보내지 않는다 —
            # 영일중1 2세트(출력이 끊겨 1문항)가 PDF 로 나갈 뻔했다 (2026-10-04).
            if any(k in p for p in d["diagnostics"]["problems"]
                   for k in ("선택형 ", "서술형 ", "배점 합계")) and                     (len(d["items"]) != d["spec"]["selective"] or
                     len(d["essays"]) != d["spec"].get("essay", 0)):
                print(f"  {base}  ✖ 건너뜀 — 구조가 깨졌다 (선택 {len(d['items'])} · 서술 {len(d['essays'])}). 재생성 필요")
                continue
            bad = [p for p in d["diagnostics"]["problems"]
                   if "줄바꿈" not in p and "고쳐 썼다" not in p and "채워 넣음" not in p]
            for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
                html = os.path.join(tmp, f"{base}{suffix}.html")
                pdf = os.path.join(a.out, f"{base}{suffix}.pdf")
                io.open(html, "w", encoding="utf-8").write(build(d, logo, part, title=base))
                to_pdf(chrome, html, pdf)
                stamp_file(pdf)                  # 아래 가운데 쪽수 — 디자인 지침 1
            flag = f"   ⚠ {' / '.join(bad)}" if bad else ""
            print(f"  {base}  선택 {len(d['items'])} · 서술 {len(d['essays'])} · "
                  f"{d['diagnostics']['total_points']}점{flag}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  → {a.out}")
    print("  시험지와 정답지는 다른 파일입니다. 정답지는 강사만 가지십시오.")


if __name__ == "__main__":
    sys.exit(main())
