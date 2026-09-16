# -*- coding: utf-8 -*-
"""
자체 드릴을 **학교 × 과 한 권**으로 엮는다 — 문제 한 권, 정답지 한 권.

  python tools/build_school_drills.py            # 네 학교 · 모든 과
  python tools/build_school_drills.py --school 영덕중

    result/readitude/영덕중2 5과 리디튜드 자체드릴.pdf
    result/readitude/영덕중2 5과 리디튜드 자체드릴 정답지.pdf

파일 이름은 result/이그잼포유/ 와 같은 꼴이다 — 학교 뒤에 학년 숫자, 그다음 과.
과를 따로 두는 이유: 영덕은 6과를 먼저 배우고 나머지는 5과를 먼저 배운다. 한 권에
두 과를 넣으면 학교마다 순서를 뒤집어야 하는데, 과별로 두면 집는 순서만 다르면 된다.

## 차례 — 원장 지정 (2026-09-16)

    어휘 → 대화문 → 본문(Read More · 본문) → 외부지문

지문 하나에는 내용 확인(우리말 → 영어) → 표현 바꿔쓰기 → 어법 순으로 붙는다.

## 학교마다 다른 것

  어휘      배부물이 학교마다 달라 세트가 갈린다. 어느 학교 것인지는 세트 제목에 적혀 있다
            ('L5 어휘 — 영일·태장·청명'). 목록을 손으로 들고 있지 않고 제목을 읽는다.
  외부지문   학교가 자기 배부물로 낸 지문. EXTERNAL 에 적는다.
  대화·본문  교과서가 같으니 네 학교 공통.

## build_drill_pdf.py 와 다른 점

그쪽은 **드릴 종류별** 8권이다 — 1차 우리말을 먼저 주고 2차 영어를 일주일 뒤에 주는
배부 순서가 권이 됐다. 이쪽은 **학교 × 과** 두 권씩이다. 강사가 "영덕 5과" 하나만 집으면 된다.
렌더러와 Chrome 변환은 그쪽 것을 그대로 쓴다.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pypdf import PdfReader, PdfWriter                                # noqa: E402
from tools.build_drill_pdf import DRILLS, ORDER, find_chrome, to_pdf  # noqa: E402
from tools.render_drill_tf import build as build_tf                   # noqa: E402
from tools.render_drill_vocab import build as build_vocab             # noqa: E402
from tools.render_drill_grammar import build as build_gram            # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = os.path.join(ROOT, "result", "readitude")
SCHOOLS = ["영일중", "영덕중", "태장중", "청명중"]
GRADE = "2"          # 드릴은 동아 윤정미 중2 5·6과 (Street Art in London · Dr. Schofield)

# 외부지문 → 학교. 자기 학교 배부물이라 다른 학교에는 안 준다.
EXTERNAL = {
    "A girl with a red balloon": ["영일중"],
    "Yu Gwansun": ["영덕중"],
    "Homer Hulbert": ["영덕중"],
}

SECTION = {"textbook_dialogue": "대화문", "textbook_reading": "본문", "handout_external": "외부지문"}

# 지문 하나에 붙는 드릴 순서: (파일 꼬리, 언어, 책갈피 이름)
DRILL_SEQ = [
    ("tf",   "ko", "내용 확인 (우리말)"),
    ("tf",   "en", "내용 확인 (영어)"),
    ("para", "ko", "바꿔쓰기 (우리말)"),
    ("para", "en", "바꿔쓰기 (영어)"),
    ("gram", None, "어법"),
]


def load_all():
    """drills/*.json 을 지문 단위로 묶는다. {unit: {kind, lesson, drills: {tf, para, gram}}}"""
    passages, vocab = {}, []
    for p in sorted(glob.glob(os.path.join(DRILLS, "*.json"))):
        name = os.path.basename(p)[:-5]
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if name.endswith(".vocab"):
            vocab.append((name, p, d))
            continue
        suffix = name.rsplit(".", 1)[-1]           # tf / para / gram
        u = passages.setdefault(d["unit"], {"kind": d["kind"], "drills": {}})
        u["lesson"] = d["unit"].split()[0]         # 'L5' / 'L6'
        u["drills"][suffix] = (name, p, d)
    return passages, vocab


def passage_rank(drills):
    """같은 구역 안에서 지문을 늘어놓는 순서 — build_drill_pdf.ORDER 를 따른다."""
    tf = drills.get("tf")
    if tf and tf[0] in ORDER:
        return ORDER.index(tf[0])
    return len(ORDER)


def vocab_schools(d):
    """어휘 세트 제목에서 대상 학교를 읽는다. '네 학교' 면 전부."""
    tail = d.get("title", "").split("—", 1)[-1]
    if "네 학교" in tail:
        return set(SCHOOLS)
    return {s for s in SCHOOLS if s[:-1] in tail}


def plan_for(school, L, passages, vocab):
    """학교 한 곳 · 과 하나의 차례. [(구역, 지문 제목, [(렌더 종류, 파일, json, 언어, 이름)])]"""
    plan = []

    for name, p, d in vocab:
        if L in d.get("title", "") and school in vocab_schools(d):
            plan.append(("어휘", d["title"], [("vocab", p, d, None, "어휘")]))

    for sec_kind, sec in SECTION.items():
        units = [(u, v) for u, v in passages.items()
                 if v["kind"] == sec_kind and v["lesson"] == L]
        units.sort(key=lambda uv: passage_rank(uv[1]["drills"]))
        for unit, v in units:
            if sec_kind == "handout_external":
                owners = [s for t, ss in EXTERNAL.items() if t in unit for s in ss]
                if not owners:
                    print(f"  ! 외부지문 주인을 모른다 — EXTERNAL 에 적을 것: {unit}")
                    continue
                if school not in owners:
                    continue
            steps = []
            for suffix, lang, label in DRILL_SEQ:
                if suffix not in v["drills"]:
                    continue
                name, p, d = v["drills"][suffix]
                if lang == "en" and not any(x.get("statement_en") for x in d["items"]):
                    continue
                steps.append((suffix, p, d, lang, label))
            if steps:
                plan.append((sec, unit, steps))
    return plan


class Renderer:
    """(json, 언어, 부분) 하나를 PDF 한 번만 만든다. 네 학교가 같은 지문을 공유한다."""

    def __init__(self, chrome, tmp, logo):
        self.chrome, self.tmp, self.logo, self.cache = chrome, tmp, logo, {}

    def pdf(self, suffix, path, d, lang, part):
        key = (path, lang, part)
        if key not in self.cache:
            n = len(self.cache)
            html = os.path.join(self.tmp, f"{n:03d}.html")
            pdf = os.path.join(self.tmp, f"{n:03d}.pdf")
            if suffix == "vocab":
                body = build_vocab(d, self.logo, part)
            elif suffix == "gram":
                body = build_gram(d, self.logo, part)
            else:
                body = build_tf(d, self.logo, lang, part)
            with open(html, "w", encoding="utf-8") as f:
                f.write(body)
            to_pdf(self.chrome, html, pdf)
            self.cache[key] = pdf
        return self.cache[key]


def assemble(plan, renderer, part, dest):
    """차례대로 붙이고 구역 › 지문 › 드릴 책갈피를 단다."""
    w = PdfWriter()
    sec_item, cur_sec = None, None
    n_sets = 0
    for sec, title, steps in plan:
        pas_item = None
        for suffix, p, d, lang, label in steps:
            r = PdfReader(renderer.pdf(suffix, p, d, lang, part))
            if not r.pages:
                continue
            start = len(w.pages)
            for pg in r.pages:
                w.add_page(pg)
            if pas_item is None:
                if sec != cur_sec:
                    sec_item = w.add_outline_item(sec, start)
                    cur_sec = sec
                pas_item = w.add_outline_item(title, start, parent=sec_item)
            w.add_outline_item(label, start, parent=pas_item)
            n_sets += 1
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        w.write(f)
    return n_sets, len(w.pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--school", action="append", help="특정 학교만 (여러 번 가능)")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    schools = a.school or SCHOOLS

    passages, vocab = load_all()
    chrome = find_chrome()
    logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="schooldrill_")
    renderer = Renderer(chrome, tmp, logo)
    print(f"  지문 {len(passages)}개 · 어휘 {len(vocab)}세트\n")
    try:
        lessons = sorted({v["lesson"] for v in passages.values()})      # L5, L6, …
        for school in schools:
            for L in lessons:
                plan = plan_for(school, L, passages, vocab)
                if not plan:
                    continue
                lesson = L[1:] + "과"                                     # L5 → 5과
                print(f"■ {school}{GRADE} {lesson} — {len(plan)}지문")
                for sec, title, steps in plan:
                    print(f"     {sec:<5} {title[:38]:<40} {' · '.join(s[4] for s in steps)}")
                base = os.path.join(a.out, f"{school}{GRADE} {lesson} 리디튜드 자체드릴")
                for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
                    n, pages = assemble(plan, renderer, part, base + suffix + ".pdf")
                    print(f"   → {os.path.basename(base)}{suffix}.pdf   {n}세트 · {pages}쪽")
                print()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("  문제와 정답지는 다른 파일입니다. 정답지는 강사만 가지십시오.")


if __name__ == "__main__":
    sys.exit(main())
