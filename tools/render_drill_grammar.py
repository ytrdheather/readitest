# -*- coding: utf-8 -*-
"""
어법 확인 드릴 → 인쇄용 HTML (학습지 + 정답지 별지).

  python tools/render_drill_grammar.py data/generated/drills/L5_대화_123_길_묻고_답하기.gram.json

## 두 형식으로 낸다 — 학교가 실제로 내는 것이다

    A 괄호 안에서 고르기      태장·영덕 `Exercise A` 7번 · 영일 배부물
    B 틀린 곳 찾아 고쳐 쓰기   영덕 `Read and Correct` · 태장 `Exercise A` 5번

같은 포인트를 두 번 치되 **묻는 방식이 다르다.** 고르기는 알아보는 힘을,
고쳐 쓰기는 직접 쓰는 힘을 본다. 원장이 말한 「맞는 표현 틀린 표현, 혹은
맞는 어법 틀린 어법 확인형」이 이 둘이다.

문항을 반씩 갈라 A·B 에 배분한다. 같은 자리를 두 형식으로 두 번 묻지 않는다 —
한 학습지 안에서 같은 답을 두 번 쓰게 하면 뒤엣것은 그냥 베낀다.
"""
import argparse
import html
import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT      # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CSS = FONT + """
@page { size: A4; margin: 11mm 12mm 7mm; }
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
h2 { font-size: 10.5pt; margin: 4mm 0 1.8mm; padding: 1mm 2mm; background: #eef2f7;
     border-left: 3px solid #1f2d3d; break-after: avoid; }
h2 .n { color: #6b7a90; font-weight: 400; font-size: 9pt; margin-left: 1.5mm; }
ol.q { list-style: none; padding: 0; margin: 0; }
ol.q li { break-inside: avoid; padding: 1.5mm 0; border-bottom: 1px dotted #e3e8ee;
          display: flex; gap: 2mm; align-items: baseline; font-size: 9.5pt; }
.no { width: 7mm; text-align: right; color: #98a2b3; flex: none;
      font-variant-numeric: tabular-nums; }
.s { flex: 1; }
.sn { font-size: 7pt; color: #8a94a6; vertical-align: super; margin-right: 0.6mm; }
/* 괄호 안 선택지 — 굵게 해서 눈이 바로 간다 */
.pick { font-weight: 600; color: #1f2d3d; white-space: nowrap; }
.pick .sep { color: #99a3b0; font-weight: 400; margin: 0 1.5mm; }
/* 고쳐 쓰기 — 틀린 부분에 밑줄, 뒤에 답 쓸 자리 */
.bad { text-decoration: underline; text-underline-offset: 2px;
       text-decoration-color: #b3261e; font-weight: 600; }
.fix { display: block; margin: 1mm 0 0 7mm; border-bottom: 1px solid #ccd3dc;
       min-height: 4.6mm; }
.ans { color: #1f7a4d; font-weight: 700; }
.pt { font-size: 7.5pt; color: #6b7a90; background: #eef2f7; border-radius: 2px;
      padding: 0.3mm 1.2mm; margin-right: 1.5mm; white-space: nowrap; }
.why { color: #667; font-size: 8.5pt; display: block; margin: 0.5mm 0 0 7mm; }
.newpage { break-before: page; }
"""


def esc(s):
    return html.escape(s or "", quote=False)


def split_items(items, seed=20260909):
    """문항을 A(고르기)와 B(고쳐 쓰기)로 나눈다. 같은 자리는 한 번만 쓴다."""
    rng = random.Random(seed)
    idx = list(range(len(items)))
    rng.shuffle(idx)
    half = len(idx) // 2
    pick = sorted(idx[:half])
    fix = sorted(idx[half:])
    return [items[i] for i in pick], [items[i] for i in fix]


def mark_sentence(it, mode, ans, rng):
    """문장 안에서 그 자리만 바꿔 찍는다. 나머지는 본문 그대로다."""
    s, cor = it["sentence"], it["correct"]
    at = s.find(cor)
    if at < 0:                       # 문장 조립이 어긋나면 통째로 보여 준다
        return esc(s)
    head, tail = esc(s[:at]), esc(s[at + len(cor):])

    if mode == "pick":
        opts = [cor, it["wrong"][0]]
        rng.shuffle(opts)
        inner = f'<span class="sep">/</span>'.join(
            f'<span class="ans">{esc(o)}</span>' if (ans and o == cor) else esc(o)
            for o in opts)
        return f'{head}<span class="pick">( {inner} )</span>{tail}'

    bad = it["wrong"][0]
    shown = f'<span class="bad">{esc(bad)}</span>'
    return f'{head}{shown}{tail}'


def build(d, logo, part="both"):
    pick, fix = split_items(d["items"])

    def section(title, rows, mode, ans):
        rng = random.Random(20260909)
        li = []
        for i, it in enumerate(rows, 1):
            body = mark_sentence(it, mode, ans, rng)
            extra = ""
            if mode == "fix":
                if ans:
                    extra = (f'<span class="fix" style="border:0">'
                             f'→ <span class="ans">{esc(it["correct"])}</span></span>')
                else:
                    extra = '<span class="fix"></span>'
            why = (f'<span class="why"><span class="pt">{esc(it["point"])}</span>'
                   f'{esc(it["why_ko"])}</span>') if ans else ""
            li.append(f'<li><span class="no">{i}</span><span class="s">'
                      f'<span class="sn">{it["sentence_no"]}</span>{body}'
                      f'{extra}{why}</span></li>')
        return (f'<h2>{title}<span class="n">{len(rows)}문항</span></h2>'
                f'<ol class="q">{"".join(li)}</ol>')

    def page(ans, cls=""):
        sub = ("정답 및 해설 — 강사용 별지. 학생에게 배부하지 마십시오."
               if ans else "어법 확인 드릴")
        head = (f'<div class="{cls}"><div class="head"><div>{logo}'
                f'<h1>{esc(d["book"])} {esc(d["unit"])} — 어법 확인</h1>'
                f'<div class="sub">{sub}</div></div>'
                f'<div><div class="name">이름 ______________</div>'
                f'<div class="mark">리디튜드 · 학원 내부 지도용</div></div></div>')
        return (head
                + section("A. 괄호 안에서 어법에 맞는 것을 고르시오.", pick, "pick", ans)
                + section("B. 밑줄 친 부분이 어법상 틀렸습니다. 바르게 고쳐 쓰시오.",
                          fix, "fix", ans)
                + "</div>")

    if part == "worksheet":
        return f"<style>{CSS}</style>{page(False)}"
    if part == "answers":
        return f"<style>{CSS}</style>{page(True)}"
    return f"<style>{CSS}</style>{page(False)}{page(True, 'newpage')}"


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
    print(f"  {d['unit']} · {a.part} · {len(d['items'])}문항  →  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
