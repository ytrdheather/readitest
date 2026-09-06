# -*- coding: utf-8 -*-
"""
새로 뽑은 지문에서 **표제어만** 확정본에 옮겨 담는다.

  python tools/merge_key_expressions.py --from <새로 뽑은 폴더>
  python tools/merge_key_expressions.py --from <폴더> --apply

**본문이 같은 지문만 병합한다.** 본문이 달라진 지문은 손대지 않고 목록으로 알린다 —
확정된 `body_text` 는 불변이고(설계원칙 7), 바뀌어야 한다면 그건 병합이 아니라
**새 레코드를 만드는 일**이라 판단이 따로 필요하다.

## 왜 통째로 다시 쓰지 않는가

`build_unit.py --write` 를 그냥 돌리면 확정본을 덮어쓴다. 그러면
`transcription.status` 가 `pending` 으로 돌아가고 원장이 194줄을 본 사실이 사라진다.
표제어는 `body_text` 와 무관한 속성이므로, 그것만 옮겨 담으면 확정을 유지할 수 있다.
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FIELDS = ("key_expressions", "vocab_headwords")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True, help="새로 뽑은 지문 폴더")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    news = {}
    for f in sorted(glob.glob(os.path.join(a.src, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        news[d["passage_id"]] = d

    same, changed, missing, merged = [], [], [], []
    for pid, nd in news.items():
        cur_path = os.path.join(PASSAGES, pid + ".json")
        if not os.path.exists(cur_path):
            missing.append(pid)
            continue
        cd = json.load(open(cur_path, encoding="utf-8"))
        if cd["body_text"] != nd["body_text"]:
            changed.append((pid, cd, nd))
            continue
        same.append(pid)
        payload = {k: nd.get(k, []) for k in FIELDS}
        if any(payload.values()) and any(cd.get(k) != payload[k] for k in FIELDS):
            merged.append((pid, cur_path, cd, payload))

    print("=" * 74)
    print(f" 표제어 병합 — {'실제 적용' if a.apply else '미리보기'}")
    print("=" * 74)
    print(f"  본문 같음 {len(same)}개 · 본문 달라짐 {len(changed)}개 · 확정본 없음 {len(missing)}개\n")

    if merged:
        print(f"  [병합할 것 {len(merged)}개]")
        for pid, _, _, payload in merged:
            for x in payload["key_expressions"]:
                print(f"    {pid:22} 문형  {x['pattern']}")
            for w in payload["vocab_headwords"]:
                print(f"    {pid:22} 어휘  {w}")
    else:
        print("  병합할 표제어 없음")

    if changed:
        print(f"\n  [🔴 본문이 달라진 지문 {len(changed)}개 — 병합하지 않았다]")
        print("     확정된 body_text 는 불변이다 (설계원칙 7). 고치려면 새 레코드를")
        print("     만들고 낡은 것을 물러나게 해야 하며, 그건 원장 판단이 필요하다.\n")
        for pid, cd, nd in changed:
            print(f"    {pid}")
            print(f"      확정본 : …{cd['body_text'][-90:]!r}")
            print(f"      새로뽑음: …{nd['body_text'][-90:]!r}")

    if not a.apply:
        print("\n  실제로 병합하려면 --apply")
        return 0

    for pid, path, cd, payload in merged:
        cd.update(payload)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cd, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    print(f"\n  {len(merged)}개 병합 완료 (transcription.status 는 건드리지 않음)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
