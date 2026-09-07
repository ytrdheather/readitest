# -*- coding: utf-8 -*-
"""
내용일치 O/X 드릴을 만든다.

  python tools/make_drill_tf.py --unit "Street Art in London"      # 미리보기(호출 안 함)
  python tools/make_drill_tf.py --unit "Street Art in London" --run

`--unit` 은 **본문 한 편**을 가리킨다. DB 에 문단이 나뉘어 있으면 제목 앞부분이 같은
것을 모아 합친다 — `Street Art in London-1~4` → 한 편.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import drill_tf                                        # noqa: E402
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


def gather(rest, units):
    """제목이 units 중 하나로 시작하는 확정 지문을 모아 한 편으로 잇는다.

    본문은 `--unit "Street Art in London"` 하나로 네 문단이 잡힌다.
    대화문은 짧아서(중앙값 44단어) 한 편으로는 학습지가 안 되므로
    `--unit "L5 대화-1" --unit "L5 대화-2" …` 처럼 여러 개를 묶는다.
    """
    rows = [p for p in rest.get("/passage?select=id,title,kind,body_text,transcription_status")
            if p["transcription_status"] == "confirmed"
            and any((p["title"] or "").lower().startswith(u.lower()) for u in units)]
    if not rows:
        return None

    def order(p):
        t = p["title"] or ""
        for i, u in enumerate(units):                     # 준 순서를 지킨다
            if t.lower().startswith(u.lower()):
                m = re.search(r"-(\d+)$", t)
                return (i, int(m.group(1)) if m else 0)
        return (99, 0)
    rows.sort(key=order)
    body = "\n".join(p["body_text"] for p in rows)
    # 문단 경계를 문장 번호로 남긴다. 합쳐 놓고 나면 어디서 끊겼는지 알 수 없는데,
    # 학습지에서는 원래 문단대로 보여야 아이가 교과서와 같은 모양으로 읽는다.
    breaks, turns, acc = [], [], 0
    for p_ in rows:
        # 대화문은 **발화마다 줄을 바꾼다** (원장 지시 2026-09-07: 「한 명의 대사가
        # 한 줄에 자리잡도록. 세로로 3단을 차지하는 한이 있어도 눈에 잘 보이게」).
        # 한 발화에 문장이 여럿일 수 있으므로(‘…to find. Why don’t you take a taxi?’)
        # 발화 경계도 문장 번호로 따로 세어 둔다.
        for line in p_["body_text"].split("\n"):
            if line.strip():
                acc += len(split_sentences(line))
                turns.append(acc)
        breaks.append(acc)
    title = units[0] if len(units) == 1 else f"{units[0]} 외 {len(units)-1}"
    return {"title": title, "kind": rows[0]["kind"], "parts": [p["title"] for p in rows],
            "ids": [p["id"] for p in rows], "body": body,
            "para_breaks": breaks, "turn_breaks": turns}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", action="append", required=True,
                    help="지문 제목 (앞부분 일치). 여러 번 주면 묶는다")
    ap.add_argument("--title", help="학습지 제목 (기본: 첫 --unit)")
    ap.add_argument("--items", type=int, help="문항 수 (기본: 문장 수)")
    ap.add_argument("--mode", choices=["content", "paraphrase"], default="content",
                    help="content=내용 확인(전 문장) · paraphrase=표현 바꿔쓰기")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    env = load_env()
    u = gather(Rest(env), a.unit)
    if not u:
        raise SystemExit(f"{a.unit} 로 시작하는 확정 지문이 없습니다")
    if a.title:
        u["title"] = a.title

    sents = [t for _, _, _, t in split_sentences(u["body"])]
    n = a.items or len(sents)          # 원장 지정: 문장 하나당 대략 한 문항

    print("=" * 74)
    print(f" {'표현 바꿔쓰기' if a.mode == 'paraphrase' else '내용 확인'} O/X 드릴 — {u['title']}")
    print("=" * 74)
    print(f"  묶은 지문 {len(u['parts'])}개: {' · '.join(u['parts'])}")
    print(f"  문장 {len(sents)} · 만들 문항 {n}개 안팎\n")

    params = drill_tf.build_params(u["title"], u["kind"], sents, n, a.mode)
    if not a.run:
        print("  [미리보기] 호출하지 않습니다. 실제로 만들려면 --run")
        print(f"  system {len(params['system'][0]['text']):,}자 · "
              f"user {len(params['messages'][0]['content']):,}자")
        return 0

    api = client(env)
    msg = api.messages.create(**params)
    result = drill_tf.parse(extract_json(msg), sents)
    d = result["diagnostics"]

    print(f"  문항 {d['kept']}/{d['returned']} 유지 · O {d['answer_balance']['O']} / "
          f"X {d['answer_balance']['X']} · 문장 {d['sentences_covered']}/{d['sentence_count']} 덮음"
          + (f" · 중복근거 {d['repeated']}" if d["repeated"] else ""))
    for i, why in d["rejects"]:
        print(f"    ! 문항 #{i} 버림 — {why}")

    print()
    for i, it in enumerate(result["items"], 1):
        print(f"  {i:>2}. [{it['answer']}] {it['statement_ko']}")
        print(f"      근거 {it['evidence_sentences']} · {it['why_ko']}")

    os.makedirs(OUT, exist_ok=True)
    slug = re.sub(r"[^0-9A-Za-z가-힣]+", "_", u["title"])[:40]
    suffix = ".tf.json" if a.mode == "content" else ".para.json"
    path = os.path.join(OUT, f"{slug}{suffix}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"unit": u["title"], "parts": u["parts"], "passage_ids": u["ids"],
                   "para_breaks": u["para_breaks"], "turn_breaks": u["turn_breaks"],
                   "kind": u["kind"], "sentences": sents, **result},
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
    cost = Cost()
    cost.add(u["title"], params["model"], msg.usage)
    print()
    cost.report()
    print(f"\n  저장 → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
