# -*- coding: utf-8 -*-
"""
전사 확정 — `transcription.status` 를 pending → confirmed 로 올린다.

  python tools/confirm_transcription.py                 # 무엇이 바뀌는지 보기만
  python tools/confirm_transcription.py --apply --by 원장

## 이건 되돌리기 어려운 문턱이다

확정된 `body_text` 는 **불변**이다 (설계원칙 7). 확정 뒤에 오타가 발견되면 조용히
고치면 안 된다 — 그 지문에 붙은 태그의 글자 위치(span)가 전부 밀리는데, 밀린 채로
그럴듯하게 작동하기 때문에 아무도 눈치채지 못한다. 고치려면 **새 레코드**를 만들고
낡은 것을 물러나게 한다.

그래서 이 도구는 무엇을 근거로 확정했는지(`confirmed_by` · `confirmed_at` ·
`confirmed_via`)를 함께 적는다. 나중에 「이건 누가 언제 무엇을 보고 확정했나」를
물을 수 있어야 한다.

## 확정하지 않는 것

`needs_review_sentences` 는 **지우지 않고 옮겨 둔다**(`reviewed_sentences`).
「검토가 필요했던 문장이 무엇이었나」는 나중에 품질을 되짚을 때 쓰는 정보다.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.passage import split_sentences   # noqa: E402  (확인지와 같은 기준으로 센다)

PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", default=None,
                    help="대상 파일 패턴 (여러 번 가능)")
    ap.add_argument("--by", default="원장", help="확정한 사람")
    ap.add_argument("--via", default="전사확인지_L5_L6.html 육안 대조",
                    help="무엇을 보고 확정했는지")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    pats = a.glob or ["L[56]_*.json", "영일중2_L[56]_*.json"]
    files = []
    for pat in pats:
        files += [f for f in sorted(glob.glob(os.path.join(PASSAGES, pat)))
                  if f not in files]

    print("=" * 74)
    print(f" 전사 확정 — {'실제 적용' if a.apply else '미리보기 (쓰지 않음)'}")
    print("=" * 74)
    print("  확정하면 body_text 는 불변이다 (설계원칙 7).")
    print("  뒤에 오타가 나오면 조용히 고치지 말고 새 레코드를 만든다.\n")

    done, already, lines = [], 0, 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        tr = d.get("transcription", {})
        # 확인지가 센 것과 **같은 방식**으로 센다. 다른 방식으로 세면 원장이 확인한
        # 줄 수와 여기 찍히는 줄 수가 달라져서, 무엇을 확정한 건지 흐려진다.
        n = len(d.get("turns") or []) or len(split_sentences(d["body_text"]))
        if tr.get("status") == "confirmed":
            already += 1
            continue
        lines += n
        done.append((f, d, n))

    for _, d, n in done:
        print(f"   {d['passage_id']:44} {n:>3}줄  {d['transcription'].get('method','')}")
    print(f"\n  확정 대상 {len(done)}개 · {lines}줄 · 이미 확정 {already}개")

    if not a.apply:
        print("\n  실제로 쓰려면 --apply --by <이름>")
        return 0

    now = datetime.now(timezone.utc).isoformat()
    for f, d, _ in done:
        tr = d["transcription"]
        tr["status"] = "confirmed"
        tr["confirmed_by"] = a.by
        tr["confirmed_at"] = now
        tr["confirmed_via"] = a.via
        # 지우지 않고 옮긴다 — 무엇이 검토 대상이었는지는 남겨 둘 값이다
        if tr.get("needs_review_sentences"):
            tr["reviewed_sentences"] = tr.pop("needs_review_sentences")
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    print(f"\n  {len(done)}개 확정 완료 · {a.by} · {now[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
