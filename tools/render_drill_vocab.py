# -*- coding: utf-8 -*-
"""
어휘 드릴 → 인쇄용 HTML (학습지 + 정답지 별지).

  python tools/render_drill_vocab.py data/generated/drills/태장_L5.vocab.json

O/X 드릴(`render_drill_tf.py`)과 같은 방침이다 — 정답은 **별지**로 두고 강사만 갖는다.
`--part worksheet|answers` 로 갈라 뽑을 수 있어 `build_drill_pdf.py` 가 권으로 묶는다.
"""
import argparse
import html
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT      # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CSS = FONT + """
@page { size: A4; margin: 11mm 12mm 12mm; }   /* 바닥 12mm: 쪽수 자리 (디자인 지침 1) */
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #111; }
.logo { height: 10mm; margin-bottom: 1mm; }
h1 { font-size: 15pt; margin: 0 0 0.5mm; }
.sub { color: #667; font-size: 9pt; }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #1f2d3d; padding-bottom: 1.5mm; margin-bottom: 3mm; }
.name { font-size: 9pt; color: #445; border: 1px solid #ccd; border-radius: 2px;
        padding: 1mm 5mm; white-space: nowrap; }
.mark { font-size: 7.5pt; color: #9aa3b0; text-align: right; margin-top: 1.2mm; }
h2 { font-size: 10.5pt; margin: 4mm 0 1.6mm; padding: 1mm 2mm; background: #eef2f7;
     border-left: 3px solid #1f2d3d; break-after: avoid; }
h2 .n { color: #6b7a90; font-weight: 400; font-size: 9pt; margin-left: 1.5mm; }
h3 { font-size: 9pt; color: #5b6b80; margin: 2.5mm 0 1.2mm; break-after: avoid; }
/* 양방향은 2단. 한 칸에 「낱말 ─ 빈 줄」이 들어간다 */
ol.g { list-style: none; padding: 0; margin: 0; column-count: 2; column-gap: 7mm; }
ol.g.one { column-count: 1; }
ol.g li { break-inside: avoid; display: flex; gap: 2mm; align-items: baseline;
          padding: 1.1mm 0; font-size: 9.5pt; }
.no { width: 7mm; text-align: right; color: #98a2b3; flex: none;
      font-variant-numeric: tabular-nums; }
.q { flex: none; }
.blank { flex: 1; border-bottom: 1px solid #ccd3dc; min-height: 4.6mm; margin-left: 2mm; }
.ans { color: #1f7a4d; font-weight: 600; }
/* 영영풀이는 길어서 1단 */
ol.g.def li { align-items: baseline; }
ol.g.def .q { flex: 1; font-size: 9pt; }
ol.g.def .blank { flex: none; width: 34mm; }
.pos { color: #8a94a6; font-size: 8.5pt; margin-right: 1mm; }
.ko { color: #667; font-size: 8.5pt; margin-left: 1.5mm; }
/* 연결 문제는 세 칸을 나란히 */
table.m { width: 100%; border-collapse: collapse; margin-bottom: 2.5mm;
          break-inside: avoid; font-size: 9pt; }
table.m td { border: 1px solid #dde3ea; padding: 1.4mm 2mm; vertical-align: top; }
table.m td.d { width: 47%; } table.m td.w { width: 17%; } table.m td.k { width: 17%; }
table.m td.a { width: 19%; font-size: 8.5pt; color: #445; }
.box { border: 1px solid #c9d2dd; background: #fbfcfd; border-radius: 3px;
       padding: 1.6mm 3mm; margin-bottom: 2mm; font-size: 9pt;
       display: flex; flex-wrap: wrap; gap: 2mm 6mm; break-inside: avoid; }
.box b { color: #1f2d3d; font-weight: 600; margin-right: 2mm; }
.cl { font-size: 9.5pt; padding: 1.2mm 0; break-inside: avoid; }
.cl .ko { display: block; margin: 0.4mm 0 0 7mm; }
.newpage { break-before: page; }
"""


def esc(s):
    return html.escape(s or "", quote=False)


def blank(w=None):
    style = f' style="flex:none;width:{w}"' if w else ""
    return f'<span class="blank"{style}></span>'


def sec_html(s, ans):
    """한 절을 찍는다. ans=True 면 빈칸 자리에 정답을 넣는다."""
    t = s["kind"]
    put = (lambda v, w=None: f'<span class="ans">{esc(v)}</span>' if ans else blank(w))
    out = []

    if t == "both":
        for label, rows, qf, af in (
                ("영어 → 우리말", s["en2ko"], "word", "answer"),
                ("우리말 → 영어", s["ko2en"], "ko", "answer")):
            li = "".join(
                f'<li><span class="no">{i}</span><span class="q">{esc(r[qf])}</span>'
                f'{put(r[af])}</li>' for i, r in enumerate(rows, 1))
            out.append(f'<h3>{label} · {len(rows)}문항</h3><ol class="g">{li}</ol>')

    elif t == "def":
        rows = []
        for i, r in enumerate(s["items"], 1):
            # 우리말 뜻은 **정답지에만** 둔다. 문제지에 같이 찍으면 답이 새고,
            # 「영영풀이를 외웠는지 확인한다」는 이 절의 목적이 사라진다
            # (원장 2026-09-05: 「영영어휘 뜻을 잘 암기했는지 확인할 수 있는 드릴」).
            ko = f'<span class="ko">({esc(r["ko"])})</span>' if (ans and r.get("ko")) else ""
            rows.append(f'<li><span class="no">{i}</span>'
                        f'<span class="q">{esc(r["def_en"])}</span>'
                        f'{put(r["answer"], "34mm")}{ko}</li>')
        out.append(f'<ol class="g def one">{"".join(rows)}</ol>')

    elif t == "match":
        # 세 칸을 한 줄에 늘어놓으면 **같은 줄이 정답**처럼 보인다. 실제로는 낱말과
        # 뜻을 따로 섞어 놓았으므로, 기호를 붙이고 답 칸을 따로 둔다.
        # 원본(영덕 Basic A)은 점을 선으로 잇는 방식인데, 인쇄물에서는 기호 쓰기가
        # 채점이 빠르고 아이가 헷갈리지 않는다.
        WSYM, KSYM = "㉠㉡㉢㉣㉤㉥", "ⓐⓑⓒⓓⓔⓕ"
        for gi, g in enumerate(s["groups"], 1):
            rows = []
            for i, d in enumerate(g["defs"]):
                # `defs` 는 낱말 레코드 그대로다 — 정답 열쇠는 `word`.
                if ans:
                    a1 = f'<span class="ans">{esc(d["word"])}</span>'
                    a2 = f'<span class="ans">{esc(d.get("ko", ""))}</span>'
                else:
                    a1 = a2 = '<span style="color:#c3cad4">____</span>'
                rows.append(
                    f'<tr><td class="d">{i+1}. {esc(d["def_en"])}</td>'
                    f'<td class="w">{WSYM[i]} {esc(g["words"][i])}</td>'
                    f'<td class="k">{KSYM[i]} {esc(g["kos"][i])}</td>'
                    f'<td class="a">{a1} · {a2}</td></tr>')
            out.append(f'<h3>묶음 {gi} — 영영풀이마다 알맞은 낱말(㉠~)과 뜻(ⓐ~)을 쓰시오</h3>'
                       f'<table class="m">{"".join(rows)}</table>')

    elif t == "cloze":
        n = 1
        for c in s["chunks"]:
            words = sorted(x["answer"] for x in c)
            box = ('<div class="box"><b>[보기]</b>'
                   + "".join(f"<span>{esc(w)}</span>" for w in words) + "</div>")
            body = []
            for x in c:
                line = x["sentence"]
                if ans:
                    line = line.replace("__________",
                                        f'<span class="ans">{esc(x["answer"])}</span>')
                else:
                    line = esc(line)
                # 예문 해석도 정답지에만. 「나는 우주여행에 관한 흥미로운 기사를
                # 읽었다」가 붙어 있으면 보기에서 article 을 고르는 것이 시험이 아니다.
                ko = f'<span class="ko">{esc(x["ko"])}</span>' if (ans and x.get("ko")) else ""
                body.append(f'<div class="cl"><span class="no">{n}</span> {line}{ko}</div>')
                n += 1
            out.append(box + "".join(body))

    elif t == "phrase":
        li = "".join(
            f'<li><span class="no">{i}</span><span class="q">{esc(p["ko"])}</span>'
            f'{put(p["phrase"])}</li>' for i, p in enumerate(s["items"], 1))
        out.append(f'<ol class="g one">{li}</ol>')

    return "".join(out)


LETTER = "ABCDEFGHIJ"


def build(d, logo, part="both"):
    def body(ans):
        blocks = []
        for pi, p in enumerate(d["parts"]):
            blocks.append(f'<h2>{"Ⅰ" if pi == 0 else "Ⅱ"}. {esc(p["label"])}'
                          f'<span class="n">{p["n_words"]}개</span></h2>')
            for si, s in enumerate(p["sections"]):
                blocks.append(f'<h3><b>{LETTER[si]}</b> {esc(s["title"])}</h3>')
                blocks.append(sec_html(s, ans))
        return "".join(blocks)

    def head(sub, cls=""):
        return (f'<div class="{cls}"><div class="head"><div>{logo}'
                f'<h1>{esc(d["title"])}</h1><div class="sub">{sub}</div></div>'
                f'<div><div class="name">이름 ______________</div>'
                f'<div class="mark">리디튜드 · 학원 내부 지도용</div></div></div>')

    sheet = head("어휘 확인 드릴") + body(False) + "</div>"
    ansd = (head("정답 및 해설 — 강사용 별지. 학생에게 배부하지 마십시오.",
                 "" if part == "answers" else "newpage")
            + body(True) + "</div>")
    if part == "worksheet":
        return f"<style>{CSS}</style>{sheet}"
    if part == "answers":
        return f"<style>{CSS}</style>{ansd}"
    return f"<style>{CSS}</style>{sheet}{ansd}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("drill")
    ap.add_argument("--out")
    ap.add_argument("--part", choices=["both", "worksheet", "answers"], default="both")
    a = ap.parse_args()

    d = json.load(io.open(a.drill, encoding="utf-8"))
    suffix = "" if a.part == "both" else f".{a.part}"
    out = a.out or a.drill.replace(".json", f"{suffix}.html")
    io.open(out, "w", encoding="utf-8").write(build(d, logo_tag(DEFAULT_LOGO), a.part))
    n = sum(v for p in d["parts"] for v in p["counts"].values())
    print(f"  {d['title']} · {a.part} · 총 {n}문항")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
