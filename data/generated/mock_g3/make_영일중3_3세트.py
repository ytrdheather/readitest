# -*- coding: utf-8 -*-
"""
영일중3 5·6·7과 동형 3세트 (고난도) — 2026-11-08 원장 「다양한 문제 경험하게 두 세트 더」.

1·2세트와 지문 구간·유형을 갈랐다:
  5과 도입 + 셰르파(요지 · 언급 안 된 것) / 6과 탁자 발견 장면 / 7과 질병 예측 · 범죄 · 결말 /
  Fly Away Home (4)(9)(10) / Helping Each Other 제목 · 문장 삽입 / 학교 영영풀이 7과 세트.
  python data/generated/mock_g3/make_영일중3_3세트.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import mat, item, essay, finish      # noqa: E402

# 1 ── 영영풀이 ────────────────────────────────────────────────
mat("T1", "영영풀이", """
• to examine something carefully
• something that shows you may have a particular illness
• to realize who someone is or what something is
• to say that something is going to happen
""")
item(3, "다음 영영풀이 중 어느 것에도 해당하지 않는 단어는?",
     ["analyze", "influence", "symptom", "identify", "predict"], 2,
     "influence = to change or affect something (7과 영영풀이 13번). 나머지는 차례로 analyze · symptom · identify · predict.",
     "T1", "7과 영영풀이")

# 2 ── (가)→(나) 바꿔 쓰기 ─────────────────────────────────────
mat("T2", "7과 본문 바꿔 쓰기", """
(가) Big data is data sets that are very big and complex. As information and communication technology develops, the amount of data we have is getting much greater than before.
(나) Big data refers to ⓐenormous and ⓑcomplicated sets of data. ⓒAlong with the development of information and communication technology, the ⓓquantity of data we possess is ⓔdecreasing far more rapidly than before.
""")
item(5, "(가)를 (나)로 바꾸어 쓸 때, ⓐ~ⓔ 중 의미가 어색한 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 5,
     "getting much greater(훨씬 많아지고 있다)를 바꾼 자리 → increasing. ⓒ As ~ develops(~함에 따라) = Along with the development of.",
     "T2", "접속사 as (~함에 따라)")

# 3·4 ── 5과 도입 + 셰르파 ─────────────────────────────────────
mat("T3", "5과 본문 — Hidden People in Sports · Sherpas", """
In sports, only the players get a trophy or medal, but they don't win on their own. There are people who help the players. These people are often hidden and don't get attention. However, they are as important as the players.
The word Sherpa comes from the Sherpa tribe, which lives in the eastern part of Nepal. Sherpas have good climbing skills and know their way around the mountains well. They also have little difficulty breathing high up in the mountains. Therefore, mountain climbers started to hire Sherpas to help them climb Mount Everest. Sherpas lead mountain climbers to the top of the mountain. They support climbers in many ways. For example, they put up tents and carry climbers' bags. Sherpas are often called the invisible people of Mount Everest because people often see a picture of only the climbers at the top of the mountain.
""")
item(3, "윗글에서 셰르파에 관해 언급되지 않은 것은?",
     ["이름의 유래", "사는 지역", "등반가들에게 받는 보수", "높은 곳에서의 호흡", "등반가들을 돕는 방법"], 3,
     "유래(Sherpa tribe) · 지역(네팔 동부) · 호흡(little difficulty breathing) · 돕는 방법(텐트 · 가방)은 있고 보수는 없다.",
     "T3")
item(4, "윗글의 요지로 가장 적절한 것은?",
     ["스포츠의 영광은 결국 실력 있는 선수에게 돌아가야 한다.",
      "눈에 띄지 않게 선수를 돕는 사람들도 선수만큼 중요하다.",
      "셰르파의 등반 기술은 전문 등반가보다 뛰어나다.",
      "등반가는 셰르파 없이 에베레스트에 오를 수 없다.",
      "사진에는 늘 가장 중요한 사람이 찍힌다."], 2,
     "they are as important as the players — 셰르파는 그 예. ③④ 는 본문보다 지나치게 나간 말.",
     "T3")

# 5 ── 5과 어법 (A)(B)(C) ─────────────────────────────────────
mat("T4", "어법", """
Sherpas have little difficulty (A)[to breathe / breathing] high up in the mountains. Therefore, mountain climbers started (B)[to hiring / hiring] Sherpas to help them climb Mount Everest. In a marathon, each pacer (C)[run / runs] at a different speed and finishes the race in a different time.
""")
item(3, "(A), (B), (C)의 각 네모 안에서 어법에 맞는 표현으로 가장 적절한 것은?",
     ["to breathe – to hiring – run", "to breathe – hiring – runs", "breathing – to hiring – run",
      "breathing – hiring – runs", "breathing – hiring – run"], 4,
     "(A) have difficulty -ing (B) start -ing / to + 동사원형 — to hiring 은 안 된다 (C) each + 단수 명사 + 단수 동사.",
     "T4", "have difficulty -ing · each 수일치")

# 6 ── 현재분사 vs 동명사 ──────────────────────────────────────
mat("T5", "〈보기〉", """
(a) Pacers have flags showing their finish time.
(b) Changing the tires is especially important.
(c) Look at the sleeping baby on the sofa.
(d) My hobby is collecting old coins.
(e) He bought a new pair of running shoes.
(f) The girl waiting at the bus stop is my sister.
(g) Simply collecting data is not enough.
(h) Big data is improving the performance of players.
""")
item(5, "〈보기〉의 각 문장에 쓰인 -ing 형태 가운데 현재분사인 것의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 3,
     "현재분사 (a) 명사 수식 (c) 자고 있는 (f) 기다리고 있는 (h) 진행형. 동명사 (b)(g) 주어 (d) 보어 (e) 용도(달리기용 신발).",
     "T5", "현재분사 vs 동명사")

# 7 ── 제안 표현 ────────────────────────────────────────────────
item(3, "다음 문장과 바꿔 쓸 수 없는 것은?  「I suggest you wear running shoes.」",
     ["Why don't you wear running shoes?", "How about wearing running shoes?",
      "You'd better wear running shoes.", "I think you should wear running shoes.",
      "I'm sure you wore running shoes."], 5,
     "⑤ 는 확신 · 과거 사실. 제안이 아니다.",
     None, "제안하기")

# 8·9 ── 6과 탁자 발견 ─────────────────────────────────────────
mat("T6", "6과 본문 — One Lucky Sunday", """
"I buy old furniture. Do you have any?" asked Mr. Boggis.
"No, I don't," said Rummins.
(A) Mr. Boggis first went to the kitchen, and there was nothing. He then moved to the living room. And there it was! A table which was a priceless piece of eighteenth-century English furniture.
(B) "Can I just take a look?" asked Mr. Boggis. "Sure. Please come in," said Rummins.
(C) He was so excited that he almost fell over. "What's wrong?" Bert asked. "Oh, nothing. Nothing at all," Mr. Boggis lied. He then said with a straight face, "This table is a reproduction. It's worth only a few pounds."
""")
item(4, "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?",
     ["(B) - (A) - (C)", "(A) - (C) - (B)", "(B) - (C) - (A)", "(C) - (A) - (B)", "(C) - (B) - (A)"], 1,
     "둘러봐도 되냐(B) → 부엌 · 거실, 탁자 발견(A) → 너무 흥분해 넘어질 뻔, 시치미(C).",
     "T6")
item(3, "윗글에서 Mr. Boggis가 탁자를 복제품이라고 말한 의도로 가장 적절한 것은?",
     ["탁자를 수리해 주겠다고 제안하려고",
      "Rummins 에게 탁자의 진짜 가치를 알려 주려고",
      "자기 집 탁자가 더 귀하다고 자랑하려고",
      "탁자의 가치를 낮춰 말해 싼값에 사려고",
      "Bert 의 질문을 피해 집을 빨리 나가려고"], 4,
     "priceless 한 진품을 보고 흥분했으면서 with a straight face 로 「몇 파운드짜리」라고 거짓말 — 싸게 사려는 수작.",
     "T6")

# 10 ── 문장 전환 있는 대로 ────────────────────────────────────
mat("T7", "〈보기〉", """
(a) He was so excited that he almost fell over.
   = He was too excited to almost fall over.
(b) Mr. Boggis was so shocked that he couldn't say anything.
   = Mr. Boggis was too shocked to say anything.
(c) What he wants is only the legs.
   = The thing which he wants is only the legs.
(d) The table was what every dealer dreamed of.
   = The table was that every dealer dreamed of.
(e) On his way to the car, he couldn't help smiling.
   = On his way to the car, he couldn't but smile.
""")
item(5, "〈보기〉에서 두 문장의 의미가 같고 어법상 옳은 것만을 있는 대로 고른 것은?",
     ["(b), (c)", "(b), (c), (e)", "(a), (c), (e)", "(b), (d), (e)", "(a), (b), (c), (e)"], 2,
     "(a) 「넘어질 뻔했다」는 결과를 too ~ to 로 바꾸면 뜻이 깨진다 (b) so ~ that ... can't = too ~ to (c) what = the thing which (d) 선행사 없는 자리에 that 은 안 된다 (e) cannot help -ing = cannot but + 동사원형.",
     "T7", "관계대명사 what · so ~ that · cannot help -ing")

# 11 ── 6과 대화 ────────────────────────────────────────────────
mat("T8", "6과 대화", """
B: Mina, is anything wrong?
G: Well, I lost my smartphone. I'm upset.
B: Oh, I'm so sorry to hear that. Do you remember when you used it last?
G: Well, I remember taking it out of my bag at the snack shop.
B: Then, let's go back to the snack shop to look for it.
""")
item(3, "위 대화의 내용과 일치하지 않는 것은?",
     ["Mina is upset because she lost her smartphone.",
      "The boy expresses sympathy for Mina.",
      "Mina remembers taking her smartphone out of her bag.",
      "Mina last used her smartphone at the library.",
      "They are going to look for the smartphone together."], 4,
     "마지막으로 꺼낸 곳은 snack shop.",
     "T8", "유감 표현 · remember -ing")

# 12 ── 7과 질병 예측 빈칸 ─────────────────────────────────────
mat("T9", "7과 본문 — Disease Forecast · Crime Prevention", """
Did you know that health professionals can now forecast a disease just as weather experts forecast the weather? This is possible thanks to big data. For example, when the flu season comes, people will buy more flu medicine. They will also search online about flu symptoms more. If this kind of data is analyzed wisely, ________(A)________.
Thanks to big data, police can now predict crime before it happens. Through the analysis of big data about the type, time and place of crime, police can make a map of crime hot spots. This map identifies when and where crime is most likely to happen. Police can prevent further crime by focusing on the areas and the times this map predicts.
""")
item(3, "윗글의 빈칸 (A)에 들어갈 말로 가장 적절한 것은?",
     ["people will stop buying flu medicine",
      "weather experts can forecast the weather better",
      "the spread of the flu can be predicted",
      "the flu season will never come again",
      "online searches about flu will disappear"], 3,
     "약 구매 · 증상 검색 데이터를 분석하면 → 독감 확산을 예측할 수 있다 (질병 예보의 예).",
     "T9")

# 13 ── 접속사 as 의미 다른 것 ─────────────────────────────────
item(3, "다음 중 as의 의미가 나머지 넷과 다른 것은?",
     ["As I was getting off the bus, I saw Peter.",
      "A message arrived as she was leaving.",
      "I called my friend as I went to school.",
      "As it was late at night, we went back home.",
      "He fell asleep as he was watching TV."], 4,
     "④ 는 이유(~ 때문에). 나머지는 때 · 동시(~할 때, ~하면서).",
     None, "접속사 as")

# 14 ── 7과 문장 어법 개수 ─────────────────────────────────────
mat("T10", "〈보기〉", """
(a) Big data has already changed the world greatly.
(b) Nobody know for sure where the big data industry will go.
(c) Experts agree that big data will play a more and more important role in our lives.
(d) Police can prevent further crime by focus on the areas this map predicts.
(e) This map identifies when and where crime is most likely to happen.
(f) Big data helps companies understanding their customers' needs better.
(g) These results then can be used to make decisions or to predict the future.
(h) Many of the books looked interestingly to you.
""")
item(5, "〈보기〉에서 어법상 옳은 문장의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 3,
     "옳은 것 (a)(c)(e)(g). (b) Nobody 단수 → knows (d) 전치사 by + 동명사 → focusing (f) help + 목적어 + (to) 동사원형 → understand (h) look + 형용사 → interesting.",
     "T10", "수일치 · by -ing · help O (to) V · 감각동사")

# 15 ── 분사구문 어법 ──────────────────────────────────────────
item(4, "다음 중 어법상 옳은 문장은?",
     ["Knowing not the value, Rummins sold the table cheaply.",
      "Writing in English, the book was hard to read.",
      "Analyzing wisely, the data can predict the spread of the flu.",
      "Being late at night, we went back home.",
      "Not knowing the value of the table, Rummins sold it cheaply."], 5,
     "① not 은 분사 앞 ② 책은 「쓰인」 것 → Written ③ 데이터는 「분석되는」 것 → Analyzed ④ 주어 it 이 달라 → It being late.",
     None, "분사구문 (부정 · 수동 · 독립)")

# 16 ── Fly Away Home (4) ──────────────────────────────────────
mat("T11", "외부지문 — Fly Away Home (4)", """
Once a little brown bird got into the main terminal and couldn't get out. It fluttered in the high, hollow spaces. It threw itself at the glass, fell panting on the floor, flew to a tall, metal girder, and perched there, exhausted. "Don't stop trying," I told it silently. "Don't! You can get out!" For days the bird flew around, dragging one wing. And then it found the instant when a sliding door was open and slipped through. I watched it rise. Its wing seemed OK. "Fly, bird," I whispered. "Fly away home!" Though I couldn't hear it, I knew it was singing. Nothing made me as happy as that bird.
""")
item(3, "윗글의 마지막 문장 \"Nothing made me as happy as that bird.\"와 의미가 다른 것은?",
     ["That bird made me happier than anything else.",
      "Nothing made me happier than that bird.",
      "That bird made me the happiest of all.",
      "Nothing made me so happy as that bird.",
      "That bird made me as happy as other things did."], 5,
     "부정주어 + as 원급 as = 최상급 뜻. ⑤ 는 「다른 것들만큼」 — 똑같았다는 뜻이 되어 최상급이 사라진다.",
     "T11", "원급으로 최상급 표현")

# 17 ── Fly Away Home (9)(10) ──────────────────────────────────
mat("T12", "외부지문 — Fly Away Home (9) · (10)", """
(9) "If we get a place, you and your dad can come live with us," Denny says. "And if we get a place, you and your mom and your grandma can come live with us," I say. "Yeah!" We shake on it. That's going to be so great! After next summer, Dad says, I have to start school. "How?" I ask. "I don't know. But it's important. We'll work it out." Denny's mom says he can wait for a while. But Dad says I can't wait.
(10) Sometimes I watch people meeting people. "We missed you." "It's so good to be home." Sometimes I get mad, and I want to run at them and push them and shout, "Why do you have homes when we don't? What makes you so special?" That would get us noticed, all right.
""")
item(5, "윗글의 내용과 일치하는 것은?",
     ["Andrew and Denny promise to share a home with each other's family if they get one.",
      "Andrew's dad says Andrew can wait a few more years before starting school.",
      "Denny's mom insists that Denny start school right after next summer.",
      "Andrew feels nothing but happiness when he watches people meeting each other.",
      "Andrew actually pushed people who had homes and shouted at them."], 1,
     "We shake on it — 집이 생기면 서로 데려와 살기로 약속. ② can't wait ③ he can wait for a while ④ 화가 나기도 한다 ⑤ want to — 실제로 하지는 않았다(That would get us noticed).",
     "T12")

# 18·19 ── Helping Each Other ──────────────────────────────────
mat("T13", "외부지문", """
In every community, people rely on one another in both small and big ways. Working together and helping others is not only kind but also essential for a healthy society. When neighbors share their time, skills, or resources, they make life easier and safer for everyone.
( ① ) For example, after a big storm, some people clear fallen trees from the streets, while others deliver food and blankets to families who cannot leave their homes. In schools, students help classmates who are struggling with homework or share books and supplies. ( ② ) In hospitals, volunteers assist nurses and doctors by bringing water, guiding visitors, and comforting patients. Even children can help by picking up trash in parks or planting trees in their neighborhoods. ( ③ )
Helping each other also teaches important values such as empathy, responsibility, and respect. ( ④ ) When people cooperate, problems are solved more quickly, and everyone feels included and valued. ( ⑤ ) Communities where people work together are stronger, happier, and more resilient. In the end, living together means understanding that we are all connected.
""")
item(3, "윗글의 제목으로 가장 적절한 것은?",
     ["Why Professionals Should Solve Community Problems",
      "Small Acts, Strong Communities",
      "The Dangers of Depending on Others",
      "How Volunteers Replace Doctors in Hospitals",
      "Children Are Too Young to Help Their Neighbors"], 2,
     "크고 작은 도움이 공동체를 더 강하고 회복력 있게 만든다.",
     "T13")
item(4, "글의 흐름으로 보아, 다음 문장이 들어가기에 가장 적절한 곳은?  "
     "「Every action, no matter how small, matters.」",
     ["①", "②", "③", "④", "⑤"], 3,
     "폭풍 · 학교 · 병원 · 「아이들조차」 → 아무리 작아도 모든 행동이 중요하다로 예시를 맺는다. 다음 단락은 「가치」로 넘어간다.",
     "T13")

# 20 ── what / that / how much 조합 ────────────────────────────
mat("T14", "어법", """
The table (A)______ Mr. Boggis found in the living room was a priceless piece. "(B)______ he wants is only the legs," said Rummins. But Rummins didn't know (C)______ the table was really worth. Bert did (D)______ his father told him to do.
""")
item(5, "(A)~(D)의 빈칸에 들어갈 말로 바르게 짝지어진 것은?",
     ["that – What – how much – what", "what – That – how much – which",
      "which – What – what – that", "that – That – how much – what",
      "what – What – how many – that"], 1,
     "(A) 선행사 table → that/which (B) 선행사 없음 → What (C) 값 → how much (D) did 의 목적어, 선행사 없음 → what. ③ 은 (D) that 이 틀렸다.",
     "T14", "관계대명사 what vs that · 간접의문문")

# 21 ── 7과 대화 배열 ──────────────────────────────────────────
mat("T15", "7과 대화", """
B: Excuse me. Can you tell me how to use this machine?
(A) Then what?
(B) Thank you. I really appreciate your help.
(C) Sure. First, put the paper on the copy machine. Then choose the paper size and the number of copies.
(D) Press the START button.
""")
item(4, "주어진 말에 이어질 대화의 순서로 가장 적절한 것은?",
     ["(C) - (A) - (D) - (B)", "(C) - (D) - (A) - (B)", "(A) - (C) - (D) - (B)",
      "(D) - (A) - (C) - (B)", "(C) - (B) - (A) - (D)"], 1,
     "방법 질문 → 첫째·그다음(C) → 그다음엔?(A) → 시작 버튼(D) → 감사(B).",
     "T15", "방법 묻기 · 감사하기")

# ── 서술형 ──────────────────────────────────────────────────
essay("다음 우리말을 <조건>에 맞게 영작할 때, 4번째·6번째·10번째 단어를 쓰시오.",
      "이 탁자는 저 탁자보다 세 배 더 비싸다.",
      ["「배수사 + as + 원급 + as」 를 사용할 것 (비교급을 쓰지 말 것)",
       "두 번째 「탁자」 는 대명사 one 으로 쓸 것",
       "답안에는 지정된 순서의 단어만 쓸 것"],
      ["table", "three", "expensive"], "10 단어",
      "배수사 + as 원급 as (5과)",
      "4번째: three\n6번째: as\n10번째: one\n"
      "(완성 문장: This table is three times as expensive as that one.)",
      "배수사(three times)는 as 앞. times 를 빼먹으면 6번째가 expensive 가 된다.",
      ["4번째 단어: ________", "6번째 단어: ________", "10번째 단어: ________"])

essay("다음 우리말을 <조건>에 맞게 영작할 때, 1번째·5번째·8번째 단어를 쓰시오.",
      "Boggis 씨가 얻은 것은 다리가 없는 탁자였다.",
      ["관계대명사 what 을 사용할 것 (the thing 을 쓰지 말 것)",
       "Mr. Boggis 는 두 단어로 센다",
       "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것",
       "답안에는 지정된 순서의 단어만 쓸 것"],
      ["get", "table", "without", "legs"], "9 단어",
      "관계대명사 what (6과)",
      "1번째: What\n5번째: was\n8번째: without\n"
      "(완성 문장: What Mr. Boggis got was a table without legs.)",
      "What Mr. Boggis got 이 주어(단수) → was. 관사 a 가 6번째라 without 은 8번째.",
      ["1번째 단어: ________", "5번째 단어: ________", "8번째 단어: ________"])

essay("다음 글에서 어법상 틀린 부분 2곳을 찾아 바르게 고쳐 쓰시오.",
      "Sherpas, who knows their way around the mountains well, help climbers reach the top.\n"
      "People often see pictures of climbers stood at the top of the mountain, "
      "but they rarely see the Sherpas behind them.",
      ["틀린 곳은 정확히 2곳이다",
       "한 칸에 「틀린 말 → 고친 말」 로 쓸 것"],
      [], "", "관계대명사 수일치 · 현재분사 후치수식 (5과)",
      "(1) knows → know\n(2) stood → standing",
      "(1) 선행사 Sherpas 가 복수 → who know (2) 정상에 「서 있는」 등반가 → 능동 · 진행의 현재분사 standing.",
      ["(1) ____________ → ____________", "(2) ____________ → ____________"])

essay("윗글 [T9], [T11]을 읽고, 질문에 대한 답을 완성하시오.",
      "Q: How can police prevent further crime?\n"
      "A: By (1) ______ ______ the areas and the times the crime map predicts.\n"
      "Q: What did Andrew tell the bird silently when it was exhausted?\n"
      "A: He told it, \"(2) ______ ______ ______.\"",
      ["본문의 표현을 그대로 사용할 것",
       "(1) 은 2단어, (2) 는 3단어로 쓸 것"],
      [], "", "내용 확인 · by -ing",
      "(1) focusing on\n(2) Don't stop trying",
      "(1) prevent further crime by focusing on ~ (2) \"Don't stop trying,\" I told it silently.",
      ["(1) ____________", "(2) ____________"])

finish(3)
