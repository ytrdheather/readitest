# -*- coding: utf-8 -*-
"""
영일중2 7과 어법 **보충** 드릴의 문항 — make_form_drill.py 가 읽는다 (--unit 영일중2L7).

원장 2026-11-12 「보충드릴 만들어」. 범위는 영일중2 L7 학습지 7~8쪽 「동사 call 과 5형식 문장」
(data/stage0/comparisons/중2_영일_L7_학습지.md §4). 공용 형태 드릴 `동아윤정미 중2 7과 어법드릴`
(tools/form_drill_l7.py) 은 call 3형식 / 5형식 구별 · 능동 영작까지만 묻고, 영일이 가르친
**5형식 수동태**(People call the boy a genius → The boy is called a genius) 와
**5형식 동사 정리**(make + 형용사 · want + to부정사 · see/hear + v-ing · call + 명사) 는 없다. 그것만 싣는다.
It ~ to부정사 · 의미상 주어 for / of 는 공용 형태 드릴이 덮으므로 여기엔 안 넣는다.

문장은 학습지 예문 · 연습문제(A 괄호 고르기 · B 배열 · C 바꿔 쓰기)를 그대로 쓰거나 같은 틀로 새로 썼다.
자료 꼴은 form_drill_yd1_l7.py 와 같다 (kind build / fill / fix · mix).
"""

# ── 1. 괄호 고르기 (학습지 연습문제 [A] 꼴) ───────────────────────────────
CHOOSE = [
    ('They ( call / calls ) the new building "Sky Tower".', "call"),
    ("We call the Earth ( a blue planet / to a blue planet ).", "a blue planet"),
    ("The great king ( called / is called ) Sejong by Koreans.", "is called"),
    ("The beautiful song made everyone ( emotional / emotionally ).", "emotional"),
    ("I want you ( apologize / to apologize ) to me right now.", "to apologize"),
    ("My cat ( calls / is called ) Kitty.", "is called"),
    ("People ( call / are called ) Chicago the Windy City.", "call"),
    ("Chicago ( calls / is called ) the Windy City.", "is called"),
    ("He calls ( his dog Rex / Rex his dog ). (그는 자기 개를 Rex 라고 부른다)", "his dog Rex"),
    ("The baby will ( call / be called ) Lily.", "be called"),
    ("They heard people ( shouting / to shout ).", "shouting"),
    ("The news made her ( sad / sadly ).", "sad"),
    ("My parents want me ( study / to study ) harder.", "to study"),
    ("I saw him ( dancing / to dance ) on the stage.", "dancing"),
    ("The boy was called ( a genius / as a genius ) by his teachers.", "a genius"),
    ("Seoul ( called / was called ) Hanyang in the past.", "was called"),
    ("Vietnamese people call ( the hat non la / non la the hat ).", "the hat non la"),
    ("This day ( calls / is called ) the Day of the Dead in Mexico.", "is called"),
    ("Many people ( call / are called ) that actor a legend.", "call"),
    ("The puppy was ( called / calling ) Max by the children.", "called"),
]

# ── 2. 능동 ↔ 수동 바꿔 쓰기 (학습지 [4] · 연습문제 [C] 꼴) ───────────────
# hint 첫머리가 '수동태로' / '능동태로' — 회차마다 고르게 나누는 기준 (mix)
VOICE = [
    ("People call the boy a genius.", "수동태로", "The boy is called a genius (by people)."),
    ("They will call their daughter Lily.", "수동태로", "Their daughter will be called Lily (by them)."),
    ("I called my cat Kitty.", "수동태로", "My cat was called Kitty by me."),
    ('People call New York "The Big Apple".', "수동태로", 'New York is called "The Big Apple" (by people).'),
    ("People call Chicago the Windy City.", "수동태로", "Chicago is called the Windy City (by people)."),
    ("Vietnamese people call the hat non la.", "수동태로", "The hat is called non la by Vietnamese people."),
    ("Tim calls his dog a family member.", "수동태로", "His dog is called a family member by Tim."),
    ("Many people call that actor a legend.", "수동태로", "That actor is called a legend by many people."),
    ("My friends call me Bob.", "수동태로", "I am called Bob by my friends."),
    ("She calls her cleaning robot Clean Master.", "수동태로", "Her cleaning robot is called Clean Master by her."),
    ("People in Mexico call the festival the Day of the Dead.", "수동태로",
     "The festival is called the Day of the Dead by people in Mexico."),
    ("The students called the teacher Mr. Smile.", "수동태로", "The teacher was called Mr. Smile by the students."),
    ("We will call the new robot Tobi.", "수동태로", "The new robot will be called Tobi (by us)."),
    ("People called Seoul Hanyang in the past.", "수동태로", "Seoul was called Hanyang (by people) in the past."),
    ("His teammates call him Captain.", "수동태로", "He is called Captain by his teammates."),
    ("The children called the puppy Max.", "수동태로", "The puppy was called Max by the children."),
    ("People call the festival Fur Rondy.", "수동태로", "The festival is called Fur Rondy (by people)."),
    ("They called the statues fallas.", "수동태로", "The statues were called fallas (by them)."),
    ("Fans call the singer the King of Pop.", "수동태로", "The singer is called the King of Pop by fans."),
    ("We will call our team the Tigers.", "수동태로", "Our team will be called the Tigers (by us)."),
    ("The boy was called a genius by his teachers.", "능동태로", "His teachers called the boy a genius."),
    ('New York is called "The Big Apple" by people.', "능동태로", 'People call New York "The Big Apple".'),
    ("The dog is called Rex by him.", "능동태로", "He calls the dog Rex."),
    ("I am called Bob by my friends.", "능동태로", "My friends call me Bob."),
    ("The baby will be called Lily by her parents.", "능동태로", "Her parents will call the baby Lily."),
    ("The robot was called Clean Master by her.", "능동태로", "She called the robot Clean Master."),
    ("That actor is called a legend by many people.", "능동태로", "Many people call that actor a legend."),
    ("The puppy was called Max by the children.", "능동태로", "The children called the puppy Max."),
    ("The singer is called the King of Pop by fans.", "능동태로", "Fans call the singer the King of Pop."),
    ("The city was called Hanyang by people.", "능동태로", "People called the city Hanyang."),
]

# ── 3. 맞으면 O, 틀리면 고쳐 쓰기 ─────────────────────────────────────────
FIX = [
    ("People call 【him as】 a hero.", "him a hero"),
    ("My friends call 【Bob me】.", "me Bob"),
    ('New York 【is called to】 "The Big Apple".', "is called"),
    ("The boy 【called】 a genius by his teachers.", "was called"),
    ("Chicago 【calls】 the Windy City.", "is called"),
    ("Their daughter will 【called】 Lily.", "be called"),
    ("I want you 【apologize】 to me.", "to apologize"),
    ("They heard people 【to shout】.", "shouting"),
    ("The ceremony made us 【emotionally】.", "emotional"),
    ("My cat 【is calling】 Kitty by me.", "is called"),
    ("He 【call】 his dog Rex.", "calls"),
    ("The hat 【is call】 non la.", "is called"),
    ("This day 【calls】 the Day of the Dead in Mexico.", "is called"),
    ("My mom wants me 【clean】 my room.", "to clean"),
    ("The news made him 【happily】.", "happy"),
    ("Seoul 【is called】 Hanyang in the past.", "was called"),
    ("The new robot 【will be call】 Tobi.", "will be called"),
    ("She calls 【to her robot】 Clean Master.", "her robot"),
    ("I saw him 【to dance】 on the stage.", "dancing"),
    ("They 【are called】 their son Tom.", "call"),
    ("The boy 【is called】 a genius.", "O"),
    ("People 【call】 Chicago the Windy City.", "O"),
    ("Their daughter 【will be called】 Lily.", "O"),
    ("I want you 【to apologize】 to me.", "O"),
    ("The song made everyone 【emotional】.", "O"),
    ("They heard people 【shouting】.", "O"),
    ("My friends call 【me Bob】.", "O"),
    ("Seoul 【was called】 Hanyang in the past.", "O"),
    ("He 【calls】 his dog Rex.", "O"),
    ("The hat is called 【non la】 by Vietnamese people.", "O"),
]

# ── 4. 우리말 → 영어 (학습지 연습문제 [B] 꼴 + 수동태) ─────────────────────
BUILD = [
    ("내 친구들은 나를 Bob 이라고 부른다.", "call, Bob", "My friends call me Bob."),
    ("그 소년은 천재라고 불린다.", "수동태 · a genius", "The boy is called a genius."),
    ("사람들은 시카고를 Windy City 라고 부른다.", "people, call, the Windy City", "People call Chicago the Windy City."),
    ('뉴욕은 사람들에 의해 "The Big Apple" 이라고 불린다.', "수동태 · by people", 'New York is called "The Big Apple" by people.'),
    ("그들은 딸을 Lily 라고 부를 것이다.", "will, their daughter", "They will call their daughter Lily."),
    ("그들의 딸은 Lily 라고 불릴 것이다.", "수동태 · will", "Their daughter will be called Lily."),
    ("베트남 사람들은 그 모자를 non la 라고 부른다.", "Vietnamese people, the hat", "Vietnamese people call the hat non la."),
    ("Tim 은 자신의 개를 가족의 일원이라고 부른다.", "his dog, a family member", "Tim calls his dog a family member."),
    ("많은 사람들은 그 배우를 전설이라고 부른다.", "that actor, a legend", "Many people call that actor a legend."),
    ("그 소년은 선생님들에 의해 천재라고 불렸다.", "수동태 · his teachers", "The boy was called a genius by his teachers."),
    ("나는 내 고양이를 Kitty 라고 불렀다.", "call, my cat", "I called my cat Kitty."),
    ("내 고양이는 Kitty 라고 불렸다.", "수동태 · 과거", "My cat was called Kitty."),
    ("그 의식은 우리를 감동하게 만들었다.", "the ceremony, make, emotional", "The ceremony made us emotional."),
    ("나는 네가 나에게 사과하기를 원한다.", "want, apologize", "I want you to apologize to me."),
    ("그들은 사람들이 소리치는 것을 들었다.", "hear, shout", "They heard people shouting."),
    ("서울은 과거에 한양이라고 불렸다.", "수동태 · in the past", "Seoul was called Hanyang in the past."),
    ("그녀는 자신의 청소 로봇을 Clean Master 라고 부른다.", "her cleaning robot", "She calls her cleaning robot Clean Master."),
    ("멕시코 사람들은 이 날을 망자의 날이라고 부른다.", "people in Mexico, the Day of the Dead",
     "People in Mexico call this day the Day of the Dead."),
    ("그 축제는 Fur Rondy 라고 불린다.", "수동태 · the festival", "The festival is called Fur Rondy."),
    ("우리는 새 로봇을 Tobi 라고 부를 것이다.", "will, the new robot", "We will call the new robot Tobi."),
]

SECTIONS = [
    {"key": "choose", "kind": "fill", "per": 10, "diag": 2, "items": CHOOSE,
     "head": "괄호 안에서 알맞은 것을 고르시오",
     "rule": "<b>5형식</b> 주어 + 동사 + 목적어 + 목적격 보어 — make + 목적어 + <b>형용사</b> (부사 ✕) · "
             "want + 목적어 + <b>to부정사</b> · see / hear + 목적어 + <b>v-ing</b> · call + 목적어 + <b>명사</b> "
             "(as · to 를 넣지 않는다). 주어가 「불리는」 쪽이면 <b>be called</b>."},
    {"key": "voice", "kind": "build", "per": 15, "diag": 2, "items": VOICE, "mix": ["수동태로", "능동태로"],
     "head": "다음 문장을 지시대로 바꿔 쓰시오",
     "rule": "<b>능동</b> 주어 + call + 목적어 + 명사 → <b>수동</b> 목적어 + <b>be called</b> + 명사 (+ by 행위자). "
             "목적격 보어(명사)는 called 뒤에 <b>그대로</b> 둔다. 시제는 be동사로: is · was · will be. "
             "행위자가 people · they 처럼 일반 사람이면 by ~ 생략 가능. 대명사는 by <b>목적격</b>(me · him · them)."},
    {"key": "fix", "kind": "fix", "per": 15, "diag": 2, "items": FIX, "mix": "OX",
     "head": "밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오",
     "rule": "call A B — A(목적어) 다음 B(이름), 사이에 as · to 없음. 주어가 불리는 것이면 <b>be + called</b> "
             "(calling · call ✕). 과거 일이면 was / were called, 미래는 will be called. "
             "make + 형용사 · want + to부정사 · see / hear + v-ing."},
    {"key": "build", "kind": "build", "per": 10, "diag": 2, "items": BUILD,
     "head": "괄호 안의 말을 이용해 우리말과 같도록 영어로 쓰시오",
     "rule": "「A를 B라고 부르다」 call A B · 「A는 B라고 불린다」 A is called B (과거 was · 미래 will be). "
             "주어진 말은 알맞은 형태로 바꾼다."},
]
