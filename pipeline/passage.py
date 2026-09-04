# -*- coding: utf-8 -*-
"""
문장 분리와 스팬 해석.

**스팬은 모델이 아니라 여기서 만든다.** 모델은 `surface`(원문 그대로의 문자열)만 내고,
그게 body_text 어디에 있는지는 파이썬이 찾는다. 이유는 두 가지다:

  · LLM 의 문자 오프셋은 조용히 한두 칸씩 밀린다. 이 프로젝트에서 그건 가장 잡기 어려운
    버그다 — 태깅이 그럴듯한 채로 전부 어긋난다 (설계원칙 7).
  · 부수 효과로 환각 탐지가 공짜로 딸려온다. 지문에 없는 surface 는 여기서 걸린다.
"""
import re

# 닫는 따옴표는 문장부호 뒤에 온다: like a “virus.”  ← 여기서도 끊어야 한다
_SENT_END = re.compile(r"[.!?]+[”\"'’]*(?=\s|$)")
# 약어에서 문장을 끊으면 번호가 통째로 밀린다. 'Mt. Tambora' 가 두 문장이 되면
# 논리 태깅의 sentence_no 와 태그의 sentence_no 가 전부 어긋난다.
# (2026-09-01: Bicycle 이 11문장인데 12문장으로 잡히던 원인이었다.)
ABBREV = ("Mt.", "Dr.", "Mr.", "Mrs.", "Ms.", "St.", "Prof.", "a.m.", "p.m.")
_INITIAL = re.compile(r"\b[A-Z]\.$")          # Frank W. Schofield
# 'Take bus No. 12.' 의 'No.' 는 약어다. 그런데 대화문에서는 'No. I can’t.' 처럼
# 진짜 문장 끝이기도 하다. **뒤에 숫자가 오는지**로 가른다 — 이게 유일한 구분점이다.
# (2026-09-05: L5 대화-3 이 '12.' 를 한 문장으로 세고 있었다. Mt. 때와 같은 부류다.)
_NO_NUM = re.compile(r"\bNo\.$")


def split_sentences(body_text):
    """(sentence_no, start, end, text) 목록. 재조립하면 원문과 정확히 같아야 한다."""
    spans, pos = [], 0
    for m in _SENT_END.finditer(body_text):
        end = m.end()
        head = body_text[:end].rstrip()
        if head.endswith(ABBREV) or _INITIAL.search(head):
            continue                          # 약어·이니셜이었다. 아직 문장이 안 끝났다
        if _NO_NUM.search(head) and re.match(r"\s*\d", body_text[end:]):
            continue                          # 'No. 12' — 번호지 문장 끝이 아니다
        chunk = body_text[pos:end]
        stripped = chunk.strip()
        if stripped:
            offset = len(chunk) - len(chunk.lstrip())
            spans.append((pos + offset, pos + offset + len(stripped), stripped))
        pos = end
    tail = body_text[pos:].strip()
    if tail:
        offset = body_text[pos:].index(tail)
        spans.append((pos + offset, pos + offset + len(tail), tail))
    return [(i, s, e, t) for i, (s, e, t) in enumerate(spans, 1)]


def sentences_only(body_text):
    return [t for _, _, _, t in split_sentences(body_text)]


def verify_split(body_text):
    """분리가 원문을 왜곡하지 않았는지. 문장 텍스트가 전부 원문의 부분문자열이어야 한다."""
    problems = []
    for no, s, e, t in split_sentences(body_text):
        if body_text[s:e] != t:
            problems.append(f"문장 {no}: 스팬이 텍스트와 불일치")
    return problems


class SpanResolver:
    """surface 를 body_text 안의 (start, end) 로 바꾼다. 못 찾으면 이유를 남기고 버린다."""

    def __init__(self, body_text):
        self.body = body_text
        self.sentences = split_sentences(body_text)
        self.by_no = {no: (s, e) for no, s, e, _ in self.sentences}
        self.rejects = []

    def resolve(self, surface, sentence_no, where):
        if not surface or not surface.strip():
            self.rejects.append((where, "surface 가 비어 있음", surface))
            return None
        # 1. 지정된 문장 안에서 먼저 찾는다 — 같은 표현이 여러 번 나올 때 이게 판별한다
        if sentence_no in self.by_no:
            s, e = self.by_no[sentence_no]
            idx = self.body.find(surface, s, e)
            if idx >= 0:
                return idx, idx + len(surface)
        # 2. 문장 번호가 틀렸을 수 있으니 전체에서 찾는다. 단 유일할 때만 인정.
        first = self.body.find(surface)
        if first < 0:
            self.rejects.append((where, "지문에 없는 문자열 (환각)", surface))
            return None
        if self.body.find(surface, first + 1) >= 0:
            self.rejects.append(
                (where, f"문장 {sentence_no} 안에 없고 지문 전체에는 여러 번 나옴 — 위치 확정 불가", surface))
            return None
        return first, first + len(surface)

    def sentence_of(self, start):
        for no, s, e, _ in self.sentences:
            if s <= start < e:
                return no
        return None
