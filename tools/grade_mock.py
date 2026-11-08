# -*- coding: utf-8 -*-
"""
동형 모의고사 채점 → 기록(Z:) → 학생별 결과지. OMR 을 받을 때마다 이것 하나로 한다.

  python tools/grade_mock.py <채점지.json>            # 채점 · 기록 · 결과지
  python tools/grade_mock.py <채점지.json> --dry      # 점수만 보고, 아무것도 안 씀
  python tools/grade_mock.py --history 1234           # 한 학생의 지난 기록

2026-11-08 원장: 「할 때마다 만들고 1회성이잖아? 채점을 기록하고 분석지도 저장할 방법」.
그 전에는 결과지 JSON 을 손으로 써서 build_report_card.py 에 넣었고, 기록이 남지 않았다.

## 어디에 남나 — 저장소가 아니라 Z: (CLAUDE.md 규칙 3: 학생 이름·답)

  Z:\\학원파일\\내신자료\\중등 내신 동형 모의고사\\채점\\
    기록\\2026-11-08_중1_영일중_1세트.json   시험 하나 — 채점지 + 계산한 점수·틀린 번호·영역별 점수
    학생기록.json                            출결번호별 누적 (회차마다 점수 · 영역별 점수)
    결과지\\<이름> · …결과지.pdf / .png      학부모용 (카톡은 png)

같은 날짜·세트를 다시 돌리면 **덮어쓴다** — 판정을 고쳐 다시 뽑는 것이 정상 흐름이다.
학생 테이블은 「JSON 이 굳은 뒤」 Supabase 로 옮긴다 (설계 6). 그때까지 이 파일들이 원본이다.

## 채점지 (Claude 가 OMR 을 읽어 쓴다 — 저장소 밖, 스크래치에)

  {"date": "2026-11-08", "set": "중1_영일중_1세트", "school": "영일중학교", "exam": "기말고사",
   "students": [
     {"id": "1234", "name": "홍길동", "grade": "1",
      "mc": "5,3,2,1,3,…",                  # 칠한 번호 20개. 빈칸은 "" · 두 칸은 "2/4" (오답)
      "essay": {"21": {"answer": "(I)'m going to ride a bike", "lost": 0, "note": "a bike 인정"},
                "22": {"answer": "(1) stops raining\\n(2) will play soccer", "lost": 0}, …},
      "summary"?: "…", "weak": ["…"], "todo": ["…"]}]}

  · 선택형은 기계가 정답과 대조한다. 서술형 감점(`lost`)과 인정 여부는 사람(원장)·Claude 가 정한다.
  · 실행할 때 **같은 세트의 이전 서술형 판정**을 보여 준다 — 같은 답에 다른 점수를 주지 않게.
  · 회차(1차·2차 …)는 그 학생의 기록 수로 정한다. 결과지에 지난 회차 점수·영역별 비교가 붙는다.
"""
import argparse
import datetime as dt
import glob
import io
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_report_card import area_scores                       # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 저장소에 JSON 이 없는 세트(다른 PC 에서 만들어 Z: 에 PDF 만 있는 것)는 --mock-dir 로 다른 폴더를 준다
MOCK = os.environ.get("READI_MOCK_DIR") or os.path.join(ROOT, "data", "generated", "mock")
LEDGER = r"Z:\학원파일\내신자료\중등 내신 동형 모의고사\채점"
CIRCLED = "①②③④⑤"


def load(p, default=None):
    if default is not None and not os.path.exists(p):
        return default
    return json.load(io.open(p, encoding="utf-8"))


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp, p)                   # 쓰다 끊겨도 기록이 반쪽이 되지 않게


def marks(mc, n):
    xs = mc.split(",") if isinstance(mc, str) else [str(x) for x in mc]
    xs = [x.strip() for x in xs]
    if len(xs) != n:
        raise SystemExit(f"선택형 마킹이 {len(xs)}개 — 세트는 {n}문항")
    return xs


def show_mark(x):
    if not x:
        return "(빈칸)"
    if x.isdigit() and 1 <= int(x) <= 5:
        return CIRCLED[int(x) - 1]
    return " · ".join(CIRCLED[int(c) - 1] for c in x.replace(",", "/").split("/") if c.isdigit()) + " (두 칸)"


def grade(d, s):
    items, essays = d["items"], d["essays"]
    ms = marks(s["mc"], len(items))
    wrong, lost_mc = [], set()
    mc_got = 0
    for it, x in zip(items, ms):
        if x == str(it["answer"]):
            mc_got += it["points"]
        else:
            lost_mc.add(it["no"])
            wrong.append({"no": it["no"], "student": show_mark(x)})
    given = {int(k): v for k, v in (s.get("essay") or {}).items()}
    missing = [e["no"] for e in essays if e["no"] not in given]
    if missing:
        raise SystemExit(f"{s['name']}: 서술형 {missing} 판정이 없음 (빈 답이면 answer \"\" · lost 만점)")
    lost_es, es_got = {}, 0
    for e in essays:
        g = given[e["no"]]
        lost = int(g.get("lost", 0))
        if not 0 <= lost <= e["points"]:
            raise SystemExit(f"{s['name']} 서술형 {e['no']}번 감점 {lost} — 배점 {e['points']}")
        es_got += e["points"] - lost
        if lost:
            lost_es[e["no"]] = lost
            w = {"no": e["no"], "student": (g.get("answer") or "(빈칸)").split("\n"), "lost": lost}
            if g.get("note"):
                w["note"] = g["note"]
            wrong.append(w)
    mc_full = sum(it["points"] for it in items)
    es_full = sum(e["points"] for e in essays)
    areas = area_scores(d, lost_mc, lost_es)
    return {"score": mc_got + es_got, "mc": [mc_got, mc_full], "essay": [es_got, es_full],
            "wrong": wrong, "areas": areas}


def auto_summary(areas):
    full = [k for k, v in areas.items() if v[2] == v[3]]
    lost = [k for k, v in areas.items() if v[2] < v[3]]
    if not lost:
        return "모든 영역을 만점으로 마쳤습니다."
    head = f"{' · '.join(full)} 영역은 모두 맞혔습니다. " if full else ""
    return head + f"점수를 잃은 영역은 {' · '.join(lost)} 영역입니다."


def prior_judgments(root, set_name, skip):
    """같은 세트를 다른 날 채점한 기록의 서술형 판정 — 같은 답에 같은 점수를 주려고."""
    out = {}
    for p in sorted(glob.glob(os.path.join(root, "기록", f"*_{set_name}.json"))):
        if os.path.abspath(p) == os.path.abspath(skip):
            continue
        for s in load(p)["students"]:
            for no, g in (s.get("essay") or {}).items():
                out.setdefault(int(no), set()).add(
                    (" / ".join((g.get("answer") or "").split("\n")), int(g.get("lost", 0)), g.get("note", "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", nargs="?")
    ap.add_argument("--root", default=LEDGER, help="기록 폴더 (기본 Z:)")
    ap.add_argument("--dry", action="store_true", help="점수만 보고 아무것도 쓰지 않음")
    ap.add_argument("--history", help="출결번호 — 그 학생의 지난 기록")
    ap.add_argument("--mock-dir", help="세트 JSON 폴더 (기본 data/generated/mock)")
    a = ap.parse_args()
    global MOCK
    if a.mock_dir:
        MOCK = os.path.abspath(a.mock_dir)
        os.environ["READI_MOCK_DIR"] = MOCK          # 결과지(build_report_card) 도 같은 폴더를 읽게
    book_p = os.path.join(a.root, "학생기록.json")

    if a.history:
        st = load(book_p, {}).get(a.history)
        if not st:
            raise SystemExit(f"{a.history} 기록 없음")
        print(f"{a.history} {st['name']} · {st.get('school', '')} {st.get('grade', '')}학년")
        for r in st["records"]:
            ar = " · ".join(f"{k} {v[0]}/{v[1]}" for k, v in r["areas"].items())
            print(f"  {r['round']:>3} {r['date']} {r['set']:<18} {r['score']:>3}점  {ar}")
        return
    if not a.sheet:
        ap.error("채점지 JSON 이 필요합니다")

    sheet = load(a.sheet)
    d = load(os.path.join(MOCK, sheet["set"] + ".json"))
    rec_p = os.path.join(a.root, "기록", f"{sheet['date']}_{sheet['set']}.json")
    book = load(book_p, {})

    prev_j = prior_judgments(a.root, sheet["set"], rec_p) if os.path.isdir(a.root) else {}
    if prev_j:
        print("같은 세트 이전 서술형 판정 (같은 답이면 같은 점수로):")
        for no in sorted(prev_j):
            for ans, lost, note in sorted(prev_j[no]):
                print(f"  {no}번  −{lost}  {ans}" + (f"   ({note})" if note else ""))
        print()

    report = {"school": sheet["school"], "exam": sheet.get("exam", "중간고사"),
              "date": sheet.get("date", ""), "students": []}
    for s in sheet["students"]:
        g = grade(d, s)
        s.update({k: g[k] for k in ("score", "mc", "essay", "wrong", "areas")})
        st = book.get(s["id"]) or {"name": s["name"], "school": sheet["school"],
                                   "grade": s["grade"], "records": []}
        if st["name"] != s["name"]:
            print(f"  ⚠ {s['id']} 이름이 기록({st['name']})과 다름 — 채점지 {s['name']}. 출결번호 확인")
        others = [r for r in st["records"] if not (r["date"] == sheet["date"] and r["set"] == sheet["set"])]
        others.sort(key=lambda r: (r["date"], r["set"]))
        # 회차는 「이 시험보다 앞선 기록 수 + 1」 — 지난 시험을 다시 돌려도 뒤 기록까지 세지 않게
        # (2026-11-08: 1세트를 다시 돌렸더니 이미 있던 2세트까지 세어 「2차」 가 됐다)
        rnd = f"{sum(1 for r in others if (r['date'], r['set']) < (sheet['date'], sheet['set'])) + 1}차"
        rec = {"date": sheet["date"], "set": sheet["set"], "round": rnd, "score": g["score"],
               "mc": g["mc"], "essay": g["essay"], "wrong": [w["no"] for w in g["wrong"]],
               "areas": {k: [v[2], v[3]] for k, v in g["areas"].items()},
               "file": os.path.basename(rec_p)}
        st["records"] = sorted(others + [rec], key=lambda r: (r["date"], r["set"]))
        for i, r in enumerate(st["records"]):    # 앞에 끼워 넣으면 뒤 기록의 회차도 다시 매긴다
            r["round"] = f"{i + 1}차"
        st["name"] = s["name"]
        book[s["id"]] = st
        s["round"] = rnd

        ent = {"name": s["name"], "grade": s["grade"], "set": sheet["set"], "round": rnd,
               "score": g["score"], "mc": g["mc"], "essay": g["essay"], "wrong": g["wrong"],
               "summary": s.get("summary") or auto_summary(g["areas"]),
               "weak": s.get("weak", []), "todo": s.get("todo", [])}
        before = [r for r in others if (r["date"], r["set"]) < (sheet["date"], sheet["set"])]
        if before:
            p = before[-1]
            ent["prev"] = {"label": f"{p['round']}({p['date'][5:].replace('-', '/')})",
                           "score": p["score"], "areas": p["areas"]}
        report["students"].append(ent)

        if g["wrong"] and not s.get("weak"):
            print(f"  ⚠ {s['name']}: 틀린 문제가 있는데 weak 가 비었다 — 결과지에 「부족한 부분이 없었습니다」 로 찍힌다")
        wr = ", ".join(str(w["no"]) for w in g["wrong"]) or "없음"
        was = f"  (지난 {ent['prev']['score']}점)" if "prev" in ent else ""
        print(f"  {s['id']} {s['name']:<4} {rnd}  {g['score']:>3}점  선택 {g['mc'][0]}/{g['mc'][1]} · "
              f"서술 {g['essay'][0]}/{g['essay'][1]}  틀림: {wr}{was}")

    if a.dry:
        print("\n  --dry: 아무것도 쓰지 않았습니다.")
        return

    sheet["graded_at"] = dt.datetime.now().isoformat(timespec="seconds")
    # 같은 날·같은 세트를 학생 몇 명씩 나눠 채점해도 한 파일에 모인다 — 출결번호가 같으면 새 것으로 바꾼다.
    # (2026-11-08: 한 명만 담은 채점지로 돌렸더니 먼저 기록한 두 명의 마킹이 사라졌다)
    if os.path.exists(rec_p):
        old = load(rec_p)
        mine = {s["id"] for s in sheet["students"]}
        sheet["students"] = [s for s in old.get("students", []) if s["id"] not in mine] + sheet["students"]
    save(rec_p, sheet)
    save(book_p, book)
    tmp = tempfile.mkdtemp(prefix="grade_")
    rp = os.path.join(tmp, "report.json")
    io.open(rp, "w", encoding="utf-8").write(json.dumps(report, ensure_ascii=False))
    out = os.path.join(a.root, "결과지")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_report_card.py"), rp, "--out", out],
                   check=True)
    print(f"\n  기록 → {rec_p}\n  누적 → {book_p}")


if __name__ == "__main__":
    sys.exit(main())
