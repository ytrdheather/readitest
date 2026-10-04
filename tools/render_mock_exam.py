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
import re
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
.q .stem, .essay .stem { display: flex; gap: 1.5mm; align-items: baseline; font-weight: 600;
           font-size: 8.5pt; }
.q .no, .essay .no { flex: none; color: #1f2d3d; font-variant-numeric: tabular-nums; }
.q .pts, .essay .pts { flex: none; color: #8a94a6; font-size: 7.5pt; margin-left: auto;
          white-space: nowrap; }
.q .ref { color: #6b7a90; font-size: 7.5pt; font-weight: 400; }
ol.opt { list-style: none; padding: 0; margin: 1mm 0 0 4mm; font-size: 8.5pt; }
ol.opt li { padding: 0.4mm 0; display: flex; gap: 1.5mm; align-items: baseline; }
ol.opt .c { flex: none; color: #55606e; }
.ans { color: #1f7a4d; font-weight: 700; }
.why { color: #667; font-size: 7.5pt; display: block; margin: 0.8mm 0 0 4mm; }
.pt { font-size: 7pt; color: #6b7a90; background: #eef2f7; border-radius: 2px;
      padding: 0.2mm 1.2mm; margin-right: 1.2mm; overflow-wrap: anywhere; }
/* 서술형 */
.essay { break-inside: avoid; margin-bottom: 4mm; }
/* 서술형은 지시문 · 제시 내용 · 보기 · 조건을 각각 따로 줄을 세운다 (원장 2026-10-04
   「조건이나 내용 줄 때 줄바뀜 잘 이뤄져서 읽기 편하게」). 한 줄에 「· 」로 이어
   붙이면 아이가 세 번째 조건부터 놓친다. */
.ctx { border: 1px solid #d5dce5; border-radius: 3px; padding: 1.5mm 2.5mm;
       margin: 1.2mm 0 0 4mm; font-size: 8.5pt; line-height: 1.6; background: #fbfcfd; }
.ctx p { margin: 0 0 0.6mm; }
.words { margin: 1.2mm 0 0 4mm; font-size: 8.5pt; }
.words .lab { font-weight: 700; color: #1f2d3d; margin-right: 1.5mm; }
.words .w { display: inline-block; border: 1px solid #c9d2dd; border-radius: 2px;
            padding: 0 1.5mm; margin: 0 1mm 0.8mm 0; background: #fff; }
.cond { border: 1px dashed #c9d2dd; border-radius: 3px; padding: 1.2mm 2.5mm;
        margin: 1.2mm 0 0 4mm; font-size: 8pt; color: #333; background: #fcfdfe; }
.cond .lab { font-weight: 700; color: #1f2d3d; display: block; margin-bottom: 0.4mm; }
.cond ul { list-style: none; margin: 0; padding: 0; }
.cond li { padding: 0.2mm 0 0.2mm 3mm; text-indent: -3mm; }
.cond li::before { content: "· "; color: #6b7a90; }
.ctx p.a { padding-left: 4mm; }
/* 채점형 답칸 (2026-10-04) — 줄글 대신 「3번째 단어: ____」 · 「(1) ____」 만 쓴다 */
.slots { margin: 2mm 0 0 4mm; display: flex; flex-wrap: wrap; gap: 2.2mm 6mm;
         font-size: 8.5pt; color: #333; }
.slots span { white-space: nowrap; }
.model { margin: 1.2mm 0 0 4mm; font-size: 8.5pt; }
.model p { margin: 0 0 0.4mm; }
.write { border-bottom: 1px solid #ccd3dc; height: 6mm; margin: 1.5mm 0 0 4mm; }
h2 { font-size: 10.5pt; margin: 4mm 0 2mm; padding: 1mm 2mm; background: #eef2f7;
     border-left: 3px solid #1f2d3d; column-span: all; break-after: avoid; }
.newpage { break-before: page; }
.prob { border: 1px solid #f0c9c4; background: #fdf4f3; border-radius: 3px;
        padding: 2mm 3mm; margin-bottom: 3mm; font-size: 8pt; color: #8a3128; }
/* 정답표 — 정답지 첫 쪽 맨 위, 해설 앞 (디자인 지침 5) */
.qk { margin: 0 0 3.5mm; }
.qk .t { font-size: 10pt; font-weight: 700; color: #1f2d3d; margin-bottom: 1mm; }
.qk table { border-collapse: collapse; font-size: 11pt; }
.qk td { border: 1px solid #555; padding: 0.6mm 3mm; height: 6mm; }
.qk td.n { font-size: 9pt; color: #333; white-space: nowrap; }
.qk td.a { letter-spacing: 0.6mm; white-space: nowrap; min-width: 30mm; }
.qk td.e { font-size: 9pt; font-weight: 600; line-height: 1.5; }
.qk tr.h td { background: #eef2f7; font-size: 8.5pt; text-align: center; color: #445; }
"""


def quick_key(mc, essays=()):
    """정답표 — 선택형은 10문항씩 한 줄, 5개씩 두 칸 (`01~10번 | ④②②③② | ⑤①②⑤⑤`),
    그 아래 서술형은 한 문항 한 줄에 답만.

    mc: [(번호, '③'), …]   essays: [(번호, [답 줄, …]), …]
    2026-10-04 원장 — 채점할 때 해설 속에서 정답을 찾느라 불편했다. 원장이 보여 준 기존
    정답표 꼴: 정답지 맨 위에 번호별 정답만 나열한 표. ~~서술형은 「주」~~ — 서술형도 답을
    써 줘야 채점이 된다 (원장 같은 날).
    """
    marks = dict(mc)
    last = max(marks) if marks else 0
    rows = ['<tr class="h"><td>번호</td><td></td><td></td></tr>']
    for s in range(1, last + 1, 10):
        e = min(s + 9, last)
        half = lambda lo, hi: "".join(marks.get(i, "·") for i in range(lo, min(hi, e) + 1))
        label = f"{s:02d}~{e:02d}번" if e > s else f"{s:02d}번"
        rows.append(f'<tr><td class="n">{label}</td>'
                    f'<td class="a">{half(s, s + 4)}</td><td class="a">{half(s + 5, s + 9)}</td></tr>')
    # 중1 5과 1~3세트처럼 서술형이 1번부터 다시 세면 「서술형 1번」 으로 적어 선택형 1번과 가른다
    restart = bool(essays) and essays[0][0] <= last
    for n, lines in essays:
        label = f"서술형 {n}번" if restart else f"{n:02d}번"
        rows.append(f'<tr><td class="n">{label}</td><td class="e" colspan="2">'
                    + "".join(f"<div>{esc(l)}</div>" for l in lines) + "</td></tr>")
    return f'<div class="qk"><div class="t">정답표</div><table>{"".join(rows)}</table></div>'


def essay_key_lines(answer_en):
    """모범답에서 채점에 필요한 줄만 — 「(완성 문장: …)」 은 해설 쪽에만 둔다."""
    return [l.strip() for l in answer_en.split("\n")
            if l.strip() and not l.strip().startswith("(완성")]


def esc(s):
    return html.escape(s or "", quote=False)


def mat_html(m):
    body = "".join(f"<p>{esc(ln)}</p>" for ln in m["text"].split("\n") if ln.strip())
    t = m["title"]
    t = t if t.startswith(m["id"]) else f'{m["id"]} · {t}'     # 「T9 · T9 · …」 중복 방지
    return f'<div class="mat"><span class="t">{esc(t)}</span>{body}</div>'


def essay_parts(e):
    """서술형 한 문항을 (지시문, 제시 줄들, 조건들) 로 나눈다.

    2026-10-04 부터 모델이 `context` · `conditions` 를 따로 낸다. 그 전 세트(영일·태장
    1~5)는 `prompt_ko` 한 칸에 「…영작하시오.\\n우리말\\n<조건> · A · B · C」 를 몰아
    넣었으므로, 그 꼴이면 여기서 쪼갠다 — 다시 뽑을 때 옛 세트도 같은 모양이 된다.
    """
    lines = [ln.strip() for ln in (e.get("prompt_ko") or "").split("\n") if ln.strip()]
    stem, rest = (lines[0], lines[1:]) if lines else ("", [])
    conds = [c.strip() for c in e.get("conditions") or [] if c.strip()]
    # 「…쓰시오. 【조건 1】 A 【조건 2】 B」 — 지시문 한 줄에 붙은 조건 (영일중1 2026-09)
    if "【조건" in stem:
        stem, tail = stem.split("【조건", 1)
        conds += [re.sub(r"^\s*\d+\s*】", "", c).strip()
                  for c in ("【조건" + tail).split("【조건") if c.strip()]
        stem = stem.strip()
    # 제시 상자 안에 「1) … 2) …」 로 섞여 들어온 조건은 조건 상자로 옮긴다 (영일중1 3세트)
    ctx = []
    for ln in (e.get("context") or "").split("\n"):
        ln = ln.strip()
        if re.match(r"^\d\)\s", ln):
            conds.append(ln[2:].strip())
        elif ln:
            ctx.append(ln)
    for ln in rest:
        if "<조건>" in ln or "[조건]" in ln:
            head, body = re.split(r"<조건>|\[조건\]", ln, maxsplit=1)
            if head.strip():
                ctx.append(head.strip())
            conds += split_conds(body)
        elif re.match(r"^\d\)\s", ln):
            conds.append(ln[2:].strip())
        elif ln.strip() not in ("<조건>", "[조건]"):
            ctx.append(ln)
    conds = [CIRCLED_LEAD.sub("", c).strip() for c in conds]
    return stem, ctx, conds


CIRCLED_LEAD = re.compile(r"^[①②③④⑤⑥⑦⑧⑨]\s*")


def split_conds(body):
    """「① A ② B」 또는 「· A · B」. 괄호 안의 · (예: 진행형·to부정사)는 자르지 않는다."""
    if re.search(r"[①②③④⑤⑥⑦⑧⑨]", body):
        parts = re.split(r"\s*[①②③④⑤⑥⑦⑧⑨]\s*", body)
    else:
        parts, depth, cur = [], 0, ""
        for ch in body:
            depth += ch in "(（「" and 1 or 0
            depth -= ch in ")）」" and 1 or 0
            if ch == "·" and depth <= 0:
                parts.append(cur); cur = ""
            else:
                cur += ch
        parts.append(cur)
    return [c.strip(" ·") for c in parts if c.strip(" ·")]


def essay_html(e, ans):
    stem, ctx, conds = essay_parts(e)
    out = [f'<div class="essay"><div class="stem"><span class="no">{e["no"]}.</span>'
           f'<span>{esc(stem)}</span><span class="pts">{e["points"]}점</span></div>']
    qa = any("Q:" in c for c in ctx)
    if ctx:
        out.append('<div class="ctx">' + "".join(
            # 「Q: … / A: …」 문답일 때만 A 를 들여 쓴다 — 대화문(A:/B:)까지 들여 쓰면 어긋나 보인다
            f'<p class="{"a" if c.startswith("A:") and qa else ""}">{esc(c)}</p>' for c in ctx) + "</div>")
    words = [w for w in e.get("given_words", []) if w.strip()]
    if words and not (len(words) == 1 and words[0].startswith("(")):
        out.append('<div class="words"><span class="lab">[보기]</span>'
                   + "".join(f'<span class="w">{esc(w)}</span>' for w in words) + "</div>")
    elif words:                              # 「(P1의 단어만 사용)」 같은 안내 문구 — 조건으로
        conds.append(words[0].strip("()"))
    wl = (e.get("word_limit") or "").strip()
    if wl and wl != "제한 없음" and not any(wl.replace(" 단어", "") in c for c in conds):
        # 숫자가 없으면 단어 수가 아니라 답 쓰는 꼴 안내다 (중1 논술 4 「틀린 것 → 고친 것」 형태)
        conds.append(f"단어 수: {wl}" if any(ch.isdigit() for ch in wl) else wl)
    if conds:
        out.append('<div class="cond"><span class="lab">&lt;조건&gt;</span><ul>'
                   + "".join(f"<li>{esc(c)}</li>" for c in conds) + "</ul></div>")
    if ans:
        model = "".join(f"<p>{esc(ln)}</p>" for ln in e["answer_en"].split("\n") if ln.strip())
        out.append(f'<div class="model ans">{model}</div>'
                   f'<span class="why"><span class="pt">{esc(e.get("target_grammar", ""))}</span>'
                   f'{esc(e["why_ko"])}</span>')
    elif e.get("answer_slots"):
        out.append('<div class="slots">' + "".join(
            f"<span>{esc(x)}</span>" for x in e["answer_slots"]) + "</div>")
    else:
        n = 4 if "\n" in e.get("answer_en", "") or "(a)" in e.get("answer_en", "") else 2
        out.append('<div class="write"></div>' * n)
    out.append("</div>")
    return "".join(out)


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
                # 자료와 그 문항을 한 덩어리로 묶어 쪽이 갈리지 않게 한다 — 표는 4쪽, 문항은 5쪽으로
                # 갈라져 나왔다 (영덕중1 5세트 20번, 2026-10-04)
                head_mat = ""
                if not ans and mid in mats and mid not in shown:
                    head_mat = mat_html(mats[mid])
                    shown.add(mid)
                body.append('<div style="break-inside: avoid">' + head_mat + essay_html(e, ans) + "</div>")
            body.append("</div>")
        qk = ""
        if ans:      # 정답지 맨 위 정답표 (디자인 지침 5)
            qk = quick_key([(it["no"], CIRCLED[it["answer"] - 1]) for it in d["items"]],
                           [(e["no"], essay_key_lines(e["answer_en"])) for e in d["essays"]])
        return head + qk + prob + "".join(body) + "</div>"

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
