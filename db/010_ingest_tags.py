# -*- coding: utf-8 -*-
"""
패스 A 결과에서 **태그와 논리만** DB 에 적재한다.

  python db/010_ingest_tags.py              # 검증만
  python db/010_ingest_tags.py --apply

**INSERT 뿐이다. DELETE · DROP · TRUNCATE 없음** (CLAUDE.md 규칙 4).
이미 태그가 있는 지문은 건너뛴다 — 두 번 돌리면 태그가 두 벌 쌓이고
커버리지·과잉률이 조용히 두 배로 잡힌다.

## 문항(item)은 넣지 않는다

패스 A 는 태깅과 함께 문항도 만든다. 이번에 308개가 나왔다. 그런데 그것들은
「승인된 12유형을 골고루」 만든 것이지, 원장이 2026-09-05 에 정한 **산출물 3층**
(1층 드릴 → 2층 예상 타겟 → 3층 동형)을 따른 것이 아니다.

지금 넣으면 검수 부채 308건이 생기는데, 어차피 1층 드릴 형식이 정해지면 그 형식으로
다시 만들어야 한다. 파일에는 그대로 남아 있으므로 나중에 재료로 쓸 수 있다.
**작업 순서는 분석 정교화 → 드릴 → 동형이다** (§5.5.8 ⑥).

## 해시를 대조한다

패스 A 결과에는 그때 쓴 지문의 `body_text_sha256` 이 들어 있다. DB 의 해시와
다르면 **그 사이에 본문이 바뀐 것**이므로 스팬이 어긋난다. 그런 지문은 넣지 않고
멈춘다 — 실제로 L5 대화-1·4 가 본문이 바뀌어 재태깅했다.
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

GEN = os.path.join(ROOT, "data", "generated")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = Rest()

    pgs = r.get("/passage?select=id,title,body_text,body_text_sha256,transcription_status")
    by_id = {p["id"]: p for p in pgs}
    by_title = {p["title"]: p for p in pgs}
    points = {g["code"] for g in r.get("/grammar_point?select=code")}
    # 물러난 태그(rejected)는 「있는 것」으로 세지 않는다. 그래야 재태깅한 지문을
    # 다시 넣을 수 있다. 물러난 것은 무엇이 있었는지의 기록으로만 남는다.
    tagged = {t["passage_id"] for t in r.get("/passage_tag?select=passage_id,status")
              if t["status"] != "rejected"}
    # 논리 태깅은 (passage_id, sentence_no) 가 unique 라 두 번 넣으면 충돌한다.
    # 재태깅해도 문장 번호는 그대로이므로 이미 있으면 건너뛴다.
    logged = {l["passage_id"] for l in r.get("/passage_logic?select=passage_id")}

    print("=" * 74)
    print(f" 태그·논리 적재 — {'실제 적용' if a.apply else '검증만'}")
    print("=" * 74)
    print("  실행 SQL: INSERT 만. DELETE / DROP / TRUNCATE 없음.")
    print("  문항(item)은 넣지 않는다 — 드릴 형식이 정해진 뒤에 만든다.\n")

    tag_rows, logic_rows, skipped, problems = [], [], [], []
    for f in sorted(glob.glob(os.path.join(GEN, "*.pass_a.json"))):
        d = json.load(open(f, encoding="utf-8"))
        name = os.path.basename(f)[:-12]
        pid = d.get("passage_id")
        pg = by_id.get(pid) or by_title.get(pid) or by_title.get(name.replace("_", " "))
        if pg is None:
            pg = next((v for k, v in by_title.items() if k.startswith(name[:20])), None)
        if pg is None:
            skipped.append((name, "DB 에 지문이 없음 (전사 미확정 등)"))
            continue
        if pg["transcription_status"] == "disputed":
            skipped.append((name, "물러난 지문"))
            continue
        if d.get("body_text_sha256") and d["body_text_sha256"] != pg["body_text_sha256"]:
            problems.append(f"{name}: 태깅 당시 본문과 DB 본문의 해시가 다름 — 스팬이 어긋난다")
            continue
        if pg["id"] in tagged:
            skipped.append((name, "이미 태그가 있음"))
            continue

        body = pg["body_text"]
        for i, t in enumerate(d.get("tags", [])):
            if t["grammar_point_code"] not in points:
                problems.append(f"{name} 태그 #{i}: 마스터에 없는 코드 {t['grammar_point_code']}")
                continue
            s, e = t["span_start"], t["span_end"]
            if not (0 <= s < e <= len(body)) or body[s:e] != t["surface"]:
                problems.append(f"{name} 태그 #{i}: 스팬이 본문과 불일치 — {t['surface']!r}")
                continue
            tag_rows.append({
                "passage_id": pg["id"],
                "grammar_point_code": t["grammar_point_code"],
                "span_start": s, "span_end": e, "surface": t["surface"],
                "rationale": t.get("rationale"),
                "confidence": t.get("confidence", "medium"),
                "status": "pending",
            })
        if pg["id"] not in logged:
            for l in d.get("logic", []):
                logic_rows.append({
                    "passage_id": pg["id"],
                    "sentence_no": l["sentence_no"],
                    "role": l["role"],
                    "signal": l.get("signal"),
                    "is_blank_candidate": bool(l.get("is_blank_candidate")),
                })

    if problems:
        print(f"  X 문제 {len(problems)}건 — 아무것도 넣지 않습니다\n")
        for p in problems[:20]:
            print("    ", p)
        return 1

    print(f"  태그 {len(tag_rows)}행 · 논리 {len(logic_rows)}행")
    if skipped:
        print(f"\n  건너뜀 {len(skipped)}개")
        for n, why in skipped:
            print(f"     {n[:40]:42} {why}")

    if not a.apply:
        print("\n  실제로 넣으려면 --apply")
        return 0

    for i in range(0, len(tag_rows), 200):
        r.insert("passage_tag", tag_rows[i:i + 200])
    for i in range(0, len(logic_rows), 200):
        r.insert("passage_logic", logic_rows[i:i + 200])
    print(f"\n  적재 완료 · passage_tag {len(r.get('/passage_tag?select=id'))}행 · "
          f"passage_logic {len(r.get('/passage_logic?select=id'))}행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
