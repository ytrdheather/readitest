# -*- coding: utf-8 -*-
"""
중2 7과 어법 형태 드릴의 문항 — make_form_drill.py 가 읽는다 (--unit 중2L7).

원장 2026-11-12 「형태 드릴 따로 내라」. 범위는 태장중2 L7 학습지
(data/stage0/comparisons/중2_태장_L7_학습지.md §3)다. 본문에는 it ~ to 2곳 · call A B 2곳뿐이라
that절 진주어 · 의미상 주어 for/of · it 구별 · call 뜻 구별은 지문 드릴이 못 덮는다.

문장은 학습지 · 특급기출 예문 · 교과서 본문에서 가져오거나 같은 틀로 새로 썼다.
중1 5과와 달리 변화표가 없어서 **구역 목록**(SECTIONS)으로 적는다 — 구역마다 종류 · 회당 문항 수.

  kind   build  우리말(또는 원래 문장) + 힌트 → 한 줄 쓰기      (문장, 힌트, 정답)
         fill   ___ 빈칸                                        (문장, 정답)
         fix    밑줄 【 】 을 보고 답 쓰기                       (문장, 정답)
  mix    회차마다 답 종류가 고르게 들어가도록 나누는 기준. "OX" 는 정답이 "O" 인 것과 아닌 것.
"""

REWRITE = [
    ("To ride a bike without a helmet is dangerous.", "It ~ to", "It is dangerous to ride a bike without a helmet."),
    ("To learn a foreign language takes time.", "It ~ to", "It takes time to learn a foreign language."),
    ("To read books every day is good for you.", "It ~ to", "It is good for you to read books every day."),
    ("To keep a diary every day is hard.", "It ~ to", "It is hard to keep a diary every day."),
    ("To wear a seat belt is necessary.", "It ~ to", "It is necessary to wear a seat belt."),
    ("To lie to friends is bad.", "It ~ to", "It is bad to lie to friends."),
    ("To watch a movie with friends is fun.", "It ~ to", "It is fun to watch a movie with friends."),
    ("To remember dead people is important.", "It ~ to", "It is important to remember dead people."),
    ("To solve the problem was not easy.", "It ~ to", "It was not easy to solve the problem."),
    ("To make gimchi together will be fun.", "It ~ to", "It will be fun to make gimchi together."),
    ("To run faster than reindeer is not possible.", "It ~ to", "It is not possible to run faster than reindeer."),
    ("Learning a new language is not easy.", "It ~ to", "It is not easy to learn a new language."),
    ("Swimming in this river is dangerous.", "It ~ to", "It is dangerous to swim in this river."),
    ("That she passed the exam is surprising.", "It ~ that", "It is surprising that she passed the exam."),
    ("That he told a lie is clear.", "It ~ that", "It is clear that he told a lie."),
    ("That no one answered the phone is strange.", "It ~ that", "It is strange that no one answered the phone."),
    ("That she knows the truth is certain.", "It ~ that", "It is certain that she knows the truth."),
    ("That we keep our promises is important.", "It ~ that", "It is important that we keep our promises."),
    ("That the Earth is round is true.", "It ~ that", "It is true that the Earth is round."),
    ("That everyone was having fun was obvious.", "It ~ that", "It was obvious that everyone was having fun."),
]

# that 둘은 함정 — that절 진주어에는 의미상 주어를 쓰지 않는다 (학습지 2쪽이 따로 못박은 것)
THAT = "that (that절 진주어 — for/of 를 쓰지 않는다)"
FOROF = [
    ("It is kind ___ you to help me.", "of"),
    ("It is important ___ you to help them.", "for"),
    ("It isn't easy ___ me to exercise every day.", "for"),
    ("It was nice ___ her to help the old man.", "of"),
    ("It is necessary ___ us to save water.", "for"),
    ("It was foolish ___ him to believe the rumor.", "of"),
    ("It is hard ___ children to sit still for an hour.", "for"),
    ("It was brave ___ the boy to tell the truth.", "of"),
    ("It is dangerous ___ kids to swim here alone.", "for"),
    ("It was rude ___ him to leave without saying goodbye.", "of"),
    ("It is impossible ___ me to finish the work today.", "for"),
    ("It was wise ___ you to bring an umbrella.", "of"),
    ("It is difficult ___ foreigners to learn Korean.", "for"),
    ("It was careless ___ me to lose the key.", "of"),
    ("It is fun ___ us to play board games together.", "for"),
    ("It was polite ___ her to give her seat to the old man.", "of"),
    ("It is good ___ you to read books every day.", "for"),
    ("It was generous ___ them to share their food.", "of"),
    ("It wasn't easy ___ him to solve the problem.", "for"),
    ("It is smart ___ you to save money for the trip.", "of"),
    ("It is possible ___ visitors to enjoy winter sports there.", "for"),
    ("It was careful ___ her to check the answers twice.", "of"),
    ("It is strange ___ no one answered the phone.", THAT),
    ("It was silly ___ me to make the same mistake again.", "of"),
    ("It is important ___ Mexicans to remember dead people.", "for"),
    ("It was clever ___ the girl to solve the puzzle that way.", "of"),
    ("It is exciting ___ me to watch fireworks.", "for"),
    ("It was nice ___ you to invite us to the festival.", "of"),
    ("It is not safe ___ you to ride a bike without a helmet.", "for"),
    ("It is clear ___ she knows the truth.", THAT),
]

IT = [
    ("【It】 is dangerous to swim here.", "가주어"),
    ("【It】 is fun to play board games.", "가주어"),
    ("Is 【it】 possible to do so?", "가주어"),
    ("They believe 【it】 is important to remember dead people.", "가주어"),
    ("【It】 is clear that he told a lie.", "가주어"),
    ("【It】 was not easy to find the house.", "가주어"),
    ("【It】 is strange that she didn't come.", "가주어"),
    ("【It】 will be fun to make gimchi together.", "가주어"),
    ("【It】 is nice of you to say so.", "가주어"),
    ("【It】 is necessary to wear a seat belt.", "가주어"),
    ("I lost my umbrella. 【It】 was blue.", "대명사"),
    ("I bought a new bike. 【It】 is very fast.", "대명사"),
    ("Look at the statue. 【It】 is made of wood.", "대명사"),
    ("They have a special festival. They call 【it】 the Midsummer festival.", "대명사"),
    ("People decorate a tall pole and dance around 【it】.", "대명사"),
    ("I like the T-shirt. There is a nice picture on 【it】.", "대명사"),
    ("This bag is big, but 【it】 is very light.", "대명사"),
    ("I read the book yesterday. 【It】 was really interesting.", "대명사"),
    ("Where is my phone? — 【It】 is on the desk.", "대명사"),
    ("That bag looks nice. I'll take 【it】.", "대명사"),
    ("【It】 is cloudy today.", "비인칭"),
    ("【It】 is already ten o'clock.", "비인칭"),
    ("【It】 is raining outside, so take an umbrella.", "비인칭"),
    ("【It】 is Friday today.", "비인칭"),
    ("【It】 is November 1 today.", "비인칭"),
    ("【It】 is five kilometers from here to the station.", "비인칭"),
    ("【It】 was very dark outside.", "비인칭"),
    ("【It】 is getting cold these days.", "비인칭"),
    ("What time is 【it】 now?", "비인칭"),
    ("【It】 is summer in Australia now.", "비인칭"),
]

FIX = [
    ("It is foolish 【give】 up without trying.", "to give"),
    ("It is difficult 【learns】 a foreign language.", "to learn"),
    ("It is dangerous 【walked】 alone in the dark.", "to walk"),
    ("【That】 is always sad to say goodbye to friends.", "It"),
    ("It is bad 【for lie】 to friends.", "to lie"),
    ("It 【good】 for you to read books every day.", "is good"),
    ("It is important 【that to drink】 water every day.", "to drink"),
    ("It is clear 【for her that】 she knows the truth.", "that"),
    ("It was kind 【for】 her to help the old man.", "of"),
    ("It is necessary 【of】 us to save water.", "for"),
    ("It isn't easy for 【he】 to learn a foreign language.", "him"),
    ("It was nice of 【they】 to invite us.", "them"),
    ("【This】 is dangerous to ride a bike without a helmet.", "It"),
    ("It is possible 【learn】 a new language at any age.", "to learn"),
    ("They call 【me to Bob】.", "me Bob"),
    ("People call the boy 【as a genius】.", "a genius"),
    ("They called their daughter 【to Lily】.", "Lily"),
    ("People call 【a genius the boy】.", "the boy a genius"),
    ("My friends call 【I】 Bob.", "me"),
    ("She 【call】 her robot Clean Master.", "calls"),
    ("They believe it is important 【to remember】 dead people.", "O"),
    ("It was wise 【of】 you to bring an umbrella.", "O"),
    ("It is strange 【that】 no one answered the phone.", "O"),
    ("It wasn't easy 【for him】 to solve the problem.", "O"),
    ("People call Chicago 【the Windy City】.", "O"),
    ("They call 【this day】 the Day of the Dead.", "O"),
    ("Is 【it】 possible to run faster than reindeer?", "O"),
    ("We call 【him】 Mr. Kim.", "O"),
    ("It is necessary 【to wear】 a seat belt.", "O"),
    ("They will call their daughter 【Lily】.", "O"),
]

C3 = "3형식 · 전화하다"
C5 = "5형식 · ~을 …라고 부르다"
CALL = [
    ("I'll 【call】 you later.", C3),
    ("Please 【call】 me when you arrive.", C3),
    ("She 【called】 her mom at night.", C3),
    ("I will 【call】 the hotel tomorrow.", C3),
    ("Did you 【call】 me last night?", C3),
    ("He 【called】 the police right away.", C3),
    ("I 【called】 my grandmother on her birthday.", C3),
    ("Don't 【call】 me during class.", C3),
    ("Who 【called】 you this morning?", C3),
    ("I heard someone 【calling】 my name.", "3형식 · 부르다"),
    ("He 【calls】 his dog Max.", C5),
    ("My friends 【call】 me Bob.", C5),
    ("People 【call】 Chicago the Windy City.", C5),
    ("She 【calls】 her cleaning robot Clean Master.", C5),
    ("They 【call】 it the Midsummer festival.", C5),
    ("They 【call】 this day the Day of the Dead.", C5),
    ("We 【call】 him Mr. Kim.", C5),
    ("People 【call】 the boy a genius.", C5),
    ("They will 【call】 their daughter Lily.", C5),
    ("I decided to 【call】 my cat Kitty.", C5),
]

BUILD = [
    ("친구들과 함께 영화를 보는 것은 재미있다.", "it, fun, watch", "It is fun to watch a movie with friends."),
    ("매일 일기를 쓰는 것은 어렵다.", "it, hard, keep a diary", "It is hard to keep a diary every day."),
    ("새로운 언어를 배우는 것은 중요하다.", "it, important, learn", "It is important to learn a new language."),
    ("보드게임을 하는 것은 즐겁다.", "it, exciting, play", "It is exciting to play board games."),
    ("그녀가 진실을 알고 있는 것이 분명하다.", "it, clear, that", "It is clear that she knows the truth."),
    ("그가 그 문제를 푸는 것은 쉽지 않았다.", "it, easy, solve", "It wasn't easy for him to solve the problem."),
    ("나를 도와주다니 너는 친절하구나.", "it, kind, help", "It is kind of you to help me."),
    ("우리가 물을 절약하는 것은 필요하다.", "it, necessary, save", "It is necessary for us to save water."),
    ("그렇게 하는 것이 가능한가요?", "it, possible, do so", "Is it possible to do so?"),
    ("죽은 사람들을 기억하는 것은 중요하다.", "it, important, remember", "It is important to remember dead people."),
    ("그가 거짓말을 한 것은 사실이다.", "it, true, that, tell a lie", "It is true that he told a lie."),
    ("헬멧 없이 자전거를 타는 것은 위험하다.", "it, dangerous, without", "It is dangerous to ride a bike without a helmet."),
    ("그 노인을 도와주다니 그녀는 친절했다.", "it, kind, help, the old man", "It was kind of her to help the old man."),
    ("내 친구들은 나를 Bob이라고 부른다.", "call", "My friends call me Bob."),
    ("사람들은 그 소년을 천재라고 부른다.", "call, a genius", "People call the boy a genius."),
    ("그들은 그것을 Midsummer 축제라고 부른다.", "call, it", "They call it the Midsummer festival."),
    ("그들은 이날을 Day of the Dead라고 부른다.", "call, this day", "They call this day the Day of the Dead."),
    ("그녀는 그 로봇을 Clean Master라고 부른다.", "call, the robot", "She calls the robot Clean Master."),
    ("그들은 자신들의 딸을 Lily라고 부를 것이다.", "will, call", "They will call their daughter Lily."),
    ("나는 내 고양이를 Kitty라고 부르기로 결정했다.", "decide, call", "I decided to call my cat Kitty."),
]

SECTIONS = [
    {"key": "rewrite", "kind": "build", "per": 10, "diag": 2, "items": REWRITE,
     "head": "가주어 It 으로 시작하는 문장으로 바꿔 쓰시오",
     "rule": "주어가 <b>to부정사구 · that절</b>이면 뒤로 보내고 빈 자리에 <b>It</b>(가주어, 해석 안 함)을 쓴다. "
             "It is 형용사 <b>to + 동사원형</b> / It is 형용사 <b>that + 주어 + 동사</b>. "
             "동명사 주어도 It ~ to 로 바꿀 수 있다."},
    {"key": "forof", "kind": "fill", "per": 15, "diag": 2, "items": FOROF, "mix": ["of", "for", "that"],
     "head": "빈칸에 for · of · that 중 알맞은 말을 쓰시오",
     "rule": "to부정사의 행위자(의미상 주어)는 <b>for + 목적격</b>. 사람의 <b>성격 · 태도</b> 형용사(kind · nice · polite · "
             "rude · wise · foolish · smart · brave · careful · generous) 뒤에는 <b>of + 목적격</b> — "
             "「You are kind.」 가 말이 되면 of. <b>that절</b> 진주어에는 for/of 를 쓰지 않는다."},
    {"key": "it", "kind": "fix", "per": 15, "diag": 2, "items": IT, "mix": ["가주어", "대명사", "비인칭"],
     "head": "밑줄 친 it 이 가주어 · 대명사 · 비인칭 중 무엇인지 쓰시오",
     "rule": "<b>가주어</b> 뒤에 진주어(to부정사 · that절)가 있다, 해석 안 함 / <b>대명사</b> 앞에 나온 것을 가리킨다, 「그것」 / "
             "<b>비인칭</b> 날씨 · 시간 · 날짜 · 요일 · 거리 · 명암, 해석 안 함"},
    {"key": "fix", "kind": "fix", "per": 15, "diag": 2, "items": FIX, "mix": "OX",
     "head": "밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오",
     "rule": "It is 형용사 <b>to + 동사원형</b> · 가주어는 This/That 이 아니라 <b>It</b> · for/of 뒤는 <b>목적격</b> · "
             "<b>call + 목적어 + 명사</b> — 목적어와 명사 사이에 to · as · of 를 넣지 않는다, 순서는 「부르는 대상 → 이름」"},
    {"key": "call", "kind": "fix", "per": 10, "diag": 1, "items": CALL, "mix": ["3형식", "5형식"],
     "head": "밑줄 친 call 이 3형식인지 5형식인지, 뜻과 함께 쓰시오",
     "rule": "<b>3형식</b> call + 목적어: 전화하다 · 부르다 (I'll call you later. you ≠ later) / "
             "<b>5형식</b> call + 목적어 + 명사: ~을 …라고 부르다 (He calls his dog Max. his dog = Max)"},
    {"key": "build", "kind": "build", "per": 10, "diag": 1, "items": BUILD,
     "head": "우리말과 같도록 주어진 말을 써서 영어로 쓰시오",
     "rule": "주어진 말은 알맞은 형태로 바꾼다. 가주어 문장은 <b>It</b> 으로 시작 · 의미상 주어가 필요하면 "
             "for/of + 목적격 · 「A를 B라고 부르다」 는 <b>call A B</b>."},
]
