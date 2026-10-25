# -*- coding: utf-8 -*-
"""
영일중1 6과 **외부지문** 워크시트 데이터 (mid-eng-worksheet-8set 스킬 입력) — 2026-10-26.

원장: 교과서 본문 권과 **따로 한 권**으로 (본문 권이 이미 37쪽).

  원문   data/stage0/passages/영일중1_L6_외부지문_ChallengeUpcycle.json (확정본, 빈칸 ⓒ 채운 것)
  해석   학습지에 우리말이 없어 Claude 가 썼다 (원장 승인 2026-10-26)
  단어   학습지 13쪽 낱말 상자 8개 (영영풀이 학교 인쇄본) + 본문 구문 4개 (turn A into B · instead of ·
         how-to · perfect for). artwork 의 학교 풀이는 'art' 가 들어 있어(같은 어근 — PREP-2 정답이 보인다) 고쳐 썼다.

  python data/generated/worksheet8/make_영일중1_L6_외부지문.py   → 같은 폴더에 .json
"""
import json, os, re

S = [
 ("Mina: Did you know that we can turn trash into something new and valuable?", "Mina: 우리가 쓰레기를 새롭고 가치 있는 것으로 바꿀 수 있다는 것을 알고 있었니?"),
 ("We can even make an artwork out of it.", "우리는 그것으로 예술 작품을 만들 수도 있어."),
 ("This process is upcycling.", "이 과정이 업사이클링이야."),
 ("It is reusing trash creatively.", "그것은 쓰레기를 창의적으로 재사용하는 거야."),
 ("Today, my dog tore my bag apart, so I needed a new bag.", "오늘 우리 강아지가 내 가방을 갈기갈기 찢어 놓아서, 나는 새 가방이 필요했어."),
 ("Instead of buying a new one or fixing the old one, I decided to upcycle my old jeans.", "새것을 사거나 낡은 것을 고치는 대신, 나는 내 낡은 청바지를 업사이클하기로 결심했어."),
 ("Jeans are strong, so they are perfect for a bag.", "청바지는 튼튼해서 가방으로 딱 알맞아."),
 ("I then found a how-to for making a bag from old jeans on the Internet and made a bag.", "그러고 나서 나는 인터넷에서 낡은 청바지로 가방을 만드는 방법을 찾아서 가방을 만들었어."),
 ("I wanted to decorate the bag, so I used the pins and buttons from my old dresses.", "나는 가방을 꾸미고 싶어서, 내 낡은 원피스에서 떼어 낸 핀과 단추를 사용했어."),
 ("I showed the bag to my friend, Suna, and she said that it looked unique and very nice!", "나는 그 가방을 내 친구 수나에게 보여 줬고, 그녀는 그것이 독특하고 아주 멋져 보인다고 말했어!"),
]

PREP = [  # 학 = 영일 학습지 13쪽 · 새 = 새로 씀
 ("trash", "n.", "쓰레기", "things that you throw away because you no longer want them or need them, such as old food, paper, or plastic",  # 학
  "Please don’t leave **trash** in the park.", "공원에 쓰레기를 남기지 마세요."),
 ("valuable", "adj.", "가치 있는, 귀중한", "worth a lot of money, or very useful or important",  # 학
  "This old coin is very **valuable**.", "이 오래된 동전은 매우 귀중하다."),
 ("artwork", "n.", "예술 작품", "a painting, drawing, or sculpture that someone creates",  # 학 풀이를 고침 (art 가 들어 있었다)
  "Her **artwork** is shown in the school hall.", "그녀의 예술 작품이 학교 강당에 전시되어 있다."),
 ("process", "n.", "과정", "a series of actions or steps taken in order to achieve a particular end",  # 학
  "Learning a language is a long **process**.", "언어를 배우는 것은 긴 과정이다."),
 ("upcycle", "v.", "업사이클하다 (헌 물건을 더 좋은 것으로 다시 만들다)", "to take old or thrown away materials and objects and change them into something new and usually better",  # 학 (turn → change: 다른 PREP 단어를 풀이에서 뺌)
  "I **upcycled** an old box as a pencil case.", "나는 낡은 상자를 필통으로 업사이클했다."),
 ("decorate", "v.", "꾸미다, 장식하다", "to make something look more attractive by adding things to it",  # 학
  "We **decorated** the classroom with balloons.", "우리는 풍선으로 교실을 꾸몄다."),
 ("unique", "adj.", "독특한, 유일한", "being the only one of its kind; unusually special",  # 학
  "Everyone has a **unique** voice.", "모든 사람은 자기만의 독특한 목소리를 가지고 있다."),
 ("tear apart", "phr.", "갈기갈기 찢다", "to pull something into pieces, or to separate it by force",  # 학
  "The angry child **tore apart** the paper.", "화난 아이가 종이를 갈기갈기 찢었다."),
 ("turn A into B", "phr.", "A를 B로 바꾸다", "to change one thing so that it becomes another thing",  # 새
  "The magician **turned the scarf into** a bird.", "마술사는 스카프를 새로 바꾸었다."),
 ("instead of", "phr.", "~ 대신에", "in place of something else",  # 새
  "I drank water **instead of** soda.", "나는 탄산음료 대신 물을 마셨다."),
 ("how-to", "n.", "방법, 제작법", "instructions that show you the steps to do something",  # 새 (학습지 각주: 방법, 제작법)
  "I watched a **how-to** video about cooking.", "나는 요리 방법 영상을 봤다."),
 ("perfect for", "phr.", "~에 딱 알맞은", "exactly right for a person or a use",  # 새
  "This small backpack is **perfect for** a short trip.", "이 작은 배낭은 짧은 여행에 딱 알맞다."),
]

WS1 = [
 ("Mina: Did you know / that we can turn trash((쓰레기)) into something / new and valuable((가치 있는))?",
  "Mina: 너는 알고 있었니 / 우리가 쓰레기를 무언가로 바꿀 수 있다는 것을 / 새롭고 가치 있는"),
 ("We can even make an artwork((예술 작품)) / out of it.", "우리는 심지어 예술 작품을 만들 수도 있다 / 그것으로"),
 ("This process((과정)) is upcycling.", "이 과정이 업사이클링이다"),
 ("It is reusing trash creatively((창의적으로)).", "그것은 쓰레기를 창의적으로 재사용하는 것이다"),
 ("Today, / my dog tore my bag apart((갈기갈기 찢다)), / so I needed a new bag.",
  "오늘 / 우리 강아지가 내 가방을 갈기갈기 찢었다 / 그래서 나는 새 가방이 필요했다"),
 ("Instead of buying a new one / or fixing the old one, / I decided / to upcycle((업사이클하다)) my old jeans.",
  "새것을 사는 대신 / 또는 낡은 것을 고치는 (대신) / 나는 결심했다 / 내 낡은 청바지를 업사이클하기로"),
 ("Jeans are strong, / so they are perfect for a bag.", "청바지는 튼튼하다 / 그래서 그것은 가방으로 딱 알맞다"),
 ("I then found a how-to((방법)) / for making a bag / from old jeans / on the Internet / and made a bag.",
  "그러고 나서 나는 방법을 찾았다 / 가방을 만드는 / 낡은 청바지로 / 인터넷에서 / 그리고 가방을 만들었다"),
 ("I wanted to decorate((꾸미다)) the bag, / so I used the pins and buttons / from my old dresses.",
  "나는 그 가방을 꾸미고 싶었다 / 그래서 나는 핀과 단추를 사용했다 / 내 낡은 원피스에서 나온"),
 ("I showed the bag / to my friend, Suna, / and she said / that it looked unique((독특한)) and very nice!",
  "나는 그 가방을 보여 주었다 / 내 친구 수나에게 / 그리고 그녀는 말했다 / 그것이 독특하고 아주 멋져 보인다고"),
]

WS2 = [
 ("Mina: Did you know that we can **turn** **trash** into something new and **valuable**?",
  "Mina: 우리가 {{쓰레기}}를 새롭고 {{가치 있는}} 것으로 {{바꿀}} 수 있다는 것을 알고 있었니?"),
 ("We can even make an **artwork** out of it.", "우리는 그것으로 {{예술 작품}}을 만들 수도 있어."),
 ("This **process** is upcycling.", "이 {{과정}}이 업사이클링이야."),
 ("It is **reusing** trash **creatively**.", "그것은 쓰레기를 {{창의적으로}} {{재사용하는}} 거야."),
 ("Today, my dog **tore** my bag **apart**, so I **needed** a new bag.",
  "오늘 우리 강아지가 내 가방을 {{갈기갈기 찢어}} 놓아서, 나는 새 가방이 {{필요했}}어."),
 ("**Instead of** buying a new one or **fixing** the old one, I decided to **upcycle** my old jeans.",
  "새것을 사거나 낡은 것을 {{고치는}} {{대신}}, 나는 내 낡은 청바지를 {{업사이클하}}기로 결심했어."),
 ("Jeans are **strong**, so they are **perfect for** a bag.", "청바지는 {{튼튼해}}서 가방으로 {{딱 알맞아}}."),
 ("I then found a **how-to** for making a bag from old jeans on the Internet and made a bag.",
  "그러고 나서 나는 인터넷에서 낡은 청바지로 가방을 만드는 {{방법}}을 찾아서 가방을 만들었어."),
 ("I wanted to **decorate** the bag, so I used the **pins** and **buttons** from my old dresses.",
  "나는 가방을 {{꾸미}}고 싶어서, 내 낡은 원피스에서 떼어 낸 {{핀}}과 {{단추}}를 사용했어."),
 ("I **showed** the bag to my friend, Suna, and she said that it looked **unique** and very nice!",
  "나는 그 가방을 내 친구 수나에게 {{보여 줬}}고, 그녀는 그것이 {{독특하}}고 아주 멋져 보인다고 말했어!"),
]

WS4 = [
 ("Mina: ^^(Do)^^ you ^^(know)^^ that we ^^(can, turn)^^ trash into something new and valuable?", ["Did", "know", "can turn"]),
 ("We ^^(can, even, make)^^ an artwork out of it.", ["can even make"]),
 ("This process ^^(be)^^ upcycling.", ["is"]),
 ("It ^^(be)^^ ^^(reuse)^^ trash creatively.", ["is", "reusing"]),
 ("Today, my dog ^^(tear)^^ my bag apart, so I ^^(need)^^ a new bag.", ["tore", "needed"]),
 ("Instead of ^^(buy)^^ a new one or ^^(fix)^^ the old one, I ^^(decide)^^ ^^(upcycle)^^ my old jeans.", ["buying", "fixing", "decided", "to upcycle"]),
 ("Jeans ^^(be)^^ strong, so they ^^(be)^^ perfect for a bag.", ["are", "are"]),
 ("I then ^^(find)^^ a how-to for ^^(make)^^ a bag from old jeans on the Internet and ^^(make)^^ a bag.", ["found", "making", "made"]),
 ("I ^^(want)^^ ^^(decorate)^^ the bag, so I ^^(use)^^ the pins and buttons from my old dresses.", ["wanted", "to decorate", "used"]),
 ("I ^^(show)^^ the bag to my friend, Suna, and she ^^(say)^^ that it ^^(look)^^ unique and very nice!", ["showed", "said", "looked"]),
]

WS5 = [
 ("Mina: Did you ^^[knew / know]^^ that we can turn trash into ^^[something new / new something]^^ and valuable?", ["know", "something new"]),
 ("We can even ^^[make / makes]^^ an artwork out of ^^[them / it]^^.", ["make", "it"]),
 ("This process ^^[are / is]^^ upcycling.", ["is"]),
 ("It is ^^[reusing / reused]^^ trash ^^[creative / creatively]^^.", ["reusing", "creatively"]),
 ("Today, my dog ^^[teared / tore]^^ my bag apart, so I ^^[needed / need]^^ a new bag.", ["tore", "needed"]),
 ("Instead of ^^[buy / buying]^^ a new one or fixing the old one, I decided ^^[to upcycle / upcycling]^^ my old jeans.", ["buying", "to upcycle"]),
 ("Jeans are strong, so ^^[it / they]^^ ^^[are / is]^^ perfect for a bag.", ["they", "are"]),
 ("I then found a how-to for ^^[making / make]^^ a bag from old jeans on the Internet and ^^[making / made]^^ a bag.", ["making", "made"]),
 ("I wanted ^^[decorating / to decorate]^^ the bag, so I used the pins and buttons from my old dresses.", ["to decorate"]),
 ("I showed the bag ^^[to / for]^^ my friend, Suna, and she said that it looked ^^[uniquely / unique]^^ and very nice!", ["to", "unique"]),
]

WS6 = [
 {"lines": ["Challenge Upcycle",
            "^^Mina:^^ Did you **know** that we can **turn** trash into something **newly** and valuable? We can even **makes** "
            "an artwork out of **it**. This process **is** upcycling. It is **reusing** trash creatively. Today, my dog "
            "**teared** my bag apart, so I needed a new bag."],
  "errors": [{"wrong": "newly", "right": "new", "reason": "something 은 형용사가 뒤에서 꾸민다 (부사 X)"},
             {"wrong": "makes", "right": "make", "reason": "조동사 can + 동사원형"},
             {"wrong": "teared", "right": "tore", "reason": "tear 의 과거형은 tore (불규칙)"}]},
 {"lines": ["Instead of **buy** a new one or **fixing** the old one, I decided **to upcycle** my old jeans. Jeans are strong, "
            "so **it is** perfect for a bag. I then found a how-to for **making** a bag from old jeans on the Internet and "
            "**made** a bag. I wanted to decorate the bag, so I **used** the pins and buttons from my old dresses. I showed "
            "the bag to my friend, Suna, and she said that it looked **uniquely** and very nice!"],
  "errors": [{"wrong": "buy", "right": "buying", "reason": "전치사 of 뒤에는 동명사 (fixing 과 나란히)"},
             {"wrong": "it is", "right": "they are", "reason": "가리키는 것이 Jeans(복수)"},
             {"wrong": "uniquely", "right": "unique", "reason": "감각동사 look + 형용사"}]},
]

WS7 = [
 "Mina: (know / you / do) that (turn / can / we / trash) (something new and valuable / into)?",
 "(can / we / make / even) (out of it / an artwork).",
 "(upcycling / this process / be).",
 "(trash / be / it / reuse) creatively.",
 "Today, (my bag / tear / apart / my dog), so (a new bag / need / I).",
 "Instead of (a new one / buy) or (the old one / fix), (decide / I) (my old jeans / upcycle).",
 "(strong / jeans / be), so (perfect / they / for a bag / be).",
 "(a how-to / then / find / I) (a bag / for / make) (from old jeans / on the Internet) and (a bag / make).",
 "(decorate / want / I) the bag, so (the pins and buttons / use / I) (my old dresses / from).",
 "(the bag / show / I) (my friend, Suna / to), and (that / say / she) (unique and very nice / look / it)!",
]

WS8 = [
 (["know", "turn", "trash", "valuable"], "Mina: {{#13}}?"),
 (["even", "artwork", "out of"], "{{#9}}."),
 (["process", "upcycling"], "{{#4}}."),
 (["reuse", "trash", "creatively"], "{{#5}}."),
 (["tear", "apart", "need"], "Today, {{#6}}, so {{#5}}."),
 (["instead of", "fix", "decide", "upcycle"], "{{#11}}, {{#7}}."),
 (["strong", "perfect for"], "{{#3}}, so {{#6}}."),
 (["find", "how-to", "old jeans", "the Internet"], "I then {{#17}}."),
 (["decorate", "use", "pins and buttons"], "{{#6}}, so {{#10}}."),
 (["show", "say", "unique"], "{{#4}} to my friend, Suna, and {{#9}}!"),
]

assert len(S) == len(WS1) == len(WS2) == len(WS4) == len(WS5) == len(WS7) == len(WS8) == 10
flip = lambda s, a, b: re.sub(a, b, s)
d = {
 "unit": "Lesson 6 More reading — Challenge Upcycle", "school": "영일중", "grade": "1학년",
 "sentences": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(S, 1)],
 "prep": [dict(zip(("word", "pos", "ko", "def", "example", "example_ko"), p)) for p in PREP],
 "ws1": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(WS1, 1)],
 "ws2": [{"no": i, "en": e, "ko": k} for i, (e, k) in enumerate(WS2, 1)],
 "ws3": [{"no": i, "ko": flip(k, r"\{\{(.+?)\}\}", r"**\1**"), "en": flip(e, r"\*\*(.+?)\*\*", r"{{\1}}")}
         for i, (e, k) in enumerate(WS2, 1)],
 "ws4": [{"no": i, "en": e, "answer": a} for i, (e, a) in enumerate(WS4, 1)],
 "ws5": [{"no": i, "en": e, "answer": a} for i, (e, a) in enumerate(WS5, 1)],
 "ws6": WS6,
 "ws7": [{"no": i, "en": e, "answer": S[i - 1][0]} for i, e in enumerate(WS7, 1)],
 "ws8": [{"no": i, "keywords": k, "frame": f, "answer": S[i - 1][0]} for i, (k, f) in enumerate(WS8, 1)],
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "영일중1_L6_외부지문.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print(out)
