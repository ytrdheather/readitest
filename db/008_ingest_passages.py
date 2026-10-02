# -*- coding: utf-8 -*-
"""
확정된 지문을 `passage` 테이블에 적재한다.

  python db/008_ingest_passages.py              # 검증만
  python db/008_ingest_passages.py --apply

**INSERT 뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
이미 있는 지문(같은 `body_text_sha256`)은 건너뛴다. 두 번 돌려도 안전하다.

## 002_ingest.py 와 무엇이 다른가

`002` 는 0단계 지문 **두 개를 파일명으로 하드코딩**해서 읽는다. 태깅·문항·검수까지
한 덩어리로 넣는 스크립트라 그 형태가 맞았다.

이건 다르다. L5·L6 지문 32개는 **아직 태그도 문항도 없다.** 태깅을 하려면 먼저
지문이 DB 에 있어야 하고, 그래서 지문만 넣는 경로가 따로 필요하다.

## 확정된 것만 넣는다

`transcription.status == "confirmed"` 인 지문만 대상이다. 확정 전 지문을 넣으면
그 위에 태깅이 붙고, 나중에 본문이 바뀌면 태그의 span 이 전부 밀린다 (설계원칙 7).

## 해시를 다시 계산해서 대조한다

JSON 에 적힌 `body_text_sha256` 을 믿지 않고 `body_text` 로 다시 계산해 맞춰 본다.
어긋나면 **아무것도 넣지 않고 멈춘다** — 파일이 손으로 편집됐다는 뜻이기 때문이다.
"""
import argparse
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")
KINDS = {"textbook_reading", "textbook_dialogue", "handout_external", "exam_only"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", default=None)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    r = Rest()
    # 교과서는 **지문 파일의 `textbook` 대로** 고른다. 예전에는 중2 로 고정해서 중1 지문 27개가
    # 중2 교과서로 들어갔다 (2026-10-02 발견). DB 에 그 교과서 행이 없으면 넣지 않고 멈춘다.
    books = {(t["publisher"], t["author"], t["curriculum_version"], t["grade"]): t["id"]
             for t in r.get("/textbook?select=id,publisher,author,curriculum_version,grade")}
    have = {p["body_text_sha256"] for p in r.get("/passage?select=body_text_sha256")}

    pats = a.glob or ["*.json"]
    files = []
    for pat in pats:
        files += [f for f in sorted(glob.glob(os.path.join(PASSAGES, pat))) if f not in files]

    print("=" * 74)
    print(f" 확정 지문 적재 — {'실제 적용' if a.apply else '검증만'}")
    print("=" * 74)
    print("  실행 SQL: INSERT 만. DELETE / DROP / TRUNCATE 없음.\n")

    rows, skip_pending, skip_dup, problems = [], [], 0, []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        name = d.get("passage_id", os.path.basename(f))
        tr = d.get("transcription", {})
        if tr.get("status") != "confirmed":
            skip_pending.append((name, tr.get("status")))
            continue
        body = d["body_text"]
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if sha != d.get("body_text_sha256"):
            problems.append(f"{name}: 해시 불일치 — 파일이 손으로 고쳐졌을 수 있음")
            continue
        # 중복 판정을 kind 검사보다 **먼저** 한다. 0단계 초기 지문에는 kind 가 없는데
        # (002 가 하드코딩으로 붙였다) 그건 이미 DB 에 있으므로 여기서 걸러진다.
        if sha in have or any(x["body_text_sha256"] == sha for x in rows):
            skip_dup += 1
            continue
        if d.get("kind") not in KINDS:
            problems.append(f"{name}: kind 가 없거나 스키마 허용값이 아님 ({d.get('kind')!r})")
            continue
        textbook = None
        if d.get("source_type") == "교과서":
            tb = d.get("textbook") or {}
            textbook = books.get((tb.get("publisher"), tb.get("author"),
                                  tb.get("curriculum_version"), tb.get("grade")))
            if textbook is None:
                problems.append(f"{name}: 파일의 교과서 {tb} 가 textbook 테이블에 없음")
                continue
        rows.append({
            "kind": d["kind"],
            "title": d.get("title") or name,
            # 교과서 지문에만 교과서를 건다. 학교 배부물은 교과서 소속이 아니다.
            "textbook_id": textbook,
            "textbook_unit": d.get("textbook_unit"),
            "source_detail": d.get("source_detail"),
            "body_text": body,
            "body_text_sha256": sha,
            "word_count": d.get("word_count") or len(body.split()),
            "transcription_status": "confirmed",
            "transcription_note": tr.get("note"),
            "has_handwriting": bool(tr.get("has_handwriting")),
            "scan_file": d.get("scan_file"),
            "scan_page": d.get("scan_page"),
            "distribution_scope": d.get("distribution_scope", "internal_only"),
        })

    # 「ReadMore-1」 이 L5·L6 양쪽에 있다. 그대로 넣으면 DB 에서 어느 과인지 구분이
    # 안 되고, --passage 로 찾을 때도 둘이 같이 잡힌다. 겹치는 것만 단원을 앞에 붙인다.
    # 조용히 바꾸지 않고 무엇을 바꿨는지 화면에 찍는다.
    seen, dup = set(), set()
    for x in rows:
        (dup if x["title"] in seen else seen).add(x["title"])
    renamed = []
    for x in rows:
        if x["title"] in dup and x.get("textbook_unit"):
            short = x["textbook_unit"].replace("Lesson ", "L")
            old, x["title"] = x["title"], f"{short} {x['title']}"
            renamed.append((old, x["title"]))

    if problems:
        print("  X 문제가 있어 아무것도 넣지 않습니다\n")
        for p in problems:
            print("    ", p)
        return 1

    by_kind = {}
    for x in rows:
        by_kind[x["kind"]] = by_kind.get(x["kind"], 0) + 1
    for x in rows:
        print(f"   {x['kind']:18} {(x['title'] or '')[:36]:38} {x['word_count']:>4}단어")
    print(f"\n  새로 넣을 것 {len(rows)}개  {by_kind}")
    print(f"  건너뜀 — 이미 있음 {skip_dup}개 · 전사 미확정 {len(skip_pending)}개")
    for n, st in skip_pending:
        print(f"      [{st}] {n}")

    if not a.apply:
        print("\n  실제로 넣으려면 --apply")
        return 0
    if rows:
        r.insert("passage", rows)
    print(f"\n  {len(rows)}개 적재 완료 · passage 총 "
          f"{len(r.get('/passage?select=id'))}행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
