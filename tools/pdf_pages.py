# -*- coding: utf-8 -*-
"""
출력물 PDF 의 **아래 가운데에 쪽수**를 찍는다 — `3 / 37` 꼴.

  from tools.pdf_pages import save_pdf
  save_pdf(writer, "result/…/영덕중2 6과 리디튜드 자체드릴.pdf")

## 왜 여기서 찍는가

원장 지침 (2026-09-18): **모든 출력물은 아래 가운데에 쪽수를 표기한다.**
(`docs/출력물_디자인_지침.md` 1번)

HTML 쪽에서는 못 한다 — Chrome 은 `@page { @bottom-center }` 를 지원하지 않고,
`--print-to-pdf` 의 기본 머리글·바닥글은 날짜·URL 까지 붙어 학습지에 못 쓴다.
그리고 한 권은 세트 여러 개를 따로 찍어 pypdf 로 잇기 때문에, 세트 안에서 센 쪽수는
권 전체 쪽수와 맞지 않는다. **다 이은 뒤에** 전체 쪽수를 알고 찍어야 한다.

그래서 PDF 를 저장하는 자리는 전부 `save_pdf` 를 거친다 — `build_drill_pdf` ·
`build_school_drills` · `build_mock_pdf`. 새 build_*.py 를 만들면 `writer.write()` 대신
이것을 부를 것. 그러면 지침을 잊어도 쪽수는 붙는다.

글꼴은 Helvetica (PDF 기본 14종) — 숫자와 빗금뿐이라 한글이 필요 없고, 폰트를
심지 않아도 어느 뷰어에서나 나온다. 바닥 여백 안에 들어가야 하므로 렌더러의
`@page` 바닥 여백은 12mm 이상으로 둔다 (같은 지침 1번).
"""
import os

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject, NameObject,
                           StreamObject)

MM = 72 / 25.4
FONT_SIZE = 9
BASELINE_MM = 6            # 종이 아래 끝에서 글자 밑선까지. 프린터 인쇄 불가 영역(~5mm) 밖

# Helvetica 글자 폭 (1000 em 기준). 가운데 맞추는 데만 쓴다.
_W = {**{c: 556 for c in "0123456789"}, " ": 278, "/": 278}


def _text_width(text, size):
    return sum(_W.get(c, 556) for c in text) / 1000 * size


def _overlay(width, height, text):
    """글자 하나만 놓인 투명한 한 쪽. merge_page 로 원래 쪽 위에 얹는다."""
    w = PdfWriter()
    pg = w.add_blank_page(width=width, height=height)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    pg[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): w._add_object(font)}),
    })
    x = (float(width) - _text_width(text, FONT_SIZE)) / 2
    y = BASELINE_MM * MM
    body = f"BT /F1 {FONT_SIZE} Tf 0.27 g {x:.2f} {y:.2f} Td ({text}) Tj ET".encode("latin-1")
    stream = StreamObject()
    stream._data = body
    pg[NameObject("/Contents")] = w._add_object(stream)
    return pg


def stamp_page_numbers(writer):
    """writer 의 모든 쪽 아래 가운데에 `n / N` 을 찍는다. 제자리에서 바꾼다."""
    total = len(writer.pages)
    for i, page in enumerate(writer.pages, 1):
        box = page.mediabox
        page.merge_page(_overlay(box.width, box.height, f"{i} / {total}"))
    return writer


def save_pdf(writer, dest):
    """쪽수를 찍고 저장한다. PDF 를 파일로 내는 자리는 전부 이것을 쓴다."""
    stamp_page_numbers(writer)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with open(dest, "wb") as f:
        writer.write(f)
    return len(writer.pages)


def stamp_file(src, dest=None):
    """이미 있는 PDF 한 개에 쪽수를 찍는다 (Chrome 이 바로 낸 파일용)."""
    w = PdfWriter()
    for pg in PdfReader(src).pages:
        w.add_page(pg)
    return save_pdf(w, dest or src)
