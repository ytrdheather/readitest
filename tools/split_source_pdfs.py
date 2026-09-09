# -*- coding: utf-8 -*-
"""Source/ 의 교재 PDF를 문제/정답으로 자르고 과 단위로 하나씩 묶는다.

두 출판사가 각각 일정한 규칙으로 정답을 뒤에 붙여 둔다.
  - 이그잼포유 : 머리말이 'Answer Key' 로 바뀌는 페이지부터 끝까지가 정답
  - 교육지대   : 본문이 'N) [정답]' 으로 시작하는 페이지부터 끝까지가 정답

경계가 페이지 단위라 페이지만 갈라내면 되고, 원본 페이지를 그대로 복사하므로
글자·그림·레이아웃이 손상되지 않는다.

  python tools/split_source_pdfs.py                 # 미리보기 (파일 안 씀)
  python tools/split_source_pdfs.py --apply         # 실제로 묶음 생성
  python tools/split_source_pdfs.py --apply --lesson "7과"
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

SOURCE = Path(__file__).resolve().parent.parent / "Source"
OUT_DIRNAME = "_묶음"

ANSWER_KEY = re.compile(r"Answer\s*Key", re.I)          # 이그잼포유
# 교육지대는 상품마다 정답 표기가 다르다 — [정답] / 정답 / 모범 답안 / 오답 point.
# 공통점은 'N)' 문항 번호 바로 뒤에 그 말이 온다는 것.
ANSWER_MARK = re.compile(r"\d+\)\s*(\[정답\]|정답|모범\s*답안|오답\s*point)")

# 묶는 순서 — 어휘 → 본문 → 어법 → 실전 순으로 학습 흐름에 맞춘다.
# 문제가 없는 순수 자료 — 통째로 정답(교사용) 묶음에 넣는다.
# 학생용 묶음에 들어가면 본문 해석을 그냥 보여 주는 셈이 된다.
TEACHER_ONLY = ["본문해석지"]

ORDER = [
    "WORD TEST",
    "본문10단계 워크북 1",
    "본문10단계 워크북 4",
    "본문10단계 워크북 5",
    "본문10단계 워크북 6",
    "본문10단계 워크북 7",
    "Grammar Build Up 워크북",
    "Grammar Build Up 객관식",
    "Grammar Build Up 주관식",
    "[대표유형]",
    "[문법 공략]",
    "[서술형 공략]",
    "[최다빈출 공략]",
    "[최다오답 공략]",
    "[최상위 공략]",
    "[대단원평가]",
]


def sort_key(path: Path):
    name = path.name
    for i, token in enumerate(ORDER):
        if token in name:
            return (i, name)
    return (len(ORDER), name)


def short_title(path: Path) -> str:
    """책갈피에 쓸 짧은 이름."""
    n = path.stem
    # 이그잼포유 : (2022개정)2025년_중1_동아(윤정미)_7과_[03]WORD TEST
    n = re.sub(r"^\(2022개정\)\d+년_중\d_[^_]+_\d+과_", "", n)
    n = re.sub(r"_단계별$", "", n)
    # 교육지대 : [서술형 공략] 7.Find Your Dream(01)_동아(윤정미) 중1 영어 [25문제] [Q]
    m = re.match(r"^\[(.+?)\]", n)
    if m and not m.group(1).isdigit():  # [03]WORD TEST 같은 이그잼포유 번호는 건드리지 않는다
        label = m.group(1)
        count = re.search(r"\[(\d+문제)\]", n)
        n = f"[{label}]" + (f" {count.group(1)}" if count else "")
    n = re.sub(r"\s+", " ", n).strip()
    return n


def find_split(doc) -> tuple[int, str]:
    """정답이 시작되는 페이지 번호(0-base)와 판정 근거를 돌려준다.

    정답 페이지가 하나도 없으면 (페이지수, 'none') — 전부 문제로 본다.
    """
    for i, page in enumerate(doc):  # noqa: B007
        text = page.get_text()
        if ANSWER_MARK.search(text):
            return i, "정답표기"
        head = "\n".join(text.splitlines()[:8])
        if ANSWER_KEY.search(head):
            return i, "Answer Key"
    return len(doc), "none"


def scan(folder: Path):
    """폴더 안 PDF를 훑어 분할 계획을 만든다. (중복 파일은 제외)"""
    seen: dict[str, Path] = {}
    plan, skipped = [], []
    for pdf in sorted(folder.glob("*.pdf"), key=sort_key):
        digest = hashlib.md5(pdf.read_bytes()).hexdigest()
        if digest in seen:
            skipped.append((pdf, seen[digest]))
            continue
        seen[digest] = pdf

        doc = fitz.open(pdf)
        if any(t in pdf.name for t in TEACHER_ONLY):
            cut, why = 0, "자료"
        else:
            cut, why = find_split(doc)
        # 경계 뒤가 전부 정답 페이지인지 확인 — 아니면 사람이 봐야 한다.
        clean = all(
            ANSWER_MARK.search(doc[i].get_text())
            or ANSWER_KEY.search("\n".join(doc[i].get_text().splitlines()[:8]))
            for i in range(cut, len(doc))
        ) or why == "자료"
        plan.append(
            {
                "path": pdf,
                "title": short_title(pdf),
                "pages": len(doc),
                "cut": cut,
                "why": why,
                "clean": clean,
            }
        )
        doc.close()
    return plan, skipped


def build(plan, out_path: Path, part: str):
    """part='q' 문제 / part='a' 정답 을 하나로 합치고 책갈피를 단다."""
    merged = fitz.open()
    toc = []
    for item in plan:
        src = fitz.open(item["path"])
        lo, hi = (0, item["cut"] - 1) if part == "q" else (item["cut"], len(src) - 1)
        if lo > hi:
            src.close()
            continue
        start = merged.page_count + 1
        merged.insert_pdf(src, from_page=lo, to_page=hi)
        toc.append([1, item["title"], start])
        src.close()
    if merged.page_count == 0:
        merged.close()
        return 0
    merged.set_toc(toc)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(out_path, garbage=3, deflate=True)
    n = merged.page_count
    merged.close()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제로 파일을 만든다")
    ap.add_argument("--lesson", help="특정 과만 (예: '7과')")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    folders = sorted(
        p for p in SOURCE.glob("*/*") if p.is_dir() and p.name != OUT_DIRNAME
    )
    folders += [p for p in SOURCE.glob("*") if p.is_dir() and any(p.glob("*.pdf"))]
    if args.lesson:
        folders = [f for f in folders if args.lesson in f.name]

    for folder in folders:
        plan, skipped = scan(folder)
        if not plan:
            continue
        rel = folder.relative_to(SOURCE)
        print("=" * 78)
        print(f"■ {rel}")
        for it in plan:
            q, a = it["cut"], it["pages"] - it["cut"]
            flag = "" if it["clean"] else "   ← 확인 필요"
            src = {"정답표기": "교육지대", "Answer Key": "이그잼포유",
                   "none": "정답없음", "자료": "교사용 자료"}[it["why"]]
            print(f"   {it['title'][:44]:<46} {it['pages']:>3}p  문제 {q:>3}  정답 {a:>3}  ({src}){flag}")
        for dup, orig in skipped:
            print(f"   [중복 제외] {dup.name}  ≡  {orig.name}")

        if args.apply:
            out = folder / OUT_DIRNAME
            tag = f"{rel.parts[0]}_{rel.parts[-1]}" if len(rel.parts) > 1 else rel.parts[0]
            nq = build(plan, out / f"{tag}_문제.pdf", "q")
            na = build(plan, out / f"{tag}_정답.pdf", "a")
            print(f"   → {out.name}/{tag}_문제.pdf ({nq}p), {tag}_정답.pdf ({na}p)")


if __name__ == "__main__":
    main()
