# -*- coding: utf-8 -*-
"""
지문 속 밑줄 — 문항이 「어디에 밑줄을 긋는지」 적고, 렌더러가 찍을 때 긋는다.

2026-11-08 원장 「왜 우리는 시험지 만들 때 밑줄을 긋지 못하는거야?」. 그때까지 렌더러는
지문을 글자 그대로만 찍었다 — **「밑줄 친 ①~⑤」 문항 174개가 밑줄 없이 나갔다.**
①~⑤ 기호만 있어서 ⓐ 가 낱말 하나인지 구절인지 학생이 알 수 없었다.

지문 글자는 고치지 않는다 (설계 7 — 같은 본문이 세트마다 다른 글이 되면 안 된다).
밑줄 자리는 **문항**의 `underline` 칸에 적는다:

  "underline": ["①[that you fixed]",                   ← 지문에 그대로 있는 글. [ ] 안만 밑줄
                "Jeans are strong, so [they] are perfect"]  ← 앞뒤 글은 자리를 찾는 닻
  [ ] 가 없으면 글 전체에 밑줄.

모델이 지문에 직접 「①[so exciting that]」 처럼 쓴 세트도 있다 (영덕중2 2세트) —
기호 바로 뒤의 [ ] 와 _ _ (태장중2 3세트) 는 밑줄로 바꾸고 괄호는 지운다.
"""
import html
import re

MARKER = r"(?:[①-⑤ⓐ-ⓔ]|\([A-Ea-e]\))"
_INLINE = re.compile(r"(" + MARKER + r")\s?(?:\[([^\]\n]+)\]|_([^_\n]+)_)")
_Q = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def parse_entry(u):
    """「앞[밑줄]뒤」 → (닻 글, 밑줄 시작, 밑줄 끝) — 닻 글 기준 위치."""
    if "[" in u and "]" in u.split("[", 1)[1]:
        pre, rest = u.split("[", 1)
        inner, post = rest.split("]", 1)
        return pre + inner + post, len(pre), len(pre) + len(inner)
    return u, 0, len(u)


def locate(text, entries):
    """(밑줄 구간 [(시작, 끝)], 지울 위치 집합, 못 찾은 항목 목록). 네모 구간은 locate.boxes 에."""
    spans, drop, missing, boxes = [], set(), [], []
    locate.boxes = boxes
    for m in _INLINE.finditer(text):                       # 지문에 직접 쓴 「①[…]」 · 「①_…_」
        g = 2 if m.group(2) is not None else 3
        lb = m.start(g) - 1
        if g == 2 and "/" in m.group(2):                   # 「(A)[to collect / collecting]」 — 네모 고르기
            boxes.append((m.start(g), m.end(g)))           # 밑줄이 아니라 네모 상자
        else:
            spans.append((m.start(g), m.end(g)))
        drop.update({lb, m.end(g)})
        if text[m.end(1):lb] == " ":                       # 「① [x]」 의 띄움도 지운다
            drop.add(m.end(1))
    norm = text.translate(_Q)
    for u in entries or []:
        anchor, a, b = parse_entry(u)
        i = norm.find(anchor.translate(_Q))
        if i < 0:                                          # 띄어쓰기 차이(줄바꿈·두 칸)까지는 봐준다
            pat = r"\s+".join(map(re.escape, anchor.translate(_Q).split()))
            mm = re.search(pat, norm) if pat else None
            if not mm:
                missing.append(u)
                continue
            # 닻 안의 위치를 실제 글 위치로 옮긴다 — 앞부분 낱말 수로 맞춘다
            seg = norm[mm.start():mm.end()]
            pre_words = len(anchor[:a].split())
            idx = [w.start() for w in re.finditer(r"\S+", seg)]
            s = mm.start() + (idx[pre_words] if pre_words < len(idx) else 0)
            spans.append((s, s + len(anchor[a:b])))
            continue
        spans.append((i + a, i + b))
    return sorted(spans), drop, missing


def html_with_underline(text, entries):
    """지문 한 덩어리를 HTML 로 — 줄마다 <p>, 밑줄은 <u>."""
    spans, drop, _ = locate(text, entries)
    boxes = locate.boxes
    bstart = {a for a, _ in boxes}
    bend = {b for _, b in boxes}
    starts, ends = {}, {}
    for s, e in spans:
        if e > s:
            starts[s] = starts.get(s, 0) + 1
            ends[e] = ends.get(e, 0) + 1
    out, depth = [], 0
    for i, ch in enumerate(text + "\0"):
        if i in ends and depth:
            k = min(ends[i], depth)
            out.append("</u>" * k)
            depth -= k
        if i in bend:
            out.append("</span>")
        if i in starts:
            out.append("<u>" * starts[i])
            depth += starts[i]
        if i in bstart:
            out.append('<span class="choice">')
        if ch == "\0" or i in drop:
            continue
        if ch == "\n":
            out.append("</u>" * depth + "\n" + "<u>" * depth)   # 줄을 넘는 밑줄도 줄마다 닫는다
            continue
        out.append(html.escape(ch, quote=False))
    out.append("</u>" * depth)
    return "".join(f"<p>{ln}</p>" for ln in "".join(out).split("\n")
                   if re.sub(r"</?u>", "", ln).strip())
