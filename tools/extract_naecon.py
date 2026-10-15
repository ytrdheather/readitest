# -*- coding: utf-8 -*-
"""
비상(황종배) 중1 → passage JSON (대화문 · 본문). 청명중1 용 (원장 2026-10-16).

  python tools/extract_naecon.py --lesson 5
  python tools/extract_naecon.py --lesson 5 --write

동아(윤정미)는 특급기출 본책에서 뽑았다 (extract_teukgeup.py). 비상은 특급기출이 없어서
두 군데서 나눠 뽑는다 — 둘 다 텍스트 레이어가 살아 있다:

  대화  내신콘서트 중1 2학기 비상황 「LESSON n_DIALOGUES_대화」 해설 쪽
        (Everyday Communication 1·2 의 A1~C · Talk & Play · Wrap Up). 해설 번호 ➊➋ 를 뗀다
  본문  이그잼포유 「본문10단계 워크북 1 본문해석지」 — 왼쪽 영어 / 오른쪽 우리말

## 동아 지문과 부딪히지 않게

동아 중1 에 이미 '중1 L5 대화-1' · passage_id '중1L5_대화1' 이 있다. 비상은 제목에
'비상' 을, id 에 '비상' 을 붙인다 → '중1 L5 비상 대화-1' · '중1L5비상_대화1'.
제목이 '중1 L5' 로 시작하므로 build_school_drills.GRADE_RE 는 그대로 학년·과를 읽는다
— **그래서 그 도구는 교과서로도 거르지 않으면 동아 L5 를 청명에 섞는다.** 드릴을 묶기 전에 막을 것.

## 그래도 확정은 사람이 한다

status 는 'pending'. make_review_sheet.py 로 확인지를 만들어 원장이 영어만 대조한다.
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import sys

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.passage import split_sentences          # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")
NAECON = "Z:/학원파일/수업용 PDF/내신콘서트/중1/내콘 중1 2학기 비상황.pdf"
EXAM4U = "Z:/학원파일/내신자료/중등 내신 대비 교재 정리/1학년/청명중(비상황)/{n}과*/*본문해석지*.pdf"

MARK = re.compile(r"[➊-➓]")
HANGUL = re.compile(r"[가-힣]")
SECTION = re.compile(r"^(Everyday Communication \d|Talk & Play|Wrap Up)\s*$")
SUB = re.compile(r"^([A-C]\d?|\d)\s*$")                 # A1 · C · C3 · (Wrap Up) 1
SPEAKER = re.compile(r"(?:^|\s)([A-Z])\s*:\s*")          # 'M\t: ' · 'M\t:Yes.'


def clean(s):
    return " ".join(MARK.sub("", s).split()).strip()


def dialogues(doc, lesson):
    """[(block, turns)] — turns 는 [(speaker, text)]. 화자가 없으면 독백 하나."""
    # 머리글 'LESSON n_DIALOGUES' 는 홀수 쪽에만 있다. 처음~마지막 그 쪽 사이를 다 읽는다.
    texts = [p.get_text() for p in doc]
    hit = [k for k, t in enumerate(texts) if f"LESSON {lesson}_DIALOGUES" in t]
    pages = texts[hit[0] - 1:hit[-1] + 1] if hit else []
    out, section = [], None
    for text in pages:
        lines = [l.strip() for l in text.splitlines()]
        i = 0
        while i < len(lines):
            s = lines[i]
            if SECTION.match(s):
                section = s
                i += 1
                continue
            if section and SUB.match(s) and i + 1 < len(lines) and not HANGUL.search(lines[i + 1]):
                block, buf = f"{section} {s}" if section != "Talk & Play" else section, []
                i += 1
                # 대화 줄은 우리말 요약 줄(' 서점에서 남자는 …')이 나오기 전까지
                while i < len(lines) and not HANGUL.search(lines[i]) and not SECTION.match(lines[i]):
                    buf.append(lines[i])
                    i += 1
                body = clean(" ".join(buf))
                parts = SPEAKER.split(" " + body)
                if len(parts) > 1:
                    turns = [(parts[k], clean(parts[k + 1])) for k in range(1, len(parts) - 1, 2)]
                else:
                    turns = [("", body)]
                if re.search(r"[A-Za-z]{3}", body):      # 쪽 번호 '021' 이 'Wrap Up 5' 로 잡혔다
                    out.append((block, turns))
                continue
            if section == "Talk & Play" and SPEAKER.match(s) and not HANGUL.search(s):
                # Talk & Play 는 하위 번호 없이 바로 대화가 온다.
                # 우리말 줄은 뒤쪽 문제 쪽('A: (A)너는 무엇에…')이다 — 안 거르면 i 가 안 움직여 멈춘다
                buf = []
                while i < len(lines) and not HANGUL.search(lines[i]):
                    buf.append(lines[i])
                    i += 1
                body = clean(" ".join(buf))
                parts = SPEAKER.split(" " + body)
                out.append((section, [(parts[k], clean(parts[k + 1])) for k in range(1, len(parts) - 1, 2)]))
                continue
            i += 1
    # 같은 대화가 빈칸 연습 쪽에 또 나온다 — 빈칸이라 글자가 빠져 있다. 처음 것만 (해설 쪽)
    seen, uniq = set(), []
    for block, turns in out:
        if block in seen:
            continue
        seen.add(block)
        uniq.append((block, turns))
    return uniq


def reading(path):
    """본문해석지 → (title, [영어 줄]). 왼쪽 단이 영어, 오른쪽 단이 우리말."""
    doc = fitz.open(path)
    title, sents = None, []
    for page in doc:
        words = page.get_text("blocks")
        w = page.rect.width
        for b in sorted(words, key=lambda b: (b[1], b[0])):
            x0, text = b[0], b[4]
            if x0 > w * 0.5:
                continue                         # 오른쪽 단 = 우리말
            for l in text.splitlines():
                s = l.strip()
                if not s or HANGUL.search(s) or re.fullmatch(r"\d+|- \d+ -|Lesson|Lesson \d+", s):
                    continue
                if "LIKEs" in s or (title is None and not sents and not re.search(r"[.!?:”]$", s)):
                    title = title or s
                    continue
                sents.append(s)
    # 감긴 줄 잇기: 앞줄이 문장부호로 안 끝나고 'STEP' 머리줄도 아니면 붙인다
    out = []
    for s in sents:
        if out and not re.search(r"[.!?:”\"]$", out[-1]) and not out[-1].startswith("STEP"):
            out[-1] = clean(out[-1] + " " + s)
        else:
            out.append(clean(s))
    return title, out


def record(pid, kind, title, body, lesson, src, method, note, extra):
    d = {
        "passage_id": pid, "kind": kind, "title": title,
        "textbook": {"publisher": "비상", "author": "황종배",
                     "curriculum_version": "2022개정", "grade": 1},
        "textbook_unit": f"Lesson {lesson}", "source_type": "교과서",
        "body_text": body,
        "body_text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "word_count": len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body)),
        "transcription": {
            "status": "pending", "method": method,
            "source_file": os.path.basename(src), "note": note,
            "has_handwriting": False, "has_cutoff": False, "unreadable_spans": [],
            "needs_review_sentences": [],
        },
        "distribution_scope": "internal_only",
        "_copyright": "출판사 부가자료에서 추출. 기획서 §6.6 — 학원 내부 지도용.",
    }
    d.update(extra)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", type=int, required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    L = a.lesson
    recs = []

    doc = fitz.open(NAECON)
    for n, (block, turns) in enumerate(dialogues(doc, L), 1):
        body = "\n".join(f"{sp}: {tx}" if sp else tx for sp, tx in turns)
        recs.append(record(
            f"중1L{L}비상_대화{n}", "textbook_dialogue", f"중1 L{L} 비상 대화-{n}", body, L, NAECON,
            "workbook_pdf_text_layer",
            "내신콘서트 「DIALOGUES_대화」 해설 쪽에서 추출. 해설 번호 ➊➋ 를 떼고 감긴 줄을 이었다. "
            "텍스트 레이어라 오독은 없으나 빠진 대화는 기계가 모른다 — 원장 대조 필요.",
            {"block": block, "textbook_page": None,
             "turns": [{"no": i, "speaker": sp, "text": tx} for i, (sp, tx) in enumerate(turns, 1)],
             "functions": [], "key_expressions": [], "vocab_headwords": []}))

    src = glob.glob(EXAM4U.format(n=L))
    if src:
        title, sents = reading(src[0])
        body = " ".join(s for s in sents if not s.startswith("STEP"))
        recs.append(record(
            f"중1L{L}비상_본문", "textbook_reading", f"중1 L{L} 비상 본문 — {title}", body, L, src[0],
            "workbook_pdf_text_layer",
            "이그잼포유 본문해석지 왼쪽 단(영어)에서 추출. 'STEP n …' 소제목은 body 에서 빼고 "
            "headings 에 남겼다. 원장 대조 필요.",
            {"reading_title": title, "sentence_count": len(split_sentences(body)),
             "headings": [s for s in sents if s.startswith("STEP")]}))

    print(f"■ 비상(황종배) 중1 Lesson {L}")
    for r in recs:
        n = len(r.get("turns") or []) or r.get("sentence_count")
        unit = "발화" if r.get("turns") else "문장"
        print(f"   {r['title']:<46} {unit} {n:>2} · 단어 {r['word_count']:>3}   {r.get('block', '')}")

    if not a.write:
        print("\n   --write 를 붙이면 data/stage0/passages/ 에 저장합니다 (status=pending).")
        return
    for r in recs:
        p = os.path.join(PASSAGES, r["passage_id"] + ".json")
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(f"\n   {len(recs)}개 저장 → {PASSAGES}")


if __name__ == "__main__":
    sys.exit(main())
