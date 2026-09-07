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
/* 대화문은 발화마다 한 줄. 둘째 줄부터 들여써서 화자 표시가 눈에 걸리게 한다. */
.passage p.turn { margin: 0 0 0.6mm; padding-left: 6mm; text-indent: -6mm;
                  line-height: 1.55; }
/* 묶인 대화는 서로 다른 대화라는 것이 한눈에 보여야 한다 — 원장 지시 2026-09-07.
   간격만으로는 같은 대화의 문단처럼 읽힌다. 이름표를 달고 선으로 가른다. */
.dlg { border-top: 1px dashed #c9d2dd; padding-top: 2.2mm; margin-top: 2.6mm; }
.dlg:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
.dlg-label { font-size: 8.5pt; font-weight: 700; color: #1f2d3d;
             background: #e8edf3; border-radius: 2px; padding: 0.4mm 2mm;
             display: inline-block; margin-bottom: 1.2mm; }
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
/* 2차 정답지: 영어 진술 밑에 1차 때 쓴 우리말을 같이 둔다 */
.ko2 { color: #5b6b80; font-size: 9pt; }
.tag { font-size: 7.5pt; color: #6b7a90; background: #eef2f7; border-radius: 2px;
       padding: 0.3mm 1.2mm; margin-right: 1.5mm; white-space: nowrap; }
.tag.p { background: #fdf0e6; color: #9a5b1e; }
.round { font-size: 9.5pt; font-weight: 600; color: #5b6b80; margin-left: 2mm; }
/* 영어 진술은 한국어보다 길다. 2단이 좁으면 줄이 많이 접힌다. */
ol.q.en { column-gap: 6mm; }
ol.q.en li { font-size: 9pt; }
.newpage { break-before: page; }
.foot { font-size: 8.5pt; color: #889; margin-top: 5mm; }
"""


def esc(s):
    return html.escape(s or "", quote=False)


def numbered(sentences, breaks=None, turns=None, dialogue=False):
    """문장마다 번호를 달고 끊는다.

    본문은 **문단**에서, 대화문은 **발화**에서 끊는다. 대화문을 이어 붙이면
    누가 무슨 말을 했는지 눈으로 따라가기 어렵다 — 원장 지시(2026-09-07):
    「한 명의 대사가 한 줄에 자리잡도록. 세로로 3단을 차지하는 한이 있어도.」

    그리고 대화문 여러 편을 묶었을 때는 **어디까지가 한 대화인지** 이름표를 단다.
    간격만 두면 같은 대화의 문단처럼 읽힌다 —
    「각기 다른 대화문의 경우는 줄이나 칸 나눔으로 분리해서 <대화 1> <대화 2>」.
    """
    cut = set((turns if dialogue and turns else breaks) or [])
    para = list(breaks or [])
    if not dialogue:
        out, cur = [], []
        for i, s in enumerate(sentences, 1):
            cur.append(f'<span class="sn">{i}</span>{esc(s)}')
            if i in cut:
                out.append(f'<p class="line">{" ".join(cur)}</p>')
                cur = []
        if cur:
            out.append(f'<p class="line">{" ".join(cur)}</p>')
        return "".join(out)

    # ── 대화문: 대화 한 편씩 상자로 묶고 그 안에서 발화마다 줄을 바꾼다 ──
    blocks, cur, lines, n_dlg = [], [], [], 0
    for i, s in enumerate(sentences, 1):
        cur.append(f'<span class="sn">{i}</span>{esc(s)}')
        if i in cut:
            lines.append(f'<p class="line turn">{" ".join(cur)}</p>')
            cur = []
        if i in para:                       # 대화 한 편이 끝났다
            n_dlg += 1
            label = (f'<span class="dlg-label">대화 {n_dlg}</span>'
                     if len(para) > 1 else "")
            blocks.append(f'<div class="dlg">{label}{"".join(lines)}</div>')
            lines = []
    if cur:
        lines.append(f'<p class="line turn">{" ".join(cur)}</p>')
    if lines:
        blocks.append(f'<div class="dlg">{"".join(lines)}</div>')
    return "".join(blocks)


def build(d, logo, lang="ko"):
    """lang: ko = 1차(한국어 진술) · en = 2차(영어 진술)

    원장 지시(2026-09-07): 한국어판을 먼저 보고 **1주일 뒤** 영어판을 다시 본다.
    같은 문항이므로 번호도 같다 — 아이가 1차 때 틀린 번호를 그대로 짚을 수 있다.
    """
    unit = d["unit"]
    items = d["items"]
    if lang == "en":
        items = [x for x in items if x.get("statement_en")]
    n = len(items)
    n_para = sum(1 for x in items if x.get("type") == "paraphrase")
    para_note = f" (그중 바꿔쓰기 {n_para}문항)" if n_para else ""
    round_no = "2차 (영어)" if lang == "en" else "1차 (우리말)"
    head = (f'<div class="head"><div>{logo}'
            f'<h1>{esc(unit)} — 내용 확인 <span class="round">{round_no}</span></h1>'
            f'<div class="sub" style="margin:0">읽고 맞으면 O, 틀리면 X 하시오. '
            f'· 총 {n}문항{para_note}</div></div>'
            f'<div class="name">이름 ______________</div></div>')

    def tag(it):
        # 바꿔쓰기 문항만 표시한다. 내용 확인이 기본이라 굳이 이름을 안 붙인다.
        return '<span class="tag p">바꿔쓰기</span>' if it.get("type") == "paraphrase" else ""

    def text(it):
        return it["statement_en"] if lang == "en" else it["statement_ko"]

    q = "".join(
        f'<li><span class="no">{i}</span><span class="ox">O X</span>'
        f'<span class="st">{tag(it)}{esc(text(it))}</span></li>'
        for i, it in enumerate(items, 1))

    sheet = (head
             + f'<div class="passage">{numbered(d["sentences"], d.get("para_breaks"), d.get("turn_breaks"), d.get("kind") == "textbook_dialogue")}</div>'
             + f'<ol class="q">{q}</ol>'
             + '<div class="foot">리디튜드 · 학원 내부 지도용</div>')

    def ans_body(it):
        """2차(영어)는 영어를 위에, 우리말을 아래에 둔다.

        아이 답안지에는 영어 진술이 찍혀 있는데 정답지가 우리말만 보이면
        강사가 눈으로 짝을 못 맞춘다. 1차와 같은 문항이라 번호는 같지만,
        틀린 이유를 짚어 주려면 영어 문장 그대로가 손에 있어야 한다.
        """
        if lang == "en":
            return (f'{esc(it["statement_en"])}<br>'
                    f'<span class="ko2">{esc(it["statement_ko"])}</span>')
        return esc(it["statement_ko"])

    a = "".join(
        f'<li><span class="no">{i}</span>'
        f'<span class="st"><span class="ans-tag {it["answer"]}">{it["answer"]}</span>'
        f'{tag(it)}{ans_body(it)}<br>'
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
    ap.add_argument("--lang", choices=["ko", "en"], default="ko",
                    help="ko=1차(한국어) · en=2차(영어). 같은 문항의 두 판이다")
    a = ap.parse_args()

    with open(a.drill, encoding="utf-8") as f:
        d = json.load(f)
    suffix = ".en.html" if a.lang == "en" else ".html"
    out = a.out or a.drill.replace(".json", suffix)
    n = len([x for x in d["items"] if x.get("statement_en")]) if a.lang == "en"         else len(d["items"])
    if a.lang == "en" and n == 0:
        raise SystemExit("영어 진술이 없습니다. 먼저 tools/make_drill_en.py 를 돌리십시오")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(d, logo_tag(DEFAULT_LOGO), a.lang))
    print(f"  {d['unit']} · {a.lang} · 문항 {n} · 지문 {len(d['sentences'])}문장")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
