# -*- coding: utf-8 -*-
"""
학교별 동형 모의고사를 만든다.

  python tools/make_mock_exam.py --school 영일중                # 미리보기
  python tools/make_mock_exam.py --school 영일중 --set 1 --run   # 1세트만
  python tools/make_mock_exam.py --all --run                    # 4개교 × 3세트

설계도는 `data/stage0/mock_exam_blueprint.json`.

## 자료는 우리가 넣는다

교과서 본문·대화문·Read More 와 **그 학교 외부지문**을 `P1 P2 …` 로 번호 붙여 넣는다.
모델은 번호로만 가리키고 본문은 못 바꾼다 — `pipeline/mock_exam.py` 의 잠금 참조.

세트마다 **다른 지문 묶음**을 준다. 세 세트가 같은 지문이면 두 번째부터는 훈련이
아니라 암기 확인이 된다.
"""
import argparse
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline import mock_exam                                       # noqa: E402
from pipeline.env import load_env                                    # noqa: E402
from pipeline.models import Cost, client                             # noqa: E402
from pipeline.pass_a import extract_json                             # noqa: E402
from pipeline.supabase import Rest                                   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BP = os.path.join(ROOT, "data", "stage0", "mock_exam_blueprint.json")
OUT = os.path.join(ROOT, "data", "generated", "mock")

# 세트마다 지문 묶음을 갈아 준다. 같은 지문 세 번이면 암기 확인이 된다.
SET_PASSAGES = {
    1: [("L5 본문", ["Street Art in London-1", "Street Art in London-2",
                     "Street Art in London-3", "Street Art in London-4"]),
        ("L5 대화 ①②③", ["L5 대화-1", "L5 대화-2", "L5 대화-3"]),
        ("L6 Read More", ["L6 ReadMore-1", "L6 ReadMore-2",
                          "L6 ReadMore-3", "L6 ReadMore-4"])],
    2: [("L6 본문", ["Dr. Schofield, a Foreigner Who Loved Korea"]),
        ("L6 대화 ④⑤⑥", ["L6 대화-4", "L6 대화-5", "L6 대화-6"]),
        ("L5 Read More", ["L5 ReadMore-1", "L5 ReadMore-2",
                          "L5 ReadMore-3", "L5 ReadMore-4"])],
    3: [("L5 대화 ⑦⑧⑨", ["L5 대화-7", "L5 대화-8", "L5 대화-9"]),
        ("L6 대화 ⑦⑧⑨", ["L6 대화-7", "L6 대화-8", "L6 대화-9"]),
        ("L5 본문", ["Street Art in London-1", "Street Art in London-2",
                     "Street Art in London-3", "Street Art in London-4"])],
}


def points_hint(spec):
    """배점을 어떻게 나눌지 힌트를 준다. 합계가 총점과 맞아야 한다."""
    n_s, n_e = spec["selective"], spec.get("essay", 0)
    e_pts = spec.get("essay_points", 0)
    s_pts = spec["total_points"] - e_pts
    base = s_pts / n_s
    return (f"선택형 {n_s}문항에 {s_pts}점 (평균 {base:.1f}점) · "
            f"서술형 {n_e}문항에 {e_pts}점.\n"
            f"문항마다 3~5점 사이에서 정하되 **합계가 정확히 "
            f"{spec['total_points']}점**이 되게 하십시오.")


def gather(rest, spec, set_no):
    ps = {p["title"]: p for p in rest.get(
        "/passage?select=id,title,kind,body_text,transcription_status&limit=500")
        if p["transcription_status"] == "confirmed"}
    mats, given = [], {}
    n = 1
    for label, parts in SET_PASSAGES[set_no]:
        rows = [ps[t] for t in parts if t in ps]
        if not rows:
            print(f"    ! 지문 없음, 건너뜀: {label}")
            continue
        text = "\n".join(r["body_text"] for r in rows)
        mid = f"P{n}"; n += 1
        mats.append({"id": mid, "kind": "given", "title": label, "text": text})
        given[mid] = text
    for t in spec.get("external_passages", []):
        row = ps.get(t)
        if not row:
            print(f"    ! 외부지문 없음(전사 미확정?), 건너뜀: {t}")
            continue
        mid = f"P{n}"; n += 1
        mats.append({"id": mid, "kind": "given", "title": f"외부지문 — {t}",
                     "text": row["body_text"]})
        given[mid] = row["body_text"]
    return mats, given


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--school")
    ap.add_argument("--set", type=int, choices=[1, 2, 3])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    bp = json.load(io.open(BP, encoding="utf-8"))
    schools = list(bp["schools"]) if a.all else ([a.school] if a.school else [])
    if not schools:
        raise SystemExit("--school 또는 --all 을 주십시오. " + ", ".join(bp["schools"]))
    sets = [a.set] if a.set else [1, 2, 3]

    env = load_env()
    rest = Rest(env)
    os.makedirs(OUT, exist_ok=True)
    api = client(env) if a.run else None
    cost = Cost()

    for school in schools:
        spec = bp["schools"][school]
        for set_no in sets:
            print("=" * 74)
            print(f" {school} 동형 {set_no}세트 — 선택 {spec['selective']} · "
                  f"서술 {spec.get('essay', 0)} · {spec['grammar_vessel']}")
            print("=" * 74)
            mats, given = gather(rest, spec, set_no)
            for m in mats:
                print(f"    {m['id']} {m['title'][:34]:36} {len(m['text']):>5}자")
            if not a.run:
                print("    [미리보기] 호출하지 않습니다. 실제로 만들려면 --run\n")
                continue

            params = mock_exam.build_params(school, spec, bp["common"],
                                            mats, points_hint(spec), set_no)
            # 시험지 한 벌은 출력이 길다(선택 21~25 × 선지 5 + 서술 4).
            # max_tokens 가 크면 SDK 가 스트리밍을 요구한다 — 10분을 넘길 수 있어서다.
            with api.messages.stream(**params) as stream:
                msg = stream.get_final_message()
            usd = cost.add(f"{school}-{set_no}", params["model"], msg.usage)
            # 세트마다 실비를 파일에 남긴다. 2026-09-16 크레딧이 중간에 바닥나 프로세스가
            # 죽었고, 끝에 찍는 cost.report() 가 안 나와 4세트분 비용을 알 수 없었다.
            usage = {"model": params["model"], "input": msg.usage.input_tokens,
                     "output": msg.usage.output_tokens, "usd": round(usd, 4)}
            res = mock_exam.parse(extract_json(msg), spec, given)
            res["usage"] = usage
            d = res["diagnostics"]

            print(f"    선택 {d['n_items']} · 서술 {d['n_essays']} · "
                  f"배점 {d['total_points']} · ${usd:.3f} "
                  f"(입력 {usage['input']:,} · 출력 {usage['output']:,})")
            for p in d["problems"]:
                print(f"      ! {p}")
            for w in d.get("warnings", []):
                print(f"      · {w}")
            if not d["problems"]:
                print("      구조 검사 통과")

            path = os.path.join(OUT, f"{school}_{set_no}세트.json")
            with io.open(path, "w", encoding="utf-8") as f:
                json.dump({"school": school, "set_no": set_no, "spec": spec, **res},
                          f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"    저장 → {path}\n")

    if a.run:
        cost.report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
