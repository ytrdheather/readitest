# -*- coding: utf-8 -*-
"""
영일중1 6과 본문확인 워크시트 데이터 (mid-eng-worksheet-8set 스킬 입력) — 2026-10-26.

원장: 「우리 드릴은 내용 확인 위주라, 영영어휘·본문 주요 단어 암기용으로 이 스킬 워크시트를 같이 쓰자.
실력이 낮은 아이들에게 특히 도움이 된다」.

  원문   data/stage0/passages/중1L6_본문.json (확정본) — 'Challenge 0N …' 소제목 네 줄은 문장이 아니라 뺐다
         (제목 낱말 reduce · reuse · single-use · recycle 은 PREP 단어로 들어간다)
  해석   특급기출 중1 2학기 6과 「주요 문장」 쪽의 우리말
  단어   영일중1 L6 학습지 New Words 중 본문에 나오는 25개. 영영풀이는 학교 인쇄본이 있으면 그대로
         (vocab/영일중1_L6_vocab_handout.json), 없으면 자습서 풀이(중1_L6_vocab.json) · 새로 씀

  python data/generated/worksheet8/make_영일중1_L6_본문.py   → 같은 폴더에 .json
"""
import json, os, re

S = [  # (영어, 우리말)
 ("Every day, we produce lots of waste, and the Earth is getting sicker and sicker.", "매일 우리는 많은 양의 쓰레기를 생산하고, 지구는 점점 더 병들고 있습니다."),
 ("Do you want to save the Earth?", "지구를 구하고 싶나요?"),
 ("Then, join the zero-waste challenge, and share your stories.", "그렇다면 제로 웨이스트 챌린지에 동참하고 당신의 이야기를 공유해 주세요."),
 ("Olivia: My birthday was last Saturday, and my family and I ate out.", "Olivia: 내 생일은 지난주 토요일이었고, 나의 가족과 나는 외식을 했어."),
 ("There were lots of leftovers, but we brought them home.", "남은 음식이 많았지만, 우리는 그것들을 집으로 가져왔어."),
 ("The next day, I made a nice lunch out of them.", "그 다음 날 나는 그것들로 맛있는 점심을 만들었어."),
 ("FYI, you can find great cooking ideas for leftovers on the Internet.", "참고로, 남은 음식을 활용하는 멋진 요리 아이디어는 인터넷에서 찾을 수 있어."),
 ("Domingo: My dog tore my bag.", "Domingo: 내 강아지가 내 가방을 찢어 버렸어."),
 ("I wanted to buy a new one, but I thought again.", "나는 새것을 사고 싶었지만, 다시 생각해 봤어."),
 ("I learned that reusing is important for zero-waste living.", "나는 재사용하는 것은 제로 웨이스트 생활에 중요하다고 배웠어."),
 ("So, I decided to fix it and reuse it.", "그래서 나는 그것을 고쳐서 다시 사용하기로 결심했어."),
 ("I’m not very good at sewing, and I don’t think that the bag looks perfect.", "나는 바느질을 잘하지 못해서, 가방이 완벽해 보인다고 생각하진 않아."),
 ("I guess it’s all right.", "그래도 괜찮은 것 같아."),
 ("Emma: I often use food delivery services, but today I didn’t.", "Emma: 나는 음식 배달 서비스를 자주 이용하는데, 오늘은 이용하지 않았어."),
 ("Instead, I walked to my favorite restaurant with a reusable container and picked up the food.", "대신에, 재사용 가능한 용기를 가지고 내가 가장 좋아하는 식당으로 걸어가서 음식을 가져왔어."),
 ("I heard that plastic never goes away completely.", "나는 플라스틱은 절대로 완전히 없어지지 않는다고 들었어."),
 ("I didn’t use any single-use plastic today.", "나는 오늘 어떠한 일회용 플라스틱도 사용하지 않았어."),
 ("I felt good!", "기분이 좋았어!"),
 ("Minsu: Yesterday, I took some plastic and glass bottles to a recycling machine near my house.", "민수: 어제 나는 플라스틱 병과 유리병 몇 개를 집 근처에 있는 재활용 기계로 가져갔어."),
 ("I put them into the machine one by one, and I got some points in return.", "나는 그것들을 하나씩 기계에 집어넣었고, 대가로 포인트를 얻었어."),
 ("What can I do with those points?", "그 포인트로 뭘 할 수 있냐고?"),
 ("Well, I can use them like money.", "음, 나는 포인트를 돈처럼 사용할 수 있어."),
 ("Don’t you think that’s cool?", "멋지다고 생각하지 않니?"),
]

PREP = [  # word, pos, ko, def, example, example_ko   (def 출처: 학 = 영일 학습지 · 자 = 자습서 · 새 = 새로 씀)
 ("challenge", "n.", "도전", "something that needs great mental or physical effort to be done successfully",  # 학
  "Climbing that mountain was a big **challenge** for me.", "그 산을 오르는 것은 나에게 큰 도전이었다."),
 ("produce", "v.", "생산하다, 만들어 내다", "to make or grow something",  # 학
  "This farm **produces** fresh milk every day.", "이 농장은 매일 신선한 우유를 생산한다."),
 ("waste", "n.", "쓰레기, 낭비", "things that people throw away because they do not need them",  # 새
  "Please put your **waste** in the right bin.", "쓰레기를 알맞은 통에 넣어 주세요."),
 ("reduce", "v.", "줄이다", "to make something less or smaller",  # 학
  "We should **reduce** the time we spend on our phones.", "우리는 휴대폰에 쓰는 시간을 줄여야 한다."),
 ("eat out", "phr.", "외식하다", "to have a meal in a restaurant, not at home",  # 자 다듬음
  "We **eat out** on Friday nights.", "우리는 금요일 밤마다 외식한다."),
 ("leftover", "n.", "남은 음식", "food remaining after a meal",  # 학
  "Mom put the **leftovers** in the fridge.", "엄마가 남은 음식을 냉장고에 넣었다."),
 ("make A out of B", "phr.", "B로 A를 만들다", "to use one thing as the material to create another thing",  # 새
  "He **made a boat out of** old paper.", "그는 낡은 종이로 배를 만들었다."),
 ("FYI", "phr.", "참고로", "a short way to say 'for your information'",  # 새
  "**FYI**, the library closes at six today.", "참고로, 도서관은 오늘 6시에 문을 닫아."),
 ("reuse", "v.", "재사용하다", "to use again or more than once",  # 학
  "You can **reuse** this paper bag many times.", "이 종이봉투는 여러 번 재사용할 수 있다."),
 ("tear", "v.", "찢다 (tear-tore-torn)", "to pull paper, cloth, or another material into two pieces",  # 학
  "Be careful not to **tear** the page.", "페이지를 찢지 않도록 조심해."),
 ("fix", "v.", "고치다, 수리하다", "to make something work well again",  # 새
  "My dad **fixed** my bike yesterday.", "아빠가 어제 내 자전거를 고쳐 주셨다."),
 ("sew", "v.", "바느질하다 (sew-sewed-sewed/sewn)", "to use a needle and thread to make or repair clothes",  # 학 (fix → repair: 다른 PREP 단어를 풀이에서 뺌)
  "Grandma **sewed** a button on my coat.", "할머니가 내 코트에 단추를 달아 주셨다."),
 ("single-use", "adj.", "일회용의", "designed to be used once and then disposed of or destroyed",  # 학
  "Try not to buy **single-use** cups.", "일회용 컵을 사지 않도록 노력해."),
 ("delivery", "n.", "배달", "the act of taking goods, letters, etc. to people's houses or places of work",  # 학
  "The pizza **delivery** took thirty minutes.", "피자 배달은 30분이 걸렸다."),
 ("instead", "adv.", "대신에", "in place of something else",  # 새
  "It was raining, so we stayed home **instead**.", "비가 와서 우리는 대신 집에 있었다."),
 ("reusable", "adj.", "재사용할 수 있는", "able to be used again or more than once",  # 학
  "I always carry a **reusable** water bottle.", "나는 항상 재사용할 수 있는 물병을 가지고 다닌다."),
 ("container", "n.", "그릇, 용기", "an object for holding things, such as a can, box, or bottle",  # 자
  "Keep the cookies in a glass **container**.", "쿠키를 유리 용기에 보관해."),
 ("go away", "phr.", "없어지다, 사라지다", "to disappear or stop being there",  # 새
  "My headache finally **went away**.", "내 두통이 마침내 사라졌다."),
 ("completely", "adv.", "완전히", "in every way; totally",  # 자
  "I **completely** forgot her birthday.", "나는 그녀의 생일을 완전히 잊어버렸다."),
 ("recycle", "v.", "재활용하다", "to put old paper, glass, or other materials through a special process so that they can be used again",  # 학
  "We **recycle** cans and paper at school.", "우리는 학교에서 캔과 종이를 재활용한다."),
 ("machine", "n.", "기계", "a piece of equipment that you use to do a job",  # 학
  "This **machine** makes ice cream.", "이 기계는 아이스크림을 만든다."),
 ("take A to B", "phr.", "A를 B로 가져가다", "to carry something with you to a place",  # 새
  "Please **take this book to** the teacher.", "이 책을 선생님께 가져다 드려."),
 ("put A into B", "phr.", "A를 B에 넣다", "to place one thing inside another thing",  # 새
  "**Put the eggs into** the basket.", "달걀을 바구니에 넣어라."),
 ("one by one", "phr.", "하나씩, 차례차례", "one person or thing following another in order",  # 학
  "The students came in **one by one**.", "학생들이 한 명씩 들어왔다."),
 ("in return", "phr.", "대가로, 보답으로", "as a response, exchange, or reward for something",  # 학
  "I helped him, and he bought me lunch **in return**.", "내가 그를 도왔고, 그는 보답으로 내게 점심을 사 주었다."),
]

WS1 = [
 ("Every day, / we produce((생산하다)) lots of waste((쓰레기)), / and the Earth / is getting sicker and sicker.",
  "매일 / 우리는 많은 쓰레기를 생산한다 / 그리고 지구는 / 점점 더 병들어 가고 있다"),
 ("Do you want / to save the Earth?", "당신은 원하는가 / 지구를 구하기를"),
 ("Then, / join the zero-waste challenge((도전)), / and share your stories.",
  "그렇다면 / 제로 웨이스트 챌린지에 동참하라 / 그리고 당신의 이야기를 공유하라"),
 ("Olivia: My birthday was last Saturday, / and my family and I / ate out((외식하다)).",
  "Olivia: 내 생일은 지난 토요일이었다 / 그리고 나의 가족과 나는 / 외식을 했다"),
 ("There were lots of leftovers((남은 음식)), / but we brought them / home.",
  "남은 음식이 많이 있었다 / 하지만 우리는 그것들을 가져왔다 / 집으로"),
 ("The next day, / I made a nice lunch / out of them.", "그 다음 날 / 나는 맛있는 점심을 만들었다 / 그것들로"),
 ("FYI((참고로)), / you can find great cooking ideas / for leftovers / on the Internet.",
  "참고로 / 당신은 멋진 요리 아이디어를 찾을 수 있다 / 남은 음식을 위한 / 인터넷에서"),
 ("Domingo: My dog tore((찢다)) my bag.", "Domingo: 내 강아지가 내 가방을 찢었다"),
 ("I wanted to buy a new one, / but I thought again.", "나는 새것을 사고 싶었다 / 하지만 나는 다시 생각했다"),
 ("I learned / that reusing is important / for zero-waste living.",
  "나는 배웠다 / 재사용하는 것이 중요하다는 것을 / 제로 웨이스트 생활에"),
 ("So, / I decided to fix it / and reuse((재사용하다)) it.", "그래서 / 나는 그것을 고치기로 결심했다 / 그리고 그것을 재사용하기로"),
 ("I’m not very good at sewing((바느질하다)), / and I don’t think / that the bag looks perfect.",
  "나는 바느질을 아주 잘하지는 못한다 / 그리고 나는 생각하지 않는다 / 그 가방이 완벽해 보인다고"),
 ("I guess it’s all right.", "나는 그것이 괜찮다고 생각한다"),
 ("Emma: I often use food delivery((배달)) services, / but today I didn’t.",
  "Emma: 나는 자주 음식 배달 서비스를 이용한다 / 하지만 오늘 나는 이용하지 않았다"),
 ("Instead, / I walked to my favorite restaurant / with a reusable((재사용할 수 있는)) container((그릇, 용기)) / and picked up the food.",
  "대신에 / 나는 내가 가장 좋아하는 식당으로 걸어갔다 / 재사용할 수 있는 용기를 가지고 / 그리고 음식을 가져왔다"),
 ("I heard / that plastic never goes away((없어지다)) completely((완전히)).",
  "나는 들었다 / 플라스틱은 절대 완전히 없어지지 않는다고"),
 ("I didn’t use / any single-use((일회용의)) plastic today.", "나는 사용하지 않았다 / 오늘 어떤 일회용 플라스틱도"),
 ("I felt good!", "나는 기분이 좋았다"),
 ("Minsu: Yesterday, / I took some plastic and glass bottles / to a recycling machine((기계)) / near my house.",
  "민수: 어제 / 나는 플라스틱 병과 유리병 몇 개를 가져갔다 / 재활용 기계로 / 우리 집 근처에 있는"),
 ("I put them into the machine / one by one((하나씩)), / and I got some points / in return((대가로)).",
  "나는 그것들을 기계에 넣었다 / 하나씩 / 그리고 나는 약간의 포인트를 얻었다 / 대가로"),
 ("What can I do / with those points?", "내가 무엇을 할 수 있을까 / 그 포인트로"),
 ("Well, / I can use them / like money.", "음 / 나는 그것들을 사용할 수 있다 / 돈처럼"),
 ("Don’t you think / that’s cool?", "당신은 생각하지 않는가 / 그것이 멋지다고"),
]

WS2 = [  # 영어(굵게) / 우리말(빈칸) — ③ 은 이것을 뒤집어 만든다
 ("Every day, we **produce** lots of **waste**, and the Earth is getting sicker and sicker.",
  "매일 우리는 많은 양의 {{쓰레기}}를 {{생산하}}고, 지구는 점점 더 병들고 있습니다."),
 ("Do you want to **save** the Earth?", "지구를 {{구하}}고 싶나요?"),
 ("Then, **join** the zero-waste **challenge**, and **share** your stories.",
  "그렇다면 제로 웨이스트 {{챌린지}}에 {{동참하}}고 당신의 이야기를 {{공유해}} 주세요."),
 ("Olivia: My birthday was last Saturday, and my family and I **ate out**.",
  "Olivia: 내 생일은 지난주 토요일이었고, 나의 가족과 나는 {{외식}}을 했어."),
 ("There were lots of **leftovers**, but we **brought** them home.",
  "{{남은 음식}}이 많았지만, 우리는 그것들을 집으로 {{가져왔}}어."),
 ("The next day, I **made** a nice lunch out of them.", "그 다음 날 나는 그것들로 맛있는 점심을 {{만들었}}어."),
 ("**FYI**, you can find great cooking ideas for **leftovers** on the Internet.",
  "{{참고로}}, {{남은 음식}}을 활용하는 멋진 요리 아이디어는 인터넷에서 찾을 수 있어."),
 ("Domingo: My dog **tore** my bag.", "Domingo: 내 강아지가 내 가방을 {{찢어}} 버렸어."),
 ("I wanted to buy a new one, but I **thought again**.", "나는 새것을 사고 싶었지만, {{다시 생각해}} 봤어."),
 ("I learned that **reusing** is **important** for zero-waste living.",
  "나는 {{재사용하는}} 것은 제로 웨이스트 생활에 {{중요하}}다고 배웠어."),
 ("So, I **decided** to **fix** it and reuse it.", "그래서 나는 그것을 {{고쳐서}} 다시 사용하기로 {{결심했}}어."),
 ("I’m not very good at **sewing**, and I don’t think that the bag looks **perfect**.",
  "나는 {{바느질}}을 잘하지 못해서, 가방이 {{완벽해}} 보인다고 생각하진 않아."),
 ("I **guess** it’s all right.", "그래도 괜찮은 {{것 같아}}."),
 ("Emma: I **often** use food **delivery** services, but today I didn’t.",
  "Emma: 나는 음식 {{배달}} 서비스를 {{자주}} 이용하는데, 오늘은 이용하지 않았어."),
 ("**Instead**, I walked to my favorite restaurant with a **reusable container** and **picked up** the food.",
  "{{대신에}}, {{재사용 가능한 용기}}를 가지고 내가 가장 좋아하는 식당으로 걸어가서 음식을 {{가져왔}}어."),
 ("I heard that plastic never **goes away** **completely**.",
  "나는 플라스틱은 절대로 {{완전히}} {{없어지}}지 않는다고 들었어."),
 ("I didn’t use any **single-use** plastic today.", "나는 오늘 어떠한 {{일회용}} 플라스틱도 사용하지 않았어."),
 ("I **felt good**!", "{{기분이 좋았}}어!"),
 ("Minsu: Yesterday, I **took** some plastic and glass bottles to a **recycling machine** near my house.",
  "민수: 어제 나는 플라스틱 병과 유리병 몇 개를 집 근처에 있는 {{재활용 기계}}로 {{가져갔}}어."),
 ("I put them into the machine **one by one**, and I got some points **in return**.",
  "나는 그것들을 {{하나씩}} 기계에 집어넣었고, {{대가로}} 포인트를 얻었어."),
 ("What can I do with those **points**?", "그 {{포인트}}로 뭘 할 수 있냐고?"),
 ("Well, I can use them **like** money.", "음, 나는 포인트를 돈{{처럼}} 사용할 수 있어."),
 ("Don’t you think that’s **cool**?", "{{멋지}}다고 생각하지 않니?"),
]

WS4 = [
 ("Every day, we ^^(produce)^^ lots of waste, and the Earth ^^(get)^^ sicker and sicker.", ["produce", "is getting"]),
 ("^^(Do)^^ you ^^(want)^^ ^^(save)^^ the Earth?", ["Do", "want", "to save"]),
 ("Then, ^^(join)^^ the zero-waste challenge, and ^^(share)^^ your stories.", ["join", "share"]),
 ("Olivia: My birthday ^^(be)^^ last Saturday, and my family and I ^^(eat)^^ out.", ["was", "ate"]),
 ("There ^^(be)^^ lots of leftovers, but we ^^(bring)^^ them home.", ["were", "brought"]),
 ("The next day, I ^^(make)^^ a nice lunch out of them.", ["made"]),
 ("FYI, you ^^(can, find)^^ great ^^(cook)^^ ideas for leftovers on the Internet.", ["can find", "cooking"]),
 ("Domingo: My dog ^^(tear)^^ my bag.", ["tore"]),
 ("I ^^(want)^^ ^^(buy)^^ a new one, but I ^^(think)^^ again.", ["wanted", "to buy", "thought"]),
 ("I ^^(learn)^^ that ^^(reuse)^^ ^^(be)^^ important for zero-waste ^^(live)^^.", ["learned", "reusing", "is", "living"]),
 ("So, I ^^(decide)^^ ^^(fix)^^ it and ^^(reuse)^^ it.", ["decided", "to fix", "reuse"]),
 ("I’m not very good at ^^(sew)^^, and I don’t ^^(think)^^ that the bag ^^(look)^^ perfect.", ["sewing", "think", "looks"]),
 ("I ^^(guess)^^ it’s all right.", ["guess"]),
 ("Emma: I often ^^(use)^^ food delivery services, but today I didn’t.", ["use"]),
 ("Instead, I ^^(walk)^^ to my favorite restaurant with a reusable container and ^^(pick)^^ up the food.", ["walked", "picked"]),
 ("I ^^(hear)^^ that plastic never ^^(go)^^ away completely.", ["heard", "goes"]),
 ("I didn’t ^^(use)^^ any single-use plastic today.", ["use"]),
 ("I ^^(feel)^^ good!", ["felt"]),
 ("Minsu: Yesterday, I ^^(take)^^ some plastic and glass bottles to a ^^(recycle)^^ machine near my house.", ["took", "recycling"]),
 ("I ^^(put)^^ them into the machine one by one, and I ^^(get)^^ some points in return.", ["put", "got"]),
 ("What ^^(can)^^ I ^^(do)^^ with those points?", ["can", "do"]),
 ("Well, I ^^(can, use)^^ them like money.", ["can use"]),
 ("Don’t you ^^(think)^^ that’s cool?", ["think"]),
]

WS5 = [
 ("Every day, we ^^[produce / produces]^^ lots of waste, and the Earth is getting ^^[sick and sicker / sicker and sicker]^^.", ["produce", "sicker and sicker"]),
 ("Do you want ^^[saving / to save]^^ the Earth?", ["to save"]),
 ("Then, ^^[join / joins]^^ the zero-waste challenge, and share your stories.", ["join"]),
 ("Olivia: My birthday ^^[is / was]^^ last Saturday, and my family and I ^^[ate / eat]^^ out.", ["was", "ate"]),
 ("There ^^[were / was]^^ lots of leftovers, but we brought ^^[it / them]^^ home.", ["were", "them"]),
 ("The next day, I made a nice lunch out of ^^[them / it]^^.", ["them"]),
 ("FYI, you can ^^[found / find]^^ great cooking ideas for leftovers on the Internet.", ["find"]),
 ("Domingo: My dog ^^[tore / torn]^^ my bag.", ["tore"]),
 ("I wanted ^^[buying / to buy]^^ a new one, but I ^^[thought / think]^^ again.", ["to buy", "thought"]),
 ("I learned that reusing ^^[are / is]^^ important for zero-waste living.", ["is"]),
 ("So, I decided ^^[to fix / fixing]^^ it and reuse it.", ["to fix"]),
 ("I’m not very good at ^^[sew / sewing]^^, and I don’t think that the bag looks ^^[perfect / perfectly]^^.", ["sewing", "perfect"]),
 ("I guess ^^[its / it’s]^^ all right.", ["it’s"]),
 ("Emma: I ^^[often use / use often]^^ food delivery services, but today I ^^[don’t / didn’t]^^.", ["often use", "didn’t"]),
 ("Instead, I walked to my favorite restaurant with a reusable container and ^^[picked / pick]^^ up the food.", ["picked"]),
 ("I heard that plastic never ^^[go / goes]^^ away ^^[completely / complete]^^.", ["goes", "completely"]),
 ("I didn’t ^^[used / use]^^ any single-use plastic today.", ["use"]),
 ("I felt ^^[good / nicely]^^!", ["good"]),
 ("Minsu: Yesterday, I ^^[taken / took]^^ some plastic and glass bottles to a recycling machine near my house.", ["took"]),
 ("I put them into the machine one by one, and I ^^[got / get]^^ some points in return.", ["got"]),
 ("What can I ^^[to do / do]^^ with those points?", ["do"]),
 ("Well, I can use ^^[them / it]^^ like money.", ["them"]),
 ("^^[Doesn’t / Don’t]^^ you think that’s cool?", ["Don’t"]),
]

WS6 = [
 {"lines": ["Every day, we **produce** lots of waste, and the Earth is **getting** sicker and **sicker**. "
            "Do you want **saving** the Earth? Then, **joins** the zero-waste challenge, and **share** your stories."],
  "errors": [{"wrong": "saving", "right": "to save", "reason": "want 는 to부정사를 목적어로"},
             {"wrong": "joins", "right": "join", "reason": "명령문은 동사원형으로 시작"}]},
 {"lines": ["Challenge 01 Reduce Food Waste",
            "^^Olivia:^^ My birthday **is** last Saturday, and my family and I **ate** out. There **was** lots of leftovers, "
            "but we **brought** **it** home. The next day, I **made** a nice lunch out of them. "
            "FYI, you can **find** great cooking ideas for leftovers on the Internet."],
  "errors": [{"wrong": "is", "right": "was", "reason": "last Saturday 는 과거"},
             {"wrong": "was", "right": "were", "reason": "There + be 는 뒤 명사(leftovers 복수)에 맞춘다"},
             {"wrong": "it", "right": "them", "reason": "가리키는 것이 leftovers(복수)"}]},
 {"lines": ["Challenge 02 Reuse",
            "^^Domingo:^^ My dog **teared** my bag. I wanted **to buy** a new **one**, but I thought again. "
            "I learned that reusing **are** important for zero-waste living. So, I decided **to fix** it and reuse it. "
            "I’m not very good at **sewing**, and I don’t think that the bag looks **perfectly**. I guess it’s all right."],
  "errors": [{"wrong": "teared", "right": "tore", "reason": "tear 의 과거형은 tore (불규칙)"},
             {"wrong": "are", "right": "is", "reason": "동명사 주어(reusing)는 단수 취급"},
             {"wrong": "perfectly", "right": "perfect", "reason": "감각동사 look + 형용사"}]},
 {"lines": ["Challenge 03 Say No to Single-Use Plastic",
            "^^Emma:^^ I often **uses** food delivery services, but today I **didn’t**. Instead, I walked to my favorite "
            "restaurant with a **reusable** container and **pick** up the food. I heard that plastic never **goes** away "
            "**complete**. I didn’t use any single-use plastic today. I felt **good**!"],
  "errors": [{"wrong": "uses", "right": "use", "reason": "주어 I 에는 use"},
             {"wrong": "pick", "right": "picked", "reason": "walked 와 and 로 나란히 — 과거형"},
             {"wrong": "complete", "right": "completely", "reason": "동사 goes away 를 꾸미는 부사"}]},
 {"lines": ["Challenge 04 Recycle",
            "^^Minsu:^^ Yesterday, I **took** some plastic and glass bottles to a **recycling** machine near my house. "
            "I put **it** into the machine one by one, and I **got** some points in return. What can I **do** with those "
            "points? Well, I can **used** them like money. Don’t you think **that’s** cool?"],
  "errors": [{"wrong": "it", "right": "them", "reason": "가리키는 것이 bottles(복수)"},
             {"wrong": "used", "right": "use", "reason": "조동사 can + 동사원형"}]},
]

WS7 = [
 "Every day, (lots of waste / produce / we), and (sicker and sicker / the Earth / get).",
 "(want / do / you) (the Earth / save)?",
 "Then, (the zero-waste challenge / join), and (your stories / share).",
 "Olivia: (last Saturday / my birthday / be), and (out / eat / my family and I).",
 "(lots of leftovers / there / be), but (home / them / bring / we).",
 "The next day, (out of them / a nice lunch / I / make).",
 "FYI, (great cooking ideas / can / you / find) (on the Internet / for leftovers).",
 "Domingo: (my bag / tear / my dog).",
 "(a new one / buy / want / I), but (again / I / think).",
 "(learn / I) that (important / reuse / be) (zero-waste living / for).",
 "So, (fix it / decide / I) and (it / reuse).",
 "(at / I’m / not very good / sew), and (think / don’t / I) that (perfect / the bag / look).",
 "(all right / it’s / guess / I).",
 "Emma: (food delivery services / often / use / I), but (didn’t / today / I).",
 "Instead, (to my favorite restaurant / walk / I) (a reusable container / with) and (the food / pick up).",
 "(hear / I) that (completely / never / go away / plastic).",
 "(any single-use plastic / didn’t / use / I) today.",
 "(good / feel / I)!",
 "Minsu: Yesterday, (some plastic and glass bottles / take / I) (near my house / to a recycling machine).",
 "(into the machine / them / put / I) one by one, and (in return / some points / get / I).",
 "(do / can / what / I) (those points / with)?",
 "Well, (them / can / use / I) (money / like).",
 "(think / you / don’t) (cool / that’s)?",
]

WS8 = [
 (["produce", "waste", "get"], "Every day, {{#5}}, and {{#7}}."),
 (["want", "save"], "{{#7}}?"),
 (["join", "challenge", "share"], "Then, {{#4}}, and {{#3}}."),
 (["birthday", "last Saturday", "eat out"], "Olivia: {{#5}}, and {{#6}}."),
 (["leftovers", "bring", "home"], "{{#5}}, but {{#4}}."),
 (["the next day", "make", "out of"], "The next day, {{#8}}."),
 (["find", "cooking ideas", "the Internet"], "FYI, {{#11}}."),
 (["dog", "tear", "bag"], "Domingo: {{#5}}."),
 (["want", "buy", "think"], "{{#7}}, but {{#3}}."),
 (["learn", "reuse", "important", "living"], "{{#2}} that {{#6}}."),
 (["decide", "fix", "reuse"], "So, {{#8}}."),
 (["good at", "sew", "think", "look"], "{{#6}}, and {{#3}} that {{#4}}."),
 (["guess", "all right"], "{{#5}}."),
 (["often", "delivery", "today"], "Emma: {{#6}}, but {{#3}}."),
 (["walk", "reusable container", "pick up"], "Instead, {{#15}}."),
 (["hear", "never", "go away", "completely"], "{{#2}} that {{#5}}."),
 (["single-use", "plastic", "today"], "{{#7}}."),
 (["feel", "good"], "{{#3}}!"),
 (["take", "bottles", "recycling machine", "near"], "Minsu: Yesterday, {{#14}}."),
 (["put", "one by one", "in return"], "{{#9}}, and {{#6}}."),
 (["can", "do", "points"], "{{#7}}?"),
 (["use", "like", "money"], "Well, {{#6}}."),
 (["think", "cool"], "{{#5}}?"),
]

assert len(S) == len(WS1) == len(WS2) == len(WS4) == len(WS5) == len(WS7) == len(WS8) == 23
flip = lambda s, a, b: re.sub(a, b, s)
d = {
 "unit": "Lesson 6 Good for the Earth, Good for Us", "school": "영일중", "grade": "1학년",
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
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "영일중1_L6_본문.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print(out)
