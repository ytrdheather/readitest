# -*- coding: utf-8 -*-
"""
어법 **형태** 드릴 — 규칙에서 답이 나오는 것만. 모델을 부르지 않는다.

  python tools/make_form_drill.py --unit 중1L5            # 미리보기
  python tools/make_form_drill.py --unit 중1L5 --build    # PDF

    result/readitude/동아윤정미 중1 5과 어법드릴.pdf
    result/readitude/동아윤정미 중1 5과 어법드릴 정답지.pdf

## 왜 따로 만드나 (원장 2026-09-21)

「애들이 비교급 변화, 불규칙, one of the 최상급, of/in 을 헷갈려한다」.
지문 드릴(드릴 a)은 본문 문장을 그대로 쓰므로 5과에 비교급 문장이 넷뿐이다. 네 문장을
맞혀도 규칙을 아는 게 아니라 그 문장을 기억하는 것이고, heavy → heavier 는 한 번도
안 물었다. 형태·구조 규칙은 **같은 표를 순서만 바꿔 여러 번** 돌려야 붙는다.

기획서 §7.1.2 「단문 나열형은 훈련 가치 없음」은 시험 대비 **문항**에 대한 말이다.
이건 문항이 아니라 **암기 훈련**이다 — 성격이 다르다 (기획서에 적을 것).

## 왜 모델을 안 부르나

답이 규칙에서 기계적으로 나온다. 불규칙 목록만 사람이 적으면 검수가 필요 없다.
학교 오답 유형(heavyer · more good · the more largest · tallest of my class)은
[중1_영덕_L5_학습지.md](../data/stage0/comparisons/중1_영덕_L5_학습지.md) §3 에서 가져왔다.

## 구성

  0 진단 10문항       어느 칸이 비는지 본다 — 형태 / 불규칙 / of·in / one of the / there is·are
  1 변화표 ×3         원급 → 비교급 → 최상급. 같은 42개, 순서만 다르다
  2 고치기 ×2         O 또는 고쳐 쓰기. 학교가 낸 틀린 형태 그대로
  3 구조 문장 ×2      우리말 + 주어진 말 → 영작. of/in · one of the + 최상급 + 복수
  4 There is/are ×2   단수·복수·셀 수 없는 명사·과거·부정·의문·대답
"""
import argparse
import io
import json
import os
import random
import shutil
import sys
import tempfile
from html import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pypdf import PdfReader, PdfWriter                                # noqa: E402
from tools.build_drill_pdf import find_chrome, to_pdf                 # noqa: E402
from tools.pdf_pages import save_pdf                                  # noqa: E402
from tools.render_worksheet import logo_tag, DEFAULT_LOGO, FONT       # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = os.path.join(ROOT, "result", "readitude")
GEN = os.path.join(ROOT, "data", "generated", "drills")

# ──────────────────────────────────────────────────────────────────────────
# 형용사·부사 — (원급, 비교급, 최상급, 규칙 이름). 규칙별로 섞어 넣는다.
# ──────────────────────────────────────────────────────────────────────────
ADJ = [
    # -er / -est
    ("tall", "taller", "tallest", "-er"), ("short", "shorter", "shortest", "-er"),
    ("long", "longer", "longest", "-er"), ("fast", "faster", "fastest", "-er"),
    ("old", "older", "oldest", "-er"), ("young", "younger", "youngest", "-er"),
    ("cheap", "cheaper", "cheapest", "-er"), ("strong", "stronger", "strongest", "-er"),
    ("high", "higher", "highest", "-er"), ("small", "smaller", "smallest", "-er"),
    ("light", "lighter", "lightest", "-er"), ("cold", "colder", "coldest", "-er"),
    ("smart", "smarter", "smartest", "-er"), ("kind", "kinder", "kindest", "-er"),
    # -e → -r / -st
    ("large", "larger", "largest", "-e"), ("nice", "nicer", "nicest", "-e"),
    ("safe", "safer", "safest", "-e"), ("close", "closer", "closest", "-e"),
    ("late", "later", "latest", "-e"), ("wise", "wiser", "wisest", "-e"),
    # 자음 겹침
    ("big", "bigger", "biggest", "겹침"), ("hot", "hotter", "hottest", "겹침"),
    ("thin", "thinner", "thinnest", "겹침"), ("sad", "sadder", "saddest", "겹침"),
    ("fat", "fatter", "fattest", "겹침"),
    # -y → -ier / -iest
    ("easy", "easier", "easiest", "-y"), ("heavy", "heavier", "heaviest", "-y"),
    ("early", "earlier", "earliest", "-y"), ("happy", "happier", "happiest", "-y"),
    ("busy", "busier", "busiest", "-y"), ("pretty", "prettier", "prettiest", "-y"),
    ("healthy", "healthier", "healthiest", "-y"), ("funny", "funnier", "funniest", "-y"),
    # more / most
    ("expensive", "more expensive", "most expensive", "more"),
    ("important", "more important", "most important", "more"),
    ("difficult", "more difficult", "most difficult", "more"),
    ("popular", "more popular", "most popular", "more"),
    ("interesting", "more interesting", "most interesting", "more"),
    ("beautiful", "more beautiful", "most beautiful", "more"),
    ("famous", "more famous", "most famous", "more"),
    ("delicious", "more delicious", "most delicious", "more"),
    ("useful", "more useful", "most useful", "more"),
    ("dangerous", "more dangerous", "most dangerous", "more"),
    # 불규칙
    ("good", "better", "best", "불규칙"), ("well", "better", "best", "불규칙"),
    ("bad", "worse", "worst", "불규칙"), ("many", "more", "most", "불규칙"),
    ("much", "more", "most", "불규칙"), ("little", "less", "least", "불규칙"),
    ("far", "farther", "farthest", "불규칙"),
]

# 고치기 — (문장, 정답). 정답이 "O" 면 맞는 문장. 밑줄은 【 】.
FIX = [
    ("My backpack is 【heavyer】 than yours.", "heavier"),
    ("This phone is 【more good】 than my old one.", "better"),
    ("This is 【the more largest】 building in the city.", "the largest"),
    ("They arrived 【the most earliest】 of all.", "the earliest"),
    ("Her dress was 【the beautifulest】 one at the party.", "the most beautiful"),
    ("The air was 【more bad】 than last week.", "worse"),
    ("This question is 【more easy】 than that one.", "easier"),
    ("Math is 【the harder】 than English for me.", "harder"),
    ("This pizza is 【the best delicious】 in town.", "the most delicious"),
    ("The blue box is 【the very biggest】 of the three.", "the biggest"),
    ("Tom is 【the most biggest】 boy in his class.", "the biggest"),
    ("He is the tallest student 【of】 my class.", "in"),
    ("She is the smartest 【in】 all.", "of"),
    ("Seoul is one of the biggest 【city】 in Korea.", "cities"),
    ("It is one of the best 【movie】 of the year.", "movies"),
    ("One of the most popular sports 【are】 soccer.", "is"),
    ("Today is 【hoter】 than yesterday.", "hotter"),
    ("My dog is 【more smarter】 than my friend's dog.", "smarter"),
    ("Minho is 【the most close】 friend in my life.", "the closest"),
    ("This puzzle is 【difficulter】 than the last one.", "more difficult"),
    ("I got 【the highest】 score in my class.", "O"),
    ("The weather today is 【worse】 than yesterday.", "O"),
    ("Health is 【more important】 than money.", "O"),
    ("Jim is 【the strongest】 in the town.", "O"),
    ("Hallasan is 【the highest】 mountain in Korea.", "O"),
    ("Running is 【easier】 than swimming for me.", "O"),
    ("She is one of 【the busiest】 people I know.", "O"),
    ("This is 【the most expensive】 of all the bags.", "O"),
    ("He speaks 【louder】 than his brother.", "O"),
    ("Eating fruits is 【better】 than eating candies.", "O"),
]

# 구조 문장 — (우리말, 주어진 말, 정답)
BUILD = [
    ("그는 우리 반에서 가장 키가 크다.", "tall, class", "He is the tallest in my class."),
    ("이 상자가 셋 중 제일 크다.", "big, the three", "This box is the biggest of the three."),
    ("서울은 세계에서 가장 큰 도시 중 하나이다.", "big, city", "Seoul is one of the biggest cities in the world."),
    ("그것은 올해 최고의 영화 중 하나였다.", "good, movie, the year", "It was one of the best movies of the year."),
    ("건강이 돈보다 더 중요하다.", "important", "Health is more important than money."),
    ("수학이 모든 과목 중에서 제일 어렵다.", "difficult, all the subjects", "Math is the most difficult of all the subjects."),
    ("그녀는 모두 중에서 가장 똑똑하다.", "smart, all", "She is the smartest of all."),
    ("오늘은 이번 여름 중 가장 더운 날이다.", "hot, day, this summer", "Today is the hottest day of this summer."),
    ("이 스마트폰이 저것보다 더 좋아 보인다.", "good, that one", "This smartphone looks better than that one."),
    ("Jim은 마을에서 가장 힘이 세다.", "strong, the town", "Jim is the strongest in the town."),
    ("세상에서 가장 인기 있는 스포츠는 무엇이니?", "popular, sport, the world", "What is the most popular sport in the world?"),
    ("피자는 한국에서 가장 인기 있는 음식 중 하나이다.", "popular, food, Korea", "Pizza is one of the most popular foods in Korea."),
    ("에펠탑은 자유의 여신상보다 더 높다.", "high, the Statue of Liberty", "The Eiffel Tower is higher than the Statue of Liberty."),
    ("돌고래는 다른 바다 동물들보다 더 영리하다.", "smart, other sea animals", "Dolphins are smarter than other sea animals."),
    ("나에게는 달리기가 수영보다 쉽다.", "easy, swimming", "Running is easier than swimming for me."),
    ("그는 우리 학교에서 가장 빠른 선수 중 한 명이다.", "fast, runner, school", "He is one of the fastest runners in our school."),
    ("아침에는 날씨가 최악이었다.", "bad, the morning", "The weather was the worst in the morning."),
    ("이 책이 저 책보다 더 흥미롭다.", "interesting, that one", "This book is more interesting than that one."),
    ("Minho는 내 인생에서 가장 가까운 친구이다.", "close, friend, my life", "Minho is the closest friend in my life."),
    ("그 빨간 드레스가 모든 것 중에서 가장 비싸다.", "expensive, all", "The red dress is the most expensive of all."),
]

# There is/are — (문장 with ___, 정답). 힌트가 필요하면 괄호로.
THERE = [
    ("There ___ a book on the table.", "is"),
    ("There ___ clouds in the sky.", "are"),
    ("There ___ some water in the bottle.", "is"),
    ("There ___ a lot of people on the subway.", "are"),
    ("There ___ not many books on the shelf.", "are"),
    ("There ___ some cheese on the pizza.", "is"),
    ("There ___ two cats over there.", "are"),
    ("There ___ a red car in front of the house.", "is"),
    ("There ___ three trees in the garden last year. (과거)", "were"),
    ("There ___ an old woman at the door yesterday. (과거)", "was"),
    ("There ___ a lot of snow last winter. (과거)", "was"),
    ("There ___ five people in the park last weekend. (과거)", "were"),
    ("___ there a park near here?", "Is"),
    ("___ there many cars on the street?", "Are"),
    ("___ there any guests at the party last night? (과거)", "Were"),
    ("___ there a good restaurant around here? — Yes, there ___.", "Is / is"),
    ("Are there many students in the gym? — No, there ___.", "aren't"),
    ("Is there any butter in the fridge? — Yes, there ___.", "is"),
    ("Were there any mistakes in my report? — No, there ___.", "weren't"),
    ("There ___ (not) a cup on the shelf. → There ___ a cup on the shelf.", "isn't"),
    ("There ___ (not) flowers in the garden. → There ___ flowers in the garden.", "aren't"),
    ("There ___ not many cars on the street yesterday. (과거)", "weren't"),
    ("There ___ no homework today.", "is"),
    ("There ___ some mistakes in your report.", "are"),
    ("There ___ a bus stop near here.", "is"),
    ("There ___ enough chairs for everyone.", "are"),
    ("There ___ (not) much cheese on the pizza. → There ___ much cheese on the pizza.", "isn't"),
    ("There ___ twenty questions on the exam.", "are"),
    ("There ___ an empty seat on the bus?  → ___ there an empty seat on the bus?", "Is"),
    ("There ___ (1)___ a beautiful park near my house. In the park, there (2)___ a small lake. There (3)___ flowers around the lake.", "(1) is (2) is (3) are"),
]

UNITS = {
    "중1L5": {
        "title": "동아윤정미 중1 5과 어법드릴",
        "sub": "비교급·최상급 / There is/are — 규칙 훈련 (교과서 단위 · 학교 무관)",
        "adj": ADJ, "fix": FIX, "build": BUILD, "there": THERE,
    },
}


def plan(u, seed=20260921):
    rng = random.Random(seed)
    adj, fix, build, there = u["adj"], list(u["fix"]), list(u["build"]), list(u["there"])
    # 0 진단 — 각 칸에서 골고루
    diag = []
    for rule in ("-y", "겹침", "more", "불규칙", "불규칙"):
        w = rng.choice([a for a in adj if a[3] == rule])
        diag.append(("form", w))
    diag += [("fix", f) for f in rng.sample([f for f in fix if f[1] != "O"], 2)]
    diag += [("build", b) for b in rng.sample([b for b in build if "one of" in b[2] or " of " in b[2]], 2)]
    diag += [("there", t) for t in rng.sample(there, 1)]
    # 1 변화표 ×3 — 같은 단어, 순서만
    tables = []
    for i in range(3):
        rows = list(adj); rng.shuffle(rows); tables.append(rows)
    # 2 고치기 ×2 — 15개씩, O 는 5개 안팎
    wrong = [f for f in fix if f[1] != "O"]; right = [f for f in fix if f[1] == "O"]
    rng.shuffle(wrong); rng.shuffle(right)
    fixes = []
    for i in range(2):
        s = wrong[i*10:(i+1)*10] + right[i*5:(i+1)*5]; rng.shuffle(s); fixes.append(s)
    # 3 구조 ×2 — 10개씩
    rng.shuffle(build); builds = [build[:10], build[10:20]]
    # 4 there ×2 — 15개씩
    rng.shuffle(there); theres = [there[:15], there[15:30]]
    return {"diag": diag, "tables": tables, "fixes": fixes, "builds": builds, "theres": theres}


# ──────────────────────────────────────────────────────────────────────────
# 렌더
# ──────────────────────────────────────────────────────────────────────────
CSS = FONT + """
@page { size: A4; margin: 11mm 12mm 12mm; }   /* 바닥 12mm: 쪽수 자리 (디자인 지침 1) */
body { font-family: Pretendard, 'Malgun Gothic', sans-serif; font-size: 10.5pt; line-height: 1.5; color: #111; }
.logo { height: 10mm; margin-bottom: 1mm; }
h1 { font-size: 15pt; margin: 0 0 0.5mm; }
.sub { color: #667; font-size: 9pt; }
.head { display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #1f2d3d; padding-bottom: 1.5mm; margin-bottom: 3mm; }
.name { font-size: 9pt; color: #445; border: 1px solid #ccd; border-radius: 2px; padding: 1mm 5mm; white-space: nowrap; }
h2 { font-size: 10.5pt; margin: 4mm 0 1.8mm; padding: 1mm 2mm; background: #eef2f7; border-left: 3px solid #1f2d3d; break-after: avoid; }
h2 .n { color: #6b7a90; font-weight: 400; font-size: 9pt; margin-left: 1.5mm; }
.rule { font-size: 8.5pt; color: #556; background: #fafbfc; border: 1px solid #e3e8ee; padding: 1.5mm 2.5mm; margin: 0 0 2mm; border-radius: 2px; }
table.t { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
table.t th, table.t td { border: 1px solid #d5dbe3; padding: 1.1mm 2mm; }
table.t th { background: #f2f5f8; font-weight: 600; font-size: 9pt; }
table.t td.w { width: 30%; }
table.t td.b { color: #8a94a6; }
table.t td.a { color: #1f2d3d; font-weight: 600; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 0 6mm; }
ol.q { list-style: none; padding: 0; margin: 0; }
ol.q li { break-inside: avoid; padding: 1.4mm 0; border-bottom: 1px dotted #e3e8ee; display: flex; gap: 2mm; align-items: baseline; font-size: 9.5pt; }
.no { width: 7mm; text-align: right; color: #98a2b3; flex: none; font-variant-numeric: tabular-nums; }
.s { flex: 1; }
u.x { text-decoration: underline; text-underline-offset: 2px; font-weight: 600; }
.blank { display: inline-block; min-width: 26mm; border-bottom: 1px solid #333; margin-left: 2mm; }
.ko { color: #333; }
.hint { color: #6b7a90; font-size: 8.5pt; margin-left: 1.5mm; }
.ans { color: #1f2d3d; font-weight: 600; margin-left: 2mm; }
.mark { font-size: 7.5pt; color: #9aa3b0; text-align: right; margin-top: 1.2mm; }
.pb { break-before: page; }
"""

RULES = {
    "form": "비교급·최상급 만들기: -er/-est · <b>-e</b>면 -r/-st · <b>단모음+단자음</b>이면 자음 겹침(big→bigger) · "
            "<b>-y</b>는 -ier/-iest · <b>2음절 이상</b>은 more/most · 불규칙 good-better-best · bad-worse-worst · "
            "many/much-more-most · little-less-least · far-farther-farthest",
    "fix": "비교급 뒤 <b>than</b> · 최상급 앞 <b>the</b> · more와 -er, most와 -est를 <b>겹쳐 쓰지 않는다</b> · "
           "최상급 뒤 <b>in</b>+장소·집단(in my class) / <b>of</b>+복수·all·the three · "
           "<b>one of the + 최상급 + 복수명사</b> (+ 단수 동사)",
    "build": "주어진 말을 알맞은 형태로 바꿔 쓰시오. 「가장 ~한 것 중 하나」는 one of the + 최상급 + <b>복수</b>.",
    "there": "There is + 단수·셀 수 없는 명사 / There are + 복수 · 과거는 was/were · 부정 isn't/aren't · "
             "의문 Is/Are there ~? — Yes, there is. / No, there aren't.",
}


def head(u, logo, part):
    tag = "" if part == "worksheet" else " — 정답지"
    return (f'{logo}<div class="head"><div><h1>{esc(u["title"])}{tag}</h1>'
            f'<div class="sub">{esc(u["sub"])}</div></div>'
            f'<div class="name">이름 ______________</div></div>')


def form_rows(rows, ans):
    out = ['<table class="t"><tr><th>원급</th><th>비교급</th><th>최상급</th><th class="b">규칙</th></tr>']
    for w, c, s, r in rows:
        cc = f'<td class="a">{esc(c)}</td><td class="a">{esc(s)}</td>' if ans else '<td></td><td></td>'
        out.append(f'<tr><td class="w">{esc(w)}</td>{cc}<td class="b">{esc(r) if ans else ""}</td></tr>')
    out.append('</table>')
    return "".join(out)


def fix_items(items, ans, start=1):
    out = ['<ol class="q">']
    for i, (s, a) in enumerate(items, start):
        s = esc(s).replace("【", '<u class="x">').replace("】", "</u>")
        tail = f'<span class="ans">→ {esc(a)}</span>' if ans else '<span class="blank"></span>'
        out.append(f'<li><span class="no">{i}</span><span class="s">{s} {tail}</span></li>')
    out.append('</ol>')
    return "".join(out)


def build_items(items, ans, start=1):
    out = ['<ol class="q">']
    for i, (ko, hint, a) in enumerate(items, start):
        tail = f'<div class="ans">→ {esc(a)}</div>' if ans else '<div>→ <span class="blank" style="min-width:120mm"></span></div>'
        out.append(f'<li><span class="no">{i}</span><span class="s"><span class="ko">{esc(ko)}</span>'
                   f'<span class="hint">({esc(hint)})</span>{tail}</span></li>')
    out.append('</ol>')
    return "".join(out)


def there_items(items, ans, start=1):
    out = ['<ol class="q">']
    for i, (s, a) in enumerate(items, start):
        tail = f'<span class="ans">→ {esc(a)}</span>' if ans else ''
        out.append(f'<li><span class="no">{i}</span><span class="s">{esc(s)} {tail}</span></li>')
    out.append('</ol>')
    return "".join(out)


def render(u, p, logo, part):
    ans = part == "answers"
    H = []
    H.append(f"<style>{CSS}</style>{head(u, logo, part)}")
    # 0 진단
    H.append('<h2>진단 <span class="n">10문항 · 어느 규칙이 비는지 본다</span></h2>')
    d = p["diag"]
    forms = [x for k, x in d if k == "form"]
    H.append(form_rows(forms, ans))
    H.append(fix_items([x for k, x in d if k == "fix"], ans, 6))
    H.append(build_items([x for k, x in d if k == "build"], ans, 8))
    H.append(there_items([x for k, x in d if k == "there"], ans, 10))
    # 1 변화표
    for i, rows in enumerate(p["tables"], 1):
        H.append(f'<div class="pb"></div><h2>1. 변화표 {i}회 <span class="n">원급 → 비교급 → 최상급 · {len(rows)}개</span></h2>')
        H.append(f'<div class="rule">{RULES["form"]}</div>')
        half = (len(rows) + 1) // 2
        H.append(f'<div class="two">{form_rows(rows[:half], ans)}{form_rows(rows[half:], ans)}</div>')
    # 2 고치기
    for i, items in enumerate(p["fixes"], 1):
        H.append(f'<div class="pb"></div><h2>2. 밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오 — {i}회 <span class="n">{len(items)}문항</span></h2>')
        H.append(f'<div class="rule">{RULES["fix"]}</div>')
        H.append(fix_items(items, ans))
    # 3 구조
    for i, items in enumerate(p["builds"], 1):
        H.append(f'<div class="pb"></div><h2>3. 우리말과 같도록 영어로 쓰시오 — {i}회 <span class="n">{len(items)}문항</span></h2>')
        H.append(f'<div class="rule">{RULES["build"]}</div>')
        H.append(build_items(items, ans))
    # 4 there
    for i, items in enumerate(p["theres"], 1):
        H.append(f'<div class="pb"></div><h2>4. There is/are — 빈칸에 알맞은 be동사 — {i}회 <span class="n">{len(items)}문항</span></h2>')
        H.append(f'<div class="rule">{RULES["there"]}</div>')
        H.append(there_items(items, ans))
    H.append('<div class="mark">리디튜드 · 학원 내부 지도용 · 규칙 기반 생성 (모델 미사용)</div>')
    return "\n".join(H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, choices=sorted(UNITS))
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", type=int, default=20260921)
    a = ap.parse_args()
    u = UNITS[a.unit]
    p = plan(u, a.seed)
    n = (10 + sum(len(t) for t in p["tables"]) + sum(len(f) for f in p["fixes"])
         + sum(len(b) for b in p["builds"]) + sum(len(t) for t in p["theres"]))
    print(f"■ {u['title']}\n   진단 10 · 변화표 {len(p['tables'])}×{len(p['tables'][0])} · "
          f"고치기 {len(p['fixes'])}×{len(p['fixes'][0])} · 구조 {len(p['builds'])}×{len(p['builds'][0])} · "
          f"There {len(p['theres'])}×{len(p['theres'][0])}  = {n}문항")
    os.makedirs(GEN, exist_ok=True)
    with io.open(os.path.join(GEN, f"{a.unit}.form.json"), "w", encoding="utf-8") as f:
        json.dump({"unit": a.unit, "title": u["title"], "seed": a.seed, "plan": p}, f, ensure_ascii=False, indent=1)
    if not a.build:
        print("   --build 를 붙이면 PDF 를 만듭니다.")
        return
    chrome = find_chrome(); logo = logo_tag(DEFAULT_LOGO)
    tmp = tempfile.mkdtemp(prefix="formdrill_")
    try:
        for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
            html = os.path.join(tmp, f"{part}.html"); pdf = os.path.join(tmp, f"{part}.pdf")
            io.open(html, "w", encoding="utf-8").write(render(u, p, logo, part))
            to_pdf(chrome, html, pdf)
            w = PdfWriter()
            for pg in PdfReader(pdf).pages:
                w.add_page(pg)
            dest = os.path.join(OUT, f"{u['title']}{suffix}.pdf")
            pages = save_pdf(w, dest)                     # 아래 가운데 쪽수 — 디자인 지침 1
            print(f"   → {os.path.basename(dest)}  {pages}쪽")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
