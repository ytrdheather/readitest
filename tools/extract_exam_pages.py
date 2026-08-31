# -*- coding: utf-8 -*-
"""
기출 시험지 PDF → 페이지 이미지 (판독용).

  python tools/extract_exam_pages.py "Z:/.../2026 청명중2-1 기말_OOO.pdf" --out <디렉터리>

## 왜 필요한가

기출 시험지는 **텍스트 레이어가 없는 이미지 스캔**이다(2026-08-23 확인, 4개교 전부).
밑줄·네모·번호가 시각 정보라 비전으로 읽어야 하고, 그러려면 페이지를 이미지로 꺼내야 한다.
poppler(pdftoppm)가 없는 환경이라 pypdf 로 **임베드된 페이지 이미지를 직접 꺼낸다.**

## 방향 보정 — 추측하지 않는다

기획서 §6.7이 인입 파이프라인 과제로 「방향 보정」을 적어뒀는데, 실물을 보니
**PDF 가 페이지마다 `/Rotate` 값을 갖고 있다.** 영덕중 사본은 1·3쪽이 `/Rotate=180`,
조은서 사본은 2·4쪽이 180이었다. 즉 회전은 판단할 게 아니라 **읽어서 적용할 값**이다.
이미지 자체를 보고 방향을 추정하는 코드를 짤 뻔했는데 그럴 필요가 없었다.

## 중복 페이지 탐지

도윤후 사본은 5쪽 이미지가 4쪽과 동일했다 — **마지막 장이 스캔되지 않은 것.**
같은 시험의 사본이 여러 개 있으므로(sources.md) 중복이 나오면 다른 사본을 쓰면 된다.
sha256 으로 잡아 경고한다.

## 산출물은 저장소에 넣지 않는다

시험지에는 학생 이름과 손글씨가 있다 (CLAUDE.md 규칙 3). 원본은 `Z:` 에만 두고,
이 도구는 **스크래치패드 등 저장소 밖 경로**로만 내보낸다. 기본 --out 이 없으면 거부한다.
"""
import argparse
import hashlib
import io
import os
import sys

import pypdf
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract(pdf_path, out_dir, prefix, max_width=1600, quality=88):
    if os.path.abspath(out_dir).startswith(os.path.abspath(REPO)):
        raise SystemExit(
            f"거부: 저장소 안으로는 내보내지 않습니다 ({out_dir}).\n"
            "  시험지에는 학생 이름·손글씨가 있습니다 (CLAUDE.md 규칙 3).\n"
            "  스크래치패드 등 저장소 밖 경로를 지정하십시오.")
    os.makedirs(out_dir, exist_ok=True)
    reader = pypdf.PdfReader(pdf_path)
    seen, written, problems = {}, [], []

    for i, page in enumerate(reader.pages, 1):
        rot = int(page.get("/Rotate", 0) or 0)
        try:
            images = list(page.images)
        except Exception as e:                     # JBIG2 등 디코더 없는 경우
            problems.append(f"p{i}: 이미지 디코드 실패 ({type(e).__name__})")
            continue
        if not images:
            problems.append(f"p{i}: 임베드 이미지 없음")
            continue
        raw = images[0]
        h = hashlib.sha256(raw.data).hexdigest()[:12]
        dup = seen.get(h)
        seen[h] = i
        img = Image.open(io.BytesIO(raw.data))
        if rot:
            img = img.rotate(-rot, expand=True)    # /Rotate 는 시계방향 표시
        if img.width > max_width:
            img = img.resize((max_width, int(img.height * max_width / img.width)),
                             Image.LANCZOS)
        path = os.path.join(out_dir, f"{prefix}_p{i}.jpg")
        img.convert("RGB").save(path, quality=quality)
        written.append(path)
        flag = f"  ★ p{dup} 와 동일 — 이 쪽은 스캔 누락" if dup else ""
        print(f"  p{i}  /Rotate={rot:>3}  {img.size[0]}x{img.size[1]}  sha {h}{flag}")
        if dup:
            problems.append(f"p{i}: p{dup} 와 같은 이미지 (스캔 누락 의심)")

    if problems:
        print("\n  [주의]")
        for p in problems:
            print("   ·", p)
        print("   → 같은 시험의 다른 사본을 쓰십시오 (data/sources.md 참조)")
    return written, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True, help="저장소 밖 경로 (스크래치패드 등)")
    ap.add_argument("--prefix", help="파일명 접두사 (기본: 학교명 추정)")
    ap.add_argument("--max-width", type=int, default=1600)
    args = ap.parse_args()

    prefix = args.prefix or "exam"
    print("=" * 66)
    print(f" 기출 시험지 페이지 추출 — {os.path.basename(args.pdf)}")
    print("=" * 66)
    written, problems = extract(args.pdf, args.out, prefix, args.max_width)
    print(f"\n  {len(written)}쪽 저장 → {args.out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
