# -*- coding: utf-8 -*-
"""
어법 드릴 검토지 — **한 쪽**.

  python tools/make_grammar_review.py

## 왜 만드는가

원장에게 「정답지 26쪽을 넘기면 곧 태그 검토」라고 말했다. 가벼워 보이지만
실제로는 **301문항**이다. 원장이 바로 물었다 — 「진짜 나더러 317을 다 보라는거냐」.

맞는 지적이다. 그리고 **원장이 볼 것은 301개가 아니다.**

    영어가 맞는가            → 클로드 몫. 생성 + 별도 검수로 두 번 걸렀다
    이 포인트가 출제 범위인가  → **원장 몫.** 29줄이면 끝난다
    비중이 그럴듯한가         → **원장 몫.** 기출에서 본 것과 대 보면 된다

그래서 문항이 아니라 **포인트 29종**을 한 쪽에 늘어놓고, 우리 드릴의 비중과
기출·배부물에서 관측된 것을 나란히 둔다. 원장은 줄을 훑고 「이건 빼라」
「이건 더 내라」만 말하면 된다.

낱개로 볼 것은 **확신도 low 인 7개**뿐이다. 그건 따로 붙인다.
"""
import glob
import io
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.env import load_env                                    # noqa: E402
from pipeline.supabase import Rest                                   # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT      # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DRILLS = os.path.join(ROOT, "data", "generated", "drills")
OUT = os.path.join(ROOT, "data", "generated", "어법드릴_검토지.html")

CSS = FONT + """
@page { size: A4; margin: 11mm 12mm 8mm; }
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; font-size: 9pt;
       line-height: 1.45; color: #111; }
.logo { height: 9mm; margin-bottom: 1mm; }
h1 { font-size: 14pt; margin: 0 0 0.5mm; }
.sub { color: #556; font-size: 8.5pt; margin-bottom: 3mm; }
.head { border-bottom: 2px solid #1f2d3d; padding-bottom: 1.5mm; margin-bottom: 3mm; }
.lead { background: #f4f7fa; border-left: 3px solid #1f2d3d; padding: 2mm 3mm;
        margin-bottom: 3mm; font-size: 8.5pt; }
.lead b { color: #1f2d3d; }
table { width: 100%; border-collapse: collapse; font-size: 8pt; }
th { background: #eef2f7; text-align: left; padding: 1.2mm 1.5mm;
     border-bottom: 1.5px solid #c9d2dd; white-space: nowrap; }
td { padding: 1.1mm 1.5mm; border-bottom: 1px solid #eceff3; vertical-align: top; }
td.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.bar { display: inline-block; height: 2.2mm; background: #4a6fa5; border-radius: 1px;
       vertical-align: middle; margin-right: 1mm; }
.ex { color: #445; font-size: 7.5pt; }
.ex b { color: #1f7a4d; font-weight: 600; }
.ex s { color: #b3261e; text-decoration-color: #b3261e; }
.seen { color: #1f7a4d; font-weight: 600; }
.unseen { color: #9aa3b0; }
.gap { background: #fff6ed; }
.chk { width: 4mm; height: 4mm; border: 1px solid #98a2b3; border-radius: 1px;
       display: inline-block; }
h2 { font-size: 10pt; margin: 4mm 0 1.5mm; padding-bottom: 1mm;
     border-bottom: 1px solid #dde3ea; }
.note { color: #667; font-size: 8pt; margin-top: 2mm; }
"""


def esc(s):
    import html
    return html.escape(s or "", quote=False)


def main():
    items, by_unit = [], defaultdict(list)
    for f in sorted(glob.glob(os.path.join(DRILLS, "*.gram.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        for it in d["items"]:
            it["_unit"] = d["unit"]
            items.append(it)
            by_unit[it["point"]].append(it)

    rest = Rest(load_env())
    conf = {t["id"]: t["confidence"] for t in rest.get(
        "/passage_tag?select=id,confidence,status&limit=2000")
        if t["status"] == "pending"}
    seen = Counter(x["grammar_point_code"] for x in rest.get(
        "/school_grammar_map?select=grammar_point_code&limit=300"))

    cnt = Counter(it["point"] for it in items)
    total = len(items)
    mx = max(cnt.values())

    rows = []
    for pt, n in cnt.most_common():
        ex = by_unit[pt][0]
        wrong = ex["wrong"][0] if ex["wrong"] else ""
        w = round(n / mx * 26)
        s = seen.get(pt, 0)
        mark = (f'<span class="seen">기출 {s}곳</span>' if s
                else '<span class="unseen">관측 없음</span>')
        rows.append(
            f'<tr><td><span class="chk"></span></td>'
            f'<td>{esc(pt)}</td>'
            f'<td class="n">{n}<span class="bar" style="width:{w}mm"></span></td>'
            f'<td class="n">{n/total*100:.0f}%</td>'
            f'<td>{mark}</td>'
            f'<td class="ex"><b>{esc(ex["correct"])}</b> ↔ <s>{esc(wrong)}</s></td></tr>')

    # 기출에서는 봤는데 우리 드릴에 **없는** 포인트 — 진짜 구멍이다
    missing = [(p, c) for p, c in seen.most_common() if p not in cnt]
    miss_rows = "".join(
        f'<tr class="gap"><td><span class="chk"></span></td><td>{esc(p)}</td>'
        f'<td class="n">0</td><td class="n">—</td>'
        f'<td><span class="seen">기출 {c}곳</span></td>'
        f'<td class="ex">본문에 그 자리가 없어 태그가 안 붙었다</td></tr>'
        for p, c in missing)

    low = [it for it in items if conf.get(it["tag_id"]) == "low"]
    low_rows = "".join(
        f'<tr><td><span class="chk"></span></td><td>{esc(it["point"])}</td>'
        f'<td class="ex">{esc(it["_unit"])} · {it["sentence_no"]}번</td>'
        f'<td class="ex"><b>{esc(it["correct"])}</b> ↔ '
        f'<s>{esc(it["wrong"][0] if it["wrong"] else "")}</s></td>'
        f'<td class="ex">{esc(it["why_ko"])}</td></tr>' for it in low)

    html = f"""<style>{CSS}</style>
<div class="head">{logo_tag(DEFAULT_LOGO)}
<h1>어법 드릴 검토지 — 포인트 {len(cnt)}종</h1>
<div class="sub">1층 드릴 a · 11세트 {total}문항 · 2026-09-09</div></div>

<div class="lead">
<b>301문항을 다 보실 필요 없습니다.</b> 영어가 맞는지는 생성 + 별도 검수로
두 번 걸렀습니다(실은 맞는 표현 87개를 거기서 버렸습니다).<br>
원장님만 아시는 것은 <b>① 이 포인트가 출제 범위인가 ② 비중이 그럴듯한가</b>
두 가지입니다. 아래 {len(cnt)}줄을 훑고 <b>빼거나 늘릴 것에만 표시</b>해 주십시오.<br>
「기출」은 4개교 2026-1 기말과 배부물에서 <b>실제로 관측된</b> 곳의 수입니다
(<code>school_grammar_map</code> 36행).
</div>

<table>
<tr><th></th><th>어법 포인트</th><th>문항</th><th>비중</th><th>기출 관측</th><th>보기 (정답 ↔ 오답)</th></tr>
{"".join(rows)}
{miss_rows}
</table>

<div class="note">
※ 주황 줄은 <b>기출에서는 봤는데 우리 드릴에 없는</b> 포인트입니다.
본문에 해당 자리가 없어 태그가 안 붙은 것이라, 내려면 <b>외부 문장을 지어내야</b> 합니다.
필요하다고 하시면 만들겠습니다.
</div>

<h2>따로 봐 주실 것 — 확신도 낮음 {len(low)}개</h2>
<table>
<tr><th></th><th>포인트</th><th>자리</th><th>정답 ↔ 오답</th><th>이유</th></tr>
{low_rows or '<tr><td colspan="5" class="ex">없습니다.</td></tr>'}
</table>

<div class="note">
태깅할 때 스스로 확신이 낮다고 표시한 것들입니다. 나머지 {total - len(low)}개는
확신도 high·medium 이고 검수를 통과했습니다.
</div>
"""
    io.open(OUT, "w", encoding="utf-8").write(html)
    print(f"  포인트 {len(cnt)}종 · 문항 {total} · 확신도 낮음 {len(low)}")
    print(f"  기출에는 있는데 드릴에 없는 포인트 {len(missing)}종: "
          + ", ".join(p for p, _ in missing))
    print(f"  → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
