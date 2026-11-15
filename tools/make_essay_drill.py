# -*- coding: utf-8 -*-
"""
**서술형 집중드릴** — 「글 내용을 내 말로 한 문장」 꼴 논술형 훈련. 모델을 부르지 않는다.

  python tools/make_essay_drill.py --unit 영일중1            # 검사 + 미리보기
  python tools/make_essay_drill.py --unit 영일중1 --build    # PDF

    result/readitude/영일중1 5·6·7과 서술형 집중드릴.pdf
    result/readitude/영일중1 5·6·7과 서술형 집중드릴 정답지.pdf

## 왜 따로 만드나 (원장 2026-11-15)

영일중1 2026 기말 논술 두 문항이 「단어 수 지정 조건 영작」에서 「글 내용을 한 문장으로 —
비교급 / 의견+이유 — **윗글에서 연속된 3단어 이상 그대로 쓰지 말 것**」으로 바뀌었다
(data/stage0/comparisons/중1_영일_2026기말_기출.md §3). 동형 서술형은 형태만 물어서 한 문항도 못 맞혔다.
「바꿔 쓰기」와 「조건 점검」은 형태 드릴(make_form_drill)로도, 동형 한두 문항으로도 안 붙는다 — 따로 돌린다.

## 디자인 지침 4 와의 관계

지침 4 「서술형 답은 칸 하나에 몇 단어」는 **채점 부담** 때문에 만든 것이다. 이 드릴은 학교가 줄글 한 문장을
요구하기 시작해서 만드는 것이라 한 문장을 통째로 쓰게 한다. 대신 채점이 흔들리지 않게
정답지에 **감점표**와 **자주 나오는 감점 답**을 찍고, 문제지에는 학생이 스스로 보는 **조건 점검 칸**을 둔다.

## 기계 검사 (`check`)

  · 실전 범위 지문의 조각이 passages/*.json 의 body_text 에 **글자 그대로** 있는가 (설계원칙 7)
  · 실전 모범답이 지문과 **연속 3단어**를 공유하지 않는가 — 조건을 우리가 어기면 안 된다
  · A형 모범답에 비교급이 있는가 · B형 모범답에 because 가 있는가
  · 「채점자 되어 보기」에서 「그대로」로 판정한 학생 답은 실제로 3단어를 공유하고, 고친 답은 안 하는가
"""
import argparse
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
from html import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pypdf import PdfReader, PdfWriter                                # noqa: E402
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.pdf_pages import save_pdf                                  # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402
from tools.make_form_drill import CSS as BASE_CSS, head               # noqa: E402
from tools import essay_drill_yi1                                     # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = os.path.join(ROOT, "result", "readitude")
GEN = os.path.join(ROOT, "data", "generated", "drills")
PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")

UNITS = {
    "영일중1": {
        "title": "영일중1 5·6·7과 서술형 집중드릴",
        "sub": "글 내용을 내 말로 한 문장 — 바꿔 쓰기 · 비교급 요약 · 의견 + 이유 · 조건 점검 (2026 기말 논술형 꼴)",
        "mod": essay_drill_yi1,
    },
}

CSS = BASE_CSS + """
.guide { border: 1.5px solid #1f2d3d; border-radius: 3px; padding: 2.5mm 4mm; margin: 0 0 3mm; font-size: 9.5pt; }
.guide h3 { margin: 0 0 1mm; font-size: 10.5pt; }
.guide ol, .guide ul { margin: 1mm 0 1mm 5mm; padding: 0; }
.guide li { margin: 0.6mm 0; }
.guide .ex { background: #f6f8fa; border-radius: 2px; padding: 1.5mm 3mm; margin: 1.5mm 0; font-size: 9.5pt; }
.guide .bad { color: #b42318; } .guide .good { color: #1f6f43; font-weight: 600; }
table.t td.src { width: 16%; color: #8a94a6; font-size: 8pt; }
table.t td.e { width: 40%; }
ol.q li { align-items: flex-start; }
.wline { display: block; border-bottom: 1px solid #333; height: 7.5mm; margin: 0 0 0 0; }
.given { color: #445; font-size: 9pt; }
.frame { font-weight: 600; }
.stu { background: #fff8e6; border: 1px solid #f0dfae; border-radius: 2px; padding: 0.6mm 2mm; display: inline-block; margin: 0.8mm 0; }
.jl { display: flex; align-items: flex-end; gap: 2mm; margin-top: 1mm; color: #6b7a90; font-size: 8.5pt; }
.jl .wline { flex: 1; height: 6.5mm; }
.verdict { display: block; color: #6b7a90; font-size: 8.5pt; margin-top: 0.8mm; }
.passage { border: 1px solid #c9d1dc; border-radius: 2px; padding: 2.5mm 4mm; margin: 0 0 3mm; font-size: 10pt; line-height: 1.62; text-align: justify; }
.passage p { margin: 0 0 1.2mm; text-indent: 1em; } .passage p:last-child { margin-bottom: 0; }
.passage .who { font-weight: 700; text-indent: 0; margin-top: 1mm; }
.passage .ptitle { text-align: center; font-weight: 700; text-indent: 0; }
.essay { break-inside: avoid; margin: 0 0 3.5mm; }
.essay .stem { display: flex; gap: 2mm; font-weight: 600; }
.essay .stem .lab { white-space: nowrap; }
.essay .stem .pts { margin-left: auto; white-space: nowrap; font-weight: 400; color: #445; }
.essay .ctx { border: 1px solid #1f2d3d; padding: 1.8mm 3.5mm; margin: 1.5mm 0; font-size: 10pt; }
.cond { border: 1px dashed #8a94a6; padding: 1.2mm 3.5mm; margin: 1.5mm 0; font-size: 9pt; }
.cond .lab { font-weight: 700; } .cond ul { margin: 0.5mm 0 0 4.5mm; padding: 0; } .cond li { margin: 0.3mm 0; }
.check { font-size: 8.5pt; color: #445; margin-top: 1.2mm; }
.check span { margin-right: 4mm; white-space: nowrap; }
.model { background: #f1f7f3; border-left: 3px solid #1f6f43; padding: 1.2mm 3mm; margin: 1.2mm 0; font-size: 9.5pt; }
.model p { margin: 0.4mm 0; } .model .trap { color: #b42318; }
.rub { font-size: 8.5pt; color: #445; margin: 1mm 0 0; }
.srcnote { color: #8a94a6; font-size: 8pt; font-weight: 400; margin-left: 2mm; }
"""

TOK = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def toks(s):
    return TOK.findall(s.lower().replace("’", "'"))


def shared3(answer, source):
    """answer 와 source 가 공유하는 연속 3단어 (없으면 None)."""
    a, src = toks(answer), toks(source)
    grams = {tuple(src[i:i + 3]) for i in range(len(src) - 2)}
    for i in range(len(a) - 2):
        if tuple(a[i:i + 3]) in grams:
            return " ".join(a[i:i + 3])
    return None


COMPARATIVE = re.compile(r"\b(more|less|better|worse|\w+er)\b[^.]*\bthan\b|\b(harder|easier)\b", re.I)


def load_passage(pid):
    with io.open(os.path.join(PASSAGES, pid + ".json"), encoding="utf-8") as f:
        return json.load(f)["body_text"]


def mock_paragraphs(m):
    pid, parts = m["passage"]
    if pid == "new":
        return parts
    body = load_passage(pid)
    if parts is None:
        return [body]
    return parts


def check(mod):
    problems = []
    for m in mod.MOCK:
        pid, parts = m["passage"]
        paras = mock_paragraphs(m)
        if pid != "new" and parts:
            body = load_passage(pid)
            for p in parts:
                if p not in body:
                    problems.append(f"실전 「{m['title']}」 조각이 {pid} body_text 에 없음: {p[:40]}…")
        text = " ".join(paras)
        for kind in ("a", "b"):
            for ans in m[kind]["answers"]:
                hit = shared3(ans, text)
                if hit:
                    problems.append(f"실전 「{m['title']}」 {kind.upper()}형 모범답이 지문과 연속 3단어 공유: “{hit}” ← {ans}")
                if len(toks(ans)) > 16:
                    problems.append(f"실전 「{m['title']}」 {kind.upper()}형 모범답 16단어 초과: {ans}")
                if kind == "a" and not COMPARATIVE.search(ans):
                    problems.append(f"실전 「{m['title']}」 A형 모범답에 비교급 없음: {ans}")
                if kind == "b" and " because " not in ans:
                    problems.append(f"실전 「{m['title']}」 B형 모범답에 because 없음: {ans}")
            trap = m[kind]["trap"].split(" — ")[0].replace("…", "")
            if "연속 3단어" in m[kind]["trap"] and not shared3(trap, text):
                problems.append(f"실전 「{m['title']}」 {kind.upper()}형 감점 답이 실제로는 3단어를 공유하지 않음: {trap}")
    for src, frame, cond, stu, verdict, fix in mod.JUDGE:
        hit = shared3(stu, src)
        if verdict.startswith("그대로") or "그대로 —" in verdict:
            if not hit:
                problems.append(f"채점자: 「그대로」 판정인데 3단어 공유 없음: {stu}")
        elif hit:
            problems.append(f"채점자: 판정에 「그대로」가 없는데 3단어 공유 “{hit}”: {stu}")
        good = stu if fix == "O" else fix
        if shared3(good, src):
            problems.append(f"채점자: 고친 답이 3단어 공유 “{shared3(good, src)}”: {good}")
    for s, hint, a in mod.COMPARE:
        if not COMPARATIVE.search(a) and "er and " not in a:
            problems.append(f"비교급: 모범답에 비교급 없음: {a}")
    for s, hint, a in mod.REWRITE:
        if "【" not in s or "】" not in s:
            problems.append(f"바꿔 쓰기: 밑줄 표시 없음: {s}")
        inner = s[s.index("【") + 1:s.index("】")]
        if toks(inner) == toks(a):
            problems.append(f"바꿔 쓰기: 답이 원문과 같음: {s}")
    for sit, who, hint, a in mod.OPINION:
        if " because " not in a or a.split()[0] in ("would", "I"):
            problems.append(f"의견: 모범답 꼴 이상: {a}")
    return problems


def plan(mod, seed):
    rng = random.Random(seed)

    def rounds(items, per):
        xs = list(items)
        rng.shuffle(xs)
        return [xs[i:i + per] for i in range(0, len(xs), per)]

    bank_test = list(mod.BANK)
    rng.shuffle(bank_test)
    # 채점자: O 가 회차마다 고르게
    ok = [j for j in mod.JUDGE if j[5] == "O"]
    ng = [j for j in mod.JUDGE if j[5] != "O"]
    rng.shuffle(ok); rng.shuffle(ng)
    n = 3                                     # 한 회 6문항 — 9문항이면 쓰는 줄 때문에 두 쪽으로 넘친다
    judge = [[] for _ in range(n)]
    for i, j in enumerate(ng):
        judge[i % n].append(j)
    for i, j in enumerate(ok):
        judge[i % n].append(j)
    for r in judge:
        rng.shuffle(r)
    return {"bank_test": bank_test[:24], "rewrite": rounds(mod.REWRITE, 12),
            "compare": rounds(mod.COMPARE, 8), "opinion": rounds(mod.OPINION, 6), "judge": judge}


# ──────────────────────────────────────────────────────────────────────────
# 렌더
# ──────────────────────────────────────────────────────────────────────────
GUIDE = """
<div class="guide">
<h3>2026 기말 논술형은 이렇게 나왔다</h3>
<div class="ex"><b>논술1 (4점)</b> According to the passage, Maria and Jane agree that ____(A)____ in choosing a job.<br>
<b>논술2 (6점)</b> If I were Inspector Barker, I would ________________.</div>
<ul>
<li><b>&lt;조건&gt;</b> 비교급 반드시 사용 · 주어와 동사가 있는 한 문장 · 입장과 이유 · <b>윗글에서 연속된 3단어 이상을 그대로 사용하지 말 것</b></li>
<li>근거 문장을 찾아서 <b>그대로 옮겨 쓰면 감점</b>이다. 찾은 아이일수록 베끼기 쉽다 — 여기서 점수가 갈린다.</li>
</ul>
<div class="ex">근거 문장 &nbsp;… what you prefer should come first.<br>
<span class="bad">✕ what you prefer should come first</span> &nbsp;(연속 6단어 · 비교급 없음)<br>
<span class="good">○ personal preferences are more important than other things</span></div>
</div>
<div class="guide">
<h3>답 쓰는 네 걸음</h3>
<ol>
<li><b>근거 문장 찾기</b> — 답이 되는 문장에 밑줄. (요지는 보통 마지막 문장이나 but · however 뒤에 있다)</li>
<li><b>우리말로 한 줄</b> — 「직업을 고를 땐 좋아하는 게 제일 중요하다」처럼 뜻만 남긴다.</li>
<li><b>바꿔 쓰기</b> — 낱말을 바꾸거나(come first → be the most important) 구조를 바꾼다(최상급 → 비교급 + than other ~).</li>
<li><b>조건 점검</b> — ① 본문과 3단어가 연달아 같은 곳이 없나 ② 지정 어법(비교급 / would + 동사원형 / because + 주어 + 동사) ③ 주어 · 동사 · 시제 · 철자.</li>
</ol>
</div>
<div class="guide">
<h3>감점표 <span class="srcnote">학교 채점 기준은 공개되지 않았다 — 학원은 엄하게 본다</span></h3>
<ul>
<li><b>조건을 어기면 0점으로 연습한다</b> — 연속 3단어 이상 그대로 · 비교급 없음 · 주어나 동사 없음 · 입장이나 이유 없음.</li>
<li>A형 4점 = 내용(요지) 2 + 문장 정확도 2 &nbsp;/&nbsp; B형 6점 = 입장 2 + 이유 2 + 문장 정확도 2. 어법 · 철자 오류 하나에 1점 감점.</li>
<li>자주 깎이는 곳 — more better · importanter · because of + 문장 · would trusts · the Sally’s · tell for me · belive(believe).</li>
</ul>
</div>
"""

RULE = {
    "bank": "본문 표현을 <b>뜻이 같은 다른 말</b>로. 3단어 조건을 피하는 재료다 — 표를 가리고 말할 수 있을 때까지.",
    "rewrite": "밑줄 친 부분을 <b>주어진 말</b>을 써서 뜻이 같게 바꿔 쓰시오. 필요하면 형태를 바꾼다(시제 · 수 일치).",
    "compare": "주어진 내용을 <b>비교급 한 문장</b>으로. 짧은 말 -er (y → ier · 단모음+단자음은 자음 겹침) · 긴 말 more ~ · "
               "good/well → better · bad → worse · much → more · 비교급 뒤 <b>than</b> · more 와 -er 를 겹쳐 쓰지 않는다.",
    "opinion": "<b>I would + 동사원형</b> (안 한다면 would not + 동사원형) + <b>because + 주어 + 동사</b>. "
               "would 뒤에 -s · -ed 를 붙이지 않는다 · because of 뒤에는 명사만.",
    "judge": "학생 답을 채점한다. 조건을 다 지켰으면 <b>O</b>, 아니면 <b>무엇을 어겼는지</b> 쓰고 고쳐 쓰시오. "
             "「그대로」 = 근거 문장과 3단어 이상이 연달아 같다.",
}


def lines(n):
    return '<span class="wline"></span>' * n


def bank_table(rows, ans, blank):
    out = ['<table class="t"><tr><th>본문 표현</th><th>바꿔 쓸 말</th><th>나온 곳</th></tr>']
    for e, a, src in rows:
        cell = f'<td class="a">{esc(a)}</td>' if (ans or not blank) else '<td></td>'
        out.append(f'<tr><td class="e">{esc(e)}</td>{cell}<td class="src">{esc(src)}</td></tr>')
    out.append("</table>")
    return "".join(out)


def rewrite_items(items, ans):
    out = ['<ol class="q">']
    for i, (s, hint, a) in enumerate(items, 1):
        s2 = esc(s).replace("【", '<u class="x">').replace("】", "</u>")
        tail = f'<div class="ans">→ {esc(a)}</div>' if ans else f'<div>→ {lines(1)}</div>'
        out.append(f'<li><span class="no">{i}</span><span class="s">{s2} <span class="hint">({esc(hint)})</span>{tail}</span></li>')
    out.append("</ol>")
    return "".join(out)


def compare_items(items, ans):
    out = ['<ol class="q">']
    for i, (s, hint, a) in enumerate(items, 1):
        tail = f'<div class="ans">→ {esc(a)}</div>' if ans else f'<div>→ {lines(1)}</div>'
        out.append(f'<li><span class="no">{i}</span><span class="s">{esc(s)}<br>'
                   f'<span class="given">[ {esc(hint)} ]</span>{tail}</span></li>')
    out.append("</ol>")
    return "".join(out)


def opinion_items(items, ans):
    out = ['<ol class="q">']
    for i, (sit, who, hint, a) in enumerate(items, 1):
        tail = f'<div class="ans">→ … I would {esc(a)}.</div>' if ans else f'<div>{lines(2)}</div>'
        out.append(f'<li><span class="no">{i}</span><span class="s">{esc(sit)} <span class="hint">({esc(hint)})</span><br>'
                   f'<span class="frame">If I were {esc(who)}, I would</span>{tail}</span></li>')
    out.append("</ol>")
    return "".join(out)


def judge_items(items, ans):
    out = ['<ol class="q">']
    for i, (src, frame, cond, stu, verdict, fix) in enumerate(items, 1):
        if ans:
            fixed = "" if fix == "O" else f'<div class="ans">→ {esc(fix)}</div>'
            tail = f'<span class="verdict" style="color:#1f2d3d"><b>{esc(verdict)}</b></span>{fixed}'
        else:
            tail = ('<div class="jl"><span>판정 (O / 어긴 것)</span><span class="wline"></span></div>'
                    '<div class="jl"><span>고쳐 쓰기</span><span class="wline"></span></div>')
        out.append(f'<li><span class="no">{i}</span><span class="s">'
                   f'<span class="given">근거 문장: {esc(src)} &nbsp;·&nbsp; 조건: {esc(cond)}</span><br>'
                   f'{esc(frame)}<br><span class="stu">학생 답: {esc(stu)}</span>{tail}</span></li>')
    out.append("</ol>")
    return "".join(out)


def cond_html(conds):
    return ('<div class="cond"><span class="lab">&lt;조건&gt;</span><ul>'
            + "".join(f"<li>{esc(c)}</li>" for c in conds) + "</ul></div>")


def mock_html(no, m, mod, ans):
    paras = mock_paragraphs(m)
    labels = m.get("labels") or []
    P = [f'<p class="ptitle">{esc(m["title"])}</p>']
    for i, p in enumerate(paras):
        if i < len(labels):
            P.append(f'<p class="who">{esc(labels[i])}</p>')
        P.append(f"<p>{esc(p)}</p>")
    H = [f'<div class="pb"></div><h2>실전 {no}회 <span class="n">A형 4점 + B형 6점 = 10점</span>'
         f'<span class="srcnote">{esc(m["src"])}</span></h2>',
         f'<div class="passage">{"".join(P)}</div>']
    for kind, pts, conds, label in (("a", 4, mod.A_COND, "A"), ("b", 6, mod.B_COND, "B")):
        q = m[kind]
        stem = ("윗글의 내용을 바탕으로, 다음 문장의 빈칸 (A)를 영어로 완성하시오." if kind == "a"
                else "윗글을 읽고, 자신의 생각과 그 이유를 <조건>에 맞게 영어로 쓰시오.")
        if q.get("ko"):
            stem += " " + q["ko"]
        H.append(f'<div class="essay"><div class="stem"><span class="lab">【논술형 {label}】</span><span>{esc(stem)}</span>'
                 f'<span class="pts">{pts}점</span></div>')
        H.append(f'<div class="ctx">{esc(q["frame"])}</div>')
        H.append(cond_html(conds))
        if ans:
            model = "".join(f"<p>○ {esc(a)}</p>" for a in q["answers"])
            H.append(f'<div class="model">{model}<p class="trap">✕ {esc(q["trap"])}</p></div>')
            H.append('<div class="rub">' + ("내용(요지) 2 · 문장 정확도 2 — 조건 위반 0점" if kind == "a"
                                           else "입장 2 · 이유 2 · 문장 정확도 2 — 조건 위반 0점") + "</div>")
        else:
            H.append(lines(2))
            checks = (["3단어 연속 없음", "비교급", "주어 + 동사"] if kind == "a"
                      else ["3단어 연속 없음", "입장", "because + 주어 + 동사", "would + 동사원형"])
            H.append('<div class="check">내가 점검: ' + "".join(f"<span>☐ {c}</span>" for c in checks) + "</div>")
        H.append("</div>")
    return "".join(H)


def render(u, p, logo, part):
    mod, ans = u["mod"], part == "answers"
    H = [f"<style>{CSS}</style>{head(u, logo, part)}"]
    if not ans:
        H.append(GUIDE)
    half = (len(mod.BANK) + 1) // 2
    pb = "" if ans else '<div class="pb"></div>'      # 정답지는 안내 쪽이 없다 — 첫 쪽이 비지 않게
    H.append(f'{pb}<h2>1. 바꿔 쓰기 낱말 은행 <span class="n">{len(mod.BANK)}개 · 외울 것</span></h2>'
             f'<div class="rule">{RULE["bank"]}</div>'
             f'<div class="two">{bank_table(mod.BANK[:half], ans, False)}{bank_table(mod.BANK[half:], ans, False)}</div>')
    bt = p["bank_test"]
    H.append(f'<div class="pb"></div><h2>1. 낱말 은행 — 확인 <span class="n">{len(bt)}개 · 표를 덮고</span></h2>'
             f'<div class="rule">{RULE["bank"]}</div>'
             f'<div class="two">{bank_table(bt[:len(bt)//2], ans, True)}{bank_table(bt[len(bt)//2:], ans, True)}</div>')
    for key, title, fn in (("rewrite", "2. 밑줄 친 부분 바꿔 쓰기", rewrite_items),
                           ("compare", "3. 비교급으로 한 문장", compare_items),
                           ("opinion", "4. 의견 + 이유 — If I were ~, I would ~ because ~", opinion_items),
                           ("judge", "5. 채점자 되어 보기", judge_items)):
        for i, items in enumerate(p[key], 1):
            H.append(f'<div class="pb"></div><h2>{title} — {i}회 <span class="n">{len(items)}문항</span></h2>'
                     f'<div class="rule">{RULE[key]}</div>{fn(items, ans)}')
    for i, m in enumerate(mod.MOCK, 1):
        H.append(mock_html(i, m, mod, ans))
    H.append('<div class="mark">리디튜드 · 학원 내부 지도용 · 손으로 출제 (모델 미사용) · 모범답 외의 답은 감점표로 채점</div>')
    return "\n".join(H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, choices=sorted(UNITS))
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", type=int, default=20261115)
    a = ap.parse_args()
    u = UNITS[a.unit]
    mod = u["mod"]
    problems = check(mod)
    p = plan(mod, a.seed)
    n = (len(p["bank_test"]) + sum(len(r) for k in ("rewrite", "compare", "opinion", "judge") for r in p[k])
         + 2 * len(mod.MOCK))
    print(f"■ {u['title']}\n   낱말 은행 {len(mod.BANK)} (확인 {len(p['bank_test'])}) · "
          + " · ".join(f"{k} {len(p[k])}×{len(p[k][0])}" for k in ("rewrite", "compare", "opinion", "judge"))
          + f" · 실전 {len(mod.MOCK)}회 × 2  = {n}문항")
    if problems:
        print("   ✕ 검사에 걸림:")
        for x in problems:
            print("     ·", x)
        return 1
    print("   검사 통과 — 범위 지문 글자 일치 · 모범답 연속 3단어 없음 · 지정 어법 포함")
    os.makedirs(GEN, exist_ok=True)
    with io.open(os.path.join(GEN, f"{a.unit}.essay.json"), "w", encoding="utf-8") as f:
        json.dump({"unit": a.unit, "title": u["title"], "seed": a.seed, "plan": p,
                   "mock": [{k: v for k, v in m.items()} for m in mod.MOCK]}, f, ensure_ascii=False, indent=1)
    if not a.build:
        print("   --build 를 붙이면 PDF 를 만듭니다.")
        return 0
    chrome = find_chrome(); logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="essaydrill_")
    try:
        for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
            html = os.path.join(tmp, f"{part}.html"); pdf = os.path.join(tmp, f"{part}.pdf")
            io.open(html, "w", encoding="utf-8").write(render(u, p, logo, part))
            to_pdf(chrome, html, pdf)
            w = PdfWriter()
            for pg in PdfReader(pdf).pages:
                w.add_page(pg)
            dest = os.path.join(OUT, f"{u['title']}{suffix}.pdf")
            pages = save_pdf(w, dest)                     # 아래 가운데 쪽수 — 디자인 지침 1
            print(f"   → {os.path.basename(dest)}  {pages}쪽")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
