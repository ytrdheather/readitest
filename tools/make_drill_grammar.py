# -*- coding: utf-8 -*-
"""
어법 확인 드릴을 만든다.

  python tools/make_drill_grammar.py                 # 미리보기(호출 안 함)
  python tools/make_drill_grammar.py --run

## 재료

`passage_tag` 의 **pending 317개** (L5·L6 전 지문, 2026-09-07 재태깅분).
승인된 38개는 1학기 자료(`goose` · `impulse buying`)라 이번 범위가 아니다.

> ⚠️ 이 드릴은 **아직 승인되지 않은 태그** 위에 서 있다. 1층 드릴은 「예상 문항」이
> 아니라 기초 숙지 확인이므로(§5.5.12) 그대로 만들되, 강사용 정답지에 포인트 코드와
> 근거를 함께 찍는다 — **드릴을 검토하는 것이 곧 태그를 검토하는 것**이 되게 한다.

## 묶는 단위는 지문 한 편

설계원칙 3: 문항 기본 단위는 지문. `Street Art in London-1~4` 처럼 문단이 나뉜
것은 합쳐서 한 편으로 다룬다 — 드릴 b 와 같은 방식이고, 문장 번호도 같다.
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import drill_grammar                                   # noqa: E402
from pipeline.env import load_env                                    # noqa: E402
from pipeline.models import Cost, client                             # noqa: E402
from pipeline.passage import split_sentences                         # noqa: E402
from pipeline.pass_a import extract_json                             # noqa: E402
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = os.path.join(ROOT, "data", "generated", "drills")

# 드릴 b 와 같은 묶음·같은 차례. 아이가 받는 순서를 맞춘다.
UNITS = [
    ("L5 대화 ①②③ — 길 묻고 답하기", ["L5 대화-1", "L5 대화-2", "L5 대화-3"]),
    ("L5 대화 ④⑤⑥", ["L5 대화-4", "L5 대화-5", "L5 대화-6"]),
    ("L5 대화 ⑦⑧⑨", ["L5 대화-7", "L5 대화-8", "L5 대화-9"]),
    ("L5 Read More", ["L5 ReadMore-1", "L5 ReadMore-2",
                      "L5 ReadMore-3", "L5 ReadMore-4"]),
    ("L5 본문 — Street Art in London", ["Street Art in London-1", "Street Art in London-2",
                                        "Street Art in London-3", "Street Art in London-4"]),
    ("L6 대화 ①②③", ["L6 대화-1", "L6 대화-2", "L6 대화-3"]),
    ("L6 대화 ④⑤⑥", ["L6 대화-4", "L6 대화-5", "L6 대화-6"]),
    ("L6 대화 ⑦⑧⑨", ["L6 대화-7", "L6 대화-8", "L6 대화-9"]),
    ("L6 Read More", ["L6 ReadMore-1", "L6 ReadMore-2",
                      "L6 ReadMore-3", "L6 ReadMore-4"]),
    ("L6 본문 — Dr. Schofield", ["Dr. Schofield, a Foreigner Who Loved Korea"]),
    ("L5 외부지문 — A girl with a red balloon", ["A girl with a red balloon"]),
    ("L6 외부지문 — Yu Gwansun", ["Yu Gwansun"]),
    ("L6 외부지문 — Homer B. Hulbert", ["Homer B. Hulbert"]),
    # 중1 (2026-09-18). 대화 8편이라 3·3·2. 제목 앞의 '중1' 로 중2 와 구분한다.
    ("중1 L5 대화 ①②③", ["중1 L5 대화-1", "중1 L5 대화-2", "중1 L5 대화-3"]),
    ("중1 L5 대화 ④⑤⑥", ["중1 L5 대화-4", "중1 L5 대화-5", "중1 L5 대화-6"]),
    ("중1 L5 대화 ⑦⑧", ["중1 L5 대화-7", "중1 L5 대화-8"]),
    ("중1 L5 본문 — Who Threw a Cake at the Monalisa?",
     ["중1 L5 본문 — Who Threw a Cake at the Monalisa?"]),
    ("중1 L7 대화 ①②③", ["중1 L7 대화-1", "중1 L7 대화-2", "중1 L7 대화-3"]),
    ("중1 L7 대화 ④⑤⑥", ["중1 L7 대화-4", "중1 L7 대화-5", "중1 L7 대화-6"]),
    ("중1 L7 대화 ⑦⑧", ["중1 L7 대화-7", "중1 L7 대화-8"]),
    ("중1 L7 본문 — Let’s Make a Movie!", ["중1 L7 본문 — Let’s Make a Movie!"]),
    ("중1 L7 외부지문 — Two Different Jobs", ["Two Different Jobs"]),
]
EXTERNAL = {"L5 외부지문 — A girl with a red balloon": "영일중 배부물",
            "L6 외부지문 — Yu Gwansun": "영덕중 배부물",
            "L6 외부지문 — Homer B. Hulbert": "영덕중 배부물",
            "중1 L7 외부지문 — Two Different Jobs": "영일중 배부물"}


def slug(title):
    CIRCLED = {chr(0x2460 + i): str(i + 1) for i in range(20)}
    t = "".join(CIRCLED.get(c, c) for c in title)
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "_", t).strip("_")[:40]
    if not s:
        raise SystemExit(f"제목에서 파일명을 못 만들었습니다: {title!r}")
    return s


def gather(rest):
    ps = {p["title"]: p for p in rest.get(
        "/passage?select=id,title,kind,body_text,transcription_status&limit=500")}
    tags = [t for t in rest.get(
        "/passage_tag?select=id,passage_id,grammar_point_code,surface,"
        "span_start,span_end,rationale,confidence,status&limit=2000")
        if t["status"] == "pending"]
    by_pid = {}
    for t in tags:
        by_pid.setdefault(t["passage_id"], []).append(t)

    units = []
    for title, parts in UNITS:
        rows = [ps[p] for p in parts if p in ps]
        if not rows:
            print(f"  ! 지문 없음, 건너뜀: {title}")
            continue
        body, off, utags = "", 0, []
        for p in rows:
            for t in sorted(by_pid.get(p["id"], []), key=lambda x: x["span_start"]):
                t = dict(t)
                t["span_start"] += off
                t["span_end"] += off
                utags.append(t)
            body += p["body_text"] + "\n"
            off = len(body)
        body = body.rstrip("\n")
        utags = [t for t in utags if t["span_end"] <= len(body)]
        units.append({"title": title, "kind": rows[0]["kind"],
                      "book": EXTERNAL.get(title, "동아 윤정미"),
                      "parts": [p["title"] for p in rows],
                      "body": body, "tags": utags})
    return units


def dedup(items):
    """겹치는 스팬이 **같은 오답**을 물으면 한 문항만 남긴다.

    태깅이 `How long will it take` 와 `will it take` 를 따로 잡아 둔 자리가 있다.
    둘 다 `takes` 를 묻게 되어 아이에게는 같은 문제가 두 번 나온다.
    좁은 쪽(더 구체적인 자리)을 남긴다 — 어디를 보라는 것인지가 분명하다.
    """
    order = sorted(items, key=lambda x: (x["span_end"] - x["span_start"]))
    kept, dropped = [], []
    for it in order:
        clash = None
        for k in kept:
            if k["sentence_no"] != it["sentence_no"]:
                continue
            overlap = (it["span_start"] < k["span_end"]
                       and k["span_start"] < it["span_end"])
            shared = {w.lower() for w in it["wrong"]} & {w.lower() for w in k["wrong"]}
            if overlap and shared:
                clash = k
                break
        if clash:
            dropped.append((it["correct"], f"{clash['correct']!r} 와 같은 오답을 물음"))
        else:
            kept.append(it)
    kept.sort(key=lambda x: (x["sentence_no"], x["span_start"]))
    return kept, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--only", help="제목 앞부분이 일치하는 것만")
    a = ap.parse_args()

    env = load_env()
    units = gather(Rest(env))
    if a.only:
        units = [u for u in units if u["title"].startswith(a.only)]

    total = sum(len(u["tags"]) for u in units)
    print("=" * 74)
    print(f" 어법 확인 드릴 — {len(units)}세트 · 태그 {total}개")
    print("=" * 74)
    for u in units:
        print(f"  {u['title'][:40]:42} 태그 {len(u['tags']):>3} · {len(u['body']):>5}자")
    if not a.run:
        print("\n  [미리보기] 호출하지 않습니다. 실제로 만들려면 --run")
        return 0

    api = client(env)
    cost = Cost()
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for u in units:
        if not u["tags"]:
            continue
        params = drill_grammar.build_params(u["title"], u["body"], u["tags"])
        msg = api.messages.create(**params)
        cost.add(u["title"], params["model"], msg.usage)
        res = drill_grammar.parse(extract_json(msg), u["tags"], u["body"])
        d = res["diagnostics"]

        sents = split_sentences(u["body"])
        items = []
        for it in res["items"]:
            no, text = drill_grammar.in_sentence(
                u["body"], it["span_start"], it["span_end"], sents)
            if not text:
                d["rejects"].append((it["correct"], "문장을 못 찾음"))
                continue
            items.append({**it, "sentence_no": no, "sentence": text})

        items, dropped = dedup(items)
        for s, why in dropped:
            d["rejects"].append((s, why))

        print(f"\n  {u['title']}")
        print(f"    문항 {len(items)}/{d['given']} · 모델 반환 {d['returned']}"
              + (f" · 버림 {len(d['rejects'])}" if d["rejects"] else ""))
        for s, why in d["rejects"][:6]:
            print(f"      ! {s!r} — {why}")

        path = os.path.join(OUT, f"{slug(u['title'])}.gram.json")
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump({"book": u["book"], "unit": u["title"], "kind": u["kind"],
                       "parts": u["parts"], "body": u["body"],
                       "tag_status": "pending",
                       "items": items, "diagnostics": d},
                      f, ensure_ascii=False, indent=2)
            f.write("\n")
        made += 1
    print()
    cost.report()
    print(f"\n  {made}세트 저장 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
