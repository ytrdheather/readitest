# -*- coding: utf-8 -*-
"""
한국어 O/X 드릴에 **영어 진술을 덧붙인다.**

  python tools/make_drill_en.py data/generated/drills/*.tf.json --run

원장 지시(2026-09-07): 「한국어로 한 것을 1차로 본 후에 1주일 뒤에 영어로 한 것을
다시 보라고 하면 완전학습이 되잖아.」

**새 문항을 만들지 않는다.** 같은 문항의 진술만 영어로 옮긴다 — 문항이 달라지면
「같은 것을 다시」가 아니라 「다른 것을 또」가 되고 간격 반복의 값이 사라진다.
정답과 근거 문장은 그대로다.

결과는 같은 JSON 안의 `statement_en` 으로 들어간다. 파일을 따로 두지 않는 이유는,
두 판이 **같은 문항**이라는 것이 파일 구조로도 드러나야 하기 때문이다.
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import drill_tf                                        # noqa: E402
from pipeline.env import load_env                                    # noqa: E402
from pipeline.models import Cost, client                             # noqa: E402
from pipeline.pass_a import extract_json                             # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help=".tf.json / .para.json")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--force", action="store_true", help="이미 영어가 있어도 다시")
    a = ap.parse_args()

    paths = []
    for f in a.files:
        paths += sorted(glob.glob(f)) or [f]

    env = load_env()
    api = client(env) if a.run else None
    cost = Cost()

    for path in paths:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        items = d["items"]
        done = sum(1 for x in items if x.get("statement_en"))
        if done == len(items) and not a.force:
            print(f"  건너뜀  {d['unit']}  (이미 영어 {done}개)")
            continue
        print(f"  {d['unit'][:34]:36} 문항 {len(items)}개", end="")
        if not a.run:
            print("   [미리보기]")
            continue

        params = drill_tf.build_en_params(d["unit"], d["sentences"], items)
        msg = api.messages.create(**params)
        missing = drill_tf.merge_en(items, extract_json(msg))
        cost.add(d["unit"], params["model"], msg.usage)
        print(f"   → 영어 {len(items) - len(missing)}개"
              + (f"  ! 빠짐 {missing}" if missing else ""))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")

    if a.run:
        print()
        cost.report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
