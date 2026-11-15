# -*- coding: utf-8 -*-
"""
영일중3 5·6·7과 동형 모의고사 1세트 (고난도) — 손으로 출제 (2026-11-08).

중3 은 DB 대상이 아니라(§5.5.3) make_mock_exam 생성기를 쓰지 않고 문항을 여기 직접 적는다.
그릇은 data/stage0/comparisons/중3_영일_기말_그릇.md — 선택형 24문항 · 서술형 없음 · 100점.
5점 문항은 영일 기출 꼴(개수 · 있는 대로 · 바꿔 쓴 말의 어색함)로만 낸다.

  python data/generated/mock_g3/make_영일중3_1세트.py          # JSON + 시험지·정답지 PDF

출력은 build_mock_pdf.py 와 같은 길(render_mock_exam.build → to_pdf → stamp_file)을 거친다.
mock/ 가 아니라 mock_g3/ 에 두는 이유: build_mock_pdf 가 mock/*.json 을 전부 중1·중2 로 읽는다.
"""
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TITLE = "영일중3 5·6·7과 동형모의고사 1세트"

M = []          # materials
I = []          # items


def mat(mid, title, text):
    M.append({"id": mid, "title": title, "text": text.strip()})


def item(no, pts, stem, opts, ans, why, mid=None, gp=""):
    assert len(opts) == 5 and 1 <= ans <= 5
    I.append({"no": no, "points": pts, "stem_ko": stem, "options": opts, "answer": ans,
              "why_ko": why, "material_id": mid, "grammar_point": gp})


# ── 1 영영풀이 ───────────────────────────────────────────────
mat("T1", "영영풀이", """
• to pay someone to work for you
• the aim or result that you try to achieve
• to pay attention to someone or something, so that you know where they are or what is happening to them
• to use something a lot so that it no longer works or can no longer be used
""")
item(1, 3, "다음 영영풀이 중 어느 것에도 해당하지 않는 단어는?",
     ["rent", "hire", "target", "keep track of", "wear out"], 1,
     "rent 는 「to pay someone for the use of something」(7과). 「사람을 써서 돈을 주다」는 hire 다 — rent/hire 혼동 함정.",
     "T1", "5·7과 영영풀이")

# ── 2 (가)→(나) 바꿔 쓰기 ─────────────────────────────────────
mat("T2", "5과 본문 바꿔 쓰기", """
(가) In sports, only the players get a trophy or medal, but they don't win on their own. There are people who help the players. These people are often hidden and don't get attention. However, they are as important as the players.
(나) In sports, trophies and medals go ⓐexclusively to the players, but no player wins ⓑsingle-handedly. Behind every player, there are people ⓒassisting them. These people usually remain ⓓvisible and receive little attention. Nevertheless, they are ⓔno less important than the players.
""")
item(2, 5, "(가)를 (나)로 바꾸어 쓸 때, ⓐ~ⓔ 중 의미가 어색한 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 4,
     "hidden 을 바꾼 자리이므로 visible(보이는)이 아니라 invisible / unseen 이어야 한다. ⓔ no less important than = as important as.",
     "T2", "as 원급 as ↔ no less ~ than")

# ── 3·4 페이서·피트 크루 ───────────────────────────────────────
mat("T3", "5과 본문 변형 — Pacers · Pit Crews", """
Pacers in a Marathon
Pacers are experienced runners who run with other runners and lead them in a marathon. ( ① ) Their job is to help other runners manage their race better. ( ② ) There can be several pacers in one race, and each of them runs at a different speed and finishes in a different time. ( ③ ) With the help of these, runners can choose a pacer depending on their target finish time. ( ④ ) Since the pacer keeps track of the time, the runner can achieve his or her goal more easily. ( ⑤ ) In short, pacers run, but they don't run to win.
Pit Crews in Car Racing
During most car races, you may only see the car and the driver, but there is a team behind the driver called a pit crew. A pit is a place on the side of the race track where drivers stop several times during a race. The main job of the pit crew is to check the car and change the tires. A pit stop can be as short as 2 seconds, and there are as many as 20 members on a crew, so the crew has to work in perfect harmony.
""")
item(3, 4, "글의 흐름으로 보아, 다음 문장이 들어가기에 가장 적절한 곳은?  "
     "「That is why pacers usually have flags or balloons showing their finish time.」",
     ["①", "②", "③", "④", "⑤"], 3,
     "페이서마다 속도·완주 시간이 다르다 → 그래서 완주 시간을 나타내는 깃발·풍선을 든다 → With the help of these(깃발·풍선)로 이어진다. ④ 에 넣으면 these 가 가리킬 것이 없다.",
     "T3", "현재분사 후치수식 (showing)")
item(4, 4, "윗글의 내용과 일치하는 것은?",
     ["Pacers are usually beginners who try to win the race for their teams.",
      "Every pacer in a marathon runs at the same speed as the others.",
      "A runner following the four-hour pacer has to keep track of the time by himself or herself.",
      "Drivers stop at the pit only once, right before the end of the race.",
      "A pit crew may consist of up to twenty members."], 5,
     "as many as 20 members = 최대 20명. ① experienced runners · don't run to win ② different speed ③ 시간은 페이서가 파악 ④ several times.",
     "T3")

# ── 5 셰르파 어법 ─────────────────────────────────────────────
mat("T4", "5과 본문 — Sherpas", """
The word Sherpa comes from the Sherpa tribe, ⓐwhich lives in the eastern part of Nepal. Sherpas have good climbing skills and know their way around the mountains well. They also have little difficulty ⓑto breathe high up in the mountains. Therefore, mountain climbers started to hire Sherpas ⓒto help them climb Mount Everest. Sherpas lead climbers to the top and support them in many ways, such as putting up tents and ⓓcarrying climbers' bags. They are often called the invisible people of Mount Everest because people often see a picture of only the climbers ⓔstanding at the top of the mountain.
""")
item(5, 4, "윗글의 ⓐ~ⓔ 중 어법상 옳지 않은 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 2,
     "have (little) difficulty + -ing → breathing. ⓐ 계속적 용법, tribe 는 단수 ⓒ 형용사적 용법 to부정사 ⓓ putting 과 병렬 ⓔ climbers 를 꾸미는 현재분사.",
     "T4", "have difficulty -ing")

# ── 6 분사 개수 ───────────────────────────────────────────────
mat("T5", "〈보기〉", """
(A) Pacers usually have flags or balloons showed their finish time.
(B) The tires wear out easily in a race played at high speed.
(C) The man sat in the back is the owner of the antique table.
(D) Mr. Boggis looked at the table with a surprised face.
(E) People often see pictures of climbers standing at the top of Mount Everest.
(F) The police made a map showing crime hot spots.
(G) The data collecting by the team included information about each player.
(H) It was a disappointed result for the team.
""")
item(6, 5, "〈보기〉에서 분사의 쓰임이 어법상 옳은 문장의 개수는?",
     ["2개", "3개", "4개", "5개", "6개"], 3,
     "옳은 것 (B)(D)(E)(F). (A) showed→showing (C) sat→sitting (G) collecting→collected (수동) (H) disappointed→disappointing (결과가 실망을 준다).",
     "T5", "현재분사 vs 과거분사")

# ── 7 as 원급 as ─────────────────────────────────────────────
item(7, 4, "다음 중 두 문장의 의미가 서로 다른 것은?",
     ["Mike can't run as fast as Jason. / Jason can run faster than Mike.",
      "This table is not as old as that one. / That table is older than this one.",
      "The reproduction is not so valuable as the original. / The reproduction is less valuable than the original.",
      "Sora practices as hard as possible. / Sora practices as hard as she can.",
      "Your bag is not so heavy as mine. / My bag is less heavy than yours."], 5,
     "「네 가방이 내 것만큼 무겁지 않다」 = 내 가방이 더 무겁다. ⑤ 는 비교 대상을 뒤집어 반대 뜻이 됐다 → Your bag is less heavy than mine.",
     None, "not as[so] ~ as = less ~ than")

# ── 8 5과 대화 ───────────────────────────────────────────────
mat("T6", "5과 대화", """
W: Hello. May I help you?
B: Yes, I came to register for a soccer class.
W: I see. ①How often do you want to take classes?
B: ②I want to take classes twice a week. I'd like to take classes on weekends.
W: ③Then, I suggest that you take the Beginner 1 class. It meets on Mondays and Wednesdays.
B: ④That sounds good. ⑤Can I sign up for it now?
""")
item(8, 3, "대화의 흐름상 ①~⑤ 중 어색한 것은?",
     ["①", "②", "③", "④", "⑤"], 3,
     "주말 수업을 원한다고 했는데 월·수 수업을 권한다. 교과서: This class meets on Saturdays and Sundays.",
     "T6", "제안하기 I suggest (that) ~")

# ── 9·10 외부지문 Helping Each Other ─────────────────────────
mat("T7", "외부지문 — Helping Each Other Makes Society Stronger", """
In every community, people depend on one another in both small and big ways. Working together and helping others is not only kind but also ⓐessential for a healthy society. When neighbors share their time, skills, or resources, life becomes easier and safer for everyone.
For example, after a big storm, some people clear fallen trees from the streets, while others deliver food and blankets to families who cannot leave their homes. In schools, students help classmates who are ⓑstruggling with homework or share books and supplies. In hospitals, volunteers ⓒassist nurses and doctors by bringing water, guiding visitors, and comforting patients. Even children can help by picking up trash in parks or planting trees in their neighborhoods. Every action, no matter how small, ⓓmatters.
Helping each other also teaches important values such as empathy, responsibility, and respect. When people cooperate, problems are solved more quickly, and everyone feels included and valued. Communities where people work together are stronger, happier, and more ⓔfragile. In the end, living together means understanding that we are all connected. A society works best when people help and support one another rather than focusing only on themselves.
""")
item(9, 5, "윗글의 ⓐ~ⓔ 중 문맥상 낱말의 쓰임이 적절하지 않은 것은?",
     ["ⓐ", "ⓑ", "ⓒ", "ⓓ", "ⓔ"], 5,
     "stronger, happier 와 나란히 「어려움에서 빨리 회복하는」 resilient 여야 한다. fragile 은 「깨지기 쉬운」 — 반대 뜻.",
     "T7", "학교 영영풀이 (resilient)")
mat("T8", "〈보기〉", """
(a) Even an action that seems trivial can make a difference to the whole community.
(b) The writer argues that only trained experts should handle problems after a disaster.
(c) Cooperation speeds up problem-solving and makes people feel accepted and appreciated.
(d) According to the passage, children can contribute only at school, not in their neighborhoods.
(e) The writer believes a society functions best when its members put themselves first.
""")
item(10, 5, "윗글의 내용과 일치하는 것만을 〈보기〉에서 있는 대로 고른 것은?",
     ["(a), (b)", "(a), (c)", "(a), (c), (d)", "(b), (d), (e)", "(a), (c), (e)"], 2,
     "(a) no matter how small, matters (c) solved more quickly · included and valued. (b) 폭풍 뒤 주민들이 직접 돕는다 (d) 공원·동네에서도 돕는다 (e) rather than focusing only on themselves 와 반대.",
     "T8")

# ── 11 6과 순서 ──────────────────────────────────────────────
mat("T9", "6과 본문 — One Lucky Sunday", """
He then added, "Hmm, I think I may buy it. The legs of my table at home are broken. I can cut off the legs of your table and attach them to mine."
(A) "Ten? It's worth more than that."
"How about fifteen?"
"Make it fifty."
(B) "How much?" Rummins asked.
"Not much, I'm afraid. This is just a reproduction," said Mr. Boggis.
"So how much?"
"Ten pounds."
(C) "Well, thirty. This is my final offer."
"OK, it's yours, but how are you going to take it? This thing will not go in a car!"
""")
item(11, 4, "주어진 글 다음에 이어질 대화의 순서로 가장 적절한 것은?",
     ["(A) - (C) - (B)", "(B) - (A) - (C)", "(B) - (C) - (A)", "(C) - (A) - (B)", "(C) - (B) - (A)"], 2,
     "가격을 묻고(B, 10파운드) → 「10이요? 더 가치가 있어요」·15·50 흥정(A) → 마지막 제안 30, 거래 성사(C).",
     "T9")

# ── 12·13 6과 결말 ───────────────────────────────────────────
mat("T10", "6과 본문 — One Lucky Sunday", """
On his way to the car, Mr. Boggis couldn't help smiling. The table was what every dealer dreamed of. He couldn't believe his luck.
"Dad, what if this thing doesn't go in his car? He might not pay you," said Bert. Rummins then had an idea. "(A)[What / That] he wants is only the legs. Let's cut the legs off for him," said Rummins. "Great idea!" said Bert. Bert then took out a saw and began to cut off the legs. By the time Mr. Boggis came back with his car, Bert (B)[already finished / had already finished] the job, and the legs (C)[had been cut / had cut] off.
"Don't worry, this was a favor. I won't charge you for this," said Rummins. Mr. Boggis was so shocked that he couldn't say anything.
""")
item(12, 4, "(A), (B), (C)의 각 네모 안에서 어법에 맞는 표현으로 가장 적절한 것은?",
     ["That - had already finished - had been cut",
      "What - already finished - had cut",
      "What - already finished - had been cut",
      "What - had already finished - had been cut",
      "That - already finished - had cut"], 4,
     "(A) 선행사를 포함한 관계대명사 what 이 주어절 (B) 돌아온 시점(과거)보다 먼저 끝남 → 과거완료 (C) 다리는 「잘린」 것 → 과거완료 수동 had been cut.",
     "T10", "관계대명사 what · 과거완료(수동)")
item(13, 3, "윗글에 드러난 Mr. Boggis의 심경 변화로 가장 적절한 것은?",
     ["thrilled → shocked", "nervous → relieved", "bored → excited",
      "guilty → satisfied", "disappointed → grateful"], 1,
     "couldn't help smiling · couldn't believe his luck(신남) → so shocked that he couldn't say anything(충격).",
     "T10")

# ── 14 what 의 쓰임 ──────────────────────────────────────────
item(14, 4, "다음 중 what의 쓰임이 〈보기〉와 같은 것은?  "
     "〈보기〉 The table was what every dealer dreamed of.",
     ["I wonder what he wants to eat.",
      "What a priceless table it is!",
      "Do you remember what you used it for?",
      "Please show me what you got from your grandmother.",
      "What do you think of this reproduction?"], 4,
     "〈보기〉·④ 는 선행사를 포함한 관계대명사(~하는 것). ①③ 간접의문문의 의문사(무엇) ② 감탄문 ⑤ 직접의문문.",
     None, "관계대명사 what vs 의문사 what")

# ── 15 6과 내용 개수 ─────────────────────────────────────────
mat("T11", "〈보기〉", """
(a) Mr. Boggis said that he could use the legs of Rummins's table for his own table.
(b) Mr. Boggis's final offer was three times as much as his first offer.
(c) Rummins agreed to sell the table but doubted that it would fit in a car.
(d) Bert cut off the legs because Mr. Boggis had asked him to.
(e) Rummins asked Mr. Boggis to pay extra for cutting off the legs.
(f) Mr. Boggis was so pleased with the legs that he thanked Rummins.
""")
item(15, 5, "One Lucky Sunday 의 두 글([T9], [T10])의 내용과 일치하는 것을 〈보기〉에서 모두 고른 것의 개수는?",
     ["1개", "2개", "3개", "4개", "5개"], 3,
     "일치 (a)(b)(c). (b) 10파운드 → 30파운드 = 세 배. (d) Rummins 의 생각 (e) I won't charge you (f) 너무 충격을 받아 아무 말도 못 했다.",
     "T11", "배수사 + as 원급 as")

# ── 16 외부지문 Fly Away Home (1) ─────────────────────────────
mat("T12", "외부지문 — Fly Away Home (1)", """
My dad and I live in an airport. That's because we don't have a home and the airport is better than the streets. We are careful not to get caught. Mr. Slocum and Mr. Vail were caught last night. "Ten green bottles, hanging on the wall," they sang. They were as loud as two moose bellowing. Dad says they broke the first rule of living here. Don't get noticed. Dad and I try not to get noticed. We stay among the crowds. We change airlines. "Delta, TWA, Northwest, we love them all," Dad says. He and I wear blue jeans and blue T-shirts and blue jackets. We each have a blue zippered bag with a change of blue clothes. Not to be noticed is to look like nobody at all.
Dad and I sleep sitting up. We use different airport areas. "Where are we tonight?" I ask. Dad checks his notebook. "Alaska Air," he says. "Over in the other terminal." That's OK. We like to walk. We know some of the airport regulars by name and by sight. There's Idaho Joe and Annie Frannie and Mars Man. But we don't sit together. "Sitting together will get you noticed faster than anything," Dad says.
""")
item(16, 4, "윗글의 내용과 일치하지 않는 것은?",
     ["Mr. Slocum and Mr. Vail were caught because they drew attention to themselves.",
      "Andrew and his dad wear clothes of the same color so that they won't stand out.",
      "Andrew and his dad know some airport regulars but avoid sitting with them.",
      "Andrew and his dad usually sleep in the same area of the airport every night.",
      "Andrew's dad keeps a record of where they will stay each night."], 4,
     "We use different airport areas — 밤마다 자리를 바꾼다. ⑤ Dad checks his notebook.",
     "T12")

# ── 17 Fly Away Home (4)(10) ─────────────────────────────────
mat("T13", "외부지문 — Fly Away Home (4) · (10)", """
Once a little brown bird got into the main terminal and couldn't get out. It fluttered in the high, hollow spaces. It threw itself at the glass, fell panting on the floor, flew to a tall, metal girder, and perched there, exhausted. "Don't stop trying," I told it silently. "Don't! You can get out!" For days the bird flew around, dragging one wing. And then it found the instant when a sliding door was open and slipped through. I watched it rise. Its wing seemed OK. "Fly, bird," I whispered. "Fly away home!"
⋯
Sometimes I just want to cry. I think Dad and I will be here forever. Then I remember the bird. It took a while, but a door opened. And when the bird left, when it flew free, I know it was singing.
""")
item(17, 4, "윗글에서 Andrew가 울고 싶을 때 새를 떠올리는 이유로 가장 적절한 것은?",
     ["It reminds him of the danger of being noticed in the airport.",
      "It gives him hope that he and his dad will someday leave the airport for a home.",
      "It makes him angry at the people who have homes to go back to.",
      "It reminds him of his mother, who used to sing to him.",
      "It makes him want to travel to other countries by plane."], 2,
     "갇혀 있던 새가 오래 걸렸지만(It took a while) 문이 열려 날아갔다 → 언젠가 공항을 떠나 집을 갖게 되리라는 희망.",
     "T13")

# ── 18 6과 대화 ──────────────────────────────────────────────
mat("T14", "6과 대화", """
B: You don't look good, Sumi. What's the matter?
G: Well, I didn't get a role in the school play. I'm very disappointed.
B: Oh, ________________ But I'm sure you can get a role next time.
G: Thanks. I'll try harder next time.
""")
item(18, 3, "대화의 빈칸에 들어갈 말로 적절하지 않은 것은?",
     ["I'm so sorry to hear that.", "That's too bad.", "That's a pity.",
      "I'm glad to hear that.", "What a shame."], 4,
     "실망한 친구에게 유감을 나타내는 자리다. I'm glad to hear that 은 기쁨.",
     "T14", "유감 표현하기")

# ── 19 7과 빈칸 ──────────────────────────────────────────────
mat("T15", "7과 본문 — Living with Big Data", """
Have you ever visited an online bookstore and been surprised by the books that the store recommended for you? Many of them looked interesting to you. So how did the bookstore know what you liked? This is all possible because of big data.
Big data is data sets that are very big and complex. As information and communication technology develops, the amount of data we have is getting much greater than before. This is mainly because almost everything that we do online leaves a trace. For example, the photos you upload on your blog and the records of your purchases at online stores are all part of big data.
________(A)________ Big data has to be analyzed, and this is done by big data experts. Using various methods, experts analyze big data and draw meaningful results from it. These results then can be used to make decisions or to predict the future.
""")
item(19, 4, "윗글의 빈칸 (A)에 들어갈 말로 가장 적절한 것은?",
     ["Simply collecting data, however, is not enough.",
      "Collecting data is the only thing that experts need to do.",
      "Big data, however, is too small to be useful.",
      "Most data, however, disappears soon after we go online.",
      "The amount of data, however, is getting smaller than before."], 1,
     "뒤에 「분석되어야 한다」가 오므로 「모으기만 해서는 충분하지 않다」. ② 는 뒤 문장과 반대 ⑤ 는 앞 문장과 반대.",
     "T15")

# ── 20 분사구문 ──────────────────────────────────────────────
mat("T16", "〈보기〉", """
(a) As experts use various methods, they analyze big data.
→ Using various methods, experts analyze big data.
(b) Big data is improving the performance of players, and it makes sports more exciting.
→ Big data is improving the performance of players, making sports more exciting.
(c) Because I did not feel well, I stayed home.
→ Feeling not well, I stayed home.
(d) If this kind of data is analyzed wisely, it can help predict the spread of the flu.
→ Analyzed wisely, this kind of data can help predict the spread of the flu.
(e) When the flu season comes, people will buy more flu medicine.
→ Coming the flu season, people will buy more flu medicine.
(f) As it was late at night, we went back home.
→ Being late at night, we went back home.
""")
item(20, 5, "〈보기〉에서 분사구문으로 바르게 바꾼 것만을 있는 대로 고른 것은?",
     ["(a), (b)", "(a), (b), (d)", "(a), (c), (d)", "(b), (d), (f)", "(a), (b), (d), (e)"], 2,
     "(c) 부정은 분사 앞 → Not feeling well (d) 수동 분사구문, Being 생략 (e) 주어가 달라 남겨야 한다 → The flu season coming (f) 주어 it 이 달라 → It being late at night.",
     "T16", "분사구문")

# ── 21 접속사 as ─────────────────────────────────────────────
item(21, 4, "다음 중 as의 의미가 〈보기〉와 같은 것은?  "
     "〈보기〉 As information and communication technology develops, the amount of data we have is getting much greater.",
     ["As we go up, the air grows colder.",
      "As you know, Julia is leaving soon.",
      "As he was out, I left a message.",
      "I called my friend as I went to school.",
      "They were all dressed as clowns."], 1,
     "〈보기〉·① ~함에 따라, ~할수록. ② ~듯이 ③ ~ 때문에 ④ ~하면서 ⑤ 전치사 ~처럼.",
     None, "접속사 as")

# ── 22 7과 내용 불일치 ───────────────────────────────────────
mat("T17", "7과 본문 — How is big data influencing our lives?", """
Disease Forecast
Did you know that health professionals can now forecast a disease just as weather experts forecast the weather? This is possible thanks to big data. For example, when the flu season comes, people will buy more flu medicine. They will also search online about flu symptoms more. If this kind of data is analyzed wisely, the spread of the flu can be predicted.
Improving Performance in Sports
A famous example is Germany's national soccer team. The team built a database by collecting and analyzing a huge amount of data on players. For example, the data included information about how much each player ran and how long he had the ball. With the help of this database, Germany's national soccer team was able to improve its performance and win the 2014 World Cup.
Crime Prevention
Thanks to big data, police can now predict crime before it happens. Through the analysis of big data about the type, time and place of crime, police can make a map of crime hot spots. This map identifies when and where crime is most likely to happen. Police can prevent further crime by focusing on the areas and the times this map predicts.
""")
item(22, 4, "윗글의 내용과 일치하지 않는 것은?",
     ["Health experts can now predict a disease in much the same way that weather experts forecast the weather.",
      "When flu season arrives, people tend to look up flu symptoms online more often.",
      "Germany's soccer team gathered data on how long each player kept the ball.",
      "A crime map helps police decide where and when to concentrate their efforts.",
      "The German team built its database only after winning the 2014 World Cup."], 5,
     "데이터베이스의 도움으로 우승했다(With the help of this database ... win) — 순서가 거꾸로다.",
     "T17")

# ── 23 대화 개수 ─────────────────────────────────────────────
mat("T18", "〈보기〉", """
(a) A: How often do you take bowling lessons?
    B: Twice a week. I'm just a beginner.
(b) A: Your shoes aren't good for running. I suggest you wear running shoes.
    B: OK. I'll change into them.
(c) A: Congratulations on winning the gold medal.
    B: I'm sorry to hear that.
(d) A: Is anything wrong?
    B: Well, I lost my smartphone. I'm upset.
(e) A: Do you know how to use this snack machine?
    B: Yeah. First, choose the snack you want.
(f) A: I really appreciate your help.
    B: Don't mention it.
(g) A: You must be very proud of yourself.
    B: No, I didn't. I did my best.
(h) A: Can you tell me how to return these books?
    B: Sure. I returned them yesterday.
""")
item(23, 5, "〈보기〉의 대화 중 자연스러운 것의 개수는?",
     ["3개", "4개", "5개", "6개", "7개"], 3,
     "자연스러운 것 (a)(b)(d)(e)(f). (c) 축하에 유감으로 답함 (g) be동사 질문 → Yes, I am (h) 방법을 물었는데 자기가 반납한 이야기.",
     "T18", "빈도 묻기 · 제안 · 감정 · 방법 묻기 · 감사")

# ── 24 종합 어법 ─────────────────────────────────────────────
mat("T19", "〈보기〉", """
(A) Changing the tires are especially important in a high speed race.
(B) Sherpas have little difficulty breathing high up in the mountains.
(C) Almost everything that we do online leave a trace.
(D) The table was what every dealer dreamed of.
(E) People asked him where had he got the furniture.
(F) The photos you upload on your blog and the records of your purchases is all part of big data.
(G) Big data helps people avoid heavy traffic.
(H) The pit crew has to work in perfect harmony.
""")
item(24, 5, "〈보기〉에서 어법상 옳은 문장만을 있는 대로 고른 것은?",
     ["(B), (D)", "(B), (D), (G)", "(B), (D), (G), (H)",
      "(A), (B), (D), (G), (H)", "(B), (C), (D), (G), (H)"], 3,
     "(A) 동명사 주어 단수 → is (C) everything 단수 → leaves (E) 간접의문문 어순 → where he had got (F) 주어 두 개 → are. (H) crew 를 한 단위로 보면 단수.",
     "T19", "주어-동사 수일치 · 간접의문문 어순")


# ── 서술형 넣기 (원장 2026-11-08 「서술형이 없는데?」) ─────────────────
# 기출 지필엔 서술형이 없었지만 우리 영일 동형은 선택 80 + 서술 4문항 20 으로 내 왔다 (영일중2 1~5세트).
# 선택형에서 가장 쉬운 3문항(7 as~as 바꿔쓰기 · 8 5과 대화 · 18 6과 대화)을 빼고 21문항 80점으로 다시 매긴다.
# 7번의 as~as 는 서술형 영작으로 옮겼다.
DROP = {7, 8, 18}
POINTS = {2: 5, 6: 5, 9: 5, 20: 5, 23: 5, 24: 5,          # 5점 — 개수 · 있는 대로 · 바꿔 쓴 말
          3: 4, 10: 4, 12: 4, 15: 4, 22: 4}               # 나머지 10문항 3점
I[:] = [it for it in I if it["no"] not in DROP]
for n, it in enumerate(I, 1):
    it["points"] = POINTS.get(it["no"], 3)
    it["no"] = n

E = []          # essays — 디자인 지침 3(줄 나눔) · 4(칸 하나에 몇 단어)


def essay(pts, prompt, context, conds, words, wl, grammar, ans, why, slots, mid=None):
    for s in ans.split("\n"):
        if s.startswith("(완성"):
            continue
        assert len(s.split(":", 1)[-1].replace("→", " ").split()) <= 14, s   # 틀린 말 → 고친 말 각 7단어 이하
    E.append({"no": len(I) + len(E) + 1, "material_id": mid, "points": pts, "prompt_ko": prompt,
              "context": context, "conditions": conds, "given_words": words, "word_limit": wl,
              "target_grammar": grammar, "answer_en": ans, "why_ko": why, "answer_slots": slots})


essay(5, "다음 우리말을 <조건>에 맞게 영작할 때, 2번째·5번째·10번째 단어를 쓰시오.",
      "셰르파는 등반가들만큼 중요하지만, 사진 속에서는 보이지 않는다.",
      ["「as + 원급 + as」 를 반드시 사용할 것",
       "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것",
       "climbers 앞에 관사를 쓰지 말 것",
       "but 뒤의 주어는 대명사로 쓸 것",
       "답안에는 지정된 순서의 단어만 쓸 것 (문장 전체를 쓰지 말 것)"],
      ["Sherpas", "important", "climbers", "invisible", "in pictures"], "12 단어",
      "as 원급 as (5과)",
      "2번째: are\n5번째: as\n10번째: invisible\n"
      "(완성 문장: Sherpas are as important as climbers, but they are invisible in pictures.)",
      "as important as 의 두 번째 as 가 5번째. but 뒤 they are invisible — are 를 빠뜨리면 10번째가 in 이 된다.",
      ["2번째 단어: ________", "5번째 단어: ________", "10번째 단어: ________"])

essay(5, "다음 우리말을 <조건>에 맞게 영작할 때, 5번째·8번째·11번째 단어를 쓰시오.",
      "Boggis 씨는 자신이 원했던 것이 이미 잘려 나갔다는 것을 알게 되었다.",
      ["관계대명사 what 을 반드시 사용할 것",
       "「원했던」 과 「잘려 나갔다」 는 모두 과거완료로 쓸 것 (하나는 수동태)",
       "found 다음의 접속사 that 을 생략하지 말 것",
       "Mr. Boggis 는 두 단어로 센다",
       "답안에는 지정된 순서의 단어만 쓸 것"],
      ["find", "want", "already", "cut off"], "13 단어",
      "관계대명사 what · 과거완료(수동) (6과)",
      "5번째: what\n8번째: wanted\n11번째: been\n"
      "(완성 문장: Mr. Boggis found that what he had wanted had already been cut off.)",
      "what he had wanted 가 that 절의 주어(단수) → had already been cut off. 수동이라 been 이 11번째.",
      ["5번째 단어: ________", "8번째 단어: ________", "11번째 단어: ________"])

essay(5, "다음 글에서 어법상 틀린 부분 2곳을 찾아 바르게 고쳐 쓰시오.",
      "Big data is influencing almost all parts of our lives.\n"
      "Collected and analyzed a huge amount of data on players, Germany's national soccer team "
      "was able to improve its performance.\n"
      "Through the analysis of big data, police can now make a map identifies when and where "
      "crime is most likely to happen.",
      ["틀린 곳은 정확히 2곳이다",
       "한 칸에 「틀린 말 → 고친 말」 로 쓸 것",
       "고친 말은 3단어 이하로 쓸 것"],
      [], "", "분사구문 · 분사 후치수식 (7과)",
      "(1) Collected and analyzed → Collecting and analyzing\n"
      "(2) identifies → identifying (that identifies 도 정답)",
      "(1) 팀이 데이터를 「모으고 분석한」 능동 → 현재분사 분사구문. (2) 동사가 둘(make · identifies) — "
      "map 을 뒤에서 꾸미는 현재분사 identifying 또는 주격 관계대명사 that identifies.",
      ["(1) ____________ → ____________", "(2) ____________ → ____________"])

essay(5, "윗글 [T7], [T12]를 읽고, 질문에 대한 답을 완성하시오.",
      "Q1: What happens when people cooperate?\n"
      "A: Problems are solved (1) ______ ______, and everyone feels included and valued.\n"
      "Q2: Why don't Andrew and his dad sit with the airport regulars?\n"
      "A: Because sitting together will (2) ______ ______ ______ faster than anything.",
      ["본문의 표현을 사용할 것",
       "(1) 은 2단어, (2) 는 3단어로 쓸 것",
       "(2) 는 Andrew 와 아빠를 가리키는 대명사를 넣을 것"],
      [], "", "내용 확인 (외부지문)",
      "(1) more quickly\n(2) get them noticed",
      "(1) When people cooperate, problems are solved more quickly. "
      "(2) 본문은 get you noticed — 질문이 Andrew 와 아빠에 관한 것이므로 them. get + 목적어 + 과거분사.",
      ["(1) ____________", "(2) ____________"])


def check():
    assert [it["no"] for it in I] == list(range(1, len(I) + 1)), "문항 번호"
    total = sum(it["points"] for it in I) + sum(e["points"] for e in E)
    assert (len(I), len(E)) == (21, 4), (len(I), len(E))
    assert sum(it["points"] for it in I) == 80, "선택형 80점"
    assert total == 100, f"배점 합계 {total}"
    dist = {k: sum(1 for it in I if it["answer"] == k) for k in range(1, 6)}
    ids = {m["id"] for m in M}
    for it in I:
        assert it["material_id"] in ids or it["material_id"] is None, it["no"]
    return total, dist


def main():
    total, dist = check()
    d = {"school": "영일중", "set_no": 1, "grade": "3", "range": "567",
         "spec": {"total_points": 100, "selective": len(I), "essay": len(E)},
         "materials": M, "items": I, "essays": E,
         "diagnostics": {"problems": [], "total_points": total}}
    js = os.path.join(HERE, "영일중3_1세트.json")
    io.open(js, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"  {TITLE} · 선택 {len(I)} · 서술 {len(E)} · {total}점 · 정답 분포 {dist}")

    from tools.build_drill_pdf import find_chrome, to_pdf
    from tools.pdf_pages import stamp_file
    from tools.render_mock_exam import build
    from tools.render_worksheet import logo_tag, DEFAULT_LOGO
    out = os.path.join(ROOT, "result", "readitude")
    os.makedirs(out, exist_ok=True)
    chrome, logo, tmp = find_chrome(), logo_tag(DEFAULT_LOGO), tempfile.mkdtemp(prefix="mock3_")
    try:
        for part, suffix in [("worksheet", ""), ("answers", " 정답지")]:
            h = os.path.join(tmp, f"{TITLE}{suffix}.html")
            pdf = os.path.join(out, f"{TITLE}{suffix}.pdf")
            io.open(h, "w", encoding="utf-8").write(build(d, logo, part, title=TITLE))
            to_pdf(chrome, h, pdf)
            stamp_file(pdf)                      # 아래 가운데 쪽수 — 디자인 지침 1
            print("  →", pdf)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
