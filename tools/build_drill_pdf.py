# -*- coding: utf-8 -*-
"""
내용 확인 O/X 드릴 12세트 → **묶음 PDF 4권**.

  python tools/build_drill_pdf.py

## 왜 4권인가

원장이 쓰는 순서가 그대로 권이 된다 (2026-09-07 · 09-08 지시).

    1차_우리말_문제.pdf     아이에게 배부       ← 지금
    1차_우리말_정답지.pdf   강사만              ← 지금
    2차_영어_문제.pdf       아이에게 배부       ← 1주일 뒤
    2차_영어_정답지.pdf     강사만              ← 1주일 뒤

**문제와 정답을 절대로 같은 권에 넣지 않는다.** `render_drill_tf.py` 가 정답지를
별지로 두는 것과 같은 이유다 — 같은 장에 정답이 있으면 아이가 본다.
12세트를 한 장씩 뽑아 두면 인쇄할 때마다 마지막 장을 떼야 하는데,
그걸 24번 하다 보면 언젠가 한 번은 딸려 나간다. 아예 권을 가른다.

## 쪽을 세지 않고 가른다

「PDF 를 만든 뒤 정답지 쪽을 잘라낸다」는 방법은 학습지가 1쪽인지 2쪽인지에 따라
경계가 달라져서 틀린다. 대신 **HTML 단계에서 갈라** 각각 뽑는다
(`render_drill_tf.py --part worksheet|answers`). 경계를 셀 일이 없다.

## Chrome 을 쓴다

학습지 CSS 가 `@page` · `break-inside: avoid` · `column-count` 를 쓴다.
weasyprint 는 다단을 제대로 안 깨고, wkhtmltopdf 는 `@page` 를 무시한다.
설치된 Chrome 의 `--headless --print-to-pdf` 가 화면에서 보던 것과 같게 나온다.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pypdf import PdfReader, PdfWriter                                # noqa: E402
from tools.render_drill_tf import build                               # noqa: E402
from tools.render_drill_vocab import build as build_vocab             # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DRILLS = os.path.join(ROOT, "data", "generated", "drills")
OUT = os.path.join(DRILLS, "pdf")

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# 권 이름 = 원장이 쓰는 순서. 파일 목록에서 정렬로 순서가 뒤집히지 않게 번호를 붙인다.
BOOKS = [
    ("ko", "worksheet", "1_1차_우리말_문제"),
    ("ko", "answers",   "2_1차_우리말_정답지"),
    ("en", "worksheet", "3_2차_영어_문제"),
    ("en", "answers",   "4_2차_영어_정답지"),
]

# 어휘는 우리말/영어 두 판이 없다 — 낱말은 한 번만 묻는다. 그래서 두 권이다.
VOCAB_BOOKS = [
    ("worksheet", "5_어휘_문제"),
    ("answers",   "6_어휘_정답지"),
]

# 어휘 세트를 뽑는 순서. 학교가 많은 쪽(L5 세 학교)을 앞에 둔다.
VOCAB_ORDER = ["태장_L5.vocab", "영덕_L5.vocab", "영덕_L6.vocab"]

# 학습지를 뽑는 순서. 대화문 → Read More → 본문 → 외부지문.
# 아이가 받는 차례이자 교과서 차례다. 파일명 사전순으로는 이 순서가 안 나온다.
ORDER = [
    "L5_대화_길_묻고_답하기.tf", "L5_대화_456.tf", "L5_대화_789.tf",
    "L5_Read_More.tf", "Street_Art_in_London.tf",
    "L6_대화_123.tf", "L6_대화_456.tf", "L6_대화_789.tf",
    "L6_Read_More.tf", "Dr_Schofield.tf",
    "A_girl_with_a_red_balloon.tf",
    "L5_대화_길_묻고_답하기.para",
]


def find_chrome():
    for p in CHROME:
        if os.path.exists(p):
            return p
    p = shutil.which("chrome") or shutil.which("msedge")
    if p:
        return p
    raise SystemExit("Chrome 을 못 찾았습니다. 경로를 CHROME 목록에 추가하십시오")


def ordered_vocab():
    have = {os.path.basename(p)[:-5]: p
            for p in glob.glob(os.path.join(DRILLS, "*.vocab.json"))}
    out = [have[n] for n in VOCAB_ORDER if n in have]
    for k in sorted(k for k in have if k not in VOCAB_ORDER):
        print(f"  ! VOCAB_ORDER 에 없어 뒤에 붙임: {k}")
        out.append(have[k])
    return out


def ordered_drills():
    """ORDER 순으로 늘어놓고, 목록에 없는 파일은 뒤에 붙인다.

    새 드릴을 만들고 ORDER 에 적는 것을 잊어도 **빠지지는 않게** 한다 —
    빠진 채로 인쇄되면 알아채기 어렵다.
    """
    have = {os.path.basename(p)[:-5]: p
            for p in glob.glob(os.path.join(DRILLS, "*.json"))
            if not p.endswith(".vocab.json")}
    out, seen = [], set()
    for name in ORDER:
        if name in have:
            out.append(have[name]); seen.add(name)
    extra = sorted(k for k in have if k not in seen)
    for k in extra:
        print(f"  ! ORDER 에 없어 뒤에 붙임: {k}")
        out.append(have[k])
    return out


def to_pdf(chrome, html_path, pdf_path):
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=8000",
         f"--print-to-pdf={pdf_path}", html_path],
        check=True, capture_output=True, timeout=180)
    if not os.path.exists(pdf_path):
        raise SystemExit(f"PDF 가 안 나왔습니다: {html_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    chrome = find_chrome()
    paths = ordered_drills()
    os.makedirs(a.out, exist_ok=True)
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="drillpdf_")
    print(f"  Chrome  {chrome}")
    print(f"  드릴 {len(paths)}세트\n")

    try:
        for lang, part, book in BOOKS:
            writer = PdfWriter()
            n_set = n_page = 0
            for i, p in enumerate(paths):
                with open(p, encoding="utf-8") as f:
                    d = json.load(f)
                if lang == "en" and not any(x.get("statement_en") for x in d["items"]):
                    print(f"    ! 영어 진술 없음, 건너뜀: {d['unit']}")
                    continue
                html = os.path.join(tmp, f"{book}_{i:02d}.html")
                pdf = os.path.join(tmp, f"{book}_{i:02d}.pdf")
                with open(html, "w", encoding="utf-8") as f:
                    f.write(build(d, logo, lang, part))
                to_pdf(chrome, html, pdf)
                r = PdfReader(pdf)
                for pg in r.pages:
                    writer.add_page(pg)
                n_set += 1
                n_page += len(r.pages)
            dest = os.path.join(a.out, f"{book}.pdf")
            with open(dest, "wb") as f:
                writer.write(f)
            print(f"  {book:24} {n_set:>2}세트 · {n_page:>2}쪽  →  {dest}")

        vocab = ordered_vocab()
        for part, book in VOCAB_BOOKS:
            writer = PdfWriter()
            n_set = n_page = 0
            for i, p in enumerate(vocab):
                with open(p, encoding="utf-8") as f:
                    d = json.load(f)
                html = os.path.join(tmp, f"{book}_{i:02d}.html")
                pdf = os.path.join(tmp, f"{book}_{i:02d}.pdf")
                with open(html, "w", encoding="utf-8") as f:
                    f.write(build_vocab(d, logo, part))
                to_pdf(chrome, html, pdf)
                r = PdfReader(pdf)
                for pg in r.pages:
                    writer.add_page(pg)
                n_set += 1
                n_page += len(r.pages)
            dest = os.path.join(a.out, f"{book}.pdf")
            with open(dest, "wb") as f:
                writer.write(f)
            print(f"  {book:24} {n_set:>2}세트 · {n_page:>2}쪽  →  {dest}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n  문제와 정답은 서로 다른 권에 있습니다. 정답지 2권은 강사만 가지십시오.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
