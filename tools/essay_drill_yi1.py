# -*- coding: utf-8 -*-
"""
영일중1 5·6·7과 **서술형 집중드릴**의 문항 — make_essay_drill.py 가 읽는다 (--unit 영일중1).

원장 2026-11-15 「이번 서술형 출제 경향을 반영 · 서술형 연습을 더 정교하게 · 서술형이 변별력이 있어야」.
근거는 data/stage0/comparisons/중1_영일_2026기말_기출.md §3·§4.

2026 기말 논술 두 문항은 한 문장 안에서 세 가지를 한꺼번에 봤다:
  ① 글의 요지를 잡는다  ② 다른 낱말·다른 구조로 바꾼다 (「윗글에서 연속된 3단어 이상 그대로 쓰지 말 것」)
  ③ 지정 어법을 틀리지 않는다 (비교급 / would + 동사원형 / because + 주어 + 동사)
우리 동형 서술형 20문항은 ③만 물었다. 이 드릴은 ①②를 따로 떼어 훈련하고 실전에서 합친다.

구역
  BANK     바꿔 쓰기 낱말 은행 — 범위 지문 표현 → 뜻이 같은 다른 말 (②의 재료)
  REWRITE  밑줄 친 부분 바꿔 쓰기 (②)
  COMPARE  비교급으로 한 문장 (논술1형의 ③)
  OPINION  If I were ~, I would ~ because ~ (논술2형의 ③)
  JUDGE    채점자 되어 보기 — 학생 답에서 어긴 조건·틀린 곳 찾기 (조건 점검 습관)
  MOCK     실전 — 지문 + A형(요약 · 비교급 · 4점) + B형(의견 · 이유 · 6점)

실전의 범위 지문은 data/stage0/passages 의 body_text 에서 **잘라 온다** (손으로 치지 않는다 — 설계원칙 7).
처음 보는 글 두 편은 여기서 새로 썼다 (2026 기말이 처음 보는 글에서 논술 6점을 냈다).
모범답이 「연속 3단어」 조건을 스스로 어기지 않는지는 make_essay_drill.py 가 기계로 본다.
"""

# ── 1. 낱말 은행 — (본문 표현, 바꿔 쓸 말, 어디서) ─────────────────────────
BANK = [
    ("come first", "be the most important", "Two Jobs"),
    ("what you enjoy", "your personal preference", "Two Jobs"),
    ("hate", "do not like / dislike", "Two Jobs"),
    ("work alone", "work by oneself", "Two Jobs"),
    ("be away from home", "leave home", "Two Jobs"),
    ("start and stop working when they want", "choose their own working hours", "Two Jobs"),
    ("make decisions quickly", "decide fast", "Two Jobs"),
    ("stay awake", "not sleep", "Two Jobs"),
    ("a few similarities", "some things in common", "Two Jobs"),
    ("few famous women", "not many well-known women", "Two Jobs"),
    ("turn trash into something new", "make something new from waste", "Upcycle"),
    ("tear ~ apart", "rip", "Upcycle"),
    ("fix", "repair", "Upcycle · L6"),
    ("look unique", "seem special", "Upcycle"),
    ("decorate", "make ~ prettier", "Upcycle"),
    ("produce lots of waste", "make too much trash", "L6"),
    ("leftovers", "the food that remained", "L6"),
    ("eat out", "have a meal at a restaurant", "L6"),
    ("bring ~ home", "take ~ to one's house", "L6"),
    ("reusable", "that you can use again", "L6"),
    ("never go away", "stay forever", "L6"),
    ("in return", "as a reward", "L6"),
    ("run after", "chase", "L5"),
    ("couldn't catch", "failed to catch", "L5"),
    ("a little taller", "slightly taller", "L5"),
    ("remember ~ clearly", "cannot forget", "L5"),
    ("be in charge of", "be responsible for", "L7"),
    ("be over", "finish / end", "L7"),
    ("calm ~", "make ~ relaxed", "L7"),
    ("get too excited", "cannot stay calm", "L7"),
    ("read a lot", "read many books", "L7"),
    ("sound real", "sound like the real thing", "L7"),
    ("cannot speak", "be not able to talk", "기출"),
    ("let ~ know", "tell ~", "기출"),
    ("solve the case", "find the answer to the crime", "기출"),
    ("be afraid of", "be scared of", "기출"),
]

# ── 2. 밑줄 친 부분 바꿔 쓰기 — (문장 【밑줄】, 주어진 말, 고친 밑줄 부분) ──────
REWRITE = [
    ("What you enjoy 【should come first】.", "be / the most", "is the most important"),
    ("Jane 【hates working alone】.", "not like / by herself", "does not like working by herself"),
    ("Pilots 【are often away from home】.", "leave / often", "often leave home"),
    ("Artists can 【start and stop working when they want】.", "choose / hours", "choose their own working hours"),
    ("Pilots sometimes have to 【make important decisions quickly】.", "decide / things / fast", "decide important things fast"),
    ("There are 【few famous women】 in both jobs.", "not many / well-known", "not many well-known women"),
    ("They agreed that there are 【a few similarities】.", "some things / common", "some things in common"),
    ("My dog 【tore my bag apart】.", "rip", "ripped my bag"),
    ("We can 【turn trash into something new】.", "make / from", "make something new from trash"),
    ("Suna said that the bag 【looked unique】.", "seem / special", "seemed special"),
    ("There were lots of leftovers, but we 【brought them home】.", "take / our house", "took them to our house"),
    ("My family and I 【ate out】.", "have dinner / restaurant", "had dinner at a restaurant"),
    ("I heard that plastic 【never goes away completely】.", "stay / forever", "stays forever"),
    ("I got some points 【in return】.", "as / reward", "as a reward"),
    ("I ran after him, but I 【couldn’t catch him】.", "fail / catch", "failed to catch him"),
    ("He was 【a little taller than me】.", "slightly / I am", "slightly taller than I am"),
    ("I’m 【in charge of】 all the cameras.", "responsible", "responsible for"),
    ("My work begins after the shooting 【is over】.", "finish", "finishes"),
    ("I use hand signals to 【calm him】.", "make / relaxed", "make him relaxed"),
    ("Storytelling skills are important for my job, so I 【read a lot】.", "many books", "read many books"),
    ("Sally 【cannot speak】.", "be / able / talk", "is not able to talk"),
    ("He 【cannot solve the case without help】.", "need / someone’s help / to", "needs someone’s help to solve the case"),
    ("In the end, she 【lets him know】 who the killer is.", "tell", "tells him"),
    ("At first, she 【is afraid of】 Inspector Barker.", "scared", "is scared of"),
]

# ── 3. 비교급으로 한 문장 — (주어진 내용, 주어진 말, 모범답) ────────────────────
COMPARE = [
    ("What you enjoy should come first when you choose a job.",
     "what you enjoy / important / other things", "What you enjoy is more important than other things."),
    ("Pilots are often away from home. Artists work at home.",
     "artists / stay home / often / pilots", "Artists stay home more often than pilots."),
    ("Pilots usually work with other people. Artists usually work alone.",
     "pilots / meet people / often / artists", "Pilots meet people more often than artists."),
    ("Jeans are strong, so they are perfect for a bag.",
     "jeans / strong / other clothes", "Jeans are stronger than other clothes."),
    ("I ran after him, but I couldn’t catch him.",
     "he / run / fast / I", "He ran faster than I did."),
    ("Recording on location is not easy, so Chris works in his studio.",
     "working in a studio / easy / recording outside", "Working in a studio is easier than recording outside."),
    ("Practice is very important. Talent is not so important.",
     "practice / important / talent", "Practice is more important than talent."),
    ("The first box was 3 kg. The second box was 5 kg.",
     "the second box / heavy / the first one", "The second box was heavier than the first one."),
    ("The Earth was sick last year. Now it is very sick.",
     "the Earth / get / sick / and", "The Earth is getting sicker and sicker."),
    ("The story was good. After editing, it was very good.",
     "the story / become / good / before", "The story became better than before."),
    ("A new bag costs 30,000 won. Fixing the old bag costs 5,000 won.",
     "fixing the old bag / cheap / buying a new one", "Fixing the old bag is cheaper than buying a new one."),
    ("We had a lot of different cakes. He wanted a very small one.",
     "his cake / small / the other cakes", "His cake was smaller than the other cakes."),
    ("Plastic stays for 500 years. Paper stays for a few months.",
     "plastic / stay / long / paper", "Plastic stays longer than paper."),
    ("Walking is good for the Earth. Driving is bad for the Earth.",
     "driving / bad / walking / for the Earth", "Driving is worse than walking for the Earth."),
    ("Max is calm at home. He gets too excited when a lot of people are around.",
     "Max / excited / around people / at home", "Max is more excited around people than at home."),
    ("Jane hates working alone. She enjoys working with people.",
     "Jane / like / working with people / much / working alone",
     "Jane likes working with people more than working alone."),
]

# ── 4. 의견 + 이유 — (상황, 누구, 입장 · 이유 힌트, 모범답: would 뒤부터) ───────
OPINION = [
    ("Domingo’s dog tore his bag.", "Domingo",
     "가방을 고친다 · 쓰레기를 줄일 수 있어서", "fix the bag because I can reduce waste"),
    ("Domingo’s dog tore his bag.", "Domingo",
     "새 가방을 산다 · 바느질을 잘 못해서", "buy a new bag because I am not good at sewing"),
    ("Camila remembers the young man with blue eyes.", "Camila",
     "경찰에게 그 남자에 대해 말한다 · 범인을 찾는 데 도움이 되어서",
     "tell the police about him because it can help them find the criminal"),
    ("Yuna asks Alex to join her plogging club.", "Alex",
     "동아리에 가입한다 · 플로깅이 건강과 지구에 좋아서",
     "join the club because plogging is good for my health and the Earth"),
    ("Yuna asks Alex to join her plogging club.", "Alex",
     "가입하지 않는다 · 토요일 아침마다 축구 연습이 있어서",
     "not join the club because I have soccer practice every Saturday morning"),
    ("Minsu got some points from the recycling machine.", "Minsu",
     "포인트를 모아 둔다 · 나중에 더 큰 것을 살 수 있어서",
     "save the points because I can buy something bigger later"),
    ("Jane hates working alone.", "Jane",
     "조종사가 된다 · 사람들과 일하는 것이 나를 행복하게 해서",
     "become a pilot because working with people makes me happy"),
    ("Max gets too excited when a lot of people are around.", "Jennifer",
     "촬영 전에 Max 와 산책한다 · 걷는 것이 그를 차분하게 해서",
     "take a walk with Max before the shooting because walking makes him calm"),
    ("Emma can delete some scenes to create a better story.", "Emma",
     "지루한 장면들을 지운다 · 더 짧은 영화가 더 재미있어서",
     "delete the boring scenes because a shorter movie is more interesting"),
    ("Mina’s dog tore her bag apart.", "Mina",
     "가방을 고친다 · 고치는 것이 새로 만드는 것보다 빨라서",
     "fix the bag because fixing is faster than making a new one"),
    ("Sally saw the murder, but she cannot speak.", "Inspector Barker",
     "Sally 를 믿는다 · 범죄를 자기 눈으로 봤으니까",
     "trust Sally because she saw the crime with her own eyes"),
    ("Sally saw the murder, but she cannot speak.", "Inspector Barker",
     "Sally 를 믿지 않는다 · 동물은 실수를 할 수 있어서",
     "not trust Sally because animals can make mistakes"),
]

# ── 5. 채점자 되어 보기 — (근거 문장, 답안 틀, 조건, 학생 답, 판정, 고친 답) ─────
# 판정 첫 낱말이 갈래: 그대로(3단어) · 어법 · 내용 · O
_J1 = ("What you enjoy should come first.", "Maria and Jane agree that ________ in choosing a job.", "비교급 · 주어+동사 · 연속 3단어 금지")
_J2 = ("Sally saw the murder. Sally is a very smart chimpanzee.", "If I were Inspector Barker, I would ________.", "입장 · 이유 · 연속 3단어 금지")
_J3 = ("He was faster than me.", "Carlos could not catch the man because the man ________.", "비교급 · 연속 3단어 금지")
_J4 = ("Jeans are strong, so they are perfect for a bag.", "Mina chose jeans because ________.", "비교급 · 주어+동사 · 연속 3단어 금지")
JUDGE = [
    (*_J1, "what you enjoy should come first", "그대로 — 연속 6단어를 옮겼고 비교급도 없다",
     "your preference is more important than other things"),
    (*_J1, "there are many things to think about", "내용 — 요지가 아닌 앞부분을 골랐다. 비교급도 없다",
     "what you like is more important than other things"),
    (*_J1, "personal preferences more important than money", "어법 — 동사가 없다 (are)",
     "personal preferences are more important than money"),
    (*_J1, "your preference is importanter than money", "어법 — 긴 형용사는 more important",
     "your preference is more important than money"),
    (*_J1, "liking a job is more better than money", "어법 — more 와 better 를 겹쳐 쓰지 않는다",
     "liking a job is better than money"),
    (*_J1, "your own taste matters more than other things", "O — 비교급(more than) · 주어+동사 · 조건 모두 지킴", "O"),
    (*_J2, "believe the Sally’s information because she saw the murder",
     "그대로 — saw the murder 가 연속 3단어. 어법 — 사람 이름의 소유격 앞에 the 를 쓰지 않는다",
     "believe Sally’s information because she watched the crime"),
    (*_J2, "trust Sally because of she watched the crime", "어법 — because of 뒤에는 명사. 문장이 오면 because",
     "trust Sally because she watched the crime"),
    (*_J2, "trusts Sally because she is clever", "어법 — would 뒤에는 동사원형 (trust)",
     "trust Sally because she is clever"),
    (*_J2, "because she is a very smart chimpanzee", "내용 — 믿을지 말지(입장)가 없다. 그대로 — 연속 6단어",
     "trust Sally because she is clever"),
    (*_J2, "trust Sally", "내용 — 이유가 없다", "trust Sally because she watched the crime"),
    (*_J2, "not trust Sally because she can tell for the police a lie", "어법 — tell + 사람 + 내용 (for 없이)",
     "not trust Sally because she can tell the police a lie"),
    (*_J2, "trust Sally because she watched the crime", "O — 입장 · 이유 · 조건 모두 지킴", "O"),
    (*_J3, "was faster than Carlos", "그대로 — was faster than 이 연속 3단어", "ran more quickly than Carlos"),
    (*_J3, "run more fast than Carlos", "어법 — 과거의 일이므로 ran · fast 의 비교급은 faster",
     "ran faster than Carlos"),
    (*_J4, "they are perfect for a bag", "그대로 — 연속 6단어를 옮겼고 비교급도 없다",
     "jeans are stronger than other clothes"),
    (*_J4, "jeans is stronger than other clothes", "어법 — jeans 는 복수 (are)",
     "jeans are stronger than other clothes"),
    (*_J4, "jeans last longer than other clothes", "O — 비교급 · 주어+동사 · 조건 모두 지킴", "O"),
]

# ── 6. 실전 — 지문 + A형(4점) + B형(6점) ────────────────────────────────────
# passage: ("id", [body_text 에서 그대로 잘라 온 조각…]) 또는 ("new", [새로 쓴 단락…])
# a / b: {"frame": 답안 틀, "ko": 발문 보충, "answers": [모범답…], "trap": 자주 나오는 감점 답}
MOCK = [
    {"title": "Two Different Jobs", "src": "외부지문 · 2026 기말 10·11번 · 논술1 지문",
     "passage": ("영일중1_L7_외부지문_TwoDifferentJobs", None),
     "a": {"frame": "According to the passage, one difference in lifestyle is that ____(A)____.",
           "answers": ["artists spend more time at home than pilots",
                       "pilots leave home more often than artists"],
           "trap": "pilots are often away from home — 연속 3단어 이상 · 비교급 없음"},
     "b": {"frame": "If I had to choose one of the two jobs, I would ________.",
           "ko": "두 직업 중 하나를 고르고 그 이유를 쓰시오.",
           "answers": ["choose the pilot’s job because I enjoy being part of a team",
                       "choose the artist’s job because I want to decide my own working time"],
           "trap": "be a pilot because pilots usually work with other people — 연속 3단어 이상"}},
    {"title": "Challenge Upcycle", "src": "외부지문 · 2026 기말 5·6번 지문",
     "passage": ("영일중1_L6_외부지문_ChallengeUpcycle", None),
     "a": {"frame": "According to the passage, Mina chose her old jeans because ____(A)____.",
           "answers": ["jeans are stronger than other clothes",
                       "they last longer than other old clothes"],
           "trap": "they are perfect for a bag — 연속 3단어 이상 · 비교급 없음"},
     "b": {"frame": "If I were Mina, I would ________.",
           "ko": "찢어진 가방을 고칠지, Mina 처럼 새로 만들지 밝히고 그 이유를 쓰시오.",
           "answers": ["also upcycle the jeans because making my own bag is more fun",
                       "fix the torn bag because repairing takes less time"],
           "trap": "make a bag from old jeans because … — 연속 3단어 이상"}},
    {"title": "Who Threw a Cake at the Monalisa?", "src": "5과 본문 · 2026 기말 23번 지문",
     "passage": ("중1L5_본문", [
         "An old man with gray hair was running away, and something fell off his head. It was his wig. I ran after him, but I couldn’t catch him. He was faster than me. In fact, the old man was not old. He was a young man with long brown hair.",
         "Last Friday, a young man came in. I spoke to him in Spanish, but he didn’t understand me. He spoke only English. We had a lot of different cakes, but he just wanted the smallest one. We sold only one cake that day, so I remember him clearly. Oh, he had blue eyes."]),
     "labels": ["Carlos Diaz, a janitor", "Camila Santos, the owner of Camila’s Bakery"],
     "a": {"frame": "According to the passage, Carlos Diaz could not catch the man because the man ____(A)____.",
           "answers": ["ran more quickly than Carlos", "was quicker than the janitor"],
           "trap": "was faster than me — 연속 3단어 이상 (me 가 가리키는 사람도 틀림)"},
     "b": {"frame": "If I were Camila Santos, I would ________.",
           "ko": "그 남자에 대해 경찰에 말할지 말지 밝히고 그 이유를 쓰시오.",
           "answers": ["tell the police about the man because I still remember his face well",
                       "not tell the police because buying a cake does not make him a criminal"],
           "trap": "tell the police because I remember him clearly — 연속 3단어 이상"}},
    {"title": "Join the Zero-Waste Challenge", "src": "6과 본문 · 2026 기말 2·4번 지문",
     "passage": ("중1L6_본문", [
         "My dog tore my bag. I wanted to buy a new one, but I thought again. I learned that reusing is important for zero-waste living. So, I decided to fix it and reuse it. I’m not very good at sewing, and I don’t think that the bag looks perfect. I guess it’s all right.",
         "I often use food delivery services, but today I didn’t. Instead, I walked to my favorite restaurant with a reusable container and picked up the food. I heard that plastic never goes away completely. I didn’t use any single-use plastic today. I felt good!"]),
     "labels": ["Domingo", "Emma"],
     "a": {"frame": "According to the passage, Domingo thinks that ____(A)____.",
           "answers": ["repairing his old bag is better than getting another bag",
                       "using an old thing again is more important than shopping"],
           "trap": "reusing is important for zero-waste living — 연속 3단어 이상 · 비교급 없음"},
     "b": {"frame": "If I were Emma, I would ________.",
           "ko": "내일도 음식을 직접 가지러 갈지 말지 밝히고 그 이유를 쓰시오.",
           "answers": ["keep walking to the restaurant because it helps reduce plastic waste",
                       "order the food at home because walking there takes too much time"],
           "trap": "walk to the restaurant because plastic never goes away — 연속 3단어 이상"}},
    {"title": "Let’s Make a Movie!", "src": "7과 본문 · 2026 기말 19·20번 지문",
     "passage": ("중1L7_본문", [
         "I’m Jennifer. I trained and took care of Max for a long time. Max is a great actor, but he sometimes gets too excited when a lot of people are around. So, I use hand signals to calm him. Who am I? I’m an animal wrangler.",
         "I’m Chris, and I’m a Foley artist. I create sound effects in my studio when recording on location is not easy. Listen carefully. Do you hear the sound of waves? I made that sound with rice and a plastic container. Doesn’t it sound real?"]),
     "a": {"frame": "According to the passage, Chris sometimes makes sounds in his studio because ____(A)____.",
           "answers": ["working in a studio is easier than recording outside",
                       "it is harder to record sounds at the real place"],
           "trap": "recording on location is not easy — 연속 3단어 이상 · 비교급 없음"},
     "b": {"frame": "If I were Jennifer, I would ________.",
           "ko": "사람이 아주 많은 촬영장에 Max 를 데려갈지 말지 밝히고 그 이유를 쓰시오.",
           "answers": ["bring Max to the busy place because my hand signals can relax him",
                       "not take Max there because big crowds make him too nervous"],
           "trap": "take Max because I use hand signals to calm him — 연속 3단어 이상"}},
    {"title": "The Secret of the Old Library", "src": "처음 보는 글 (책 소개) — 2026 기말 13~15번 · 논술2 꼴",
     "passage": ("new", [
         "This book is a mystery story for young readers. Jimin, a middle school student, finds an old letter in the school library. The letter says that a treasure is hidden somewhere in the building. Jimin wants to look for it, but she cannot read the map in the letter.",
         "The help comes from Mr. Han, the school gardener. He worked at the school for thirty years and knows every room. At first, Jimin does not talk to him because he looks scary. Later, she learns that he is kinder than any other adult at school. However, some of her friends say that Mr. Han wants the treasure for himself. If you like mysteries, you will enjoy this book."]),
     "a": {"frame": "According to the passage, Jimin finds out that Mr. Han ____(A)____.",
           "ko": "(A)에는 동사부터 쓰시오.",
           "answers": ["is nicer than the other adults at her school",
                       "is friendlier than the other grown-ups there"],
           "trap": "is kinder than any other adult — 연속 3단어 이상"},
     "b": {"frame": "If I were Jimin, I would ________.",
           "ko": "Mr. Han 에게 도움을 청할지 말지 밝히고 그 이유를 쓰시오.",
           "answers": ["ask Mr. Han for help because nobody understands the building better than him",
                       "not ask him for help because he may take the treasure away"],
           "trap": "ask him because he knows every room — 연속 3단어 이상"}},
    {"title": "My Role Model, Coach Kim", "src": "처음 보는 글 (롤 모델) — 2026 기말 16번 꼴",
     "passage": ("new", [
         "I want to be a swimmer in the future, and my role model is Coach Kim. She was the fastest swimmer in Korea ten years ago. Now she teaches children at a small pool in my town. She comes to the pool earlier than anyone else and checks the water every morning. She always says that practice is more useful than talent.",
         "Last month, I lost a race and wanted to give up swimming. She told me to try one more time. Next week, there is a big race in Busan, but my leg still hurts a little."]),
     "a": {"frame": "According to the passage, Coach Kim believes that ____(A)____.",
           "answers": ["working hard is more important than being talented",
                       "hard training helps more than natural ability"],
           "trap": "practice is more useful than talent — 연속 3단어 이상"},
     "b": {"frame": "If I were the writer, I would ________.",
           "ko": "다음 주 부산 경기에 나갈지 말지 밝히고 그 이유를 쓰시오.",
           "answers": ["join the race because Coach Kim taught me never to quit",
                       "not swim in Busan because resting my leg is better than getting hurt again"],
           "trap": "try one more time because she told me to — 연속 3단어 이상"}},
]

A_COND = ["비교급 표현을 반드시 사용할 것", "주어와 동사가 포함된 한 문장으로 완성할 것",
          "윗글에서 연속된 3단어 이상을 그대로 사용하지 말 것"]
B_COND = ["어떻게 할 것인지(입장)를 분명히 밝힐 것", "자신의 생각을 뒷받침하는 이유를 제시할 것",
          "윗글에서 연속된 3단어 이상을 그대로 사용하지 말 것", "빈칸에 들어갈 내용만 쓸 것"]
