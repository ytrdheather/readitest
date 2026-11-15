# -*- coding: utf-8 -*-
"""
영일중3 5·6·7과 동형 2세트 (고난도) — 2026-11-08 원장 「다양한 문제 경험하게 두 세트 더」.

1세트와 지문 구간·유형을 갈랐다:
  5과 피트 크루 · 페이서 전체 / 6과 도입(Boggis 의 비밀) / 7과 도입 · 스포츠 · 범죄 /
  Fly Away Home (2)(3)(5)(6)(7)(8) / 학교 영영풀이 심화B · 어휘 3지선다.
  python data/generated/mock_g3/make_영일중3_2세트.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import mat, item, essay, finish      # noqa: E402

# 1 ── 영영풀이 연결 ────────────────────────────────────────────
item(3, "다음 중 단어와 영영풀이의 연결이 바르지 않은 것은?",
     ["dealer – someone who buys and sells a particular product",
      "attach – to fasten one thing to another",
      "charge – to ask people to pay a particular amount of money for something",
      "reproduction – an old object such as a piece of furniture that has a high value",
      "shocked – very surprised and upset"], 4,
     "④ 는 antique 의 풀이. reproduction 은 「a copy of something such as a picture」.",
     None, "6과 영영풀이 (학교 심화B)")

# 2 ── 어휘 3지선다 (학교 학습지 꼴) ──────────────────────────────
mat("T1", "어휘", """
Mr. Lee bought what he thought was a(n) (A)[reproduction / original] of a famous painting at a flea market. He paid only ten dollars for it. Later, an expert told him that the painting was (B)[worth / worthy] more than a million dollars. It was not a copy but a (C)[priceless / valueless] work that the painter himself had painted.
""")
item(3, "(A), (B), (C)의 각 네모 안에서 문맥과 어법에 맞는 낱말로 가장 적절한 것은?",
     ["original – worth – valueless", "original – worthy – priceless",
      "reproduction – worthy – valueless", "reproduction – worth – valueless",
      "reproduction – worth – priceless"], 5,
     "(A) 10달러에 샀다 → 「복제품인 줄 알았다」 (B) be worth + 금액 (worthy 는 of 가 필요) (C) 진품이었으니 매우 귀중한 priceless — valueless 는 「가치 없는」.",
     "T1", "priceless ≠ valueless")

# 3·4 ── 피트 크루 ─────────────────────────────────────────────
mat("T2", "5과 본문 — Pit Crews in Car Racing", """
You may only see the car and the driver during most car races, but there is a team ⓐbehind the driver. This team is called a pit crew. A pit is a place on the side of the race track, and drivers stop there ⓑseveral times during a race. The main job of the pit crew is to check the car and change the tires. Changing the tires is especially important because the tires wear out ⓒrarely in a high speed race. A pit stop can be as short as 2 seconds, and there are as many as 20 members on a crew. Therefore, the pit crew has to work in ⓓperfect harmony. The driver may get all the attention, but as people say, "Races are ⓔwon in the pits."
""")
item(5, "윗글의 ⓐ~ⓔ 중 문맥상 낱말의 쓰임이 적절하지 않은 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 3,
     "타이어 교체가 특히 중요한 「이유」 자리 — 빠른 경주에서 타이어가 「쉽게(easily)」 닳기 때문이다. rarely 면 이유가 되지 않는다.",
     "T2")
item(3, "윗글의 마지막 문장 \"Races are won in the pits.\"가 의미하는 바로 가장 적절한 것은?",
     ["피트에서 쉬는 시간이 길수록 경주에서 이긴다.",
      "경주의 승패는 피트 크루의 숨은 노력에 크게 달려 있다.",
      "피트 크루가 직접 차를 운전해 우승을 차지한다.",
      "피트에 자주 서는 레이서는 경주에서 진다.",
      "관중은 레이서보다 피트 크루에게 더 많은 관심을 둔다."], 2,
     "레이서가 주목을 받지만(may get all the attention) 2초 만에 타이어를 갈아 주는 크루의 손에 승부가 갈린다.",
     "T2")

# 5 ── 페이서 제목 ─────────────────────────────────────────────
mat("T3", "5과 본문 — Pacers in a Marathon", """
Pacers run with other runners and lead them in a marathon. Pacers are experienced runners and their job is to help other runners manage their race better. There can be several pacers in a race. Each pacer runs at different speeds and finishes the race in different times. Pacers usually have flags or balloons showing their finish time. Runners can choose a pacer depending on their target finish time. For example, if a runner wants to finish the race in four hours, the runner will follow the four-hour pacer. Since the pacer keeps track of the time, the runner can achieve his or her goal of finishing the marathon in a particular time more easily. In short, pacers run but they don't run to win. They run for others.
""")
item(3, "윗글의 제목으로 가장 적절한 것은?",
     ["How to Become a Professional Marathon Runner",
      "Pacers: Runners Who Run for Others",
      "Why Pacers Always Win the Race",
      "The Long History of the Marathon",
      "Choosing the Right Balloons for a Race"], 2,
     "마지막 두 문장 — 이기려고 뛰지 않고 남을 위해 뛴다.",
     "T3")

# 6 ── as 원급 as 개수 ─────────────────────────────────────────
mat("T4", "〈보기〉", """
(a) A pit stop can be as short as 2 seconds.
(b) There are as many as 20 members on a crew.
(c) Sherpas are as more important as climbers.
(d) The pacer ran as fastly as possible.
(e) This table is three times as old as that one.
(f) He is not so tall as his brother.
(g) Runners can finish the race as easy as they can.
(h) She likes music as well as sports.
""")
item(5, "〈보기〉에서 어법상 옳은 문장의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 4,
     "옳은 것 (a)(b)(e)(f)(h). (c) 원급 → as important as (d) fast 는 부사도 fast (g) finish 를 꾸미는 부사 easily.",
     "T4", "as 원급 as · 배수사 · as well as")

# 7 ── 5과 대화 순서 ───────────────────────────────────────────
mat("T5", "5과 대화", """
B: Suji, how often do you take bowling lessons?
(A) Well, I love bowling. Hmm. Your bowling ball looks heavy for you. I suggest you use a lighter ball.
(B) Twice a week. I'm just a beginner. I heard you're very good.
(C) OK. I'll look for a lighter one, then.
""")
item(3, "주어진 말에 이어질 대화의 순서로 가장 적절한 것은?",
     ["(A) - (B) - (C)", "(A) - (C) - (B)", "(C) - (A) - (B)", "(C) - (B) - (A)", "(B) - (A) - (C)"], 5,
     "빈도 질문 → 일주일에 두 번, 넌 잘한다며(B) → 더 가벼운 공을 써 봐(A) → 그럼 찾아볼게(C).",
     "T5", "빈도 묻기 · 제안하기")

# 8·9 ── 6과 도입 ──────────────────────────────────────────────
mat("T6", "6과 본문 — One Lucky Sunday", """
Cyril Boggis was an antique furniture dealer in London. He was known for ⓐbuying good things at a low price and then selling them at a high price. People asked him where he ⓑhad got the furniture, but he just said, "It's a secret." Mr. Boggis' secret was simple. He went to small towns every Sunday and knocked on doors. He told people that he was a furniture dealer. People didn't know ⓒhow their things were valuable, so Mr. Boggis took advantage of them. He ⓓwas able to buy things very cheaply. Now it was another Sunday, and Mr. Boggis was in a small town again. At a house ⓔhe visited, he met two men. One was Rummins, the owner, and the other was his son Bert.
""")
item(4, "윗글의 내용과 일치하는 것은?",
     ["Mr. Boggis told people exactly where he had got his furniture.",
      "Mr. Boggis visited big cities on weekdays to find old furniture.",
      "The people Mr. Boggis visited knew how much their things were worth.",
      "Mr. Boggis bought things cheaply from people who didn't know their real value.",
      "Rummins lived alone in the house that Mr. Boggis visited."], 4,
     "took advantage of them — 값을 모르는 사람들에게서 싸게 샀다. ① It's a secret ② 작은 마을, 일요일마다 ⑤ 아들 Bert.",
     "T6")
item(4, "윗글의 ⓐ~ⓔ 중 어법상 옳지 않은 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 3,
     "how 가 형용사를 데리고 다니는 간접의문문 → how valuable their things were. ⓐ 전치사 for + 동명사 ⓑ 물은 시점보다 먼저 → 과거완료 ⓔ 목적격 관계대명사 생략.",
     "T6", "간접의문문 어순 (how + 형용사)")

# 10 ── 과거완료 있는 대로 ─────────────────────────────────────
mat("T7", "〈보기〉", """
(a) When Mr. Boggis came back, the legs had been cut off.
(b) Rummins had sold the table before Mr. Boggis has arrived.
(c) I had never seen such a priceless table until I visited the museum.
(d) She lost the book that her father had bought for her.
(e) The train has already left when he got to the station.
(f) Dinosaurs had become extinct before humans appeared on Earth.
""")
item(5, "〈보기〉에서 어법상 옳은 문장만을 있는 대로 고른 것은?",
     ["(a), (c)", "(a), (c), (d)", "(a), (c), (d), (f)", "(a), (b), (d), (f)", "(c), (d), (e), (f)"], 3,
     "(b) 과거완료의 기준 시점은 과거 → arrived (e) 과거 시점(got)보다 먼저 → had already left.",
     "T7", "과거완료")

# 11 ── 6과 대화 ────────────────────────────────────────────────
mat("T8", "6과 대화", """
B: You look excited, Sally. What's up?
G: I'm going to go to the Dream Concert.
B: ____________________
G: Thanks. I'm so happy to get a chance to see my favorite singer.
""")
item(3, "대화의 빈칸에 들어갈 말로 가장 적절한 것은?",
     ["Congratulations! I know how much you wanted to go.",
      "I'm sorry to hear that. Cheer up.",
      "That's too bad. Maybe next time.",
      "I hope you feel better soon.",
      "Don't worry. You can go to the concert next time."], 1,
     "기뻐하는 친구에게 축하 → Thanks. 나머지는 유감·위로.",
     "T8", "축하하기")

# 12 ── 7과 문장 삽입 ──────────────────────────────────────────
mat("T9", "7과 본문 — Living with Big Data", """
Have you ever visited an online bookstore and been surprised by the books that the store recommended for you? Many of them looked interesting to you. ( ① ) So how did the bookstore know what you liked? This is all possible because of big data. ( ② ) Big data is data sets that are very big and complex. ( ③ ) As information and communication technology develops, the amount of data we have is getting much greater than before. ( ④ ) For example, the photos you upload on your blog and the records of your purchases at online stores are all part of big data. ( ⑤ ) Simply collecting data, however, is not enough.
""")
item(4, "글의 흐름으로 보아, 다음 문장이 들어가기에 가장 적절한 곳은?  "
     "「This is mainly because almost everything that we do online leaves a trace.」",
     ["①", "②", "③", "④", "⑤"], 4,
     "데이터가 많아지는 「이유」 → 온라인 활동이 흔적을 남긴다 → For example 사진·구매 기록(흔적의 예). ⑤ 에 넣으면 예시가 이유보다 먼저 온다.",
     "T9")

# 13 ── 분사구문 → 부사절 접속사 ──────────────────────────────
item(3, "다음 문장을 부사절로 바꿔 쓸 때 빈칸에 들어갈 말로 가장 적절한 것은?  "
     "「Not knowing the true value of the table, Rummins sold it for only thirty pounds.」 → "
     "____ Rummins didn't know the true value of the table, he sold it for only thirty pounds.",
     ["If", "Because", "Unless", "Although", "Until"], 2,
     "값을 몰랐기 「때문에」 싸게 팔았다 — 이유. Not -ing 는 부정 분사구문.",
     None, "분사구문의 의미 (이유)")

# 14 ── 7과 스포츠·범죄 개수 ───────────────────────────────────
mat("T10", "7과 본문 — Improving Performance in Sports · Crime Prevention", """
Are you a sports fan? Well, big data is improving the performance of players, making sports more exciting. A famous example is Germany's national soccer team. The team built a database by collecting and analyzing a huge amount of data on players. For example, the data included information about how much each player ran and how long he had the ball. With the help of this database, Germany's national soccer team was able to improve its performance and win the 2014 World Cup.
Thanks to big data, police can now predict crime before it happens. Through the analysis of big data about the type, time and place of crime, police can make a map of crime hot spots. This map identifies when and where crime is most likely to happen. Police can prevent further crime by focusing on the areas and the times this map predicts.
""")
mat("T11", "〈보기〉", """
(a) Big data makes sports more exciting by improving players' performance.
(b) Germany's team began to analyze data only after the 2014 World Cup was over.
(c) The German team's data showed how far each player ran.
(d) A map of crime hot spots shows the places where crime has never happened.
(e) Police can use big data to predict crime before it happens.
(f) The crime map is based on the analysis of the type, time, and place of crime.
""")
item(5, "윗글 [T10]의 내용과 일치하는 것을 〈보기〉에서 모두 고른 것의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 3,
     "일치 (a)(c)(e)(f). (b) 데이터베이스 덕분에 우승 — 순서가 반대 (d) 범죄가 「가장 일어날 것 같은」 곳.",
     "T11")

# 15 ── 분사구문 → 부사절 ──────────────────────────────────────
item(4, "다음 중 분사구문을 부사절로 바르게 바꾼 것은?",
     ["Turning to the right, you'll find the station. → If you will turn to the right, …",
      "Not feeling well, I took a rest. → Because I felt well, …",
      "Written in English, the book is hard for me. → Because it wrote in English, …",
      "Walking down the street, I met an old friend. → While I was walking down the street, …",
      "Being rich, he couldn't buy happiness. → Because he was rich, …"], 4,
     "① 조건절은 현재시제 → If you turn ② 부정 → didn't feel well ③ 수동 → it is written ⑤ 부자였지만 → Although.",
     None, "분사구문의 의미 · 부정 · 수동")

# 16 ── Fly Away Home (2)(3) ───────────────────────────────────
mat("T12", "외부지문 — Fly Away Home (2) · (3)", """
(2) Once we saw a woman pushing a metal cart full of stuff. She wore a long, dirty coat and she lay down across a row of seats in front of Continental Gate 6. The cart, the dirty coat, the lying down were all noticeable. Security moved her out real fast.
(3) Everything in the airport is on the move — passengers, pilots, flight attendants, cleaners with their brooms. Jets roar in, close to the windows. Other jets roar out. Luggage bounces down chutes, escalators glide up and down, disappearing under the floors. Everyone's going somewhere except Dad and me. We stay.
""")
item(3, "윗글 (2)의 여자 이야기가 보여 주는 것으로 가장 적절한 것은?",
     ["공항에서 눈에 띄는 행동을 하면 쫓겨난다는 것",
      "공항 보안 요원들이 노숙인에게 친절하다는 것",
      "공항에서는 누구나 원하는 곳에서 잘 수 있다는 것",
      "짐을 많이 가진 사람일수록 공항에서 안전하다는 것",
      "Andrew 가 그 여자와 친구가 되고 싶어 한다는 것"], 1,
     "noticeable → Security moved her out real fast. 「눈에 띄지 말라」는 규칙의 이유.",
     "T12")

# 17 ── Fly Away Home (5)(6) ───────────────────────────────────
mat("T13", "외부지문 — Fly Away Home (5) · (6)", """
(5) The airport's busy and noisy even at night. Dad and I sleep anyway. When it gets quiet, between two and four A.M., we wake up. "Dead time," Dad says. "Almost no flights coming in or going out." At dead time there aren't many people around, so we're extra careful. In the mornings Dad and I wash up in one of the bathrooms, and he shaves. The bathrooms are extra crowded, no matter how early. And that's the way we like it.
(6) On the weekends Dad takes the bus to work. He's a janitor in an office in the city. The bus fare's a dollar each way. On those days Mrs. Medina looks out for me. The Medinas live in the airport, too — Grandma, Mrs. Medina, and Denny, who's my friend. He and I collect rented luggage carts that people have left outside and return them for fifty cents each. If the crowds are big and safe, we offer to carry bags. Sometimes passengers don't tip. Then Denny whispers, "Stingy!" But he doesn't whisper too loud. The Medinas understand that it's dangerous to be noticed.
""")
item(4, "윗글의 내용과 일치하지 않는 것은?",
     ["Andrew and his dad wake up at dead time, when few flights come in or go out.",
      "Andrew and his dad prefer to wash up when the bathrooms are crowded.",
      "Andrew's dad works as a janitor in the city on weekends.",
      "Andrew and Denny get fifty cents for each luggage cart they return.",
      "Denny loudly complains to passengers who don't give them tips."], 5,
     "doesn't whisper too loud — 들리지 않게 작게 말한다. 눈에 띄면 위험하니까.",
     "T13")

# 18 ── 학교 영영풀이 어휘 (Helping Each Other) ───────────────
mat("T14", "어휘", """
When people (A)[cooperate / compete], problems are solved more quickly, and everyone feels included and valued. Helping each other also teaches important values such as (B)[empathy / apathy], the ability to understand and share the feelings of another person. Communities where people work together are stronger and more (C)[resilient / vulnerable], so they recover quickly after difficulties.
""")
item(3, "(A), (B), (C)의 각 네모 안에서 문맥에 맞는 낱말로 가장 적절한 것은?",
     ["compete – empathy – resilient", "cooperate – empathy – resilient",
      "cooperate – apathy – vulnerable", "compete – apathy – resilient",
      "cooperate – empathy – vulnerable"], 2,
     "(A) 함께 일하다 (B) 뒤에 풀이(다른 사람의 감정을 이해·공유) = empathy, apathy 는 무관심 (C) 빨리 회복한다 = resilient.",
     "T14", "학교 영영풀이 (community 세트)")

# 19 ── Helping Each Other 요약 ─────────────────────────────────
mat("T15", "외부지문 — Helping Each Other Makes Society Stronger", """
In every community, people rely on one another in both small and big ways. Working together and helping others is not only kind but also essential for a healthy society. When neighbors share their time, skills, or resources, they make life easier and safer for everyone.
For example, after a big storm, some people clear fallen trees from the streets, while others deliver food and blankets to families who cannot leave their homes. In schools, students help classmates who are struggling with homework or share books and supplies. In hospitals, volunteers assist nurses and doctors by bringing water, guiding visitors, and comforting patients. Even children can help by picking up trash in parks or planting trees in their neighborhoods. Every action, no matter how small, matters.
""")
item(3, "윗글의 내용을 한 문장으로 요약할 때, 빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?  "
     "「Whether big or (A)____, the ways people help one another make life (B)____ for the whole community.」",
     ["small – easier and safer", "small – harder and lonelier", "selfish – easier and safer",
      "professional – more expensive", "large – more dangerous"], 1,
     "both small and big ways · make life easier and safer for everyone.",
     "T15")

# 20 ── what 개수 ───────────────────────────────────────────────
mat("T16", "〈보기〉", """
(a) ______ he wants is only the legs.
(b) The table ______ he bought was a reproduction.
(c) I can't believe ______ I heard yesterday.
(d) This is the book ______ the store recommended for me.
(e) The bookstore knew ______ you liked.
(f) Big data is data sets ______ are very big and complex.
(g) ______ surprised me most was the price of the table.
(h) Do you know the man ______ is standing next to Bert?
""")
item(5, "〈보기〉의 빈칸 중 what이 들어가야 하는 것의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 3,
     "what: (a)(c)(e)(g) — 선행사가 없고 빈칸 뒤가 불완전. (b)(d)(f) 선행사 있음 → that/which (h) who/that.",
     "T16", "관계대명사 what vs that")

# 21 ── 대화 개수 ───────────────────────────────────────────────
mat("T17", "〈보기〉", """
(a) A: Can you tell me how to use this application?
    B: Sure. First, log in to the application.
(b) A: How often do you exercise?
    B: For two hours.
(c) A: I didn't get a role in the school play.
    B: I'm sorry to hear that. I'm sure you can get a role next time.
(d) A: Do you know how to make tea?
    B: Sure. First, put a tea bag in a cup.
(e) A: I really appreciate your help.
    B: You're welcome.
(f) A: I suggest you use a lighter ball.
    B: OK. I'll look for a heavier one, then.
(g) A: You don't look so good. What's the matter?
    B: I have the flu.
(h) A: Congratulations on winning the gold medal.
    B: Thanks. I'm very disappointed.
""")
item(5, "〈보기〉의 대화 중 자연스러운 것의 개수는?",
     ["1개", "2개", "3개", "4개", "5개"], 5,
     "자연스러운 것 (a)(c)(d)(e)(g). (b) 빈도를 물었는데 시간의 길이 (f) 가벼운 공을 권했는데 무거운 공 (h) 축하에 실망.",
     "T17", "방법 묻기 · 빈도 · 유감 · 감사 · 제안 · 축하")

# ── 서술형 ──────────────────────────────────────────────────
essay("다음 우리말을 <조건>에 맞게 영작할 때, 3번째·9번째·10번째 단어를 쓰시오.",
      "트랙 옆에서 타이어를 교체하고 있는 사람들은 피트 크루라고 불린다.",
      ["현재분사가 명사를 뒤에서 꾸미게 할 것 (관계대명사를 쓰지 말 것)",
       "수동태를 사용할 것",
       "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것",
       "답안에는 지정된 순서의 단어만 쓸 것"],
      ["people", "change", "the tires", "beside", "the track", "call", "a pit crew"], "13 단어",
      "현재분사 후치수식 · 수동태 (5과)",
      "3번째: changing\n9번째: are\n10번째: called\n"
      "(완성 문장: The people changing the tires beside the track are called a pit crew.)",
      "people 을 뒤에서 꾸미는 changing — that are changing 이면 단어 수가 어긋난다. 주어가 복수 → are called.",
      ["3번째 단어: ________", "9번째 단어: ________", "10번째 단어: ________"])

essay("다음 글에서 어법상 틀린 부분 2곳을 찾아 바르게 고쳐 쓰시오.",
      "When Mr. Boggis came back with his car, Bert already cut off the legs of the table.\n"
      "Rummins didn't charge him for it because he thought it was a favor.\n"
      "Mr. Boggis was so shocked that he couldn't say anything. He realized that he has made a big mistake.",
      ["틀린 곳은 정확히 2곳이다",
       "한 칸에 「틀린 말 → 고친 말」 로 쓸 것"],
      [], "", "과거완료 (6과)",
      "(1) already cut → had already cut\n(2) has made → had made",
      "(1) 돌아온 시점(came back)보다 먼저 끝난 일 → 과거완료 (2) 깨달은 시점(realized)보다 먼저 저지른 실수 → 과거완료.",
      ["(1) ____________ → ____________", "(2) ____________ → ____________"])

essay("다음 밑줄 친 부분을 <조건>에 맞게 분사구문으로 바꿔 쓰시오.",
      "(1) Because police analyze crime data, they can make a map of crime hot spots.\n"
      "→ ______________, police can make a map of crime hot spots.\n"
      "(2) If it is used wisely, big data can help people avoid heavy traffic.\n"
      "→ ______________, big data can help people avoid heavy traffic.\n"
      "(3) As it was raining heavily, the soccer game was canceled.\n"
      "→ ______________, the soccer game was canceled.",
      ["Being 은 생략할 것",
       "주절과 주어가 다르면 주어를 남길 것",
       "(1) 은 3단어, (2) 는 2단어, (3) 은 3단어로 쓸 것"],
      [], "", "분사구문 (7과)",
      "(1) Analyzing crime data\n(2) Used wisely\n(3) It raining heavily",
      "(1) 주어가 같다 → 접속사·주어 생략 (2) 수동 → (Being) Used (3) 날씨 it ≠ the soccer game → 주어 It 을 남긴 독립분사구문.",
      ["(1) ____________", "(2) ____________", "(3) ____________"])

mat("T18", "외부지문 — Fly Away Home (7) · (8)", """
(7) When Dad comes home from work, he buys hamburgers for us and the Medinas. That's to pay them for watching out for me. If Denny and I've had a good day, we treat for pie. But I've stopped doing that. I save my money in my shoe. "Will we ever have our own apartment again?" I ask Dad. I'd like it to be the way it was, before Mom died. "Maybe we will," he says. "If I can find more work. If we can save some money."
(8) But I know he's trying all the time to find us a place. He takes newspapers from the trash baskets and makes pencil circles around letters and numbers. Then he goes to the phones. When he comes back he looks sad. Sad and angry. I know he's been calling about an apartment. I know the rents are too high for us. "I'm saving money, too," I tell him, and I lift one foot and point to my shoe. Dad smiles. "Atta boy!"
""")
essay("윗글을 읽고, 질문에 대한 답을 완성하시오.",
      "Q: Why does Andrew's dad buy hamburgers for the Medinas?\n"
      "A: To pay them for (1) ______ ______ ______ Andrew.\n"
      "Q: Why does Andrew's dad look sad after calling about an apartment?\n"
      "A: Because the rents are (2) ______ ______ ______ ______.",
      ["본문의 표현을 사용할 것",
       "(1) 은 3단어, (2) 는 4단어로 쓸 것",
       "(2) 는 Andrew 와 아빠를 가리키는 대명사를 넣을 것"],
      [], "", "내용 확인 (외부지문)",
      "(1) watching out for\n(2) too high for them",
      "(1) That's to pay them for watching out for me — 전치사 for 뒤 동명사 (2) the rents are too high for us → 질문은 3인칭이므로 them.",
      ["(1) ____________", "(2) ____________"], mid="T18")

finish(2)
