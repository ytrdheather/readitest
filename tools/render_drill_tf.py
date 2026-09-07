# -*- coding: utf-8 -*-
"""
내용일치 O/X 드릴 → 인쇄용 HTML (학습지 + 정답지 별지).

  python tools/render_drill_tf.py data/generated/drills/Street_Art_in_London.tf.json

## 왜 정답지를 별지로 두는가

같은 장에 정답이 있으면 아이가 본다. 학습지와 정답지를 따로 뽑아 강사만 갖는다.
`render_worksheet.py` 와 같은 방침이다.

## 문장 번호를 지문에 박는다

문항마다 근거 문장 번호가 붙어 있으므로, 지문에도 같은 번호가 보여야 짝이 맞는다.
번호는 `pipeline.passage.split_sentences` 가 매기는 것과 **같은 번호**다 —
드릴을 만들 때 쓴 것과 학습지에 찍히는 것이 어긋나면 해설이 엉뚱한 곳을 가리킨다.
"""
import argparse
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT      # noqa: E402
from pipeline.passage import split_sentences                          # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CSS = FONT + """
@page { size: A4; margin: 13mm 12mm 12mm; }
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #111; }
.logo { height: 10mm; margin-bottom: 1mm; }
h1 { font-size: 15pt; margin: 0 0 0.5mm; }
.sub { color: #667; font-size: 9pt; margin-bottom: 4mm; }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #1f2d3d; padding-bottom: 1.5mm; margin-bottom: 3mm; }
.name { font-size: 9pt; color: #445; border: 1px solid #ccd; border-radius: 2px;
        padding: 1mm 5mm; white-space: nowrap; }
.passage { border: 1px solid #d8dde3; border-radius: 3px; padding: 3mm 4mm;
           background: #fbfcfd; margin-bottom: 4mm; line-height: 1.8;
           break-inside: avoid; font-size: 10pt; }
.passage p { margin: 0 0 1.8mm; }
.passage p:last-child { margin-bottom: 0; }
.sn { font-size: 7pt; color: #8a94a6; vertical-align: super; margin-right: 0.6mm; }
.howto { font-size: 9pt; color: #555; margin-bottom: 3mm; }
/* 문항은 한국어 한 줄이라 2단이 들어간다. 한 장에 담으면 아이가 지문과 함께 본다. */
ol.q { list-style: none; padding: 0; margin: 0; column-count: 2; column-gap: 7mm;
       column-rule: 1px solid #eef; }
ol.q li { break-inside: avoid; padding: 1.3mm 0; border-bottom: 1px dotted #dde;
          display: flex; gap: 2mm; align-items: baseline; font-size: 9.5pt; }
ol.q.ans { column-count: 1; }
.no { width: 7mm; text-align: right; color: #98a2b3; flex: none;
      font-variant-numeric: tabular-nums; }
.ox { width: 11mm; flex: none; color: #99a; letter-spacing: 1.5mm; font-size: 9pt; }
.st { flex: 1; }
.ans-tag { display: inline-block; width: 6mm; font-weight: 700; }
.O { color: #1f7a4d; } .X { color: #b3261e; }
.ev { color: #667; font-size: 8.5pt; }
.tag { font-size: 7.5pt; color: #6b7a90; background: #eef2f7; border-radius: 2px;
       padding: 0.3mm 1.2mm; margin-right: 1.5mm; white-space: nowrap; }
.tag.p { background: #fdf0e6; color: #9a5b1e; }
.newpage { break-before: page; }
.foot { font-size: 8.5pt; color: #889; margin-top: 5mm; }
"""


def esc(s):
    return html.escape(s or "", quote=False)


def numbered(sentences, breaks=None):
    """문장마다 번호를 달고, 문단 경계에서 끊는다."""
    breaks = set(breaks or [])
    paras, cur = [], []
    for i, s in enumerate(sentences, 1):
        cur.append(f'<span class="sn">{i}</span>{esc(s)}')
        if i in breaks:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return "".join(f"<p>{x}</p>" for x in paras)


def build(d, logo):
    unit = d["unit"]
    items = d["items"]
    n = len(items)
    n_para = sum(1 for x in items if x.get("type") == "paraphrase")
    para_note = f" (그중 바꿔쓰기 {n_para}문항)" if n_para else ""
    head = (f'<div class="head"><div>{logo}<h1>{esc(unit)} — 내용 확인</h1>'
            f'<div class="sub" style="margin:0">읽고 맞으면 O, 틀리면 X 하시오. '
            f'· 총 {n}문항{para_note}</div></div>'
            f'<div class="name">이름 ______________</div></div>')

    def tag(it):
        # 바꿔쓰기 문항만 표시한다. 내용 확인이 기본이라 굳이 이름을 안 붙인다.
        return '<span class="tag p">바꿔쓰기</span>' if it.get("type") == "paraphrase" else ""

    q = "".join(
        f'<li><span class="no">{i}</span><span class="ox">O X</span>'
        f'<span class="st">{tag(it)}{esc(it["statement_ko"])}</span></li>'
        for i, it in enumerate(items, 1))

    sheet = (head
             + f'<div class="passage">{numbered(d["sentences"], d.get("para_breaks"))}</div>'
             + f'<ol class="q">{q}</ol>'
             + '<div class="foot">리디튜드 · 학원 내부 지도용</div>')

    a = "".join(
        f'<li><span class="no">{i}</span>'
        f'<span class="st"><span class="ans-tag {it["answer"]}">{it["answer"]}</span>'
        f'{tag(it)}{esc(it["statement_ko"])}<br>'
        f'<span class="ev">본문 {", ".join(map(str, it["evidence_sentences"]))}번 · '
        f'{esc(it["why_ko"])}</span></span></li>'
        for i, it in enumerate(items, 1))
    ans = (f'<div class="newpage">{logo}<h1>{esc(unit)} — 정답 및 해설</h1>'
           f'<div class="sub">강사용 별지. 학생에게 배부하지 마십시오.</div>'
           f'<ol class="q ans">{a}</ol></div>')
    return f"<style>{CSS}</style>{sheet}{ans}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("drill", help="tools/make_drill_tf.py 가 만든 .tf.json")
    ap.add_argument("--out")
    a = ap.parse_args()

    with open(a.drill, encoding="utf-8") as f:
        d = json.load(f)
    out = a.out or a.drill.replace(".tf.json", ".tf.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(d, logo_tag(DEFAULT_LOGO)))
    print(f"  {d['unit']} · 문항 {len(d['items'])} · 지문 {len(d['sentences'])}문장")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
