# -*- coding: utf-8 -*-
"""Source/ 의 교재 PDF를 문제/정답으로 자르고 과 단위로 하나씩 묶는다.

출판사·상품마다 정답을 붙이는 방식이 다르다. 규칙은 세 갈래다.

  1) 이그잼포유 워크북·Grammar·WORD TEST
     머리말이 'Answer Key' 로 바뀌는 페이지부터 끝까지가 정답
  2) 이그잼포유 예상문제
     머리말에 '정답' 한 줄이 서는 페이지부터 끝까지가 정답
  3) 교육지대 공략·평가
     문항 번호 뒤에 [정답] / 정답 / 모범 답안 / 오답 point 가 오는 페이지부터

경계가 페이지 단위라 페이지만 갈라내면 되고, 원본 페이지를 그대로 복사하므로
글자·그림·레이아웃이 손상되지 않는다.

  python tools/split_source_pdfs.py                 # 미리보기 (파일 안 씀)
  python tools/split_source_pdfs.py --apply
  python tools/split_source_pdfs.py --apply --lesson "6과"
  python tools/split_source_pdfs.py --apply --워크북-전부   # 1~10 다 담기
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

SOURCE = Path(__file__).resolve().parent.parent / "Source"
OUT_DIRNAME = "_묶음"

ANSWER_KEY = re.compile(r"Answer\s*Key", re.I)
ANSWER_HEAD = re.compile(r"^\s*정답\s*$", re.M)          # 예상문제 정답장 머리말
ANSWER_MARK = re.compile(r"\d+\)\s*(\[정답\]|정답|모범\s*답안|오답\s*point)")

# 문제가 없는 자료 — 통째로 정답(교사용) 묶음으로 보낸다.
# 학생용 묶음에 들어가면 본문·해석·정답을 그냥 넘겨주는 셈이 된다.
TEACHER_ONLY = ("본문해석지", "(교사용)")

# 본문10단계 워크북 중 실제로 쓰는 단계. 비상은 1~10이 다 오지만 동아에 맞춰 골라 담는다.
# 통합본(1~10)은 개별 파일과 내용이 같아 언제나 뺀다.
WORKBOOK_STEPS = {1, 4, 5, 6, 7}

# 예상문제는 학생용·교사용이 따로 온다. 교사용에 문제와 정답이 같이 있고
# 해설은 학생용 뒤쪽 것과 같으므로, 학생용에서는 문제만 쓰고 해설은 버린다.
EXAM_PAPER = re.compile(r"^\[0[456]\]예상문제")

# 파일이 어느 교재 것인지 — 폴더를 잘못 짚고 넣은 자료를 걸러내는 데 쓴다.
PUBLISHER = re.compile(r"(동아|비상)\s*\(")


def kind(path: Path) -> str:
    """파일 이름에서 상품 종류만 뽑는다. 책갈피 이름으로도 쓴다."""
    n = re.sub(r"^\(2022개정\)\d+년_중\d_[^_]+_\d+과_", "", path.stem)
    n = re.sub(r"_단계별(_\(\d{8}수정\))?$", "", n)
    m = re.match(r"^\[(.+?)\]", n)
    if m and not m.group(1).isdigit():  # [03] 같은 이그잼포유 번호는 건드리지 않는다
        label = m.group(1)
        count = re.search(r"\[(\d+문제)\]", n)
        n = f"[{label}]" + (f" {count.group(1)}" if count else "")
    return re.sub(r"\s+", " ", n).strip()


def sort_key(k: str):
    """학습 흐름 순 — 본문 → 워크북 → 어휘 → 어법 → 예상문제 → 실전."""
    if "내용정리" in k:
        return (0, 0, k)
    if k == "본문":
        return (1, 0, k)
    m = re.match(r"본문10단계 워크북 (\d+)", k)
    if m:
        return (10, int(m.group(1)), k)
    if "워크북 통합본" in k:
        return (10, 99, k)
    for i, tok in enumerate(["WORD TEST", "Grammar Build Up 워크북",
                             "Grammar Build Up 객관식", "Grammar Build Up 주관식"]):
        if tok in k:
            return (20 + i, 0, k)
    m = re.match(r"\[0[456]\]예상문제", k)
    if m:
        return (40, 0, k)
    for i, tok in enumerate(["[대표유형]", "[문법 공략]", "[서술형 공략]", "[최다빈출 공략]",
                             "[최다오답 공략]", "[최상위 공략]", "[대단원평가]"]):
        if k.startswith(tok):
            return (50 + i, 0, k)
    return (90, 0, k)


def find_split(doc) -> tuple[int, str]:
    """정답이 시작되는 페이지(0-base)와 판정 근거. 없으면 (페이지수, 'none')."""
    for i, page in enumerate(doc):
        text = page.get_text()
        if ANSWER_MARK.search(text):
            return i, "정답표기"
        head = "\n".join(text.splitlines()[:8])
        if ANSWER_KEY.search(head):
            return i, "Answer Key"
        if ANSWER_HEAD.search(head):
            return i, "정답 머리말"
    return len(doc), "none"


def route(pdf: Path, k: str, all_steps: bool, teacher_kinds: set[str]) -> str:
    """이 파일을 묶음에 어떻게 넣을지 정한다."""
    if "워크북 통합본" in k:
        return "drop"                      # 개별 워크북과 내용 중복
    m = re.match(r"본문10단계 워크북 (\d+)", k)
    if m and not all_steps and int(m.group(1)) not in WORKBOOK_STEPS:
        return "drop"
    if k == "본문" or any(t in pdf.name for t in TEACHER_ONLY):
        return "teacher"                   # 통째로 정답 묶음
    if EXAM_PAPER.match(k) and f"{k}(교사용)" in teacher_kinds:
        return "q_only"                    # 해설은 교사용 쪽에만 넣는다
    # 교사용 짝이 없으면 제 뒤에 붙은 해설을 그대로 쓴다
    return "split"


def publisher_of(text: str) -> str | None:
    m = PUBLISHER.search(text)
    return m.group(1) if m else None


def check_folder(folder: Path, pdfs: list[Path]) -> str | None:
    """폴더가 말하는 교재와 파일이 말하는 교재가 다르면 그 이유를 돌려준다.

    2026-09-10 비상 7과 폴더에 동아 7과 파일 16개가 통째로 들어가 있었다.
    그대로 묶었으면 '비상 7과 문제지'라는 이름의 동아 문제지가 나왔을 것이다.
    """
    want = publisher_of(folder.parent.name) or publisher_of(folder.name)
    if not want:
        return None
    wrong = [p for p in pdfs if (g := publisher_of(p.name)) and g != want]
    if len(wrong) > len(pdfs) / 2:
        got = publisher_of(wrong[0].name)
        return f"{want} 폴더인데 {len(wrong)}/{len(pdfs)}개가 {got} 파일이다"
    return None


def scan(folder: Path, all_steps: bool):
    """폴더 안 PDF를 훑어 분할 계획을 만든다. 중복 파일은 뺀다."""
    seen: dict[str, Path] = {}
    plan, skipped, dropped = [], [], []
    teacher_kinds = {kind(p) for p in folder.glob("*.pdf") if "(교사용)" in p.name}
    for pdf in sorted(folder.glob("*.pdf"), key=lambda p: sort_key(kind(p))):
        digest = hashlib.md5(pdf.read_bytes()).hexdigest()
        if digest in seen:
            skipped.append((pdf, seen[digest]))
            continue
        seen[digest] = pdf

        k = kind(pdf)
        mode = route(pdf, k, all_steps, teacher_kinds)
        if mode == "drop":
            dropped.append(k)
            continue

        doc = fitz.open(pdf)
        cut, why = (0, "자료") if mode == "teacher" else find_split(doc)
        plan.append({"path": pdf, "title": k, "pages": len(doc),
                     "cut": cut, "why": why, "mode": mode})
        doc.close()
    return plan, skipped, dropped


def build(plan, out_path: Path, part: str) -> int:
    """part='q' 문제 / part='a' 정답 을 하나로 합치고 책갈피를 단다."""
    merged = fitz.open()
    toc = []
    for item in plan:
        if part == "a" and item["mode"] == "q_only":
            continue                       # 해설은 교사용 쪽에만 넣는다
        src = fitz.open(item["path"])
        lo, hi = (0, item["cut"] - 1) if part == "q" else (item["cut"], len(src) - 1)
        if lo > hi:
            src.close()
            continue
        toc.append([1, item["title"], merged.page_count + 1])
        merged.insert_pdf(src, from_page=lo, to_page=hi)
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
    ap.add_argument("--lesson", help="특정 과만 (예: '6과')")
    ap.add_argument("--워크북-전부", dest="all_steps", action="store_true",
                    help=f"워크북을 1~10 전부 담는다 (기본: {sorted(WORKBOOK_STEPS)})")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    folders = sorted(p for p in SOURCE.glob("*/*") if p.is_dir() and p.name != OUT_DIRNAME)
    folders += [p for p in SOURCE.glob("*") if p.is_dir() and any(p.glob("*.pdf"))]
    if args.lesson:
        folders = [f for f in folders if args.lesson in f.name]

    labels = {"정답표기": "교육지대", "Answer Key": "이그잼포유",
              "정답 머리말": "이그잼포유", "none": "정답없음", "자료": "교사용 자료"}
    for folder in folders:
        pdfs = list(folder.glob("*.pdf"))
        if not pdfs:
            continue
        rel = folder.relative_to(SOURCE)
        if bad := check_folder(folder, pdfs):
            print("=" * 78)
            print(f"■ {rel}")
            print(f"   ⚠ 건너뜀 — {bad}.")
            print("     파일을 옳은 폴더로 옮긴 뒤 다시 돌리십시오.")
            continue
        plan, skipped, dropped = scan(folder, args.all_steps)
        if not plan:
            continue
        print("=" * 78)
        print(f"■ {rel}")
        for it in plan:
            q = it["cut"]
            a = 0 if it["mode"] == "q_only" else it["pages"] - it["cut"]
            flag = "   ← 정답 못 찾음" if it["why"] == "none" else ""
            print(f"   {it['title'][:42]:<44} {it['pages']:>3}p  "
                  f"문제 {q:>3}  정답 {a:>3}  ({labels[it['why']]}){flag}")
        for dup, orig in skipped:
            print(f"   [중복 제외] {dup.name[:60]}")
        for d in dropped:
            print(f"   [제외] {d}")

        if args.apply:
            out = folder / OUT_DIRNAME
            tag = f"{rel.parts[0]}_{rel.parts[-1]}" if len(rel.parts) > 1 else rel.parts[0]
            nq = build(plan, out / f"{tag}_문제.pdf", "q")
            na = build(plan, out / f"{tag}_정답.pdf", "a")
            print(f"   → {tag}_문제.pdf ({nq}p),  {tag}_정답.pdf ({na}p)")


if __name__ == "__main__":
    main()
