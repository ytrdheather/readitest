# -*- coding: utf-8 -*-
"""
교과서 본문 추출 — 「내용정리 플러스」 PDF → passage JSON.

  python tools/extract_textbook.py "C:/.../3과_[01]내용정리 플러스.pdf" --lesson 3
  python tools/extract_textbook.py ... --lesson 3 --write

## 비전 전사를 쓰지 않는 이유

기획서 §6.2.1은 텍스트 레이어 없는 스캔본을 전제로 이중 전사 + diff 를 설계했다.
이 PDF들은 텍스트 레이어가 있다. 이미 문자로 있는 걸 이미지로 다시 읽는 건 정확도를
올리는 게 아니라 내리는 선택이고 토큰도 쓴다. 스캔본이 오면 그때 §6.2.1 경로를 쓴다.

## 본문이 두 벌로 실려 있다

  ① 상단 'READING 본문❶Bicycle 1Mt. Tambora…'
     2단 조판이라 구문분석 라벨이 본문 사이에 끼어 추출된다:
       "…two wooden wheels but no ‘장소 부사구…’의 어순 \uf000‘하지만’pedals."
     붙어버린 곳도 있다: "enough foodto eat"          ← 손상

  ② 하단 문장별 블록 '3As a result, … to eat.그 결과, …enough+명사❮…❯설명'
     띄어쓰기가 온전하다.                              ← 깨끗

②를 우선 쓴다. 그런데 **②에 없는 문장이 있다** — 부교재가 모든 문장을 분석하진 않는다
(예: Bicycle 8번). 그 문장만 ①에서 복구하고 `needs_review` 로 표시한다.

## 복구를 어떻게 믿는가

①에서 한글·기호를 걷어내는 복구 함수를, **②로 이미 정답을 아는 문장들에 먼저 돌려본다.**
그 문장들에서 복구 결과가 ②와 글자 단위로 일치하면, 같은 함수가 ②에 없는 문장에
대해서도 동작한다고 볼 근거가 된다. 일치하지 않으면 복구를 신뢰하지 않고 사람에게 넘긴다.

## 그래도 확정은 사람이 한다

`transcription.status` 는 'pending' 으로 저장된다. body_text 는 확정 후 불변이므로
(설계원칙 7) 여기서 틀리면 뒤의 모든 span 이 어긋난 채 그럴듯하게 작동한다.
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

STRUCT = "\u276e"          # ❮ — 문장별 분석 블록에만 나온다
HANGUL = re.compile(r"[가-힣]")
# 제목이 없는 본문도 있다 (L4 도입부, L5 전부). 표시만 있고 바로 '1문장' 이 온다.
# 'READING본문│빈칸 완성 … 정답' 은 뒤쪽 정답 섹션이라 ❶~❺ 가 안 붙어 자연히 걸러진다.
TITLE = re.compile(r"READING\s*본문([❶❷❸❹❺])[ \t]*([A-Za-z][A-Za-z \-']*)?")
SPEAKER = re.compile(r"[A-Z][a-z]+$")
# 문장 시작 표시 = 숫자 + 대문자. 설명문 안의 '1. 주어가…' 같은 건 숫자 뒤가 마침표라 안 걸린다.
NUM = re.compile(r"(?<![0-9])(\d{1,2})(?=[A-Z“\"('])")
SPLIT_MERGED = re.compile(r"(?<=[.?!])\s*(\d{1,2})(?=[A-Z“\"('])")
APOS = "\x01"


def page_texts(path):
    return [(p.extract_text() or "") for p in pypdf.PdfReader(path).pages]


def strip_annotations(s):
    """상단 블록에서 한글 구문분석 라벨을 걷어낸다. 영문 아포스트로피는 보존한다."""
    s = re.sub(r"(?<=[A-Za-z])[’'](?=[A-Za-z]|\s|$)", APOS, s)   # didn’t / inventors’
    s = s.replace("\uf000", " ")
    s = re.sub(r"[^\x00-\x7f]+", " ", s)      # 한글·❮❯·↳·화살표 등 비ASCII 제거
    s = s.replace(APOS, "’")
    return re.sub(r"\s+", " ", s).strip()


def parse_clean_blocks(pages, lo, hi):
    """② 문장별 블록. ❮ 가 있는 줄만 본다 — 손상된 상단 블록을 배제한다.

    한 줄에 '{번호}{영문}{국문해석}{라벨}❮구조❯{설명}' 이 여러 개 이어 붙어 있다.
    번호 표시로 구간을 자르고, 구간 안에서 **한글이 시작되기 전까지**를 영문으로 본다.
    그 다음 **마지막 문장부호**에서 끊는다 — 'Mt.' 같은 약어에서 조기 종료하지 않으려면
    첫 마침표가 아니라 마지막 마침표를 봐야 한다.
    """
    got = {}
    for i in range(lo, hi):
        for line in pages[i].split("\n"):
            if STRUCT not in line:
                continue
            marks = list(NUM.finditer(line))
            for k, m in enumerate(marks):
                end = marks[k + 1].start() if k + 1 < len(marks) else len(line)
                seg = line[m.end():end]
                h = HANGUL.search(seg)
                eng = seg[:h.start()] if h else seg
                cut = max(eng.rfind("."), eng.rfind("?"), eng.rfind("!"))
                if cut < 0:
                    continue
                end_i = cut + 1
                # 닫는 따옴표는 문장부호 뒤에 온다: like a “virus.”
                while end_i < len(eng) and eng[end_i] in "”\"'’":
                    end_i += 1
                _add(got, int(m.group(1)), eng[:end_i])
    return got


def _add(store, no, eng):
    """한 매치 안에 문장 여러 개가 붙어 나오면 쪼갠다 ('…difficult. 5Why?').

    같은 번호가 여러 번 잡히면 **긴 쪽을 남긴다.** 페이지에 따라 손상된 상단 블록이
    문장별 블록과 같은 줄로 추출되는데(pypdf 가 두 단을 한 줄로 합침), 그때 상단 블록
    조각이 먼저 걸린다. 조각은 한글 라벨에서 잘려 짧으므로 길이로 구별된다.
    """
    parts = SPLIT_MERGED.split(eng.strip())
    cur = no
    for k in range(0, len(parts), 2):
        text = re.sub(r"\s+", " ", parts[k]).strip()
        if text and len(text) > len(store.get(cur, "")):
            store[cur] = text
        if k + 1 < len(parts):
            cur = int(parts[k + 1])


def parse_top_block(pages, lo, hi):
    """① 상단 블록. 라벨을 걷어낸 뒤 번호로 쪼갠다. 손상 가능 — 검증용·복구용."""
    joined = " ".join(pages[i] for i in range(lo, hi))
    m = TITLE.search(joined)
    if not m:
        return {}
    # 국문 해석 문단이 시작되기 전까지가 상단 블록
    region = joined[m.end():]
    stripped = strip_annotations(region)
    got = {}
    marks = list(re.finditer(r"(?<![0-9])(\d{1,2})(?=[A-Z“\"('])", stripped))
    for k, mm in enumerate(marks):
        no = int(mm.group(1))
        end = marks[k + 1].start() if k + 1 < len(marks) else len(stripped)
        text = stripped[mm.end():end].strip()
        if no in got:
            continue
        cut = re.search(r"[.?!]", text[::-1])
        if cut:
            text = text[:len(text) - cut.start()]
        got[no] = re.sub(r"\s+", " ", text).strip()
    return got


def validate_recovery(clean, top):
    """②로 정답을 아는 문장들에 복구 함수를 돌려 일치율을 잰다."""
    both = sorted(set(clean) & set(top))
    agree = [n for n in both if clean[n] == top[n]]
    return both, agree


def check(sents, expected_max):
    problems = []
    if not sents:
        return ["문장을 하나도 못 찾음"]
    nos = sorted(sents)
    if nos != list(range(1, expected_max + 1)):
        problems.append(
            f"문장 번호 불연속 — 있어야 할 1..{expected_max}, 누락 "
            f"{sorted(set(range(1, expected_max + 1)) - set(nos))}")
    for n in nos:
        s = sents[n]
        if HANGUL.search(s):
            problems.append(f"문장 {n}: 한글 혼입 — {s[:60]!r}")
        elif not (s[0].isupper() or s[0] in "“\"('"):
            problems.append(f"문장 {n}: 대문자로 시작 안 함 — {s[:40]!r}")
        elif s.rstrip("”\"'’")[-1:] not in (".", "?", "!"):
            problems.append(f"문장 {n}: 문장부호로 안 끝남 — {s[-40:]!r}")
    return problems


def build(lesson, title, sents, needs_review, src):
    ordered = [sents[n] for n in sorted(sents)]
    body = " ".join(ordered)
    spans, cur = [], 0
    for n in sorted(sents):
        spans.append({"no": n, "start": cur, "end": cur + len(sents[n])})
        cur += len(sents[n]) + 1
    slug = re.sub(r"[^0-9A-Za-z가-힣]", "", title)[:40]
    return {
        "passage_id": f"교과서_동아윤정미_중2_L{lesson}_{slug}",
        "kind": "textbook_reading",
        "title": title,
        "textbook": {"publisher": "동아", "author": "윤정미",
                     "curriculum_version": "2022개정", "grade": 2},
        "textbook_unit": f"Lesson {lesson}",
        "source_type": "교과서",
        "source_detail": f"동아(윤정미) 중2 Lesson {lesson} READING 본문 — {title}",
        "body_text": body,
        "body_text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "word_count": len(body.split()),
        "sentence_count": len(sents),
        "sentence_spans": spans,
        "emphasis_spans": [],
        "transcription": {
            "status": "pending",
            "method": "pdf_text_layer",
            "note": ("문장별 분석 블록에서 추출. 분석 블록이 없는 문장은 상단 본문 블록에서 "
                     "한글 라벨을 걷어내 복구했고 needs_review 에 번호를 남겼다. "
                     "비전 전사 아님 — 원본이 이미 문자다."),
            "needs_review_sentences": needs_review,
            "source_file": src,
            "has_handwriting": False,
            "has_cutoff": False,
            "unreadable_spans": [],
        },
        "distribution_scope": "internal_only",
        "_copyright": ("출판사 부가자료에서 추출. 기획서 §6.6 — 학원 내부 지도용으로만 저장. "
                       "외부 배포·상품화는 별도 확인 필요."),
    }


# ── 본문만 있는 PDF (6과) ────────────────────────────────────────────
# 「내용정리 플러스」가 아니라 본문 PDF는 구조가 다르다. 문장별 분석 블록이 없고,
# 영문이 통짜로 나오는데 **문장 사이 공백이 없다**: "…house.A man: Dr. Schofield, …"
# 마침표 뒤 대문자에서 끊되, 약어(Dr. 등)에서 끊기면 안 된다.
ABBREV = ("Dr.", "Mr.", "Mrs.", "Ms.", "St.", "Prof.", "Mt.", "a.m.", "p.m.")
INITIAL = re.compile(r"\b[A-Z]\.$")          # Frank W. Schofield
# 문단 경계는 공백 없이 붙고("house.A man:"), 문단 안에서는 공백이 있다("outside. He began").
# 둘 다 끊어야 하므로 공백을 선택적으로 둔다.
PLAIN_SPLIT = re.compile(r"(?<=[.?!])[ ]*(?=[A-Z“\"])")


def split_plain(text):
    out = []
    for piece in PLAIN_SPLIT.split(text):
        piece = piece.strip()
        if not piece:
            continue
        prev = out[-1].rstrip() if out else ""
        if prev and (prev.endswith(ABBREV) or INITIAL.search(prev)):
            out[-1] = prev + " " + piece      # 약어·이니셜이었으므로 문장이 아니었다
        else:
            out.append(piece)
    return [re.sub(r"\s+", " ", s).strip() for s in out if s.strip()]


def parse_plain(pages, strip_title=None):
    """저작권 고지·머리말·쪽번호를 걷어내고 영문 본문만 문장 목록으로 만든다."""
    eng = []
    for t in pages:
        for line in t.split("\n"):
            s = line.strip()
            if not s or HANGUL.search(s) or s.startswith("-") or "본문" in s:
                continue
            eng.append(s)
    body = re.sub(r"\s+", " ", " ".join(eng)).strip()
    # 제목이 본문 첫 글자에 붙어 나온다: "…Loved KoreaOn February 28, 1919, …"
    if strip_title and body.startswith(strip_title):
        body = body[len(strip_title):].lstrip()
    return split_plain(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--lesson", type=int, required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--plain", action="store_true",
                    help="「내용정리 플러스」가 아니라 본문만 있는 PDF (6과)")
    ap.add_argument("--title", help="--plain 일 때 본문 제목")
    args = ap.parse_args()

    pages = page_texts(args.pdf)

    if args.plain:
        title = args.title or f"L{args.lesson}본문"
        raw = parse_plain(pages, strip_title=args.title)
        sents = {i: s for i, s in enumerate(raw, 1)}
        print("=" * 74)
        print(f" 교과서 본문 추출 (본문 PDF) — Lesson {args.lesson} · {title}")
        print("=" * 74)
        for n in sorted(sents):
            print(f"   {n:>2} {sents[n]}")
        problems = check(sents, max(sents) if sents else 0)
        for p in problems:
            print(f"   X {p}")
        print("\n ⚠ 이 경로는 문장별 분석 블록이 없어 **교차 검증이 없습니다.**")
        print("   문장 경계를 원장이 반드시 눈으로 확인해야 합니다.")
        if problems or not args.write:
            return 1 if problems else 0
        d = build(args.lesson, title, sents, list(sents), os.path.basename(args.pdf))
        d["transcription"]["method"] = "pdf_text_layer_plain_body"
        d["transcription"]["note"] = (
            "본문 PDF에서 추출. 문장별 분석 블록이 없어 교차 검증을 하지 못했다. "
            "문장 사이 공백이 없는 원본이라 마침표+대문자로 끊었고 약어(Dr. 등)를 예외 처리했다. "
            "전 문장이 원장 확인 대상이다.")
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, d["passage_id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n  저장  {os.path.basename(path)}  {d['word_count']}단어")
        return 0

    src = os.path.basename(args.pdf)
    marks = []
    for i, t in enumerate(pages):
        for m in TITLE.finditer(t):
            title = (m.group(2) or "").strip()
            # '❷Hunger MarketingJunho: 1What?' — 화자 이름이 제목에 붙어 나온다.
            # 제목 바로 뒤가 콜론이면 끝의 대문자 단어 하나를 화자로 보고 뗀다.
            if title and t[m.end():m.end() + 1] == ":":
                title = SPEAKER.sub("", title).strip()
            marks.append({"title": title or f"본문{'❶❷❸❹❺'.index(m.group(1)) + 1}",
                          "untitled": not title, "page": i})

    print("=" * 74)
    print(f" 교과서 본문 추출 — Lesson {args.lesson}  ({len(pages)}쪽)  {src}")
    print("=" * 74)
    if not marks:
        raise SystemExit("  'READING 본문❶…' 를 못 찾았습니다. PDF 구조가 다릅니다.")
    print("  본문 " + str(len(marks)) + "개: " + " · ".join(m["title"] for m in marks))

    docs, blocked = [], False
    for i, r in enumerate(marks):
        hi = marks[i + 1]["page"] if i + 1 < len(marks) else len(pages)
        clean = parse_clean_blocks(pages, r["page"], hi)
        top = parse_top_block(pages, r["page"], hi)
        # 상단 블록은 손상돼 있어 번호 판독도 못 믿는다. 문장 수의 기준은 분석 블록.
        expected = max(clean) if clean else 0

        both, agree = validate_recovery(clean, top)
        rate = f"{len(agree)}/{len(both)}" if both else "0/0"
        trustworthy = both and len(agree) == len(both)

        sents, needs = dict(clean), []
        for n in range(1, expected + 1):
            if n in sents:
                continue
            if n in top and trustworthy:
                sents[n] = top[n]
                needs.append(n)

        print(f"\n── {r['title']} ──")
        print(f"   분석 블록에서 {len(clean)}문장 · 상단 블록에서 {len(top)}문장 · "
              f"총 {expected}문장이어야 함")
        print(f"   복구 함수 검증: 두 곳에 다 있는 {len(both)}문장 중 {rate} 글자 단위 일치"
              f"  → {'복구 신뢰함' if trustworthy else '복구 신뢰 안 함'}")

        problems = check(sents, expected)
        for n in sorted(sents):
            flag = "  ← 복구분. 확인 필요" if n in needs else ""
            print(f"   {n:>2} {sents[n]}{flag}")
        if not trustworthy and both:
            for n in both:
                if clean[n] != top[n]:
                    print(f"    ! 불일치 문장 {n}\n      분석블록: {clean[n]!r}\n"
                          f"      상단복구: {top[n]!r}")
        if problems:
            blocked = True
            for p in problems:
                print(f"   X {p}")
        else:
            print(f"   O 자동 검증 통과" + (f" (복구 {len(needs)}문장 포함)" if needs else ""))
            docs.append(build(args.lesson, r["title"], sents, needs, src))

    print("\n" + "=" * 74)
    if blocked:
        print(" 검증 실패 — 저장하지 않습니다.")
        return 1
    review = sum(len(d["transcription"]["needs_review_sentences"]) for d in docs)
    if review:
        print(f" ⚠ 복구분 {review}문장은 원장 확인이 필요합니다 (위 '확인 필요' 표시).")
    if not args.write:
        print(" 저장하려면 --write 를 붙이십시오.")
        return 0

    os.makedirs(OUT, exist_ok=True)
    for d in docs:
        path = os.path.join(OUT, d["passage_id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  저장  {os.path.basename(path)}  {d['word_count']}단어  "
              f"sha {d['body_text_sha256'][:12]}")
    print("\n ※ status='pending'. 원장 확인 뒤 confirmed 로 올리면 그때부터 불변입니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
