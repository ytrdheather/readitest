# -*- coding: utf-8 -*-
"""
단원 하나를 원장이 정한 분류 기준으로 통째 정리한다 (2026-09-05 지정).

  python tools/build_unit.py --lesson 5 --workbook "C:/…/L5.pdf"
  python tools/build_unit.py --lesson 5 --workbook "…" --write

## 분류 기준

    지문종류 1  대화문      기능 표현으로 묶어서 이름
                            L5 = 교통수단 묻고 답하기 / 소요 시간 묻고 답하기
                            → 「교통수단 표현-1」 「교통수단 표현-2」 …

    지문종류 2  본문        제목 하나 + 문단별로 「제목-1」 「제목-2」 …
                            L5 = Street Art in London-1 ~ -4

    지문종류 3  Read More   추가로 배부되는 것. 두 갈래다.
                            · 교과서 추가자료 (More 섹션: Speak Up, Think and Write 등)
                            · 학교별 배부 외부지문 (영일중 「A girl with a red balloon」 등)
                            → 「지문 1」 「지문 2」 …

## 왜 다시 짰나

`extract_textbook.py` 는 「내용정리 플러스」의 `READING 본문❶` 표시만 보고 **제목 없이**
지문을 쪼갰다. 그 결과 L5 가 서로 무관해 보이는 `본문1~4` 가 됐다 —
실제로는 「Street Art in London」 한 편의 네 문단이다. 원장이 이걸 잡아냈다.

대화문도 「Watch and Talk C」 하나만 뽑았는데 실제로는 9개가 있었다.
자습서(L5.pdf/l6.pdf)에 전부 실려 있는데 그 파일을 대화 추출에 안 썼다.

## 입력

자습서 PDF (L5.pdf / l6.pdf) 한 개면 된다. 「내용정리 플러스」보다 구조가 명확하고
대화·본문·More 가 한 파일에 다 있다.
"""
import argparse
import hashlib
import json
import os
import re
import sys

import pypdf

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "stage0", "passages")

HANGUL = re.compile(r"[가-힣]")
MARKER = re.compile(r"[①-⓿❶-➓]")
TURN_SPLIT = re.compile(r"(?<=[.?!])\s*(?=[A-Z][A-Za-z]{0,8}:\s)")
# 대화·More 블록 제목. '교과서 NN쪽' 이 뒤따르는 것이 블록의 시작 표시다.
BLOCK = re.compile(r"(Watch and Talk[- ]?[A-D]?-?\d?|Speak Up|Talk and Play|Listen Up|"
                   r"Review-\d+|Think and Write|Culture Project[-\w]*|"
                   r"Before You Read[-\w]*|After You Read[-\w]*)\s*교과서\s*(\d+)쪽")
FUNC = re.compile(r"([가-힣]{2,10}(?:\s[가-힣]{1,6})?\s*(?:묻고 답하기|요청하고 답하기|"
                  r"제안하기|권유하기|표현하기))")
# 본문은 번호가 붙어 나온다: '01 Modern street art comes in…'
READ_LINE = re.compile(r"(?:^|\s)(\d{2})\s+([A-Z“\"(][^\n]*)")

# 원장이 육안 확인해 준 개별 정정. 추측이 아니라 **확인된 값**만 넣는다.
# 코드에 남겨야 도구를 다시 돌려도 같은 결과가 나온다.
CONFIRMED_FIXES = [
    ("but c an you recommend", "but can you recommend",
     "L6 대화 · 자습서 조판으로 can 이 쪼개짐 · 원장 확인 2026-08-23"),
    ("their f aces", "their faces",
     "L5 Read More 지문3 (Culture Project) · 원장 확인 2026-09-05"),
    # ── 2026-09-05 조판 파손 일괄 정정 ────────────────────────────
    # 자습서 PDF 의 문자층이 단어 중간에 공백을 넣어 놓은 자리들이다. 왼쪽 문자열을
    # 넉넉히 잡아 붙였다 — 'w as' 같은 조각만으로 치환하면 엉뚱한 곳까지 바뀐다.
    # 어느 쪽으로 붙일지는 코퍼스 어휘로 판정하려다 포기했다: 화자 표시(B:/G:/W:)와
    # 이니셜(Frank W.)이 전부 한 글자 토큰이라 규칙이 계속 오판했다. 20군데뿐이니
    # 표로 박는 편이 재현 가능하고 감사도 된다.
    ("T ake line 4", "Take line 4", "L5 대화-1"),
    ("ho w can I get", "how can I get", "L5 대화-2"),
    ("you t ake a taxi", "you take a taxi", "L5 대화-2"),
    ("Ho w long will it take", "How long will it take", "L5 대화-7"),
    ("soda her e is good", "soda here is good", "L6 대화-2"),
    ("interested in scienc e", "interested in science", "L6 대화-4"),
    ("Can y ou recommend", "Can you recommend", "L6 대화-4"),
    ("finds his l ove for music", "finds his love for music", "L6 Read More 1"),
    ("so I s trongly recommend", "so I strongly recommend", "L6 Read More 1"),
    ("She w as a successful", "She was a successful", "L6 Read More 2"),
    ("gave it away t o poor people", "gave it away to poor people", "L6 Read More 2"),
    ("fixing ol d cars", "fixing old cars", "L6 Read More 3"),
    # 조각이 2글자 이상이라 1차 탐지기가 놓쳤던 것들. 확인지를 눈으로 보다 발견했다.
    # → 탐지기를 믿지 말고 **확인지를 실제로 읽어야 한다**는 뜻이다.
    ("Hangang St ation", "Hangang Station", "L5 대화-1"),
    ("the Br ooklyn Bridge", "the Brooklyn Bridge", "L5 대화-9"),
    ("this Satur day", "this Saturday", "L5 대화-7 (2군데)"),
    ("mak e a special artw ork", "make a special artwork", "L5 Read More 3"),
    ("He mo ves to", "He moves to", "L6 Read More 1"),
    ("helped the K orean", "helped the Korean", "L6 Read More 2"),
    ("of the Mar ch 1st", "of the March 1st", "L6 Read More 2"),
    # 지금까지는 「공백이 끼어든 것」(w as)만 봤다. 그 반대 —「공백이 빠져 붙은 것」도
    # 있다. 자습서 원본에 'telling us that' 과 'telling usthat' 이 둘 다 있는데
    # 추출기가 손상된 쪽을 골랐다. 붙어 있는 것은 눈으로 더 놓치기 쉽다 —
    # 확인지에도 이대로 실렸고 아무도 못 봤다.
    ("telling usthat", "telling us that", "L5 본문 3문단 · 2026-09-07 발견"),
    # 조판이 마지막 줄을 한 번 더 흘렸다. 문장이 아니라 **꼬리 찌꺼기**다.
    ("recommend it. I’m going to introduce today", "recommend it.", "L6 Read More 1"),
]

# 영어는 축약형 아포스트로피 **앞에 공백을 두지 않는다.** 그러니 'I ’m' / 'it ’s' 는
# 무조건 조판 파손이다. 예외가 없으므로 표에 넣지 않고 규칙으로 처리한다.
_APOS_GAP = re.compile(r"(\w)\s+([’'](?:s|m|re|ve|ll|d|t)\b)")


def pages(path):
    return [(p.extract_text() or "") for p in pypdf.PdfReader(path).pages]


def norm(s):
    s = re.sub(r"\s+([,.?!;:])", r"\1", s)
    s = re.sub(r"(\b(?:Dr|Mr|Mrs|Ms|St|Mt)\.)(?=[A-Z])", r"\1 ", s)
    # 공백을 먼저 접는다. 파손 자리에 줄바꿈이 끼어 있으면 아래 표가 안 맞는다 —
    # 'his l\nove' 는 'his l ove' 로 접힌 뒤에야 걸린다.
    s = re.sub(r"\s+", " ", s)
    for wrong, right, _ in CONFIRMED_FIXES:
        s = s.replace(wrong, right)
    s = _APOS_GAP.sub(r"\1\2", s)
    return s.strip()


# 자습서는 블록 끝에 **어휘 표제어**를 흘려 놓는다 — 'Teen’s Science. all kinds of ~'
# 의 'all kinds of ~' 처럼. 지문이 아니라 옆단 표제어인데 문자층에서는 이어져 나온다.
# 마지막 문장부호 뒤에 남은 것은 지문이 아니라고 본다. 무엇을 버렸는지는 기록한다 —
# 조용히 버리면 진짜 문장을 잘라도 아무도 모른다.
_LAST_END = re.compile(r"[.!?][”\"'’]*(?=\s|$)")


def drop_tail(s):
    """마지막 문장부호 뒤의 찌꺼기를 떼고 (본문, 버린 것) 을 돌려준다.

    한 가지를 더 본다: 조판이 **첫머리를 끝에 한 번 더 흘리는** 경우가 있다
    ('… wrote an article about it. Frank W.'). 마지막 조각이 글의 첫머리와 같으면
    그건 문장이 아니라 메아리다. 「첫머리와 같을 때만」으로 좁힌 이유는, 짧은 끝문장
    ('It’s really good.') 을 잘못 버리지 않기 위해서다.
    """
    start, dropped = s, []
    while True:
        ends = list(_LAST_END.finditer(s))
        if not ends:
            break
        tail = s[ends[-1].end():].strip()
        if tail:                              # 문장부호 뒤에 남은 것 = 표제어
            dropped.append(tail)
            s = s[:ends[-1].end()]
            continue
        if len(ends) >= 2:                    # 첫머리가 끝에 한 번 더 흐른 경우
            last = s[ends[-2].end():].strip()
            if last and len(last) < len(start) / 2 and start.startswith(last):
                dropped.append(last)
                s = s[:ends[-2].end()]
                continue
        break
    return s.strip(), " ".join(dropped).strip()


# 목록 지문의 번호. '1. Nick Priest saw…' 의 '1.' 은 문장이 아니라 항목 번호다.
# 그대로 두면 문장 분리기가 '1.' 을 한 문장으로 세어 번호가 통째로 밀린다.
_LIST_NO = re.compile(r"(?:(?<=^)|(?<=\s))(?:\d{1,2}\.|[•▪·])\s+(?=[A-Z])")

# 「Think and Write」는 제목이 본문 첫 줄에 붙어 나온다. 제목은 지문이 아니다 —
# 붙여 두면 첫 문장이 'Kim Mandeok and Her Selfless Love Kim Mandeok was born…' 이 된다.
HEADINGS = {
    ("Think and Write", 96): "The Red Room by Henri Matisse",
    ("Think and Write", 114): "Kim Mandeok and Her Selfless Love",
}

# ── 자습서 표제어 수확 ────────────────────────────────────────────
# 자습서는 대화 옆단에 **핵심 표현·어휘**를 단다. 문자층에서는 본문에 이어져
# 나오는데, 2026-09-06 까지는 이걸 「꼬리 찌꺼기」로 버리고 있었다.
# 원장 지적: 「~ 라는 것은 거기에 장소 이름을 넣으라는 표식이야.」
# 찌꺼기가 아니라 **대표 문형**이다. 버리지 않고 자리를 옮긴다.
#
#   '~' 가 있으면  → 패턴 (슬롯 있음).  'How can I get to ~?'
#   없으면         → 어휘 표제어.        'usually' 'favorite'
#
# 슬롯 이름은 **규칙 표로만** 붙인다. 기능에서 추론하면 틀린다 —
# 'all kinds of ~' 의 자리는 장소가 아니라 명사다. 표에 없으면 이름을 비우고
# 화면에 찍어서 원장이 채우게 한다. 모르는 것을 아는 척하지 않는다.
SLOT_RULES = [
    (re.compile(r"\bget to ~"), "장소"),
    (re.compile(r"\bway to ~"), "장소"),
    (re.compile(r"\ball kinds of ~"), "명사"),
    (re.compile(r"\bkinds? of ~"), "명사"),
]


def harvest(raw, body):
    """떼어낸 표제어를 **패턴**과 **어휘**로 나눈다.

    ── 판정 기준 ──
      '~' 가 있다        → 대표 문형 (자리표시가 있는 틀)
      소문자로 시작한다  → 어휘 표제어
      그 밖              → 버린다

    **「본문에 나오는가」로는 못 가른다.** 처음에 그렇게 짜 봤는데 어휘가 전부
    버려졌다 — 표제어는 당연히 본문에 나온다. 그게 표제어인 이유다.

    가르는 것은 **대문자로 시작하는가**다. 자습서의 어휘 표제어는 사전 표제형이라
    소문자로 시작한다(usually · favorite · a little). 대문자로 시작하는 것은
    등장인물 이름이거나(Henri Matisse · Nick Priest · Schofield) 잘린 조판
    조각이다(「A or B」 「Which is +」). 어느 쪽도 어휘 드릴의 재료가 아니다.
    """
    pats, vocab, junk = [], [], []
    for piece in re.split(r"\s*[「」]\s*", raw):
        piece = piece.strip(" ·•‘’\"'")
        if not piece:
            continue
        if "~" in piece:
            text, slot = to_slot(piece)
            pats.append({"pattern": text, "slot": slot})
        elif re.fullmatch(r"[a-z][A-Za-z' -]{1,28}", piece):
            vocab.append(piece)
        else:
            junk.append(piece)
    return pats, vocab, junk


def to_slot(pattern):
    """'How can I get to ~?' → ('How can I get to {장소}?', '장소')"""
    for rx, name in SLOT_RULES:
        if rx.search(pattern):
            return pattern.replace("~", "{" + name + "}"), name
    return pattern.replace("~", "{빈칸}"), None


# 대표 문형은 물음표로 끝나기도 해서 drop_tail 이 못 잡는다.
# 마지막 문장에 '~' 가 있으면 그건 본문이 아니라 표제 문형이다 —
# 영어 원문에 '~' 는 나오지 않는다.
def split_pattern_tail(text):
    """(본문, 떼어낸 표제 문형 또는 None)"""
    parts = list(_LAST_END.finditer(text))
    if "~" not in text:
        return text, None
    if not parts:
        return "", text.strip()
    for i, m in enumerate(parts):
        seg_start = parts[i - 1].end() if i else 0
        seg = text[seg_start:m.end()].strip()
        if "~" in seg:
            return (text[:seg_start] + text[m.end():]).strip(), seg
    return text, None


SPLIT_WORD = re.compile(r"(?<![’'\w])(?![aAI]\b)([a-zA-Z]) ([a-z]{2,})")


def suspect(s):
    return [f"{m.group(1)} {m.group(2)}" for m in SPLIT_WORD.finditer(s)]


# 기능 판정용 열쇠 표현. 핵심노트의 대표 문형에서 뽑았다.
FUNC_KEYS = {
    "교통수단": ["how can i get to", "how do i get to", "best way to get",
                 "you can get there", "you can take", "which line"],
    "소요 시간": ["how long will it take", "how long does it take", "it'll take",
                 "it will take", "it takes about"],
    "종류": ["what kind", "what kinds", "i like", "i usually"],
    "추천": ["can you recommend", "i recommend", "how about", "you should try"],
}


def functions_in(text, funcs):
    """이 대화에 **어떤 기능들이 들어 있는지** 전부 찾는다.

    하나를 고르지 않는다 — 한 대화가 기능 둘을 같이 쓰는 게 정상이기 때문이다.
    L5 는 「How can I get to ~?」와 「How long will it take?」가 거의 항상 같이 나온다.
    """
    low = text.lower()
    out = []
    for f in funcs:
        keys = next((v for k, v in FUNC_KEYS.items() if k in f), [])
        if any(k in low for k in keys):
            out.append(f)
    return out


def functions(pgs):
    """단원의 의사소통 기능 2개. 핵심노트 쪽에 실려 있다."""
    text = re.sub(r"\s+", " ", " ".join(pgs[2:4]))
    seen, out = set(), []
    for m in FUNC.finditer(text):
        f = m.group(1).strip()
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out[:2]


def blocks(pgs):
    """대화·More 블록을 (제목, 교과서쪽, 본문텍스트) 로 자른다."""
    found = []
    for t in pgs:
        marks = list(BLOCK.finditer(t))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(t)
            found.append({"name": m.group(1).strip(), "page": int(m.group(2)),
                          "raw": t[m.end():end]})
    return found


def turns_of(raw):
    """블록에서 화자 발화를 뽑는다. 한글 설명이 시작되면 거기서 끊는다."""
    seg = raw
    cut = re.search(r"[①-⓿❶-➓]\s*[가-힣]", seg)
    if cut:
        seg = seg[:cut.start()]
    seg = MARKER.sub(" ", seg)
    first = re.search(r"[A-Z][A-Za-z]{0,8}:\s", seg)
    if not first:
        return [], ""
    seg = re.sub(r"\s+", " ", seg[first.start():]).strip()
    if HANGUL.search(seg):
        seg = seg[:HANGUL.search(seg).start()]
    out = []
    for piece in TURN_SPLIT.split(seg):
        m = re.match(r"([A-Z][A-Za-z]{0,8}):\s*(.+)", piece.strip(), re.S)
        if m:
            out.append((m.group(1), norm(m.group(2))))
    tail = ""
    # 마지막 발화가 문장부호로 끝나지 않으면 발화가 아니다 — 옆단 표제어가 화자 표시를
    # 하나 더 만들어 낸 것이다 ('A: Schofield'). 발화째로 버린다.
    while out and not _LAST_END.search(out[-1][1]):
        tail = (out.pop()[1] + " " + tail).strip()
    if out:                                   # 마지막 발화 뒤의 어휘 표제어를 뗀다
        sp, tx = out[-1]
        tx, more = drop_tail(tx)
        # 대표 문형은 물음표로 끝나 drop_tail 을 빠져나간다. 따로 뗀다.
        tx, pat = split_pattern_tail(tx)
        out[-1] = (sp, tx)
        tail = " ".join(x for x in (more, pat, tail) if x).strip()
    return out, tail


def prose_of(raw, heading=""):
    """대화가 아닌 More 지문(Speak Up, Think and Write 등)의 영문 산문.

    돌려주는 것: (본문, 버린 꼬리). 꼬리는 확인지에 띄워 눈으로 보게 한다.
    """
    seg = raw
    cut = re.search(r"[①-⓿❶-➓]\s*[가-힣]", seg)
    if cut:
        seg = seg[:cut.start()]
    seg = MARKER.sub(" ", seg)
    h = HANGUL.search(seg)
    if h:
        seg = seg[:h.start()]
    seg = norm(seg)
    if heading and seg.startswith(heading):
        seg = seg[len(heading):].lstrip()
    seg = _LIST_NO.sub("", seg)
    seg, tail = drop_tail(seg)
    return (seg, tail) if len(seg.split()) >= 12 else ("", tail)


def reading(plus_pdf):
    """본문은 **「내용정리 플러스」**에서 가져온다.

    자습서(L5.pdf)의 Reading 쪽은 구문분석이 본문 위에 겹쳐 조판돼 있어 추출하면
    글자가 깨진다 — "well-kno wn" "giv e" "o ver" "dot s". 문장도 줄바꿈에서 잘린다.
    「내용정리 플러스」의 문장별 분석 블록은 온전하므로 그쪽을 쓴다.
    (extract_textbook.py 가 이미 검증한 경로 — 기출 원문과 5/5 대조 완료.)

    반환: [(문단번호, {문장번호: 문장})] — 부교재의 ❶❷❸❹ 가 곧 문단이다.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ext", os.path.join(ROOT, "tools", "extract_textbook.py"))
    ext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ext)
    pgs = ext.page_texts(plus_pdf)
    marks = [i for i, t in enumerate(pgs) for _ in ext.TITLE.finditer(t)]
    out = []
    for i, pg in enumerate(marks):
        hi = marks[i + 1] if i + 1 < len(marks) else len(pgs)
        sents = ext.parse_clean_blocks(pgs, pg, hi)
        # 본문도 정정 표를 태운다. 2026-09-07 까지 이 경로만 norm() 을 안 거쳤고,
        # 그래서 'telling usthat' 이 CONFIRMED_FIXES 에 있는데도 안 고쳐졌다.
        # 정정 표는 **모든 경로**가 타야 한다 — 한 곳만 빠지면 그 곳만 조용히 틀린다.
        sents = {k: norm(v) for k, v in sents.items()}
        if sents:
            out.append((i + 1, sents))
    return out


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def make(lesson, kind, title, body, src, extra=None):
    slug = re.sub(r"[^0-9A-Za-z가-힣]", "", title)[:48]
    d = {
        "passage_id": f"L{lesson}_{slug}",
        "kind": kind,
        "title": title,
        "textbook": {"publisher": "동아", "author": "윤정미",
                     "curriculum_version": "2022개정", "grade": 2},
        "textbook_unit": f"Lesson {lesson}",
        "source_type": "교과서",
        "body_text": body,
        "body_text_sha256": sha(body),
        "word_count": len(body.split()),
        "transcription": {"status": "pending", "method": "workbook_pdf_text_layer",
                          "source_file": src, "has_handwriting": False,
                          "has_cutoff": False, "unreadable_spans": [],
                          "suspect_split_words": suspect(body)},
        "distribution_scope": "internal_only",
        "_copyright": "출판사 부가자료에서 추출. 기획서 §6.6 — 학원 내부 지도용.",
    }
    d.update(extra or {})
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", type=int, required=True)
    ap.add_argument("--workbook", required=True, help="자습서 PDF (L5.pdf / l6.pdf)")
    ap.add_argument("--plus", help="「내용정리 플러스」 PDF — 본문은 여기서 가져온다")
    ap.add_argument("--reading-title", help="본문 제목 (예: Street Art in London)")
    ap.add_argument("--out", default=OUT,
                    help="저장 위치 (기본: data/stage0/passages). 확정된 파일을 "
                         "덮어쓰지 않으려면 임시 폴더를 준다")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    pgs = pages(args.workbook)
    src = os.path.basename(args.workbook)
    funcs = functions(pgs)
    blks = blocks(pgs)
    paras = reading(args.plus) if args.plus else []

    print("=" * 74)
    print(f" Lesson {args.lesson} 정리 — {src}")
    print("=" * 74)
    print(f"  의사소통 기능: {' / '.join(funcs) if funcs else '(못 찾음)'}")

    docs = []

    # ── 1. 대화문 ────────────────────────────────────────────────
    print(f"\n【지문종류 1 — 대화문】")
    dropped = []            # 어느 쪽도 아닌 조판 부스러기
    harvested = []          # 수확한 대표 문형·어휘
    dlg = [(b, *turns_of(b["raw"])) for b in blks]
    dlg = [(b, t, tail) for b, t, tail in dlg if len(t) >= 2]  # 화자 교대가 있어야 대화문
    # 이름은 **순번**, 기능은 **속성**으로만 기록한다 (원장 지정 2026-09-05).
    # 거의 모든 대화가 두 기능을 한 세트로 쓴다 — L5 는 「어떻게 가나요?」와
    # 「얼마나 걸려요?」가 같은 대화에 같이 나온다. 기능으로 이름을 나누면 억지가
    # 되고, 속성으로 두면 나중에 「이 기능만 연습」으로 골라 쓸 수 있다.
    for i, (b, turns, tail) in enumerate(dlg, 1):
        text = " ".join(l for _, l in turns)
        fs = functions_in(text, funcs)
        name = f"L{args.lesson} 대화-{i}"
        pats, vocab, junk = harvest(tail, text)   # text = 발화를 이어붙인 것
        if junk:
            dropped.append((name, " · ".join(junk)))
        harvested.append((name, pats, vocab))
        body = "\n".join(f"{s}: {l}" for s, l in turns)
        print(f"   {i:>2}. {name:10} {b['name']:22} 교과서{b['page']}쪽 · 발화 {len(turns):>2}"
              f"   [{' + '.join(fs) if fs else '기능 미판정'}]")
        docs.append(make(args.lesson, "textbook_dialogue", name, body, src,
                         {"functions": fs, "block": b["name"],
                          "textbook_page": b["page"],
                          # 자습서 옆단의 대표 문형·어휘. 지문이 아니므로 body_text 에
                          # 넣지 않고 속성으로 둔다. 드릴을 만들 때 여기서 꺼내 쓴다.
                          "key_expressions": pats,
                          "vocab_headwords": vocab,
                          "turns": [{"no": j, "speaker": s, "text": l}
                                    for j, (s, l) in enumerate(turns, 1)]}))

    # ── 2. 본문 ──────────────────────────────────────────────────
    rt = args.reading_title or "(제목 미정)"
    print(f"\n【지문종류 2 — 본문】  제목: {rt}  문단 {len(paras)}개")
    for pno, sents in paras:
        body = " ".join(sents[n] for n in sorted(sents))
        name = f"{rt}-{pno}"
        print(f"   {name}  ·  문장 {len(sents)} · {len(body.split())}단어")
        print(f"      {body[:100]}…")
        if args.reading_title:
            docs.append(make(args.lesson, "textbook_reading", name, body,
                             os.path.basename(args.plus),
                             {"reading_title": rt, "part_no": pno,
                              "sentence_count": len(sents)}))

    # ── 3. Read More ─────────────────────────────────────────────
    print(f"\n【지문종류 3 — Read More (교과서 추가자료)】")
    k = 0
    for b in blks:
        if any(b is bb for bb, _, _ in dlg):
            continue
        heading = HEADINGS.get((b["name"], b["page"]), "")
        prose, tail = prose_of(b["raw"], heading)
        if not prose:
            continue
        k += 1
        name = f"지문 {k}"
        pats, vocab, junk = harvest(tail, prose)
        if junk:
            dropped.append((f"ReadMore-{k}", " · ".join(junk)))
        if pats or vocab:
            harvested.append((f"ReadMore-{k}", pats, vocab))
        print(f"   {k}. {name:8} {b['name']:22} 교과서{b['page']}쪽 · {len(prose.split())}단어"
              f"{'  · 제목 「' + heading + '」' if heading else ''}")
        print(f"      {prose[:90]}")
        docs.append(make(args.lesson, "textbook_reading", f"ReadMore-{k}", prose, src,
                         {"read_more_no": k, "block": b["name"], "heading": heading,
                          "textbook_page": b["page"],
                          "key_expressions": pats, "vocab_headwords": vocab}))

    pat_n = sum(len(p) for _, p, _ in harvested)
    voc_n = sum(len(v) for _, _, v in harvested)
    if harvested:
        print(f"\n【수확한 표제어 — 대표 문형 {pat_n} · 어휘 {voc_n}】")
        print("   자습서 옆단 항목이다. 지문이 아니므로 body_text 에는 넣지 않고")
        print("   key_expressions / vocab_headwords 속성으로 담는다.")
        for name, pats_, vocab_ in harvested:
            for x in pats_:
                mark = "" if x["slot"] else "   ← 슬롯 이름 미정. 원장 확인 요망"
                print(f"   {name:14} 문형  {x['pattern']}{mark}")
            for w in vocab_:
                print(f"   {name:14} 어휘  {w}")
    if dropped:
        print(f"\n【버린 조판 부스러기 {len(dropped)}개】")
        for name, tail in dropped:
            print(f"   {name:14} ← {tail!r}")

    print("\n" + "=" * 74)
    print(f"  대화문 {len(dlg)} · 본문 {len(paras)}문단 · Read More {k}")
    print(f"  대표 문형 {pat_n} · 어휘 표제어 {voc_n} · 버린 부스러기 {len(dropped)}")
    if not args.write:
        print("  저장하려면 --write")
        return 0
    os.makedirs(args.out, exist_ok=True)
    for d in docs:
        p = os.path.join(args.out, d["passage_id"] + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(f"  {len(docs)}개 저장 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
