# -*- coding: utf-8 -*-
"""
자습서 「Words 만점 노트」에서 단원 어휘를 뽑는다.

  python tools/extract_vocab.py --lesson 5 --workbook "C:/…/L5.pdf"
  python tools/extract_vocab.py --lesson 5 --workbook "…" --write

## 왜 필요한가

4개교 2026-1 기말에서 **영영풀이 문항이 35점**이었다 (영덕 8 · 영일 6 · 청명 9 ·
태장 12). 원장이 정한 1층 드릴 c(어휘·영영뜻)의 재료가 이것인데, 지금까지는
자습서 옆단에서 딸려 온 표제어 3개가 전부였다.

원장이 이미지를 보여준 뒤 확인해 보니 **자습서 PDF 1·2쪽에 텍스트로 다 있었다.**
1쪽은 섹션별 단어와 한국어 뜻, 2쪽은 영영풀이와 파생어다. 눈으로 옮길 것이 아니라
문자로 읽으면 된다 — `extract_textbook.py` 와 같은 판단이다.

## 스키마는 아직 만들지 않는다

`CLAUDE.md` 6번 — 「스키마는 JSON이 굳은 뒤에」. 먼저 JSON 으로 뽑아 무엇이
들어오는지 보고, 모양이 굳으면 그때 테이블을 만든다.
"""
import argparse
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
OUT = os.path.join(ROOT, "data", "stage0", "vocab")

# 자습서가 쓰는 섹션 이름. 내 지문 분류와 그대로 이어진다 —
# Watch and Talk·Talk and Play 는 대화문, Reading 은 본문, 나머지는 Read More.
SECTIONS = ["Watch and Talk", "Talk and Play", "Reading", "Language in Use",
            "Think and Write & Culture Project", "Review"]
POS = "명동형부대전접"
# ' anyway  부  그런데, 어쨌든'  /  ' bridge 명 다리  minute 명 (시간 단위의) 분'
ENTRY = re.compile(rf"([A-Za-z][A-Za-z'’\-]*(?:\s[A-Za-z][A-Za-z'’\-]*)*)\s+([{POS}])\s+")
def split_phrase(line):
    """품사 없는 숙어 줄을 (표제어, 뜻) 으로 가른다.

    정규식으로 표제어 모양을 적기를 포기했다. 실제로 들어오는 꼴이 제각각이다:

        get off (말·차 등에서) 내리다
        at the invitation of ~의 초청으로
        lots〔a lot〕 of 많은
        share A with B A를 B와 공유하다〔함께 쓰다〕      ← 뜻이 'A를' 로 시작한다

    영어 표제어와 한국어 뜻의 경계는 **한글이 섞인 첫 토큰**이다. 그 앞까지가
    표제어다. 'share A with B' 는 뜻이 대문자 A 로 시작해서 「뜻은 한글이나 물결로
    시작한다」는 가정이 깨졌는데, 토큰 기준으로 보면 'A를' 에서 정확히 갈린다.
    """
    toks = line.split()
    for i, t in enumerate(toks):
        if re.search(r"[가-힣]", t):
            if i == 0:
                return None
            return " ".join(toks[:i]), " ".join(toks[i:])
    return None


def pages(path):
    return [(p.extract_text() or "") for p in pypdf.PdfReader(path).pages]


def parse_headword_page(text):
    """1쪽: 섹션별 단어 + 품사 + 한국어 뜻."""
    # 섹션 머리말 위치를 찾아 구간을 자른다. 2단 조판이라 순서가 뒤섞여 나오지만
    # 머리말 자체는 한 줄을 차지하므로 구간 나누기에는 문제가 없다.
    marks = []
    for name in SECTIONS:
        # 머리말이 앞줄 끝에 붙어 나오기도 한다:
        # '* 완벽히 외운 단어는  안에 표 해 봅시다.Watch and Talk'
        # 줄 전체 일치로 찾으면 그 섹션이 통째로 빠진다.
        for m in re.finditer(rf"{re.escape(name)}\s*$", text, re.M):
            marks.append((m.start(), m.end(), name))
    marks.sort()
    out = []
    for i, (s, e, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        for line in text[e:end].split("\n"):
            line = line.strip()
            if not line or "완벽히" in line:
                continue
            hits = list(ENTRY.finditer(line))
            if hits:
                for j, m in enumerate(hits):
                    stop = hits[j + 1].start() if j + 1 < len(hits) else len(line)
                    gloss = line[m.end():stop].strip()
                    # 한 단어에 품사가 둘인 경우: 'volunteer 형 자발적인 명 자원봉사자'
                    # 뜻 안에 남은 품사 표시를 세미콜론으로 바꾸고 품사를 모은다.
                    poss = [m.group(2)] + re.findall(rf"\s([{POS}])\s", gloss)
                    gloss = re.sub(rf"\s([{POS}])\s", "; ", gloss).strip()
                    gloss = gloss.rstrip("* ").strip()   # 파생어 표시가 꼬리에 남는다
                    out.append({"word": " ".join(m.group(1).split()),
                                "pos": "".join(poss),
                                "gloss_ko": gloss,
                                "section": name})
                continue
            p = split_phrase(line)
            if p and re.match(r"^[a-zA-Z]", p[0]):
                out.append({"word": p[0], "pos": None,
                            "gloss_ko": p[1].strip(), "section": name})
    return out


def parse_definition_page(text):
    """2쪽: 영영풀이. ' artwork 예술 작품, 미술품 something made by an artist, …'"""
    defs = {}
    cut = text.find("영영풀이")
    body = text[:cut] if cut > 0 else text
    for line in body.split("\n"):
        line = line.strip()
        # 단어 · 한글뜻 · 영문풀이 순. 한글이 끝나는 지점부터가 영영풀이다.
        m = re.match(r"^([a-zA-Z][A-Za-z'’\- ]*?)\s+([^A-Za-z]*[가-힣][^A-Za-z]*)\s+([a-z].+)$", line)
        if m:
            defs[" ".join(m.group(1).split())] = m.group(3).strip()
    return defs


def parse_derivations(text):
    """2쪽 아래 파생어 표. 'friend(친구) - friendly(친절한)'"""
    out = []
    for m in re.finditer(r"([A-Za-z][A-Za-z'’\-]*)\(([^)]+)\)\s*[-–—]\s*"
                         r"([A-Za-z][A-Za-z'’\-]*)\(([^)]+)\)", text):
        out.append({"base": m.group(1), "base_ko": m.group(2),
                    "derived": m.group(3), "derived_ko": m.group(4)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", type=int, required=True)
    ap.add_argument("--workbook", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    pg = pages(a.workbook)
    words = parse_headword_page(pg[0])
    defs = parse_definition_page(pg[1])
    derivs = parse_derivations(pg[1])

    title = ""
    m = re.search(r"Lesson\s*\d+\s+([A-Z][A-Za-z ,'’]+)", pg[0])
    if m:
        title = m.group(1).strip()

    # 표제형이 두 쪽에서 다를 수 있다: 만점 노트는 'share A with B', 영영풀이 쪽은
    # 'share'. 정확히 맞는 게 없으면 **첫 낱말**로 한 번 더 찾되, 그 낱말이 영영풀이
    # 쪽에서도 한 낱말 표제일 때만 인정한다 — 'be famous for' 의 'be' 로 엉뚱한 데
    # 붙는 것을 막는다. 무엇으로 이었는지는 남긴다.
    for w in words:
        d = defs.get(w["word"])
        how = "표제어" if d else None
        if not d and " " in w["word"]:
            first = w["word"].split()[0]
            if first in defs:
                d, how = defs[first], "첫 낱말"
        w["definition_en"] = d
        w["definition_matched_by"] = how

    print("=" * 74)
    print(f" Lesson {a.lesson} 어휘 — {title}")
    print("=" * 74)
    by_sec = {}
    for w in words:
        by_sec.setdefault(w["section"], []).append(w)
    for name in SECTIONS:
        got = by_sec.get(name, [])
        if not got:
            continue
        n_def = sum(1 for w in got if w["definition_en"])
        print(f"\n  [{name}]  {len(got)}개 · 영영풀이 {n_def}개")
        for w in got:
            d = f"  · {w['definition_en'][:52]}" if w["definition_en"] else ""
            print(f"     {w['word']:22} {w['pos'] or '  '}  {w['gloss_ko'][:22]:24}{d}")

    used = {w["word"] for w in words}
    used |= {w["word"].split()[0] for w in words
             if w.get("definition_matched_by") == "첫 낱말"}
    orphan = sorted(set(defs) - used)
    print(f"\n  단어 {len(words)} · 영영풀이 {sum(1 for w in words if w['definition_en'])} "
          f"· 파생어 {len(derivs)}쌍")
    if orphan:
        print(f"  ! 영영풀이는 있는데 단어 목록에 없는 것: {orphan}")

    if not a.write:
        print("\n  저장하려면 --write")
        return 0
    os.makedirs(OUT, exist_ok=True)
    doc = {"lesson": a.lesson, "unit_title": title,
           "textbook": {"publisher": "동아", "author": "윤정미",
                        "curriculum_version": "2022개정", "grade": 2},
           "source_file": os.path.basename(a.workbook),
           "source_detail": "자습서 「Words 만점 노트」 + Words 영영풀이 쪽",
           "transcription": {"status": "pending", "method": "workbook_pdf_text_layer"},
           "words": words, "derivations": derivs,
           "distribution_scope": "internal_only"}
    p = os.path.join(OUT, f"L{a.lesson}_vocab.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n  저장 → {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
