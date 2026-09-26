# -*- coding: utf-8 -*-
"""
특급기출 본책 PDF → passage JSON (대화문 · 본문).

  python tools/extract_teukgeup.py "Z:/…/특급기출 … 5과 추출.pdf" --grade 1 --lesson 5
  python tools/extract_teukgeup.py … --write

중2 는 「내용정리 플러스」(extract_textbook.py)에서 뽑았다. 중1 은 원장이 특급기출을
줬다 — 글자가 다 살아 있고, 단원마다 두 쪽이 쓸 만하다:

  「주요 표현 · 구문 해설」 / 「STEP A Listening & Speaking」   대화문 전문 + 교과서 쪽수
  「주요 문장」 / 「STEP A Reading」                            본문이 번호 매긴 문장으로

같은 단원에 「해석」 쪽도 있는데 그건 **빈칸 학습지**라 영어가 뚫려 있다. 안 쓴다.

## 걷어내는 것

대화·본문 안에 해설 번호 ➊➋➌ 가 박혀 있다 (`You ➍play the guitar`). 떼면 원문이다.
발화·문장이 줄바꿈으로 감겨 있다 (`talk on the phone \\nhere.`) — 다음 화자·번호가
나올 때까지 이어 붙인다.

## 중2 와 부딪히지 않게

동형 생성기(make_mock_exam.gather)가 지문을 **제목**으로 찾는다. 중2 에 이미
'L5 대화-1' 이 있으므로 중1 은 '중1 L5 대화-1' 로 학년을 붙인다. passage_id 도 같다.

## 그래도 확정은 사람이 한다

status 는 'pending'. make_review_sheet.py 로 확인지를 만들어 원장이 영어만 대조한다.
텍스트 레이어라 오독은 없지만, **빠진 대화·문장**은 기계가 모른다.
"""
import argparse
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
MARK = re.compile(r"[➊-➓]")
SPEAKER = re.compile(r"^([A-Z]{1,2}):\s*(.*)$")
BLOCK = re.compile(r"^(Watch and Talk [A-Z](?:-\d)?|Talk and Play|Review-\d|"
                   r"Everyday Communication(?: \d)?|Communication Task|Listen and Talk .*)\s*$")
PAGE_REF = re.compile(r"^교과서\s*(\d+)쪽")
NUMBERED = re.compile(r"^(\d{2})\t\s*(.*)$")
HANGUL = re.compile(r"[가-힣]")


def clean(s):
    s = MARK.sub("", s)
    return " ".join(s.split()).strip()


def dialogues(pages, lesson):
    """대화문 블록 → [(block, page_no, turns)]"""
    out, seen = [], set()
    for text in pages:
        if "주요 표현" not in text and "Listening & Speaking" not in text:
            continue
        lines = [l.rstrip() for l in text.splitlines()]
        i = 0
        while i < len(lines):
            m = BLOCK.match(lines[i].strip())
            if not m:
                i += 1
                continue
            block, page_no, turns = m.group(1), None, []
            i += 1
            if i < len(lines) and PAGE_REF.match(lines[i].strip()):
                page_no = int(PAGE_REF.match(lines[i].strip()).group(1))
                i += 1
            while i < len(lines):
                s = lines[i].strip()
                # 해설 줄은 '➊ look over는 …' 처럼 번호 뒤에 우리말이 온다.
                # '➋by Van Gogh.' 는 번호로 시작해도 감긴 발화의 뒷부분이다.
                if (BLOCK.match(s) or (MARK.match(s) and HANGUL.search(s))
                        or re.match(r"^Q\d", s) or PAGE_REF.match(s)):
                    break
                sm = SPEAKER.match(s)
                if sm:
                    turns.append([sm.group(1), clean(sm.group(2))])
                elif turns and s and not HANGUL.search(s):
                    turns[-1][1] = clean(turns[-1][1] + " " + s)
                i += 1
            # 원장이 같은 쪽을 두 번 넣기도 한다 (7과: 3~5쪽 = 6~8쪽). 같은 대화는 한 번만.
            if turns and (block, page_no, tuple(map(tuple, turns))) not in seen:
                seen.add((block, page_no, tuple(map(tuple, turns))))
                out.append((block, page_no, turns))
    return out


def reading(pages):
    """본문 → (title, [sentences])"""
    # 번호는 **오르기만 한다.** 번호가 되돌아가면 다른 구간이 시작된 것이므로 거기서 끊는다.
    # 2026-09-26: 1학기 본책을 단원 구간(182~236쪽)으로 읽었더니 「주요 문장」 뒤에 오는
    # 괄호 선택 학습지까지 같은 `NN	` 번호를 달고 있어 본문 끝에 붙었다 —
    # 'I'm especially looking forward to ( visit / visiting )' · 'Answers p. 47'.
    # 정렬만 하면 조용히 섞여서 body_text 가 오염된다. 설계원칙 7 상 확정 뒤엔 못 고친다.
    title, sents, last_no, stop = None, [], 0, False
    for text in pages:
        if stop:
            break
        if "주요 문장" not in text and "STEP A   Reading" not in text:
            continue
        lines = [l.rstrip() for l in text.splitlines()]
        if title is None:
            for k, l in enumerate(lines):
                if re.search(r"Lesson \d", l) and k + 1 < len(lines):   # '144	 Lesson 7 …' 도
                    title = lines[k + 1].strip()
                    break
        cur = None
        for l in lines:
            s = l.strip()
            nm = NUMBERED.match(l)
            if nm:
                if HANGUL.search(nm.group(2)):
                    cur = None                  # 우리말 해석 구간에 들어왔다
                    continue
                no = int(nm.group(1))
                if no <= last_no:
                    stop = True
                    break
                last_no = no
                cur = [no, clean(nm.group(2))]
                sents.append(cur)
            elif cur and s and not HANGUL.search(s) and not re.match(r"^[A-Z]\s*$|^STEP|^\d+\s*$", s):
                cur[1] = clean(cur[1] + " " + s)
            else:
                cur = None
    sents.sort(key=lambda x: x[0])
    return title, [t for _, t in sents]


def record(pid, kind, title, body, grade, lesson, src, extra):
    d = {
        "passage_id": pid, "kind": kind, "title": title,
        "textbook": {"publisher": "동아", "author": "윤정미",
                     "curriculum_version": "2022개정", "grade": grade},
        "textbook_unit": f"Lesson {lesson}", "source_type": "교과서",
        "body_text": body,
        "body_text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "word_count": len(re.findall(r"[A-Za-z][A-Za-z'’-]*", body)),
        "transcription": {
            "status": "pending", "method": "workbook_pdf_text_layer",
            "source_file": os.path.basename(src),
            "note": "특급기출 본책의 「주요 표현·구문 해설」(대화) · 「주요 문장」(본문) 쪽에서 추출. "
                    "해설 번호 ➊➋ 를 떼고 감긴 줄을 이었다. 텍스트 레이어라 오독은 없으나 "
                    "빠진 대화·문장은 기계가 모른다 — 원장 대조 필요.",
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
    ap.add_argument("pdf")
    ap.add_argument("--grade", type=int, required=True)
    ap.add_argument("--lesson", type=int, required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pages", help=(
        "읽을 쪽 구간 'A-B' (1부터, 양끝 포함). 특급기출 **1학기 본책**처럼 한 권에 "
        "네 단원이 다 들어 있는 파일은 이것을 주지 않으면 책 전체를 한 단원으로 긁는다. "
        "2026-09-26 에 1-1 본책으로 실제로 그랬다 — 대화 39편에 교과서 12~62쪽이 섞여 나왔다. "
        "단원 구간은 tools/teukgeup_lessons.py 로 찾는다."))
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    pages = [p.get_text() for p in doc]
    if a.pages:
        lo, hi = (int(x) for x in a.pages.split("-"))
        pages = ["" if not (lo <= i <= hi) else t for i, t in enumerate(pages, 1)]
        print(f"   [쪽 구간] {lo}~{hi} 만 읽는다 (전체 {len(doc)}쪽)")
    G, L = f"중{a.grade}", a.lesson
    recs = []

    for n, (block, page_no, turns) in enumerate(dialogues(pages, L), 1):
        body = "\n".join(f"{sp}: {tx}" for sp, tx in turns)
        recs.append(record(
            f"{G}L{L}_대화{n}", "textbook_dialogue", f"{G} L{L} 대화-{n}", body,
            a.grade, L, a.pdf,
            {"block": block, "textbook_page": page_no,
             "turns": [{"no": i, "speaker": sp, "text": tx} for i, (sp, tx) in enumerate(turns, 1)],
             "functions": [], "key_expressions": [], "vocab_headwords": []}))

    title, sents = reading(pages)
    if sents:
        body = " ".join(sents)
        recs.append(record(
            f"{G}L{L}_본문", "textbook_reading", f"{G} L{L} 본문 — {title}", body,
            a.grade, L, a.pdf,
            {"reading_title": title, "sentence_count": len(sents)}))

    print(f"■ {os.path.basename(a.pdf)} — {G} Lesson {L}")
    for r in recs:
        n = len(r.get("turns") or []) or r.get("sentence_count")
        unit = "발화" if r.get("turns") else "문장"
        meta = f"{r.get('block','')} · 교과서 {r.get('textbook_page','?')}쪽" if r.get("turns") else r.get("reading_title")
        print(f"   {r['title']:<42} {unit} {n:>2} · 단어 {r['word_count']:>3}   {meta}")
    # 본문 문장 수와 split_sentences 가 세는 수가 다르면 확인지 번호가 어긋난다
    if sents:
        got = len(split_sentences(body))
        if got != len(sents):
            print(f"   · 책 번호 {len(sents)}문장 vs 분리기 {got}문장 — 마침표 없는 제목줄"
                  f"('Ann Jones, a visitor')이 다음 문장에 붙는다. 확인지 번호는 분리기 기준.")

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
