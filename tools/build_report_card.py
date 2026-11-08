# -*- coding: utf-8 -*-
"""
동형 모의고사 채점 결과 → 학부모에게 보내는 학생별 1회성 결과지 (PDF + 쪽마다 PNG).

  python tools/build_report_card.py <결과지.json>          # → result/personal_test/결과지/

2026-10-04 원장: 「오늘 바로 보내게 — 제목, 틀린 문제, 학생 오답, 뭐가 공부가 안 됐는지,
뭘 정리해야 하는지. 이 정도만」. 리디플랜 쪽 정식 리포트를 만들기 전의 임시 도구다.

결과지 JSON (학생 이름·점수가 들어 있으니 **저장소 밖에** 둔다 — CLAUDE.md 규칙 3):

  {"round": "1차", "school": "영덕중학교", "exam"?: "기말고사" (없으면 중간고사),
   "date"?: 시행일 (없으면 안 찍음), "areas"?: false 면 영역별 표를 뺀다,
   "students": [{"name", "grade", "set", "score", "mc": [얻은, 만점], "essay": [얻은, 만점],
                 "wrong": [{"no", "student": "③" | [줄, …], "lost"?, "note"?}],
                 "summary", "weak": [...], "todo": [...]}]}

틀린 문제는 지문(자료)까지 다시 싣는다 — 「T1 의 ①~⑤ 중 틀린 것은?」 같은 문항은
지문이 없으면 학부모가 읽을 수 없다.
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

import pypdfium2 as pdfium

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.pdf_pages import stamp_file                                # noqa: E402
from tools.render_mock_exam import (CIRCLED, esc, essay_key_lines,    # noqa: E402
                                    essay_parts, mat_html)
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT      # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 저장소에 JSON 이 없는 세트(다른 PC 에서 만들어 Z: 에 PDF 만 있는 것)는 --mock-dir 로 다른 폴더를 준다
MOCK = os.environ.get("READI_MOCK_DIR") or os.path.join(ROOT, "data", "generated", "mock")
OUT = os.path.join(ROOT, "result", "personal_test", "결과지")

CSS = FONT + """
@page { size: A4; margin: 13mm 13mm 14mm; }   /* 바닥 12mm 이상: 쪽수 자리 (디자인 지침 1) */
body { font-family: Pretendard,'Malgun Gothic',sans-serif; font-size: 9.5pt;
       line-height: 1.55; color: #1b2430; }
.logo { height: 10mm; }
.top { border-bottom: 2.5px solid #1f2d3d; padding-bottom: 2mm; margin-bottom: 4mm; }
h1 { font-size: 15pt; margin: 1.5mm 0 0; letter-spacing: -0.2px; }
.who { display: flex; gap: 3mm; align-items: stretch; margin-bottom: 4mm; }
.card { border: 1px solid #d5dce5; border-radius: 4px; padding: 2.5mm 4mm; }
.name { flex: 1; }
.name b { font-size: 15pt; }
.name div { color: #5b6878; font-size: 9pt; }
.score { text-align: center; min-width: 32mm; background: #f3f7fb; }
.score .big { font-size: 24pt; font-weight: 800; color: #1f2d3d; line-height: 1.1; }
.score .big small { font-size: 11pt; color: #6b7a90; font-weight: 600; }
.part { min-width: 30mm; font-size: 9pt; color: #445; }
.part b { color: #1f2d3d; }
h2 { font-size: 11pt; margin: 4.5mm 0 2mm; padding: 1mm 2.5mm; background: #eef2f7;
     border-left: 3.5px solid #1f2d3d; }
.sum { font-size: 10pt; margin: 0 0 1mm; }
ul.pts { margin: 0; padding-left: 5mm; }
ul.pts li { margin: 0.8mm 0; }
.two { display: flex; gap: 4mm; }
.two > div { flex: 1; }
.q { border: 1px solid #e1e6ec; border-radius: 4px; padding: 2.5mm 3.5mm; margin-bottom: 3mm;
     break-inside: avoid; }
.q .stem { font-weight: 600; font-size: 9.5pt; display: flex; gap: 1.5mm; }
.q .no { color: #1f2d3d; flex: none; }
.q .lost { margin-left: auto; color: #b23a2e; font-size: 8.5pt; white-space: nowrap; }
.mat { border: 1px solid #c9d2dd; background: #fbfcfd; border-radius: 3px;
       padding: 1.8mm 2.5mm; margin: 1.5mm 0; font-size: 8.3pt; line-height: 1.6; }
.mat .t { font-size: 7.5pt; font-weight: 700; color: #1f2d3d; background: #e8edf3;
          border-radius: 2px; padding: 0.3mm 1.5mm; display: inline-block; margin-bottom: 1mm; }
.mat p { margin: 0 0 0.8mm; }
.mat .choice { border: 1px solid #333; padding: 0 1.2mm; margin: 0 0.3mm; white-space: nowrap; }
.mat u { text-decoration-thickness: 1.2px; text-underline-offset: 0.7mm; }
ol.opt { list-style: none; padding: 0; margin: 1.2mm 0 0 3mm; font-size: 9pt; }
ol.opt li { padding: 0.3mm 0; }
ol.opt li.me { color: #b23a2e; font-weight: 700; }
ol.opt li.ok { color: #1f7a4d; font-weight: 700; }
.tag { font-size: 7.5pt; border-radius: 2px; padding: 0.2mm 1.4mm; margin-left: 1.5mm;
       font-weight: 700; }
.tag.me { background: #fbe9e7; color: #b23a2e; }
.tag.ok { background: #e6f4ec; color: #1f7a4d; }
.ctx { font-size: 8.8pt; color: #334; margin: 1mm 0 0 3mm; }
.ctx p { margin: 0.3mm 0; }
.ans { display: flex; gap: 3mm; margin-top: 1.8mm; font-size: 9pt; }
.ans > div { flex: 1; border-radius: 3px; padding: 1.5mm 2.5mm; }
.ans .me { background: #fdf3f2; }
.ans .ok { background: #f0f8f3; }
.ans .lab { font-size: 7.5pt; font-weight: 700; display: block; margin-bottom: 0.5mm; }
.ans .me .lab { color: #b23a2e; } .ans .ok .lab { color: #1f7a4d; }
.note { font-size: 8.5pt; color: #6b5a2a; background: #fbf6e6; border-radius: 3px;
        padding: 1mm 2.5mm; margin-top: 1.5mm; }
.perfect { text-align: center; padding: 6mm; color: #1f7a4d; font-size: 11pt; font-weight: 700;
           border: 1px dashed #9cc9ae; border-radius: 4px; background: #f3faf6; }
.keep { break-inside: avoid; }
.howto { font-size: 8.8pt; color: #445; margin: 0 0 2.5mm; }
.redo { margin: 1.8mm 0 0 3mm; font-size: 9pt; color: #334; }
.redo .blank { display: inline-block; width: 22mm; border-bottom: 1px solid #889; }
.ans .again { background: #fff; border: 1px dashed #b8c2cf; }
.ans .again .lab { color: #1f2d3d; }
.ans .again .line { border-bottom: 1px solid #c9d2dd; height: 6.5mm; display: flex; align-items: flex-end;
                    font-size: 8pt; color: #6b7a90; padding-bottom: 0.5mm; }
.crit { margin-top: 1.8mm; border: 1px solid #c9d6e6; background: #f4f8fc; border-radius: 3px;
        padding: 1.6mm 2.5mm; font-size: 8.6pt; }
.crit .lab { font-size: 8pt; font-weight: 800; color: #1f2d3d; display: block; margin-bottom: 0.6mm; }
.crit .sub { font-size: 7.6pt; font-weight: 700; color: #5b6878; margin-top: 0.8mm; }
.crit ul { margin: 0.3mm 0 0; padding-left: 4.5mm; }
.crit li { margin: 0.3mm 0; }
.score .was { font-size: 8.5pt; color: #6b7a90; margin-top: 0.8mm; }
table.area tr.hd td { font-size: 7.5pt; color: #6b7a90; padding-top: 0; padding-bottom: 0.5mm; }
table.area td.prev { width: 30mm; text-align: right; font-size: 8.5pt; color: #445; white-space: nowrap; }
table.area .up { color: #1f7a4d; font-weight: 700; } table.area .down { color: #b23a2e; font-weight: 700; }
table.area { width: 100%; border-collapse: collapse; font-size: 9pt; }
table.area th, table.area td { border-bottom: 1px solid #e1e6ec; padding: 1.4mm 2mm; text-align: left; }
table.area th { width: 34mm; font-weight: 700; color: #1f2d3d; }
table.area th small { display: block; font-weight: 400; font-size: 7.3pt; color: #6b7a90; }
table.area td.bar { width: 45mm; }
table.area td.bar span { display: block; height: 2.6mm; border-radius: 2px; background: #c0533f; }
table.area tr.full td.bar span { background: #2f8a5a; }
table.area td.mark { width: 14mm; text-align: right; font-weight: 700; color: #b23a2e; }
table.area tr.full td.mark { color: #1f7a4d; }
"""

# 영역별 표 — 문항 유형(type) 접두어로 나눈다. 여기 없는 유형은 내용 이해.
AREAS = ["어법", "어휘", "내용 이해", "서술형 영작"]
AREA_BY_TYPE = [("T-GRAMMAR", "어법"), ("T-FORM-CHOICE", "어법"), ("T-WORD-ORDER", "어법"),
                ("T-VOCAB", "어휘")]
AREA_NOTE = {"어법": "어법 판단 · 네모 고르기 · 배열", "어휘": "영영풀이 · 문맥 속 낱말",
             "내용 이해": "세부 내용 · 주제·제목 · 빈칸 · 지칭", "서술형 영작": "조건에 맞게 쓰기"}


def lines_html(x):
    x = x if isinstance(x, list) else [x]
    return "".join(f"<div>{esc(l)}</div>" for l in x)


def mats_for(q, field, mats, shown):
    """문항이 쓰는 자료 — material_id 하나 + 발문에 이름이 나온 [T7] · [T12] 도 (시험지 렌더러와 같게).

    영일중3 1세트 25번 「윗글 [T7], [T12]를 읽고」 에서 T12 가 결과지에 빠졌다 (2026-11-08).
    """
    out = ""
    for mid in [q.get("material_id")] + re.findall(r"\[([PT]\d+)\]", q.get(field) or ""):
        if mid in mats and mid not in shown:
            out += mat_html(mats[mid], q.get("underline", ()))
            shown.add(mid)
    return out


def item_html(it, w, mats, shown, show_answers=False):
    """틀린 선택형 — 기본은 **정답을 싣지 않는다** (2026-11-08 원장 「답 표기해주지마. 다시 풀어보라고만」).
    학생이 고른 번호만 「내 답」 으로 표시한다. show_answers=True 는 강사용."""
    mat = mats_for(it, "stem_ko", mats, shown)
    me = w["student"]
    opts = ""
    for i, o in enumerate(it.get("options", [])[:5]):
        c = CIRCLED[i]
        ok = show_answers and it["answer"] == i + 1
        cls = "ok" if ok else ("me" if c == me else "")
        tag = ('<span class="tag ok">정답</span>' if cls == "ok" else
               '<span class="tag me">내 답</span>' if cls == "me" else "")
        opts += f'<li class="{cls}">{c} {esc(o)}{tag}</li>'
    # 발문 안의 <보기> 줄(a. b. c. …)은 줄을 나눠 찍는다 — 한 줄로 이으면 학부모가 못 읽는다
    stem, *rest = it["stem_ko"].split("\n")
    box = ('<div class="ctx">' + "".join(f"<p>{esc(l)}</p>" for l in rest if l.strip()) + "</div>") if rest else ""
    redo = "" if show_answers else '<div class="redo">다시 푼 답: <span class="blank"></span></div>'
    return (f'<div class="q"><div class="stem"><span class="no">{it["no"]}.</span>'
            f'<span>{esc(stem)}</span><span class="lost">−{it["points"]}점</span></div>'
            f'{box}{mat}<ol class="opt">{opts}</ol>{redo}</div>')


_SLOT = re.compile(r"^\s*(\(\d\)|\d+번째(?: 단어)?)")


def essay_slots(e):
    """답 칸 이름 — 「3번째 단어」 · 「(1)」 · 빈칸 하나. 모범답 줄로 센다 (복원 세트는 answer_slots 가 비었다)."""
    names = [m.group(1) for k in essay_key_lines(e.get("answer_en", "")) for m in [_SLOT.match(k)] if m]
    if not names:
        names = [m.group(1) for sl in e.get("answer_slots") or [] for m in [_SLOT.match(sl)] if m]
    return names or ["빈칸"]


def scoring_rule(e):
    """서술형 채점 기준 — 정답 없이 「무엇을 보고 몇 점을 빼는지」 (2026-11-08 원장 「애들도 판단할 수 있게」).

    grade_mock 의 서술형 판정이 이 규칙을 따른다. 세트 JSON 에 `grading_ko` 가 있으면 그것이 이긴다.
    """
    if e.get("grading_ko"):
        return list(e["grading_ko"])
    pts = e.get("points", 5)
    slots = essay_slots(e)
    keys = essay_key_lines(e.get("answer_en", ""))
    if "고쳐" in (e.get("prompt_ko") or "") or any("→" in k for k in keys):
        return [f"틀린 곳 {len(slots)}곳을 각각 「틀린 말 → 고친 말」 로 봅니다. 틀린 말을 정확히 찾고 바르게 고쳐야 그 곳을 인정합니다.",
                "한 곳만 맞으면 2점, 모두 맞으면 5점입니다." if len(slots) == 2 else f"곳마다 점수를 나눠 줍니다 (모두 맞으면 {pts}점)."]
    if len(slots) >= 2 and all("번째" in x for x in slots):
        return [f"지정된 {len(slots)}칸({' · '.join(slots)})을 칸마다 따로 봅니다. 완성 문장 전체가 조건에 맞아야 단어 순서도 맞습니다.",
                {2: "한 칸이 틀리면 −3점, 두 칸 모두 틀리면 0점입니다.",
                 3: "한 칸 틀릴 때마다 −2점, 세 칸 모두 틀리면 0점입니다."}.get(len(slots), "칸마다 점수를 나눠 줍니다.")]
    if len(slots) >= 2:
        return [f"{' · '.join(slots)} 칸을 따로 봅니다. 한 칸 안에서는 단어가 모두 맞아야 인정합니다.",
                {2: "(1) 2점 · (2) 3점입니다 (단어 수가 많은 칸에 점수를 더 줍니다).",
                 3: "한 칸 틀릴 때마다 −2점, 세 칸 모두 틀리면 0점입니다."}.get(len(slots), "칸마다 점수를 나눠 줍니다.")]
    return ["빈칸 전체를 한 덩어리로 봅니다.",
            "핵심 문법 형태가 맞고 조건 하나(시제 · 수 일치 · 관사 등)만 어긋나면 −2점, 핵심 형태가 틀리면 0점입니다.",
            "철자 실수 하나는 −1점입니다."]


def essay_html(e, w, mats, shown, show_answers=False):
    """틀린 서술형 — 내 답 · 다시 써 보기 · 채점 기준(정답 없이) · 감점 이유."""
    mat = mats_for(e, "prompt_ko", mats, shown)
    stem, ctx, conds = essay_parts(e)
    ctx_html = ('<div class="ctx">' + "".join(f"<p>{esc(c)}</p>" for c in ctx) + "</div>") if ctx else ""
    words = [x for x in e.get("given_words") or [] if x.strip()]
    cond_lis = ([f"주어진 단어: {' · '.join(words)}"] if words else []) + list(conds)
    wl = (e.get("word_limit") or "").strip()
    if wl and not any(wl in c for c in cond_lis):
        cond_lis.append(f"단어 수: {wl}")
    crit = ('<div class="crit"><span class="lab">서술형 채점 기준</span>'
            + (("<div class='sub'>이 조건을 모두 지켰는지 봅니다</div><ul>"
                + "".join(f"<li>{esc(c)}</li>" for c in cond_lis) + "</ul>") if cond_lis else "")
            + "<div class='sub'>점수 주는 법</div><ul>"
            + "".join(f"<li>{esc(r)}</li>" for r in scoring_rule(e)) + "</ul></div>")
    note = f'<div class="note"><b>감점 이유</b> · {esc(w["note"])}</div>' if w.get("note") else ""
    if show_answers:
        ans = (f'<div class="ans"><div class="me"><span class="lab">학생 답</span>{lines_html(w["student"])}</div>'
               f'<div class="ok"><span class="lab">정답</span>{lines_html(essay_key_lines(e["answer_en"]))}</div></div>')
    else:
        again = "".join(f'<div class="line"><span>{esc(sl)}</span></div>' for sl in essay_slots(e))
        ans = (f'<div class="ans"><div class="me"><span class="lab">내 답</span>{lines_html(w["student"])}</div>'
               f'<div class="again"><span class="lab">다시 써 보기</span>{again}</div></div>')
    return (f'<div class="q"><div class="stem"><span class="no">{e["no"]}.</span>'
            f'<span>[서술형] {esc(stem)}</span><span class="lost">−{w.get("lost", e["points"])}점</span></div>'
            f'{mat}{ctx_html}{ans}{crit}{note}</div>')


def area_of(type_):
    for k, name in AREA_BY_TYPE:
        if type_.startswith(k):
            return name
    return "내용 이해"


def area_scores(d, lost_mc, lost_es):
    """영역별 {이름: [맞은 수, 문항 수, 얻은 점, 배점]} — grade_mock.py 도 이것으로 기록한다.

    lost_mc: 틀린 선택형 번호 집합 · lost_es: {서술형 번호: 감점}
    """
    rows = {name: [0, 0, 0, 0] for name in AREAS}
    for it in d["items"]:
        r = rows[area_of(it["type"])]
        ok = it["no"] not in lost_mc
        r[0] += ok; r[1] += 1; r[2] += it["points"] if ok else 0; r[3] += it["points"]
    for e in d["essays"]:
        r = rows["서술형 영작"]
        lost = lost_es.get(e["no"], 0)
        r[0] += lost == 0; r[1] += 1; r[2] += e["points"] - lost; r[3] += e["points"]
    return {k: v for k, v in rows.items() if v[1]}


def area_html(d, s, is_mc):
    """영역별 표 — 틀린 문제가 1~2개뿐인 학생도 무엇을 잘했는지 보이게 (2026-11-08 원장).

    s["prev"] = {"label": "1차", "areas": {이름: [얻은 점, 배점]}} 가 있으면 지난 회차 칸을 붙인다.
    영역별 비율로 비교한다 — 세트마다 영역 배점이 조금씩 다르다.
    """
    rows = area_scores(d, {w["no"] for w in s["wrong"] if is_mc(w)},
                       {w["no"]: w.get("lost", 0) for w in s["wrong"] if not is_mc(w)})
    prev = (s.get("prev") or {}).get("areas") or {}
    head = ""
    if prev:
        head = (f'<tr class="hd"><th></th><td>맞은 문항</td><td>점수</td><td></td><td></td>'
                f'<td class="prev">{esc(s["prev"].get("label", "지난 회차"))}</td></tr>')
    trs = ""
    for name in AREAS:
        if name not in rows:
            continue
        got, n, pts, full = rows[name]
        pct = round(100 * pts / full)
        cls = "full" if pts == full else ""
        cmp_ = ""
        if prev:
            pp = prev.get(name)
            if pp and pp[1]:
                was = round(100 * pp[0] / pp[1])
                diff = pct - was
                arrow = ("▲" if diff > 0 else "▼" if diff < 0 else "–")
                cmp_ = (f'<td class="prev">{was}% → {pct}% '
                        f'<span class="{"up" if diff > 0 else "down" if diff < 0 else ""}">{arrow}</span></td>')
            else:
                cmp_ = '<td class="prev">—</td>'
        trs += (f'<tr class="{cls}"><th>{name}<small>{AREA_NOTE[name]}</small></th>'
                f'<td>{got} / {n}문항</td><td><b>{pts}</b> / {full}점</td>'
                f'<td class="bar"><span style="width:{pct}%"></span></td>'
                f'<td class="mark">{"만점" if pts == full else f"−{full - pts}점"}</td>{cmp_}</tr>')
    return f'<h2>영역별 결과</h2><table class="area">{head}{trs}</table>'


def page(res, s, logo):
    d = json.load(io.open(os.path.join(MOCK, s["set"] + ".json"), encoding="utf-8"))
    # 시험 이름은 결과지 JSON 의 exam (영일중1 은 기말) — 없으면 예전처럼 중간고사
    title = (f"리디튜드 {res.get('exam', '중간고사')} 대비 {res['school']} {s['grade']}학년 "
             f"{s.get('round', res.get('round', ''))} 동형모의고사 결과지")
    items = {it["no"]: it for it in d["items"]}
    essays = {e["no"]: e for e in d["essays"]}
    mats = {m["id"]: m for m in d["materials"]}
    shown = set()
    qs = []
    # 서술형은 「lost」 가 있는 줄 — 번호만으로 가르면 서술형이 1번부터 다시 세는 세트(중1 7세트)에서
    # 서술형 4번이 선택형 4번으로 잡힌다 (2026-10-06)
    is_mc = lambda w: "lost" not in w and w["no"] in items
    show = bool(res.get("show_answers"))         # 강사용만 True — 학생·학부모용은 정답 없이
    for w in s["wrong"]:
        if is_mc(w):
            qs.append(item_html(items[w["no"]], w, mats, shown, show))
        else:
            qs.append(essay_html(essays[w["no"]], w, mats, shown, show))
    wrong_nos = ", ".join(f'{w["no"]}번' if is_mc(w) else f'서술형 {w["no"]}번' for w in s["wrong"])
    weak = "".join(f"<li>{esc(x)}</li>" for x in s["weak"]) or "<li>이번 시험에서는 부족한 부분이 없었습니다.</li>"
    todo = "".join(f"<li>{esc(x)}</li>" for x in s["todo"])
    body = (f'<div class="top">{logo}<h1>{esc(title)}</h1></div>'
            f'<div class="who"><div class="card name"><b>{esc(s["name"])}</b>'
            f'<div>{esc(res["school"])} {s["grade"]}학년'
            + (f' · 시행일 {esc(res["date"])}' if res.get("date") else "") + '</div>'
            f'<div>틀린 문항: {esc(wrong_nos) if s["wrong"] else "없음"}</div></div>'
            f'<div class="card part">선택형 <b>{s["mc"][0]}</b> / {s["mc"][1]}<br>'
            f'서술형 <b>{s["essay"][0]}</b> / {s["essay"][1]}</div>'
            f'<div class="card score"><div class="big">{s["score"]}<small>점</small></div>100점 만점'
            + (f'<div class="was">{esc(s["prev"].get("label", "지난 회차"))} {s["prev"]["score"]}점</div>'
               if s.get("prev") and s["prev"].get("score") is not None else "") + '</div></div>'
            f'<p class="sum">{esc(s["summary"])}</p>'
            + (area_html(d, s, is_mc) if res.get("areas", True) else "") +
            f'<div class="two"><div><h2>공부가 덜 된 부분</h2><ul class="pts">{weak}</ul></div>'
            f'<div><h2>앞으로 정리할 것</h2><ul class="pts">{todo}</ul></div></div>'
            # 제목이 쪽 끝에 홀로 남지 않게 첫 문제와 한 덩어리로 (2026-11-08)
            + (f'<div class="keep"><h2>{"틀린 문제 다시 보기" if show else "틀린 문제 다시 풀기"}</h2>'
               + ("" if show else '<p class="howto">정답은 싣지 않았습니다. 지문을 다시 읽고 스스로 풀어 본 뒤 선생님과 확인하세요. '
                  '서술형은 「서술형 채점 기준」 을 보고 내 답이 왜 감점됐는지 먼저 따져 보세요.</p>')
               + f'{qs[0]}</div>' + "".join(qs[1:]) if qs else
               '<h2>틀린 문제 다시 풀기</h2><div class="perfect">모든 문항을 맞혔습니다. 훌륭합니다!</div>'))
    return title, f"<style>{CSS}</style>{body}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)      # Chrome 은 상대 경로를 제 작업 폴더 기준으로 읽는다

    res = json.load(io.open(a.report_json, encoding="utf-8"))
    chrome = find_chrome()
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="report_")
    os.makedirs(a.out, exist_ok=True)
    try:
        for s in res["students"]:
            title, html_text = page(res, s, logo)
            base = re.sub(r'[\\/:*?"<>|]', "_", f"{s['name']} · {res['school']} {s['grade']}학년 {s.get('round', res.get('round', ''))} 동형모의고사 결과지")
            html = os.path.join(tmp, "r.html")
            pdf = os.path.join(a.out, base + ".pdf")
            io.open(html, "w", encoding="utf-8").write(html_text)
            to_pdf(chrome, html, pdf)
            n = stamp_file(pdf)              # 아래 가운데 쪽수 — 디자인 지침 1
            # 다시 뽑을 때 쪽수가 바뀌면 옛 「(2of3)」 PNG 가 남아 섞인다 — 이 학생·회차의 PNG 를 먼저 지운다
            for old in glob.glob(os.path.join(a.out, glob.escape(base) + "*.png")):
                if re.fullmatch(re.escape(base) + r"( \(\d+of\d+\))?\.png", os.path.basename(old)):
                    os.remove(old)
            doc = pdfium.PdfDocument(pdf)
            for i in range(len(doc)):        # 카톡으로 바로 보내기용 — 쪽마다 한 장
                suffix = "" if len(doc) == 1 else f" ({i + 1}of{len(doc)})"
                doc[i].render(scale=2).to_pil().save(os.path.join(a.out, base + suffix + ".png"))
            doc.close()
            print(f"  {s['name']}  {s['score']}점  · {n}쪽")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  → {a.out}")


if __name__ == "__main__":
    sys.exit(main())
