# -*- coding: utf-8 -*-
"""
이미 받아 둔 pass_a 결과에 **verbatim 검사를 다시 돌린다** (API 호출 없음, 과금 없음).

  python tools/recheck_verbatim.py

## 왜 따로 필요한가

검사기를 고쳤을 때 「고친 게 맞나」를 확인하려면 다시 태깅해야 하는데, 그건 돈이
든다. 결과 JSON 과 지문은 이미 손에 있으므로 판정만 다시 하면 된다.

**검사 규칙을 여기서 새로 쓰지 않는다.** `pipeline.pass_a._canon` 을 그대로 가져다
쓴다 — 규칙이 두 벌이 되면 한쪽만 고치게 되고, 이 저장소는 그 실수를 이미
세 번(문장 분리기) 겪었다.
"""
import json
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.pass_a import _canon                                   # noqa: E402
from pipeline.passage import split_sentences                         # noqa: E402
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QUOTES = {"T-GRAMMAR-INLINE", "T-GRAMMAR-USAGE", "T-GRAMMAR-STANDALONE", "T-WRITE-FIX"}
GEN = os.path.join(ROOT, "data", "generated")


def check(item, sents, sents_np):
    bad = []
    for o in item.get("options", []):
        if o.get("via_modification") not in (None, "NONE") \
           or o.get("violates_point_code") not in (None, "NONE"):
            continue
        cand = re.sub(r"\s*\(\[\d+\]\)\s*$", "", " ".join(o["body"].split())).strip()
        if len(cand) < 20 or "___" in cand:
            continue
        if not (cand[0].isupper() and cand[-1] in ".?!"):
            continue
        if _canon(cand) in sents or _canon(cand, True) in sents_np:
            continue
        bad.append((o["label"], cand))
    return bad


def main():
    r = Rest()
    pgs = r.get("/passage?select=id,title,body_text")
    bodies = {p["title"]: p["body_text"] for p in pgs}
    by_id = {p["id"]: p["body_text"] for p in pgs}
    total_before = total_after = 0
    still = []

    for f in sorted(glob.glob(os.path.join(GEN, "*.pass_a.json"))):
        d = json.load(open(f, encoding="utf-8"))
        pid = d.get("passage_id")
        body = bodies.get(pid)
        if body is None:
            body = by_id.get(pid)              # passage_id 가 UUID 인 경우
        if body is None:
            # 파일명에서 되살린다. 긴 제목은 파일명이 잘려 있으므로 앞부분 일치로 찾는다.
            key = os.path.basename(f)[:-12].replace("_", " ")
            body = next((v for k, v in bodies.items()
                         if k == key or k.startswith(key[:20])), None)
        if body is None:
            print(f"  ? 지문을 못 찾음 — {os.path.basename(f)}")
            continue
        sents = {_canon(s) for _, _, _, s in split_sentences(body)}
        sents_np = {_canon(s, True) for _, _, _, s in split_sentences(body)}
        for it in d["items"]:
            if it.get("question_type_code") not in QUOTES:
                continue
            total_before += len(it.get("_verbatim_problem") or [])
            bad = check(it, sents, sents_np)
            total_after += len(bad)
            for label, text in bad:
                still.append((pid, it["question_type_code"], label, text))

    print(f"  고치기 전 지적 {total_before}건  →  고친 뒤 {total_after}건")
    if still:
        print("\n  남은 지적 — 조판 차이가 아니라 진짜 다른 것:")
        for pid, qt, label, text in still:
            print(f"    {pid[:34]:36} {qt:22} {label} {text[:70]}")
    else:
        print("  남은 지적 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
