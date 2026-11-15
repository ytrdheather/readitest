# -*- coding: utf-8 -*-
"""
영일중3 동형 세트 공용 조립 — 2·3세트부터 (2026-11-08). 1세트 파일은 그대로 둔다.

그릇: 선택 21문항 80점(5점 6 · 4점 5 · 3점 10) + 서술형 4문항 × 5점 = 100점.
근거 data/stage0/comparisons/중3_영일_기말_그릇.md · STATUS 2026-11-08.

세트 파일은 mat() · item() · essay() 만 부르고 마지막에 finish(set_no) 를 부른다.
"""
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

M, I, E = [], [], []


def mat(mid, title, text):
    M.append({"id": mid, "title": title, "text": text.strip()})


def item(pts, stem, opts, ans, why, mid=None, gp=""):
    assert len(opts) == 5 and 1 <= ans <= 5 and pts in (3, 4, 5)
    I.append({"no": len(I) + 1, "points": pts, "stem_ko": stem, "options": opts, "answer": ans,
              "why_ko": why, "material_id": mid, "grammar_point": gp})


def essay(prompt, context, conds, words, wl, grammar, ans, why, slots, mid=None):
    for s in ans.split("\n"):
        if not s.startswith("(완성"):
            # 디자인 지침 4 — 한 칸 7단어 이하 (고쳐 쓰기는 양쪽 각각)
            for side in s.split(":", 1)[-1].split("→"):
                assert len(side.replace("(", " ").split()) <= 9, s
    E.append({"no": None, "material_id": mid, "points": 5, "prompt_ko": prompt,
              "context": context, "conditions": conds, "given_words": words, "word_limit": wl,
              "target_grammar": grammar, "answer_en": ans, "why_ko": why, "answer_slots": slots})


def finish(set_no):
    title = f"영일중3 5·6·7과 동형모의고사 {set_no}세트"
    for n, e in enumerate(E, len(I) + 1):
        e["no"] = n
    pts = [it["points"] for it in I]
    assert (len(I), len(E)) == (21, 4), (len(I), len(E))
    assert sorted(pts).count(5) == 6 and pts.count(4) == 5 and pts.count(3) == 10, pts
    total = sum(pts) + sum(e["points"] for e in E)
    assert total == 100, total
    ids = {m["id"] for m in M}
    for x in I + E:
        assert x["material_id"] is None or x["material_id"] in ids, x["no"]
    dist = {k: sum(1 for it in I if it["answer"] == k) for k in range(1, 6)}
    assert max(dist.values()) - min(dist.values()) <= 2, dist

    d = {"school": "영일중", "set_no": set_no, "grade": "3", "range": "567",
         "spec": {"total_points": 100, "selective": len(I), "essay": len(E)},
         "materials": M, "items": I, "essays": E,
         "diagnostics": {"problems": [], "total_points": total}}
    js = os.path.join(HERE, f"영일중3_{set_no}세트.json")
    io.open(js, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"  {title} · 선택 {len(I)} · 서술 {len(E)} · {total}점 · 정답 분포 {dist}")

    from tools.build_drill_pdf import find_chrome, to_pdf
    from tools.pdf_pages import stamp_file
    from tools.render_mock_exam import build
    from tools.render_worksheet import logo_tag, DEFAULT_LOGO
    out = os.path.join(ROOT, "result", "readitude")
    os.makedirs(out, exist_ok=True)
    chrome, logo, tmp = find_chrome(), logo_tag(DEFAULT_LOGO), tempfile.mkdtemp(prefix="mock3_")
    try:
        for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
            h = os.path.join(tmp, f"{title}{suffix}.html")
            pdf = os.path.join(out, f"{title}{suffix}.pdf")
            io.open(h, "w", encoding="utf-8").write(build(d, logo, part, title=title))
            to_pdf(chrome, h, pdf)
            stamp_file(pdf)                      # 아래 가운데 쪽수 — 디자인 지침 1
            print("  →", pdf)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
