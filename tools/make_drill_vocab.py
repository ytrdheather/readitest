# -*- coding: utf-8 -*-
"""
어휘 드릴을 만든다. **API 를 부르지 않는다** — 재료가 이미 파일에 있다.

  python tools/make_drill_vocab.py --set 태장_L5
  python tools/make_drill_vocab.py --all

## 어느 목록을 누구에게 주는가

[어휘 대조](../data/stage0/comparisons/어휘_자습서_학교_대조.md) 의 결론이다.

    영일·태장·청명 L5   태장 37개(영일을 통째로 덮는다) + 자습서 나머지
    영덕 L5            자습서 54개  ← 배부물이 약 9/22 도착이라 관측이 없다
    네 학교 L6          영덕 32개(단어장 ∪ Warm-Up) + 자습서 나머지

학교 목록은 **배제가 아니라 우선순위**다 (§5.5.15). 그래서 「학교분」과
「자습서 나머지」를 **한 부 안에서 갈라** 낸다 — 아이는 다 풀되 무엇이 학교가
직접 준 것인지 강사가 안다.
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import drill_vocab                                     # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VOCAB = os.path.join(ROOT, "data", "stage0", "vocab")
OUT = os.path.join(ROOT, "data", "generated", "drills")


def load(name):
    return json.load(io.open(os.path.join(VOCAB, f"{name}.json"), encoding="utf-8"))


def key(w):
    return re.sub(r"\s+", " ", w.strip().lower())


def norm(w, src):
    """서로 다른 파일의 낱말 레코드를 한 모양으로 맞춘다."""
    return {"word": w["word"],
            "ko": w.get("ko") or w.get("gloss_ko") or "",
            "def_en": w.get("def_en") or w.get("workbook_definition_en")
                      or (w.get("definition_en") if w.get("definition_en") != "None" else "")
                      or "",
            "example_en": w.get("example_en") or "",
            "example_ko": w.get("example_ko") or "",
            "page": w.get("page"),
            "src": src}


def merge(school_files, jasup_file):
    """학교분을 앞에, 자습서에만 있는 것을 뒤에. 같은 낱말은 **정보가 많은 쪽**으로."""
    school = {}
    for f in school_files:
        d = load(f)
        for w in d["words"]:
            k = key(w["word"])
            cand = norm(w, "학교")
            old = school.get(k)
            if not old or _rich(cand) > _rich(old):
                # 둘 다 있으면 빈 칸만 서로 채운다 — 한쪽에만 예문이 있는 일이 흔하다
                if old:
                    for fld in ("ko", "def_en", "example_en", "example_ko"):
                        cand[fld] = cand[fld] or old[fld]
                school[k] = cand
            else:
                for fld in ("ko", "def_en", "example_en", "example_ko"):
                    old[fld] = old[fld] or cand[fld]
    # 학교 레코드의 **빈 칸을 자습서로 채운다.**
    # 태장 1쪽은 뜻 칸이 학생 손글씨인 낱말이 있어 우리가 옮기지 않았고(원장 지시
    # 2026-09-05), 영일 파일은 애초에 우리말 뜻이 없다. 그대로 두면 「우리말 → 영어」
    # 문항의 문제 칸이 비어 버린다 — 못 푸는 문항이 된다.
    # 낱말이 같으면 뜻도 같으므로 자습서에서 가져오는 것이 안전하다.
    extra = {}
    for w in load(jasup_file)["words"]:
        k = key(w["word"])
        j = norm(w, "자습서")
        if k in school:
            s = school[k]
            for fld in ("ko", "def_en", "example_en", "example_ko"):
                s[fld] = s[fld] or j[fld]
        else:
            extra[k] = j
    return list(school.values()), list(extra.values())


def _rich(w):
    return sum(1 for f in ("ko", "def_en", "example_en", "example_ko") if w.get(f))


# 세트 = (제목, 학교 원천들, 자습서 원천, 구(句) 원천)
SETS = {
    "태장_L5": ("동아 윤정미 L5 어휘 — 영일·태장·청명",
                ["태장중2_L5_vocab_handout", "영일중2_L5_vocab_handout"], "L5_vocab", None),
    "영덕_L5": ("동아 윤정미 L5 어휘 — 영덕 (배부물 미도착, 자습서 전체)",
                [], "L5_vocab", None),
    "영덕_L6": ("동아 윤정미 L6 어휘 — 네 학교",
                ["영덕중2_L6_vocab_handout", "영덕중2_L6_warmup"], "L6_vocab",
                "영덕중2_L6_warmup"),
    # 중1. 제목에 '중1' 을 넣는다 — build_school_drills 가 학년을 제목에서 읽는다.
    "영덕중1_L5": ("동아 윤정미 중1 L5 어휘 — 영덕",
                  ["영덕중1_L5_vocab_handout"], "중1_L5_vocab", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", choices=sorted(SETS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=20260909)
    a = ap.parse_args()

    names = sorted(SETS) if a.all else (a.set or [])
    if not names:
        raise SystemExit("--set 또는 --all 을 주십시오. 세트: " + ", ".join(sorted(SETS)))

    os.makedirs(OUT, exist_ok=True)
    for name in names:
        title, sfiles, jfile, pfile = SETS[name]
        school, extra = merge(sfiles, jfile)
        phrases = []
        if pfile:
            phrases = [{"phrase": p["phrase"], "ko": p["ko"]}
                       for p in load(pfile).get("phrases", [])]

        print("=" * 74)
        print(f" {title}")
        print("=" * 74)
        print(f"  학교분 {len(school)}개 · 자습서에만 {len(extra)}개 · 합 {len(school)+len(extra)}")

        parts = []
        if school:
            parts.append(("학교가 직접 준 낱말", drill_vocab.build(
                title, school, seed=a.seed, phrases=phrases)))
        if extra:
            parts.append(("자습서에만 있는 낱말", drill_vocab.build(
                title, extra, kinds=("both", "def", "cloze"), seed=a.seed + 1)))

        for label, part in parts:
            print(f"    · {label}: " + " · ".join(
                f"{k} {v}" for k, v in part["counts"].items()))

        path = os.path.join(OUT, f"{name}.vocab.json")
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump({"set": name, "title": title,
                       "sources": {"school": sfiles, "jasup": jfile},
                       "parts": [{"label": l, **p} for l, p in parts]},
                      f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  저장 → {path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
