# -*- coding: utf-8 -*-
"""
이미 만든 동형 세트를 일반 출제 원리로 검사한다 — **문항은 바꾸지 않는다.**

  python tools/check_item_principles.py                      # 전 세트 보고 (네트워크 안 씀)
  python tools/check_item_principles.py --verify 영덕중_7세트   # 선지 유일성 검증 (API 1회)

이미 인쇄해 나간 세트는 정답 위치를 옮기면 학생 시험지와 정답지가 어긋난다
(디자인 지침 5 의 2026-10-04 사고). 그래서 여기서는 **보고만** 하고, 정답 배치는
새로 만드는 세트부터 `make_mock_exam.py` 가 한다.

`--verify` 는 그 세트 JSON 의 `diagnostics.review_needed` 만 채운다 — 정답지를 다시
뽑으면 맨 위에 「검수 필요」 상자가 붙는다. 문항·선지 순서는 건드리지 않는다.

결과 숫자는 `data/stage0/mock_item_principles.json` 에 남긴다.
"""
import argparse
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import item_principles as ip                           # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MOCK = os.path.join(ROOT, "data", "generated", "mock")
OUT = os.path.join(ROOT, "data", "stage0", "mock_item_principles.json")


def report():
    total = [0] * 5
    rows = []
    for f in sorted(glob.glob(os.path.join(MOCK, "*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        items = d.get("items", [])
        mats = {m["id"]: m for m in d.get("materials", [])}
        seq = [it.get("answer") for it in items]
        for a in seq:
            if 1 <= (a or 0) <= 5:
                total[a - 1] += 1
        pp, ww = ip.check(items, mats)
        neg = sum(1 for it in items if ip.NEG.search(it.get("stem_ko", "")))
        fixed = sum(1 for it in items if ip.fixed_reason(it, mats))
        name = os.path.basename(f)[:-5]
        rows.append({"set": name, "answers": "".join(ip.CIRC[a - 1] for a in seq),
                     "fixed": fixed, "negative_stems": neg, "problems": pp, "warnings": ww,
                     "review_needed": d.get("diagnostics", {}).get("review_needed")})
        print(f"{name:22} {rows[-1]['answers']}  고정 {fixed:>2} · 부정발문 {neg:>2}")
        for p in pp:
            print(f"      ! {p}")
        for w in ww:
            print(f"      · {w}")
    n = sum(total)
    print("\n전체 정답 분포 " + "  ".join(f"{ip.CIRC[p]} {total[p]} ({total[p] / n:.0%})" for p in range(5)))
    with io.open(OUT, "w", encoding="utf-8") as fo:
        json.dump({"note": "tools/check_item_principles.py 결과 — 문항은 바꾸지 않음",
                   "distribution": total, "sets": rows}, fo, ensure_ascii=False, indent=2)
        fo.write("\n")
    print(f"저장 → {OUT}")


def verify(name):
    from pipeline import mock_verify
    from pipeline.models import Cost, client
    from pipeline.pass_a import extract_json
    path = os.path.join(MOCK, name if name.endswith(".json") else name + ".json")
    d = json.load(io.open(path, encoding="utf-8"))
    params = mock_verify.build_params(f"{d['school']} {d['set_no']}세트", d["materials"], d["items"])
    with client().messages.stream(**params) as stream:
        msg = stream.get_final_message()
    cost = Cost()
    usd = cost.add(name, params["model"], msg.usage)
    flagged = mock_verify.apply(d["items"], extract_json(msg))
    d.setdefault("diagnostics", {})["review_needed"] = flagged
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{name} 선지 유일성 검증 ${usd:.3f} — 검수 필요 {len(flagged)}문항")
    for r in flagged:
        print(f"  ? {r['no']}번 {r['kind']}: {r['note']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", metavar="세트", help="예: 영덕중_7세트")
    a = ap.parse_args()
    if a.verify:
        verify(a.verify)
    else:
        report()


if __name__ == "__main__":
    main()
