# -*- coding: utf-8 -*-
"""
패스 A 산출물 → 인쇄용 학습지 (HTML).

  python tools/render_worksheet.py data/generated/Bicycle.pass_a.json
  python tools/render_worksheet.py ... --school 영덕중 --out out.html

## 왜 HTML 인가

원장이 종이로 나눠줘야 한다. HTML 은 브라우저에서 Ctrl+P → PDF 저장이면 끝이고,
추가 설치가 없다. DOCX/PDF 라이브러리를 넣으면 학원 컴퓨터마다 세팅이 늘어난다.
A4 기준으로 스타일을 잡아뒀다.

## 무엇을 뽑는가

  · 학습지  — 지문(문장 번호) + 문항. 학생 배부용
  · 정답지  — 정답 + 해설 + 겨냥 포인트. 원장·강사용. 별지로 나온다

`--answers-only` / `--sheet-only` 로 한쪽만 뽑을 수 있다.

## 아직 없는 것

이건 **패스 A 한 세트를 그대로 종이로 옮기는 것**이다. §5.5.8 이 말하는 「드릴」
(같은 포인트를 여러 방식으로 반복)은 생성 쪽이 먼저 바뀌어야 한다.
지금은 형식을 원장에게 보여 판단을 받는 것이 목적이다.
"""
import argparse
import base64
import html
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S0 = os.path.join(ROOT, "data", "stage0", "passages")
# 로고는 여기 두면 자동으로 들어간다. --logo 로 다른 파일을 지정할 수도 있다.
DEFAULT_LOGO = os.path.join(ROOT, "assets", "logo.png")

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}


def logo_tag(path):
    """로고를 base64 로 박아 넣는다.

    외부 파일을 참조하면 HTML 을 옮기거나 메일로 보낼 때 로고가 깨진다.
    학습지는 원장이 파일째 주고받을 물건이므로 자체 완결이어야 한다.
    """
    if not path or not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    if ext not in MIME:
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f'<img class="logo" src="data:{MIME[ext]};base64,{b64}" alt="">'




TYPE_LABEL = {
    "T-GRAMMAR-INLINE": "어법", "T-GRAMMAR-USAGE": "어법·쓰임",
    "T-VOCAB-CONTEXT": "어휘추론", "T-PHRASE-INFER": "어구추론",
    "T-TOPIC": "주제", "T-DETAIL": "내용일치", "T-BLANK": "빈칸추론",
    "T-WRITE-COND": "서술형·조건영작", "T-WRITE-FIX": "서술형·오류수정",
    "T-FORM-CHOICE": "어법·어형", "T-WORD-ORDER": "어순배열",
    "T-GRAMMAR-STANDALONE": "어법(단문)",
}
DIFF_LABEL = {"easy": "하", "medium": "중", "hard": "상"}

# Pretendard 는 원장 컴퓨터에 설치돼 있다(2026-09-02 확인). 설치된 폰트를 먼저 쓰고,
# 다른 컴퓨터에서 열 때를 대비해 CDN 웹폰트를 대체로 건다.
# 폰트를 base64 로 박지 않는 이유: Pretendard 한글 전체는 수 MB 라 학습지마다 붙으면
# 파일이 너무 커진다. 로고(51KB)와 달리 감당이 안 된다.
FONT = """
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
"""

CSS = FONT + """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: Pretendard, "Pretendard Variable", -apple-system,
       "Malgun Gothic", "맑은 고딕", sans-serif; font-size: 10.5pt;
       line-height: 1.65; color: #111; margin: 0;
       -webkit-font-feature-settings: "tnum"; font-feature-settings: "tnum"; }
h1 { font-size: 15pt; margin: 0 0 2mm; }
.head { border-bottom: 2px solid #111; padding-bottom: 3mm; margin-bottom: 5mm;
        display: flex; justify-content: space-between; align-items: flex-end; }
.logo { height: 11mm; width: auto; display: block; margin-bottom: 2mm; }
.brand { display: flex; align-items: flex-end; gap: 4mm; }
.meta { font-size: 9pt; color: #555; text-align: right; line-height: 1.5; }
.namebox { font-size: 9pt; border: 1px solid #999; padding: 1.5mm 3mm; margin-top: 2mm; }
.passage { border: 1px solid #333; padding: 4mm 5mm; margin: 0 0 6mm;
           background: #fcfcfc; line-height: 1.9; }
.passage .sn { color: #888; font-size: 8pt; vertical-align: super; margin-right: 1px; }
.item { margin: 0 0 5.5mm; page-break-inside: avoid; }
.q { font-weight: 700; }
.tag { font-size: 8pt; font-weight: 400; color: #fff; background: #555;
       padding: 0.6mm 2mm; border-radius: 2px; margin-left: 2mm; }
.tag.hard { background: #a11; } .tag.easy { background: #888; }
.stem { white-space: pre-wrap; margin: 1mm 0 2mm; }
ol.opts { list-style: none; padding-left: 4mm; margin: 1mm 0; }
ol.opts li { margin: 0.8mm 0; }
.lbl { display: inline-block; min-width: 6mm; font-weight: 600; }
.passage, ol.opts li { letter-spacing: -0.01em; }
.write { border-bottom: 1px solid #bbb; height: 7mm; margin: 2mm 0; }
.ansbox { border: 1px solid #333; padding: 3mm 4mm; margin-bottom: 4mm; }
.ansrow { margin: 0 0 3mm; padding-bottom: 2mm; border-bottom: 1px dotted #ccc; }
.ansrow:last-child { border: 0; }
.key { font-weight: 700; color: #a11; }
.why { font-size: 9.5pt; color: #333; }
.pt { font-size: 8.5pt; color: #666; }
.pagebreak { page-break-before: always; }
@media print { .noprint { display: none; } }
.noprint { background: #eef; border: 1px solid #99c; padding: 3mm; font-size: 9pt;
           margin-bottom: 5mm; }
"""


def esc(s):
    return html.escape(s or "")


# 'Mt.' 'Dr.' 에서 문장이 끊기면 번호가 밀린다. extract_textbook.py 와 같은 예외 목록.
ABBREV = ("Mt.", "Dr.", "Mr.", "Mrs.", "Ms.", "St.", "Prof.", "a.m.", "p.m.")


def number_passage(body):
    """문장마다 위첨자 번호. 학생이 문항의 '문장 3' 을 바로 찾을 수 있게."""
    pieces, buf = [], ""
    for part in re.split(r"(?<=[.?!])(\s+)", body):
        buf += part
        if part.isspace():
            continue
        if buf.rstrip().endswith(ABBREV):
            continue          # 약어였다. 아직 문장이 안 끝났다
        pieces.append(buf)
        buf = ""
    if buf.strip():
        pieces.append(buf)
    return "".join(f'<span class="sn">{i}</span>{esc(x)}'
                   for i, x in enumerate(pieces, 1))


def render_item(it, no):
    d = it.get("difficulty")
    tag = TYPE_LABEL.get(it["question_type_code"], it["question_type_code"])
    parts = [f'<div class="item"><div class="q">{no}. '
             f'<span class="tag {d}">{tag} · {DIFF_LABEL.get(d, d)}</span></div>',
             f'<div class="stem">{esc(it["stem"])}</div>']
    if it["options"]:
        parts.append('<ol class="opts">')
        for o in it["options"]:
            parts.append(f'<li><span class="lbl">{esc(o["label"])}</span>{esc(o["body"])}</li>')
        parts.append("</ol>")
    else:
        parts.append('<div class="write"></div><div class="write"></div>')
    parts.append("</div>")
    return "".join(parts)


def render_answer(it, no, tags):
    pts = []
    for i in it.get("source_tags", []):
        if 0 <= i < len(tags):
            t = tags[i]
            pts.append(f"{t['grammar_point_code']} <i>{esc(t['surface'][:28])}</i>")
    return (f'<div class="ansrow"><b>{no}.</b> <span class="key">{esc(it["answer_key"])}</span>'
            f'<div class="why">{esc(it["explanation"])}</div>'
            + (f'<div class="pt">겨냥 포인트 — {" / ".join(pts)}</div>' if pts else "")
            + "</div>")


def build(passage, gen, school, sheet=True, answers=True, logo=""):
    title = passage.get("title") or passage["passage_id"]
    unit = passage.get("textbook_unit", "")
    items = gen["items"]
    head = (f'<div class="head"><div>{logo}<h1>{esc(title)}</h1>'
            f'<div style="font-size:9pt;color:#555">{esc(unit)} · '
            f'{passage.get("word_count", 0)}단어 · 문항 {len(items)}</div></div>'
            f'<div class="meta">{esc(school or "")}<br>2학년 영어'
            f'<div class="namebox">이름 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</div>'
            f'</div></div>')
    body = [f"<style>{CSS}</style>",
            '<div class="noprint">브라우저에서 <b>Ctrl+P → 대상: PDF로 저장</b> 하면 '
            '인쇄본이 됩니다. 이 안내는 인쇄에 나오지 않습니다.</div>']
    if sheet:
        body += [head,
                 f'<div class="passage">{number_passage(passage["body_text"])}</div>',
                 "".join(render_item(it, i) for i, it in enumerate(items, 1))]
    if answers:
        body.append(f'<div class="{"pagebreak" if sheet else ""}">'
                    f'<div class="head"><div>{logo}<h1>{esc(title)} — 정답 및 해설</h1>'
                    f'<div style="font-size:9pt;color:#555">배부용 아님 · 원장·강사용</div></div>'
                    f'</div><div class="ansbox">'
                    + "".join(render_answer(it, i, gen["tags"])
                              for i, it in enumerate(items, 1))
                    + "</div></div>")
    return f"<!doctype html><meta charset=utf-8><title>{esc(title)}</title>" + "".join(body)


def find_passage(passage_id):
    path = os.path.join(S0, passage_id + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    raise SystemExit(f"지문 파일을 못 찾았습니다: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("generated", help="data/generated/*.pass_a.json")
    ap.add_argument("--school", help="머리말에 넣을 학교명")
    ap.add_argument("--out", help="출력 HTML 경로")
    ap.add_argument("--sheet-only", action="store_true")
    ap.add_argument("--answers-only", action="store_true")
    ap.add_argument("--logo", default=DEFAULT_LOGO,
                    help=f"로고 이미지 (기본: {os.path.relpath(DEFAULT_LOGO, ROOT)})")
    args = ap.parse_args()

    with open(args.generated, encoding="utf-8") as f:
        gen = json.load(f)
    passage = find_passage(gen["passage_id"])

    if passage["body_text_sha256"] != gen["body_text_sha256"]:
        raise SystemExit(
            "해시 불일치 — 이 문항들은 지금 지문으로 만든 게 아닙니다.\n"
            "  지문이 바뀌었으면 문항을 다시 생성해야 합니다 (설계원칙 7).")

    out = args.out or os.path.splitext(args.generated)[0] + ".html"
    logo = logo_tag(args.logo)
    doc = build(passage, gen, args.school,
                sheet=not args.answers_only, answers=not args.sheet_only, logo=logo)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)

    status = passage["transcription"]["status"]
    print(f"  저장  {out}")
    if not logo:
        print(f"  ! 로고 없음 — {os.path.relpath(args.logo, ROOT)} 에 파일을 두면 자동으로 들어갑니다")
    print(f"  지문  {passage.get('title')} · {passage.get('word_count')}단어 · "
          f"문항 {len(gen['items'])}개")
    if status != "confirmed":
        print(f"  ! 전사 status={status} — 아직 확정 전입니다. "
              f"본문이 바뀌면 문항을 다시 만들어야 합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
