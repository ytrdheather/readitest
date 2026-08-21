# -*- coding: utf-8 -*-
"""
패스 A 평가 — 자동 태깅이 수동 태깅의 게이트 수치를 재현하는가.

0단계에서 원장이 손으로 태깅한 지문(goose)에는 **기출 정답지**가 붙어 있다.
블라인드 대조로 커버리지 1.00 / 과잉률 2.57 이 나왔고, 그게 0단계 통과 근거였다.
같은 지문에 파이프라인을 돌려 **같은 방식으로** 재채점한다. 이게 유일하게 의미 있는 질문이다:

    사람 없이 만든 태깅이 사람이 만든 태깅만큼 실제 출제 지점을 덮는가?

판정 규칙은 수동 대조와 동일하다 — 표면형이 아니라 **「같은 위치 · 같은 포인트」**.
시험 지문이 배부 지문과 달라서(교사가 변형함) 표면형 일치를 요구할 수 없기 때문이다.

  적중(hit)      : 기출 지점의 구간과 겹치고 grammar_point_code 도 같은 자동 태그가 있음
  위치만(pos)    : 구간은 겹치는데 코드가 다름 — 부분 적중. 커버리지에 넣지 않는다
  놓침(miss)     : 겹치는 태그가 아예 없음

  커버리지 = 적중 / 기출 지점 수          게이트 ≥ 0.90
  과잉률   = 태그 수 / 기출 지점 수        게이트 ≤ 3.00

사용:
  python tools/eval_pass_a.py
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S0 = os.path.join(ROOT, "data", "stage0")
GEN = os.path.join(ROOT, "data", "generated")

GATE_COVERAGE = 0.90
GATE_EXCESS = 3.00

CASES = [
    {
        "name": "goose (영덕중2 2025-2 중간 5과 학습지3 p2)",
        "gold": "compare",          # 기출 대조 파일의 details 7개
        "blind": False,
        "blind_note": "이 지문으로 프롬프트를 2회 고쳤다. 커버리지는 적합된 수치이지 블라인드가 아니다.",
        "generated": os.path.join(GEN, "goose_(5과_학습지_3).pass_a.json"),
        "manual_tags": os.path.join(S0, "tags", "영덕중2_2025-2-중간_5과학습지3_p2.tags.json"),
        "compare": os.path.join(S0, "comparisons",
                                "영덕중2_2025-2-중간_5과학습지3_p2.compare.json"),
        "passage": os.path.join(S0, "passages", "영덕중2_2025-2-중간_5과학습지3_p2.json"),
    },
    {
        "name": "impulse buying (영덕중2 2026-1 기말 L4)",
        "gold": "exam_underlined",  # 태깅 파일의 exam_underlined 7개 (기출 문항16 밑줄)
        "blind": True,
        "blind_note": "프롬프트를 이 지문에 맞춰 고친 적이 없다. 준-블라인드 수치.",
        "generated": os.path.join(GEN, "impulse_buying.pass_a.json"),
        "manual_tags": os.path.join(S0, "tags",
                                    "영덕중2_2026-1-기말_L4_impulse-buying.tags.json"),
        "passage": os.path.join(S0, "passages",
                                "영덕중2_2026-1-기말_L4_impulse-buying.json"),
    },
    {
        "name": "Bicycle (교과서 L3 · 영덕중2 2026-1 기말 문항10)",
        "gold": "gold_file",
        "blind": True,
        "blind_label": "완전 블라인드",
        "blind_note": "이 지문으로 프롬프트를 고친 적이 없고, 정답지는 실행 전에 파일로 봉인했다.",
        "generated": os.path.join(GEN, "Bicycle.pass_a.json"),
        "manual_tags": None,
        "gold_file": os.path.join(S0, "comparisons",
                                  "교과서_L3_Bicycle_2026-1기말_정답지.json"),
        "passage": os.path.join(S0, "passages", "교과서_동아윤정미_중2_L3_Bicycle.json"),
    },
]


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def score(tags, targets, label):
    """tags: [{span_start, span_end, grammar_point_code, surface}] / targets: 기출 지점"""
    hits, pos_only, misses = [], [], []
    used = set()
    for t in targets:
        span = (t["span_start"], t["span_end"])
        same_code = [i for i, g in enumerate(tags)
                     if overlaps((g["span_start"], g["span_end"]), span)
                     and g["grammar_point_code"] == t["grammar_point_code"]]
        any_pos = [i for i, g in enumerate(tags)
                   if overlaps((g["span_start"], g["span_end"]), span)]
        if same_code:
            hits.append((t, tags[same_code[0]]))
            used.update(same_code)
        elif any_pos:
            pos_only.append((t, tags[any_pos[0]]))
            used.update(any_pos)
        else:
            misses.append(t)
    n = len(targets)
    cov = len(hits) / n if n else 0.0
    exc = len(tags) / n if n else 0.0
    return {"label": label, "n_tags": len(tags), "n_targets": n,
            "hits": hits, "pos_only": pos_only, "misses": misses,
            "coverage": cov, "excess": exc}


def show(r):
    print(f"\n── {r['label']} ──")
    print(f"  태그 {r['n_tags']}개 vs 기출 지점 {r['n_targets']}개")
    for t, g in r["hits"]:
        print(f"    O {t['exam_label']:>6} {t['grammar_point_code']:22} "
              f"← {g['surface'][:38]!r}")
    for t, g in r["pos_only"]:
        print(f"    ~ {t['exam_label']:>6} {t['grammar_point_code']:22} "
              f"위치만 겹침, 코드는 {g['grammar_point_code']} — {g['surface'][:30]!r}")
    for t in r["misses"]:
        print(f"    X {t['exam_label']:>6} {t['grammar_point_code']:22} 놓침 "
              f"({t['exam_point'][:40]})")
    cov_ok = r["coverage"] >= GATE_COVERAGE
    exc_ok = r["excess"] <= GATE_EXCESS
    print(f"  커버리지 {r['coverage']:.2f}  (게이트 ≥{GATE_COVERAGE:.2f})  "
          f"{'통과' if cov_ok else '실패'}")
    print(f"  과잉률   {r['excess']:.2f}  (게이트 ≤{GATE_EXCESS:.2f})  "
          f"{'통과' if exc_ok else '실패'}")
    return cov_ok and exc_ok


def build_targets(case, body, manual):
    """기출 지점의 구간은 수동 태그의 스팬을 쓴다.
    시험 지문이 배부 지문과 달라(교사가 변형함) 기출 표면형으로는 배부본에서 위치를 못 잡는다."""
    by_no = {t["tag_no"]: t for t in manual["tags"]} if manual else {}

    def span_of(mt, ref):
        if body[mt["span_start"]:mt["span_end"]] != mt["surface"]:
            raise SystemExit(f"수동 태그 {ref} 스팬이 지문과 불일치")
        return mt["span_start"], mt["span_end"]

    targets = []
    if case["gold"] == "compare":
        for d in jload(case["compare"])["details"]:
            mt = by_no.get(d["matched_tag_no"])
            if not mt:
                raise SystemExit(f"수동 태그 {d['matched_tag_no']} 없음")
            s, e = span_of(mt, d["matched_tag_no"])
            targets.append({**d, "span_start": s, "span_end": e})
    elif case["gold"] == "gold_file":
        # 기출 정답지를 별도 파일로 봉인한 경우. surface 를 지문에서 찾아 스팬을 만든다.
        for u in jload(case["gold_file"])["underlined"]:
            i = body.find(u["surface"])
            if i < 0:
                raise SystemExit(f"정답지의 surface 가 지문에 없습니다: {u['surface']!r}")
            if body.find(u["surface"], i + 1) >= 0:
                raise SystemExit(f"정답지의 surface 가 지문에 여러 번 나옵니다: {u['surface']!r}")
            targets.append({
                "exam_label": u["label"],
                "grammar_point_code": u["grammar_point_code"],
                "exam_point": u["성격"],
                "is_exam_answer": u["is_exam_answer"],
                "span_start": i, "span_end": i + len(u["surface"]),
            })
    else:  # exam_underlined — 기출에서 밑줄이 그어진 지점
        for t in manual["tags"]:
            if not t.get("exam_underlined"):
                continue
            s, e = span_of(t, t["tag_no"])
            targets.append({
                "exam_label": t["exam_underlined"].split()[0],
                "grammar_point_code": t["grammar_point_code"],
                "exam_point": t["rationale"],
                "is_exam_answer": bool(t.get("exam_wrong_form")),
                "span_start": s, "span_end": e,
            })
    return targets


def run_case(case):
    if not os.path.exists(case["generated"]):
        print(f"\n  ! 생성 결과 없음: {os.path.basename(case['generated'])}"
              f"\n    먼저:  python -m pipeline.run pass-a --all --run")
        return None
    passage = jload(case["passage"])
    manual = jload(case["manual_tags"]) if case.get("manual_tags") else None
    gen = jload(case["generated"])
    targets = build_targets(case, passage["body_text"], manual)

    print("\n" + "=" * 70)
    print(f" {case['name']}")
    print("=" * 70)
    tag = case.get("blind_label", "준-블라인드") if case["blind"] else "적합됨 (블라인드 아님)"
    print(f"  기출 지점 {len(targets)}개 · {tag}")
    print(f"  {case['blind_note']}")

    auto = score(gen["tags"], targets, "자동 태깅 (패스 A)")
    man = None
    if manual:
        man = score([{**t} for t in manual["tags"]], targets, "수동 태깅 (기준선)")
        show(man)
    else:
        print("\n   (수동 태깅 기준선 없음 — 교과서 본문이라 사람이 태깅한 적이 없다)")
    ok = show(auto)
    return {"case": case, "manual": man, "auto": auto, "ok": ok}


def main():
    print("=" * 70)
    print(" 패스 A 평가 — 자동 태깅 vs 수동 태깅 vs 기출")
    print("=" * 70)
    print("\n판정: 「같은 위치 · 같은 포인트」 (0단계 수동 대조와 동일 규칙)")

    results = [r for r in (run_case(c) for c in CASES) if r]
    if not results:
        return 1

    print("\n" + "─" * 70)
    print(f"  {'지문':30} {'커버리지':>18} {'과잉률':>16}")
    print(f"  {'':30} {'수동':>8} {'자동':>9} {'수동':>7} {'자동':>8}")
    for r in results:
        n = r["case"]["name"].split(" (")[0]
        mc = f"{r['manual']['coverage']:>8.2f}" if r["manual"] else f"{'—':>8}"
        me = f"{r['manual']['excess']:>7.2f}" if r["manual"] else f"{'—':>7}"
        print(f"  {n:30} {mc} {r['auto']['coverage']:>9.2f} "
              f"{me} {r['auto']['excess']:>8.2f}")

    # 합산 (기획서 §3 은 3~5개 합산 판정을 요구한다)
    th = sum(len(r["auto"]["hits"]) for r in results)
    tt = sum(r["auto"]["n_targets"] for r in results)
    tg = sum(r["auto"]["n_tags"] for r in results)
    cov, exc = th / tt, tg / tt
    withman = [r for r in results if r["manual"]]
    mtt = sum(r["manual"]["n_targets"] for r in withman) or 1
    mh = sum(len(r["manual"]["hits"]) for r in withman)
    mtg = sum(r["manual"]["n_tags"] for r in withman)
    print(f"  {'─' * 66}")
    print(f"  {'합산':30} {mh / mtt:>8.2f} {cov:>9.2f} "
          f"{mtg / mtt:>7.2f} {exc:>8.2f}")
    print(f"  {'(수동 열은 기준선이 있는 2개 지문만)':30}")

    ok = cov >= GATE_COVERAGE and exc <= GATE_EXCESS
    print("\n" + "=" * 70)
    print(f" 합산 커버리지 {cov:.2f} (≥{GATE_COVERAGE}) · 과잉률 {exc:.2f} (≤{GATE_EXCESS})")
    print(f" 결과: {'게이트 통과' if ok else '게이트 미달 — 프롬프트를 고쳐야 합니다'}")
    print("=" * 70)

    print("\n⚠️  한계")
    print(f"    · 표본 {len(results)}개. 기획서 §3의 3~5개 합산 판정 하한에 겨우 걸쳤습니다.")
    print("    · goose 는 이 지문을 보고 프롬프트를 2회 고쳤습니다 — 블라인드 수치가 아닙니다.")
    bl = [r for r in results if r["case"]["blind"]]
    bh = sum(len(r["auto"]["hits"]) for r in bl)
    bt = sum(r["auto"]["n_targets"] for r in bl)
    bg = sum(r["auto"]["n_tags"] for r in bl)
    print(f"      goose 를 빼면 — 블라인드 {len(bl)}개 합산 커버리지 {bh / bt:.2f} · "
          f"과잉률 {bg / bt:.2f}")
    print("    · Bicycle 의 grammar_point_code 매핑은 2026-08-22에 붙인 것이라")
    print("      원장 판단과 다를 수 있습니다 (정답지 파일의 _code_mapping_note).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
