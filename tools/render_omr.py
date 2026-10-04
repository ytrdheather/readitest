# -*- coding: utf-8 -*-
"""
동형 모의고사 OMR 답안지 — A4 한 장에 두 장 (잘라서 A5 가로 두 장).

  python tools/render_omr.py                # result/readitude/ 에 PDF + data/omr/ 에 좌표
  python tools/render_omr.py --digits 5     # 출결번호 자릿수를 바꿀 때

## 왜 새로 만들었나 (2026-10-04 원장)

원래 쓰던 `Z:\\…\\중등 내신 동형 모의고사\\OMR 최종본.pdf` 는 A4 한 장에 세 장이라
자르면 약 210×99mm — 복합기 자동 급지가 받지 못하는 크기다. 그리고

  · 학년/반/번호 마킹에 ⓪ 이 없어 10·20번을 칠할 수 없었다 → **출결번호 ⓪~⑨**
  · 세트를 적을 곳이 없었다 → **세트 마킹 ①~⑨** (스캔본만 보고 어느 세트인지 안다)
  · 서술형 칸이 4개였다 → **5개** (영덕중2 4~6세트 서술 5문항)

모양(머리줄·객관식 파란 띠·서술형 답란)은 원래 것을 따랐다 — 아이들이 보던 것과 같게.

## 좌표는 여기 한 곳에서만 정한다

PDF(HTML) 와 `data/omr/omr_layout_v{N}.json` 을 **같은 계산에서** 낸다. 채점기는 JSON 만
읽는다. 양식을 손으로 고치고 JSON 을 따로 고치면 언젠가 어긋나고, 어긋나면 엉뚱한 칸을
읽어 **틀린 점수가 성적표에 찍힌다.** 양식을 바꾸면 LAYOUT_VERSION 을 올린다.

좌표는 전부 **카드 왼쪽 위 모서리 기준 mm**. 스캔본에서는 네 모서리의 검은 표식(MARKERS)
중심을 찾아 mm → 픽셀로 옮긴다. 왼쪽 위에만 작은 표식이 하나 더 있어 거꾸로 넣은 것도 안다.
"""
import argparse
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.build_drill_pdf import find_chrome, to_pdf  # noqa: E402
from tools.pdf_pages import stamp_file                  # noqa: E402

LAYOUT_VERSION = 1
OUT_PDF = os.path.join(ROOT, "result", "readitude", "중등 내신 동형모의고사 OMR 답안지.pdf")
OUT_LAYOUT = os.path.join(ROOT, "data", "omr", f"omr_layout_v{LAYOUT_VERSION}.json")

# --- 카드 (A4 세로를 반으로 = A5 가로) ------------------------------------
CARD_W, CARD_H = 210.0, 148.5
MARK = 5.0                        # 모서리 표식 한 변
MARK_INSET = 6.5                  # 종이 끝에서 표식 중심까지
# 아래 카드의 바닥 12mm 는 쪽수 자리 (디자인 지침 1) — 표식 아래 끝이 그보다 위에 있어야 한다
assert CARD_H - (MARK_INSET + MARK / 2) - MARK / 2 >= 12 - MARK / 2

X0, X1 = 14.0, 196.0              # 내용 왼쪽·오른쪽 끝
HEAD_Y0, HEAD_Y1 = 7.0, 15.0      # 머리줄 (시험·학년·성명·확인)
BODY_Y0, BODY_Y1 = 18.0, 131.0    # 마킹·답란 영역
GAP = 2.5

BUBBLE = 3.2                      # 마킹 원 지름
BUBBLE_PITCH = 4.4                # 객관식 ①~⑤ 가로 간격 — 원 사이 1.2mm, 사인펜이 옆 칸에 번지지 않게

N_CHOICE = 30                     # 객관식 1~30 (동형은 선택 18~23)
CHOICE_COLS = 3
N_ESSAY = 5
SET_MAX = 9

INK = "#1f2a44"
BAND = "#dde6f4"


def layout(digits):
    """카드 하나의 좌표. HTML 과 JSON 이 모두 이것을 쓴다."""
    L = {"version": LAYOUT_VERSION, "unit": "mm", "card": [CARD_W, CARD_H],
         "bubble_d": BUBBLE}

    m = MARK_INSET
    L["markers"] = {"tl": [m, m], "tr": [CARD_W - m, m],
                    "bl": [m, CARD_H - m], "br": [CARD_W - m, CARD_H - m]}
    L["orient_mark"] = [m + MARK / 2 + 2.5, m]          # 왼쪽 위 표식 옆 작은 표식
    L["marker_size"] = MARK

    # 머리줄
    widths = [("시험", 62), ("학년", 26), ("성명", 64), ("확인", 30)]
    x, head = X0, []
    for label, w in widths:
        head.append({"label": label, "x": x, "w": w})
        x += w
    L["header"] = {"y0": HEAD_Y0, "y1": HEAD_Y1, "cells": head}

    # 출결번호 + 세트 — 원래 양식의 「학년 반 번호 과목」 자리
    col_w, title_h, write_h = 5.4, 6.0, 6.5
    id_x0 = X0
    id_cols = [id_x0 + 1.5 + col_w * (i + 0.5) for i in range(digits)]
    set_x = id_cols[-1] + col_w / 2 + 2.0 + col_w / 2
    id_x1 = set_x + col_w / 2 + 1.5
    rows_y0 = BODY_Y0 + title_h + write_h
    row_h = (BODY_Y1 - rows_y0) / 10
    row_c = [rows_y0 + row_h * (i + 0.5) for i in range(10)]
    L["student_id"] = {"digits": digits, "values": list(range(10)),
                       "cols": [[[cx, row_c[v]] for v in range(10)] for cx in id_cols]}
    L["set"] = {"values": list(range(1, SET_MAX + 1)),
                "bubbles": [[set_x, row_c[v]] for v in range(1, SET_MAX + 1)]}
    L["_id_box"] = {"x0": id_x0, "x1": id_x1, "col_w": col_w, "title_h": title_h,
                    "write_h": write_h, "row_c": row_c, "row_h": row_h,
                    "id_cols": id_cols, "set_x": set_x}

    # 객관식
    num_w = 6.0
    col_span = num_w + BUBBLE_PITCH * 5 + 1.2
    ch_x0 = id_x1 + GAP
    ch_x1 = ch_x0 + col_span * CHOICE_COLS
    ch_title = 7.0
    per_col = N_CHOICE // CHOICE_COLS
    ch_row_h = (BODY_Y1 - BODY_Y0 - ch_title) / per_col
    choices = {}
    for q in range(1, N_CHOICE + 1):
        c, r = divmod(q - 1, per_col)
        cy = BODY_Y0 + ch_title + ch_row_h * (r + 0.5)
        bx0 = ch_x0 + col_span * c + num_w + BUBBLE_PITCH / 2 + 0.6   # 번호 칸 세로줄에서 띄움
        choices[str(q)] = [[bx0 + BUBBLE_PITCH * k, cy] for k in range(5)]
    L["choices"] = choices
    L["_ch_box"] = {"x0": ch_x0, "x1": ch_x1, "title_h": ch_title, "row_h": ch_row_h,
                    "col_span": col_span, "num_w": num_w, "per_col": per_col}

    # 서술형 — 손글씨는 기계가 읽지 않는다. 칸 위치만 남겨 결과지에 잘라 붙인다
    es_x0 = ch_x1 + GAP
    es_title, es_num = 8.0, 6.0
    box_h = (BODY_Y1 - BODY_Y0 - es_title) / N_ESSAY
    L["essays"] = [{"n": i + 1,
                    "box": [es_x0 + es_num, BODY_Y0 + es_title + box_h * i, X1,
                            BODY_Y0 + es_title + box_h * (i + 1)]}
                   for i in range(N_ESSAY)]
    L["_es_box"] = {"x0": es_x0, "title_h": es_title, "num_w": es_num, "box_h": box_h}
    return L


# --- HTML -------------------------------------------------------------------


def _abs(x, y, w, h, style="", inner="", cls=""):
    return (f'<div class="{cls}" style="left:{x:.2f}mm;top:{y:.2f}mm;width:{w:.2f}mm;'
            f'height:{h:.2f}mm;{style}">{inner}</div>')


def _bubble(cx, cy, label):
    r = BUBBLE / 2
    return _abs(cx - r, cy - r, BUBBLE, BUBBLE, inner=label, cls="bb")


def _text(x, y, w, h, s, cls="t"):
    return _abs(x, y, w, h, inner=s, cls=cls)


def card_html(L, oy):
    out = []
    a = lambda x, y, w, h, **k: out.append(_abs(x, y + oy, w, h, **k))  # noqa: E731

    # 표식
    for cx, cy in L["markers"].values():
        a(cx - MARK / 2, cy - MARK / 2, MARK, MARK, cls="mk")
    ox, oy_ = L["orient_mark"]
    a(ox - 1.25, oy_ - 1.25, 2.5, 2.5, cls="mk")

    # 머리줄
    h = L["header"]
    for c in h["cells"]:
        a(c["x"], h["y0"], c["w"], h["y1"] - h["y0"], cls="cell",
          inner=f'<span class="lab">{c["label"]}</span>')

    # 출결번호 · 세트
    b = L["_id_box"]
    a(b["x0"], BODY_Y0, b["x1"] - b["x0"], BODY_Y1 - BODY_Y0, cls="box")
    id_cols = b["id_cols"]
    span_l = id_cols[0] - b["col_w"] / 2
    span_r = id_cols[-1] + b["col_w"] / 2
    a(b["x0"], BODY_Y0, b["x1"] - b["x0"], b["title_h"], cls="bandtitle")
    out.append(_text(span_l, BODY_Y0 + oy, span_r - span_l, b["title_h"], "출결번호", "th"))
    out.append(_text(b["set_x"] - b["col_w"] / 2 - 1, BODY_Y0 + oy, b["col_w"] + 2,
                     b["title_h"], "세트", "th"))
    wy = BODY_Y0 + b["title_h"]
    for cx in id_cols + [b["set_x"]]:
        a(cx - b["col_w"] / 2 + 0.3, wy + 0.6, b["col_w"] - 0.6, b["write_h"] - 1.2, cls="wr")
    for col in L["student_id"]["cols"]:
        for v, (cx, cy) in enumerate(col):
            out.append(_bubble(cx, cy + oy, str(v)))
    for v, (cx, cy) in zip(L["set"]["values"], L["set"]["bubbles"]):
        out.append(_bubble(cx, cy + oy, str(v)))
    # 출결번호와 세트 사이 세로줄
    sep = id_cols[-1] + b["col_w"] / 2 + 1.0
    a(sep, BODY_Y0 + b["title_h"], 0, BODY_Y1 - BODY_Y0 - b["title_h"], cls="vl")

    # 객관식
    c = L["_ch_box"]
    a(c["x0"], BODY_Y0, c["x1"] - c["x0"], BODY_Y1 - BODY_Y0, cls="box")
    a(c["x0"], BODY_Y0, c["x1"] - c["x0"], c["title_h"], cls="bandtitle",
      inner='<span class="big">객 관 식 답 란</span>')
    for k in range(CHOICE_COLS):
        x = c["x0"] + c["col_span"] * k
        if k % 2 == 1:
            a(x, BODY_Y0 + c["title_h"], c["col_span"], BODY_Y1 - BODY_Y0 - c["title_h"],
              cls="band")
        if k:
            a(x, BODY_Y0 + c["title_h"], 0, BODY_Y1 - BODY_Y0 - c["title_h"], cls="vl")
        a(x + c["num_w"], BODY_Y0 + c["title_h"], 0,
          BODY_Y1 - BODY_Y0 - c["title_h"], cls="vl thin")
    for r in range(1, c["per_col"]):
        a(c["x0"], BODY_Y0 + c["title_h"] + c["row_h"] * r, c["x1"] - c["x0"], 0,
          cls="hl" + (" mid" if r == 5 else ""))
    for q, bubbles in L["choices"].items():
        qi = int(q) - 1
        col = qi // c["per_col"]
        cy = bubbles[0][1]
        out.append(_text(c["x0"] + c["col_span"] * col, cy - 2 + oy, c["num_w"], 4,
                         q, "qn"))
        for k, (bx, by) in enumerate(bubbles):
            out.append(_bubble(bx, by + oy, str(k + 1)))

    # 서술형
    e = L["_es_box"]
    a(e["x0"], BODY_Y0, X1 - e["x0"], BODY_Y1 - BODY_Y0, cls="box")
    a(e["x0"], BODY_Y0, X1 - e["x0"], e["title_h"], cls="titlecell",
      inner='<span class="big">서 술 형 답 란</span>')
    a(e["x0"] + e["num_w"], BODY_Y0 + e["title_h"], 0,
      BODY_Y1 - BODY_Y0 - e["title_h"], cls="vl thin")
    for es in L["essays"]:
        x0, y0, x1, y1 = es["box"]
        if es["n"] > 1:
            a(e["x0"], y0, X1 - e["x0"], 0, cls="hl")
        out.append(_text(e["x0"], y0 + oy, e["num_w"], y1 - y0, str(es["n"]), "en"))

    # 원래 양식 이름을 한 줄 — 낱장으로 돌아다녀도 판(版)을 안다
    out.append(_text(X0, BODY_Y1 + 0.8 + oy, 120, 3.5,
                     f"리디튜드 동형모의고사 OMR · v{LAYOUT_VERSION} · "
                     "컴퓨터용 사인펜으로 칸을 꽉 채워 칠하십시오", "foot"))
    return "\n".join(out)


CSS = f"""
@page {{ size: A4; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: Pretendard, 'Malgun Gothic', sans-serif; color: {INK};
        width: 210mm; height: 297mm; position: relative; }}
body > div {{ position: absolute; box-sizing: border-box; }}
.mk {{ background: #000; }}
.cell {{ border: 0.45mm solid {INK}; margin-left: -0.45mm; font-size: 8pt;
         padding: 0.6mm 1.2mm; }}
.lab {{ font-weight: 600; }}
.box {{ border: 0.45mm solid {INK}; }}
.bandtitle {{ background: {BAND}; border: 0.45mm solid {INK}; display: flex;
              align-items: center; justify-content: center; }}
.titlecell {{ border: 0.45mm solid {INK}; display: flex; align-items: center;
              justify-content: center; }}
.band {{ background: {BAND}; }}
.big {{ font-size: 11.5pt; font-weight: 700; letter-spacing: 0.5mm; }}
.th {{ font-size: 7pt; font-weight: 700; display: flex; align-items: center;
       justify-content: center; }}
.wr {{ border: 0.25mm solid {INK}; background: #fff; }}
.vl {{ border-left: 0.35mm solid {INK}; }}
.vl.thin {{ border-left-width: 0.2mm; }}
.hl {{ border-top: 0.2mm solid #8a94a8; }}
.hl.mid {{ border-top: 0.35mm solid {INK}; }}
.bb {{ border: 0.22mm solid {INK}; border-radius: 50%; font-size: 5.6pt; font-weight: 500;
       display: flex; align-items: center; justify-content: center;
       line-height: 1; background: #fff; }}
.qn {{ font-size: 7.5pt; font-weight: 600; display: flex; align-items: center;
       justify-content: center; }}
.en {{ font-size: 9pt; font-weight: 600; display: flex; align-items: center;
       justify-content: center; }}
.foot {{ font-size: 5.8pt; color: #6a7388; }}
.cut {{ border-top: 0.25mm dashed #9aa3b5; }}
.cutlab {{ font-size: 6pt; color: #9aa3b5; }}
"""


def page_html(L):
    cards = [card_html(L, 0), card_html(L, CARD_H)]
    cut = (_abs(0, CARD_H, 210, 0, cls="cut")
           + _abs(2, CARD_H - 3.2, 10, 3, inner="✂", cls="cutlab"))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>" + CSS
            + "</style></head><body>" + "\n".join(cards) + cut + "</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digits", type=int, default=4, help="출결번호 자릿수")
    args = ap.parse_args()

    L = layout(args.digits)
    html = page_html(L)

    tmp = tempfile.mkdtemp(prefix="omr_")
    hp = os.path.join(tmp, "omr.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)
    to_pdf(find_chrome(), hp, OUT_PDF)
    stamp_file(OUT_PDF)                                   # 디자인 지침 1

    pub = {k: v for k, v in L.items() if not k.startswith("_")}
    pub["note"] = ("좌표는 카드 왼쪽 위 기준 mm. 생성: tools/render_omr.py — 손으로 고치지 말 것. "
                   "essays 칸은 기계가 읽지 않는다(손글씨). student_id.cols[자리][숫자] = 원 중심")
    os.makedirs(os.path.dirname(OUT_LAYOUT), exist_ok=True)
    with open(OUT_LAYOUT, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, indent=1)
    print("PDF  :", os.path.relpath(OUT_PDF, ROOT))
    print("좌표 :", os.path.relpath(OUT_LAYOUT, ROOT))


if __name__ == "__main__":
    main()
