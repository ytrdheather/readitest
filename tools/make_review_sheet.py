# -*- coding: utf-8 -*-
"""
전사 확인지 — 원장이 교과서를 옆에 놓고 한 줄씩 대조하기 위한 HTML.

**왜 도구로 만드는가**: 지난번 확인지는 손으로 만들었다. 지문을 다시 뽑을 때마다
확인지가 낡는데, 낡은 걸 보고 확인하면 확인 자체가 무효가 된다.

각 줄에 **고유 번호**를 박는다. 원장이 「L5 대화-3 · 4」 라고만 말하면 그 줄이
특정되게 하려는 것이다. 번호는 body_text 의 문장/발화 번호와 같다.
"""
import argparse, glob, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT  # noqa: E402
from pipeline.passage import split_sentences                      # noqa: E402

PASSAGES = os.path.join(ROOT, "data", "stage0", "passages")

CSS = FONT + """
@page { size: A4; margin: 14mm 12mm; }
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; font-size: 10.5pt;
       line-height: 1.55; color: #111; }
.logo { height: 11mm; margin-bottom: 2mm; }
h1 { font-size: 15pt; margin: 0 0 1mm; }
.sub { color: #666; font-size: 9pt; margin-bottom: 6mm; }
.kind { margin: 7mm 0 2mm; padding: 1.5mm 3mm; background: #1f2d3d; color: #fff;
        font-size: 11pt; font-weight: 700; border-radius: 2px; }
.p { break-inside: avoid; margin: 0 0 4mm; border: 1px solid #d8dde3; border-radius: 3px; }
.p > .t { background: #f2f5f8; padding: 1.5mm 3mm; font-weight: 700; font-size: 10pt;
          border-bottom: 1px solid #d8dde3; }
.p > .t small { font-weight: 400; color: #667; margin-left: 3mm; }
table { width: 100%; border-collapse: collapse; }
td { padding: 1.2mm 3mm; vertical-align: top; border-bottom: 1px solid #eef1f4; }
td.n { width: 9mm; color: #98a2b3; text-align: right; font-variant-numeric: tabular-nums; }
td.sp { width: 12mm; color: #445; font-weight: 600; }
tr:last-child td { border-bottom: 0; }
.note { font-size: 9pt; color: #666; margin: 4mm 0 0; }
.how { border: 1px solid #f0c36d; background: #fffaf0; padding: 3mm 4mm;
       border-radius: 3px; margin-bottom: 6mm; font-size: 9.5pt; }
"""

HOW = """<div class="how">
<b>확인 방법</b> — 교과서를 옆에 놓고 <b>영어만</b> 봅니다. 다르면 번호로 알려 주세요.
예: <b>「L5 대화-3 · 4번 줄, get off 가 아니라 get on」</b>.
줄 번호는 시스템이 쓰는 번호와 같아서, 번호만 있으면 제가 바로 그 자리를 고칩니다.<br>
빠진 지문·순서가 뒤바뀐 지문도 알려 주세요. <b>본문 문단 번호</b>가 교과서와 맞는지도 봐 주세요.
</div>"""


def esc(s):
    return html.escape(s, quote=False)


def rows(d):
    """대화문은 발화 단위, 그 외는 문장 단위로 번호를 매긴다."""
    if d.get("turns"):
        return [(t["no"], t["speaker"], t["text"]) for t in d["turns"]]
    return [(no, "", txt) for no, _, _, txt in split_sentences(d["body_text"])]


KINDS = [("textbook_dialogue", "지문종류 1 — 대화문"),
         ("textbook_reading", "지문종류 2 · 3 — 본문 / Read More"),
         ("handout_external", "지문종류 3 — 학교 배부 외부지문")]


def build(docs, logo):
    out = [f"<style>{CSS}</style>", logo,
           "<h1>교과서 전사 확인지 — L5 · L6</h1>",
           f'<div class="sub">지문 {len(docs)}개 · 확인 대상은 <b>영어 원문뿐</b>입니다</div>',
           HOW]
    for kind, label in KINDS:
        got = [d for d in docs if d["kind"] == kind]
        if not got:
            continue
        out.append(f'<div class="kind">{label} · {len(got)}개</div>')
        for d in got:
            meta = []
            if d.get("textbook_page"):
                meta.append(f"교과서 {d['textbook_page']}쪽")
            if d.get("block"):
                meta.append(d["block"])
            if d.get("functions"):
                meta.append(" + ".join(d["functions"]))
            if d.get("school"):
                meta.append(f"{d['school']} 배부")
            if d.get("glossed"):
                meta.append("낱말풀이 " + ", ".join(d["glossed"]))
            body = "".join(
                f'<tr><td class="n">{n}</td><td class="sp">{esc(sp)}</td>'
                f'<td>{esc(tx)}</td></tr>' for n, sp, tx in rows(d))
            out.append(f'<div class="p"><div class="t">{esc(d["title"])}'
                       f'<small>{esc(" · ".join(meta))}</small></div>'
                       f'<table>{body}</table></div>')
    out.append('<p class="note">출판사 부가자료에서 추출 · 학원 내부 지도용 (기획서 §6.6)</p>')
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    # 학교 배부 외부지문도 같은 확인지에 넣는다. 원장이 한 번에 훑는 편이 낫다.
    ap.add_argument("--glob", action="append", default=None,
                    help="대상 파일 패턴 (여러 번 줄 수 있음)")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "generated",
                                                  "전사확인지_L5_L6.html"))
    a = ap.parse_args()

    pats = a.glob or ["L[56]_*.json", "영일중2_L[56]_*.json"]
    docs, seen = [], set()
    for pat in pats:
        for f in sorted(glob.glob(os.path.join(PASSAGES, pat))):
            if f in seen:
                continue
            seen.add(f)
            with open(f, encoding="utf-8") as fh:
                docs.append(json.load(fh))
    if not docs:
        print(f"! {pats} 에 해당하는 지문이 없습니다")
        return 1
    # 대화 → 본문 → Read More 순서. 같은 종류 안에서는 파일 이름 순.
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(build(docs, logo_tag(DEFAULT_LOGO)))
    lines = sum(len(rows(d)) for d in docs)
    print(f"  지문 {len(docs)}개 · 확인할 줄 {lines}개")
    print(f"  → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
