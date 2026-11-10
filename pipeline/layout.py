# -*- coding: utf-8 -*-
"""
종이에 찍을 때의 줄 나눔 — 디자인 지침 7 「보기 · 지문은 줄을 나눠 찍는다」 (2026-11-08).

원장: 「시험지 만들 때 왜 줄바꿈이 하나도 안 되어 있지? 보기나 선택지 줄 때 반드시 줄바꿈」.
세어 보니 동형 자료 471개 중 긴 지문 92개가 줄바꿈 0 — 교과서 본문(`body_text`)이 한 줄로
저장돼 있어 「Challenge 01 Reduce Food Waste Olivia: My birthday…」 가 한 덩어리로 찍혔다.

**글자는 바꾸지 않는다** (설계 7 · body_text 불변). 줄을 바꿀 **자리(글자 위치)** 만 계산해
렌더러에 넘긴다. 자리는 두 가지에서 온다:

  1. 자동 — 화자 표시(`Olivia:` · `A:`) · 소제목(`Challenge 01`) · 보기 항목(`b.` `(B)` `[2]`)
     앞이 문장 끝(. ? ! ” ")이면 그 앞에서 줄을 바꾼다.
  2. 손 — 자료의 `breaks` 칸: ["Challenge 02", "Pit Crews in Car Racing"] 처럼 그 글 **앞에서**
     줄을 바꾼다. 단락처럼 기계가 모르는 자리에 쓴다.
"""
import re

# 화자: 「Olivia:」 「Mr. Boggis:」 「A:」 — 대문자로 시작하는 한 낱말 + 콜론, 뒤에 공백.
# 여러 낱말을 허용했더니 「Reduce ⏎ Food Waste Olivia:」 처럼 소제목을 잘랐다.
_SPEAKER = r"(?:(?:Mr|Mrs|Ms|Dr)\. )?[A-Z][a-zA-Z’']*:\s"
# 소제목: 「Challenge 01」 「Lesson 7」 「Step 2」 — 낱말 + 두 자리 이하 숫자
_HEADING = r"(?:Challenge|Step|Part|Lesson|Day|Tip|Rule) \d{1,2}\b"
# 보기 항목: b. ~ h. · (B) ~ (H) · (b) · [2] ~ [9] · ② ~ ⑤ (첫 항목 a/(A)/[1]/① 은 보통 줄 처음이라 제외해도 된다)
_ITEM = r"(?:[b-h]\. |\([B-Hb-h]\) |\[[2-9]\] |[②-⑤] ?)"
_END = r"[.?!”\"')\]]"
AUTO = re.compile(r"(?<=" + _END + r") +(?=" + _SPEAKER + "|" + _HEADING + "|" + _ITEM + ")")
# 소제목 바로 뒤에 화자가 오면(「Challenge 01 Reduce Food Waste Olivia:」) 화자 앞에서도 끊는다
AFTER_HEAD = re.compile(r"(?<=[A-Za-z]) +(?=" + _SPEAKER + ")")


def break_positions(text, breaks=()):
    """줄을 바꿀 자리 — 그 자리의 공백 한 칸을 줄바꿈으로 바꿔 찍는다. {위치: 지울 공백 길이}."""
    pos = {}
    for m in re.finditer(r"(?:<보기>|〈보기〉|\[보기\]) +(?=[a(A①\[])", text):   # 「<보기> a. …」 → 보기 표시 다음 줄부터
        sp = len(m.group(0)) - len(m.group(0).rstrip(" "))
        pos[m.end() - sp] = sp
    for m in AUTO.finditer(text):
        pos[m.start()] = m.end() - m.start()
    for h in re.finditer(_HEADING, text):
        # 소제목 줄 안에서 화자가 시작하면 그 앞도 끊는다 — 「Challenge 01 Reduce Food Waste ⏎ Olivia: …」
        line_end = text.find("\n", h.end())
        seg_end = line_end if line_end >= 0 else len(text)
        m = AFTER_HEAD.search(text, h.end(), min(seg_end, h.end() + 80))
        if m:
            pos[m.start()] = m.end() - m.start()
    for b in breaks or ():
        i = text.find(b)
        if i > 0:
            j = i
            while j > 0 and text[j - 1] == " ":
                j -= 1
            pos[j] = i - j
    # 이미 줄바꿈인 자리 옆은 건너뛴다
    return {p: n for p, n in pos.items() if p > 0 and text[p - 1] != "\n"}


def split_lines(text, breaks=()):
    """글자를 바꾸지 않고 줄 나눔만 적용한 문자열 — 발문 속 <보기> 처럼 밑줄이 없는 곳에 쓴다."""
    pos = break_positions(text, breaks)
    out, i = [], 0
    for p in sorted(pos):
        out.append(text[i:p])
        out.append("\n")
        i = p + pos[p]
    out.append(text[i:])
    return "".join(out)


_TABLE = None


def breaks_for(m):
    """자료 하나의 손 줄 나눔 — 자료의 `breaks` 칸, 없으면 data/stage0/passage_breaks.json (지문 첫 40글자)."""
    global _TABLE
    if m.get("breaks"):
        return m["breaks"]
    if _TABLE is None:
        import io, json, os
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "stage0", "passage_breaks.json")
        _TABLE = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    t = m.get("text") or ""
    for k, v in _TABLE.items():                  # 키는 지문 첫머리 — 길이가 조금 달라도 앞부분이 같으면
        if not k.startswith("_") and t.startswith(k):
            return v
    return ()


def unbroken(text, limit=400):
    """줄바꿈 없이 긴 글인가 — 검사용 (item_principles)."""
    return len(text) > limit and "\n" not in text and not break_positions(text)
