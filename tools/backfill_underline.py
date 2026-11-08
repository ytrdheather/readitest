# -*- coding: utf-8 -*-
"""
이미 만든 동형 세트에 `underline` 을 채운다 — 「밑줄 친 ①~⑤」 문항이 밑줄 없이 찍히던 것 (2026-11-08).

  python tools/backfill_underline.py            # 무엇을 채울지 보고만
  python tools/backfill_underline.py --apply    # 세트 JSON 에 쓴다

밑줄 범위는 **선지**에서 읽는다: 선지 k 가 「that you fixed」 이고 지문의 k 번째 기호 바로 뒤가
그 글로 시작하면 「①[that you fixed]」. 선지가 「①」 처럼 기호뿐이거나 지문과 안 맞으면
채우지 않고 목록으로 낸다 — 사람이(Claude 가) 지문을 보고 `MANUAL` 에 적는다.
문항·정답·지문 글자는 바꾸지 않는다. `underline` 칸만 더한다.
"""
import argparse
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.underline import _INLINE, locate                       # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MOCK = os.path.join(ROOT, "data", "generated", "mock")
FAMILIES = ["①②③④⑤", "ⓐⓑⓒⓓⓔ", ["(A)", "(B)", "(C)", "(D)", "(E)"], ["(a)", "(b)", "(c)", "(d)", "(e)"]]
LABEL = re.compile(r"^\s*(?:[①-⑤ⓐ-ⓔ]|\([A-Ea-e]\))\s*")

# 선지로 범위를 못 읽는 문항 — 지문을 보고 손으로 적은 것. {(세트, 번호): [underline …]}
MANUAL = {
    # 단문 나열 <보기> a~e — 문장마다 짚는 말이 하나
    ("중1_영일중_3세트", 12): ["a. I don't think [that] the bag", "b. Look at [that] painting",
                            "c. I heard [that] plastic", "d. [That] is my brother", "e. Do you know [that] Chris"],
    ("중1_영일중_5세트", 20): ["a. I went to the store [to buy]", "b. Peter uses drones [to capture]",
                            "c. Emma reads a lot [to improve]", "d. My plan is [to visit]",
                            "e. Anna travels around the country [to find]"],
    # 2세트 10번 — 발문에 문장을 인용했던 것(같은 날 오전)을 진짜 밑줄로
    ("중1_영일중_2세트", 10): ["Jeans are strong, so [they] are perfect"],
}
STEM = {("중1_영일중_2세트", 10): "윗글의 밑줄 친 they가 가리키는 것으로 가장 알맞은 것은?"}
_ENG = re.compile(r"[A-Za-z][A-Za-z’'\- ,.?!]*[A-Za-z.?!]")


def phrase_ref(it, text):
    """「○○가 가리키는」 의 ○○ 가 지문에 한 번만 나오면 거기 밑줄."""
    low = text.lower().replace("’", "'")
    best = None
    for run in _ENG.findall(it["stem_ko"]):
        run = run.strip(" ,")
        r = run.lower().replace("’", "'")
        n = len(re.findall(r"(?<![a-z])" + re.escape(r) + r"(?![a-z])", low))
        if n == 1 and (best is None or len(run) > len(best)):
            best = run
    if not best:
        return None
    i = low.find(best.lower().replace("’", "'"))
    return [text[i:i + len(best)]]


def family_in(text):
    for fam in FAMILIES:
        if sum(1 for k in fam if k in text) >= 3:
            return list(fam)
    return None


def infer(it, text):
    """(entries, why_not)."""
    fam = family_in(text)
    if not fam:
        return None, "지문에 번호 기호가 없음"
    opts = it.get("options", [])
    out = []
    for i, k in enumerate(fam):
        pos = text.find(k)
        if pos < 0:
            continue
        after = text[pos + len(k):]
        ws = after[:len(after) - len(after.lstrip(" "))]
        o = opts[i] if i < len(opts) else ""
        phrase = LABEL.sub("", o).strip()
        if not phrase or not after.lstrip(" ").startswith(phrase):
            return None, f"{k} 선지 「{o}」 가 기호 뒤 글과 다름 — 「{after.strip()[:30]}」"
        out.append(f"{k}{ws}[{phrase}]")
    return out, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    filled = left = inline = 0
    todo = []
    for f in sorted(glob.glob(os.path.join(MOCK, "*세트.json"))):
        name = os.path.basename(f)[:-5]
        d = json.load(io.open(f, encoding="utf-8"))
        mats = {m["id"]: m for m in d["materials"]}
        changed = False
        for it in d["items"]:
            if it.get("underline"):
                continue
            key = (name, it["no"])
            text = mats.get(it.get("material_id"), {}).get("text", "")
            if key in MANUAL:
                it["underline"] = MANUAL[key]
                if key in STEM:
                    it["stem_ko"] = STEM[key]
                changed = True
                filled += 1
                continue
            # 「…단락의 마지막 문장에 쓰인 it」 은 자리를 말로 댄 것 — 발문 속 다른 영어(소제목)에 긋지 않는다
            if (it["type"] == "T-PHRASE-INFER" and re.search(r"가리키|의미하", it["stem_ko"])
                    and not re.search(r"번째|마지막", it["stem_ko"])):
                ents = phrase_ref(it, text)
                if ents:
                    it["underline"] = ents
                    changed = True
                    filled += 1
                continue
            if "밑줄" not in it["stem_ko"]:
                continue
            if _INLINE.search(text):
                inline += 1                    # 지문에 「①[…]」 로 이미 적힘 — 렌더러가 긋는다
                continue
            ents, why = infer(it, text)
            if ents:
                miss = locate(text, ents)[2]
                assert not miss, (key, miss)
                it["underline"] = ents
                changed = True
                filled += 1
            else:
                left += 1
                todo.append(f"{name} {it['no']}번 [{it['type']}] {it['stem_ko'][:40]!r} — {why}")
        if changed and a.apply:
            io.open(f, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print(f"채움 {filled} · 지문에 이미 [ ] {inline} · 못 채움 {left}")
    for t in todo:
        print("  " + t)
    if not a.apply:
        print("\n  보고만 했습니다 — --apply 로 씁니다.")


if __name__ == "__main__":
    sys.exit(main())
