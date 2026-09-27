# -*- coding: utf-8 -*-
"""
동형 모의고사 → 인쇄용 HTML (시험지 + 정답지 별지).

  python tools/render_mock_exam.py data/generated/mock/영일중_1세트.json

시험지처럼 보여야 한다. 아이가 실제 시험지와 같은 모양에서 푸는 것이
「유형 대비」의 절반이다 — 원장이 3층을 주력으로 지정한 이유가 그것이다.

  · 2단 조판 (실제 중학교 시험지가 대부분 2단이다)
  · 문항마다 배점을 오른쪽에 붙인다
  · 지문은 상자에 넣어 문항과 구분한다
  · 서술형은 답 쓸 자리를 넉넉히 준다
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

CIRCLED = "①②③④⑤"

CSS = FONT + """
@page { size: A4; margin: 12mm 11mm 12mm; }   /* 바닥 12mm: 쪽수 자리 (디자인 지침 1) */
body { font-family: Pretendard,'Malgun Gothic',sans-serif; font-size: 9pt;
       line-height: 1.5; color: #111; }
.logo { height: 9mm; margin-bottom: 1mm; }
h1 { font-size: 14pt; margin: 0 0 0.5mm; }
.sub { color: #556; font-size: 8.5pt; }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2.5px solid #1f2d3d; padding-bottom: 1.5mm; margin-bottom: 3mm; }
.name { font-size: 8.5pt; color: #445; border: 1px solid #ccd; border-radius: 2px;
        padding: 1mm 4mm; white-space: nowrap; }
.mark { font-size: 7.5pt; color: #9aa3b0; text-align: right; margin-top: 1.2mm; }
/* 시험지는 2단이다 */
.cols { column-count: 2; column-gap: 7mm; column-rule: 1px solid #e6eaef; }
.mat { border: 1px solid #c9d2dd; background: #fbfcfd; border-radius: 3px;
       padding: 2mm 2.5mm; margin: 0 0 2.5mm; font-size: 8.5pt; line-height: 1.65;
       break-inside: avoid; }
.mat .t { font-size: 7.5pt; font-weight: 700; color: #1f2d3d; background: #e8edf3;
          border-radius: 2px; padding: 0.3mm 1.5mm; display: inline-block;
          margin-bottom: 1.2mm; }
.mat p { margin: 0 0 1.2mm; }
.q { break-inside: avoid; margin-bottom: 2.6mm; }
.q .stem { display: flex; gap: 1.5mm; align-items: baseline; font-weight: 600;
           font-size: 8.5pt; }
.q .no { flex: none; color: #1f2d3d; font-variant-numeric: tabular-nums; }
.q .pts { flex: none; color: #8a94a6; font-size: 7.5pt; margin-left: auto;
          white-space: nowrap; }
.q .ref { color: #6b7a90; font-size: 7.5pt; font-weight: 400; }
ol.opt { list-style: none; padding: 0; margin: 1mm 0 0 4mm; font-size: 8.5pt; }
ol.opt li { padding: 0.4mm 0; display: flex; gap: 1.5mm; align-items: baseline; }
ol.opt .c { flex: none; color: #55606e; }
.ans { color: #1f7a4d; font-weight: 700; }
.why { color: #667; font-size: 7.5pt; display: block; margin: 0.8mm 0 0 4mm; }
.pt { font-size: 7pt; color: #6b7a90; background: #eef2f7; border-radius: 2px;
      padding: 0.2mm 1.2mm; margin-right: 1.2mm; white-space: nowrap; }
/* 서술형 */
.essay { break-inside: avoid; margin-bottom: 4mm; }
.cond { border: 1px dashed #c9d2dd; border-radius: 3px; padding: 1.5mm 2.5mm;
        margin: 1mm 0; font-size: 8pt; color: #445; background: #fcfdfe; }
.cond b { color: #1f2d3d; }
.write { border-bottom: 1px solid #ccd3dc; height: 6mm; margin-top: 1.5mm; }
h2 { font-size: 10.5pt; margin: 4mm 0 2mm; padding: 1mm 2mm; background: #eef2f7;
     border-left: 3px solid #1f2d3d; column-span: all; break-after: avoid; }
.newpage { break-before: page; }
.prob { border: 1px solid #f0c9c4; background: #fdf4f3; border-radius: 3px;
        padding: 2mm 3mm; margin-bottom: 3mm; font-size: 8pt; color: #8a3128; }
"""


def esc(s):
    return html.escape(s or "", quote=False)


def mat_html(m):
    body = "".join(f"<p>{esc(ln)}</p>" for ln in m["text"].split("\n") if ln.strip())
    return f'<div class="mat"><span class="t">{esc(m["id"])} · {esc(m["title"])}</span>{body}</div>'


def build(d, logo, part="both", title=None):
    """title 을 안 주면 학년 없이 `{school} 동형 모의고사 {세트}` 만 찍는다.

    2026-09-27 원장 지적 — 내용 안에 학년이 없었다. `중1`·`중2` 는 파일명에만
    붙어 있었는데, 파일명을 잃으면(인쇄해서 낱장으로 돌면) 몇 학년 것인지 알 수
    없다. `build_mock_pdf.py` 가 파일명과 같은 문자열을 여기 그대로 넘긴다.
    """
    title = title or f"{d['school']} 동형 모의고사 {d['set_no']}세트"
    mats = {m["id"]: m for m in d["materials"]}
    used_order = []
    for it in d["items"]:
        mid = it.get("material_id")
        if mid in mats and mid not in used_order:
            used_order.append(mid)

    def page(ans, cls=""):
        sub = ("정답 및 해설 — 강사용 별지. 학생에게 배부하지 마십시오."
               if ans else f"{d['spec']['total_points']}점 · "
                           f"선택형 {len(d['items'])}문항"
                           + (f" · 서술형 {len(d['essays'])}문항"
                              if d["essays"] else ""))
        head = (f'<div class="{cls}"><div class="head"><div>{logo}'
                f'<h1>{esc(title)}</h1>'
                f'<div class="sub">{sub}</div></div>'
                f'<div><div class="name">이름 ______________</div>'
                f'<div class="mark">리디튜드 · 학원 내부 지도용</div></div></div>')

        prob = ""
        if ans and d["diagnostics"]["problems"]:
            lis = "".join(f"<li>{esc(p)}</li>" for p in d["diagnostics"]["problems"])
            prob = f'<div class="prob"><b>구조 검사에서 걸린 것</b><ul>{lis}</ul></div>'

        # 자료를 **그 자료를 처음 쓰는 문항 바로 앞**에 둔다.
        # 처음에는 자료를 다 모아 놓고 문항을 뒤에 붙였는데, 실제 시험지는 그렇지
        # 않다 — 지문이 나오고 그 지문의 문항이 바로 따라온다. 앞뒤로 넘겨 가며
        # 풀게 하면 그것만으로 아이가 시간을 잃는다.
        body = ["<div class='cols'>"]
        shown = set()

        for it in d["items"]:
            mid = it.get("material_id")
            if not ans and mid in mats and mid not in shown:
                body.append(mat_html(mats[mid]))
                shown.add(mid)
            opts = "".join(
                f'<li><span class="c">{CIRCLED[i]}</span>'
                f'<span class="{"ans" if ans and it["answer"] == i + 1 else ""}">'
                f'{esc(o)}</span></li>'
                for i, o in enumerate(it.get("options", [])[:5]))
            why = ""
            if ans:
                gp = (f'<span class="pt">{esc(it["grammar_point"])}</span>'
                      if it.get("grammar_point") else "")
                why = (f'<span class="why">{gp}<b>정답 {CIRCLED[it["answer"]-1]}</b> · '
                       f'{esc(it["why_ko"])}</span>')
            ref = (f'<span class="ref">[{esc(it["material_id"])}]</span>'
                   if it.get("material_id") else "")
            body.append(
                f'<div class="q"><div class="stem"><span class="no">{it["no"]}.</span>'
                f'<span>{esc(it["stem_ko"])} {ref}</span>'
                f'<span class="pts">{it["points"]}점</span></div>'
                f'<ol class="opt">{opts}</ol>{why}</div>')
        body.append("</div>")

        if d["essays"]:
            body.append('<h2>서술형</h2><div class="cols">')
            for e in d["essays"]:
                mid = e.get("material_id")
                if not ans and mid in mats and mid not in shown:
                    body.append(mat_html(mats[mid]))
                    shown.add(mid)
                words = ", ".join(e.get("given_words", []))
                cond = []
                if words:
                    cond.append(f"<b>주어진 단어</b> {esc(words)}")
                if e.get("word_limit"):
                    cond.append(f"<b>단어 수</b> {esc(e['word_limit'])}")
                cond_html = (f'<div class="cond">{" · ".join(cond)}</div>'
                             if cond else "")
                tail = (f'<span class="why"><span class="pt">'
                        f'{esc(e.get("target_grammar", ""))}</span>'
                        f'<b class="ans">{esc(e["answer_en"])}</b> · '
                        f'{esc(e["why_ko"])}</span>' if ans
                        else '<div class="write"></div><div class="write"></div>')
                body.append(
                    f'<div class="essay"><div class="stem">'
                    f'<span class="no">{e["no"]}.</span>'
                    f'<span>{esc(e["prompt_ko"])}</span>'
                    f'<span class="pts">{e["points"]}점</span></div>'
                    f'{cond_html}{tail}</div>')
            body.append("</div>")
        return head + prob + "".join(body) + "</div>"

    if part == "worksheet":
        return f"<style>{CSS}</style>{page(False)}"
    if part == "answers":
        return f"<style>{CSS}</style>{page(True)}"
    return f"<style>{CSS}</style>{page(False)}{page(True, 'newpage')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exam")
    ap.add_argument("--out")
    ap.add_argument("--part", choices=["both", "worksheet", "answers"], default="both")
    a = ap.parse_args()

    d = json.load(io.open(a.exam, encoding="utf-8"))
    suffix = "" if a.part == "both" else f".{a.part}"
    out = a.out or a.exam.replace(".json", f"{suffix}.html")
    io.open(out, "w", encoding="utf-8").write(build(d, logo_tag(DEFAULT_LOGO), a.part))
    print(f"  {d['school']} {d['set_no']}세트 · {a.part} · "
          f"선택 {len(d['items'])} · 서술 {len(d['essays'])}  →  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
