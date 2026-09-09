# -*- coding: utf-8 -*-
"""
어법 드릴의 오답을 검수한다 — 「그 오답이 정말 틀렸는가」.

  python tools/verify_drill_grammar.py                 # 미리보기
  python tools/verify_drill_grammar.py --run

## 왜 따로 도는가

`make_drill_grammar.py` 의 검사는 **구조**만 본다 — 정답이 본문과 같은가,
오답이 본문에 실재하는가. 「영어로서 틀렸는가」는 구조로 알 수 없다.

실물을 뽑아 보고 찾았다. `How long will it take?` 의 오답으로 나온
`How long will that take?` 는 **문법적으로 멀쩡한 문장**이다. 뜻만 다르다.
그런데 학습지 B절은 「밑줄 친 부분이 어법상 틀렸습니다」라고 단정한다 —
맞는 문장을 틀렸다고 가르치게 된다.

생성과 검수를 **다른 호출로** 나눈 이유도 그것이다. 같은 호출 안에서
「만들고 스스로 검사하라」고 하면 자기가 만든 것을 통과시킨다.
"""
import argparse
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import drill_grammar                                   # noqa: E402
from pipeline.env import load_env                                    # noqa: E402
from pipeline.models import Cost, client                             # noqa: E402
from pipeline.pass_a import extract_json                             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DRILLS = os.path.join(ROOT, "data", "generated", "drills")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--force", action="store_true", help="이미 검수한 것도 다시")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(DRILLS, "*.gram.json")))
    todo = []
    for f in files:
        d = json.load(io.open(f, encoding="utf-8"))
        if d.get("verified") and not a.force:
            print(f"  건너뜀(검수 완료): {os.path.basename(f)}")
            continue
        todo.append((f, d))

    n_cand = sum(len(w) for _, d in todo for it in d["items"] for w in [it["wrong"]])
    n_cand = sum(len(it["wrong"]) for _, d in todo for it in d["items"])
    print(f"\n  검수 대상 {len(todo)}세트 · 오답 후보 {n_cand}개")
    if not a.run:
        print("  [미리보기] 호출하지 않습니다. 실제로 하려면 --run")
        return 0

    env = load_env()
    api = client(env)
    cost = Cost()
    tot_drop_w = tot_drop_i = 0
    for f, d in todo:
        params = drill_grammar.build_verify_params(d["unit"], d["items"])
        msg = api.messages.create(**params)
        cost.add(d["unit"], params["model"], msg.usage)
        kept, dropped = drill_grammar.apply_verify(d["items"], extract_json(msg))

        n_w = sum(len(it.get("verify_dropped", [])) for it in kept)
        tot_drop_w += n_w
        tot_drop_i += len(dropped)
        d["items"] = kept
        d["verified"] = True
        d["diagnostics"]["verify"] = {
            "dropped_items": [list(x) for x in dropped],
            "dropped_wrongs": n_w,
        }
        io.open(f, "w", encoding="utf-8").write(
            json.dumps(d, ensure_ascii=False, indent=2) + "\n")

        print(f"\n  {d['unit']}")
        print(f"    문항 {len(kept)} 유지 · 문항째 버림 {len(dropped)} · 오답만 버림 {n_w}")
        for s, why in dropped[:4]:
            print(f"      ! {s!r} — {why}")
        for it in kept:
            for v in it.get("verify_dropped", [])[:0]:
                pass

    print()
    cost.report()
    print(f"\n  실은 맞는 표현이라 버린 오답 {tot_drop_w}개 · 통째로 버린 문항 {tot_drop_i}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
