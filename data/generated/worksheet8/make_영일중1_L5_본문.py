# -*- coding: utf-8 -*-
"""
영일중1 5과 본문확인 워크시트 데이터 (mid-eng-worksheet-8set) — 2026-11-09. 6·7과와 같은 방식.

  원문   data/stage0/passages/중1L5_본문.json (확정본) — 29문장
         증언자 머리줄 넷(Ann Jones, a visitor 등)은 문장이 아니라 그 사람의 첫 문장 앞에 「이름, 직업:」 으로 붙였다.
         짧은 문장 둘은 다음 문장과 묶었다: What did they say? → 앞 문장과 · He spoke only English. → 앞 문장과 → 23문항
  해석   특급기출 중1 2학기 5과 「주요 문장」 쪽(28~29쪽)의 우리말
  단어   영일중1 5과 학교 프린트는 Z: 에 없다 (school_notes/영일중1_L5-7_학교프린트.json 「missing」).
         그래서 같은 교과서(동아 윤정미)를 쓰는 영덕중1 L5 학습지 영영풀이(vocab/영덕중1_L5_vocab_handout.json) →
         자습서 풀이(중1_L5_vocab.json) → 새로 씀 순서. wheelchair 는 풀이에 chair·wheels 가 들어 있어 고쳐 썼다 (PREP-2).
  축약형  I’m 의 be 는 ④ 정답을 「’m (am)」 꼴 (7과와 같다).
  ⑧     틀은 <…> 로 칸이 될 부분을 감싸 적고, 칸 수는 여기서 센다 — 손으로 세다 틀리지 않게.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import build

S = [
 ("Last Saturday, someone threw a cake at the Monalisa in the Botero Museum in Bogota, Colombia.",
  "지난 토요일, 누군가가 콜롬비아 보고타에 있는 보테로 박물관의 ‘모나리자’에 케이크를 던졌다."),
 ("There were four eyewitnesses. What did they say?", "네 명의 목격자가 있었다. 그들이 뭐라고 말했을까?"),
 ("Read the following, and find the criminal.", "다음을 읽고, 범인을 찾아보자."),
 ("Ann Jones, a visitor: I was looking at the Monalisa, and someone threw a cake at the painting.",
  "Ann Jones, 방문객: 저는 ‘모나리자’를 보고 있었는데, 누군가가 그림을 향해 케이크를 던졌어요."),
 ("I turned around and saw an old man.", "저는 뒤를 돌아봤고 한 노인을 봤어요."),
 ("He was standing in front of a wheelchair.", "그는 휠체어 앞에 서 있었어요."),
 ("I’m about 170 cm tall, and he was a little taller than me.", "저는 키가 약 170 cm 정도인데, 그는 저보다 조금 더 컸어요."),
 ("Carlos Diaz, a janitor: An old man with gray hair was running away, and something fell off his head.",
  "Carlos Diaz, 청소부: 회색 머리의 한 노인이 도망가고 있었고, 그의 머리에서 뭔가가 떨어졌어요."),
 ("It was his wig.", "그것은 그의 가발이었어요."),
 ("I ran after him, but I couldn’t catch him.", "저는 그를 뒤쫓았지만, 잡지 못했어요."),
 ("He was faster than me.", "그는 저보다 더 빨랐어요."),
 ("In fact, the old man was not old.", "사실, 그 노인은 나이 든 사람이 아니었어요."),
 ("He was a young man with long brown hair.", "그는 긴 갈색 머리의 젊은 남자였어요."),
 ("Diego Perez, a guard: I went to the crime scene, and there were pieces of cake all over the painting.",
  "Diego Perez, 경비원: 저는 범죄 현장에 갔는데, 그림 곳곳에 케이크 조각들이 있었어요."),
 ("There was also a wheelchair near the painting, and I found a cake box next to the wheelchair.",
  "그림 근처에는 휠체어도 있었고, 저는 휠체어 옆에 있는 케이크 상자를 발견했어요."),
 ("The box was from Camila’s Bakery.", "그 상자는 카밀라 빵집의 상자였어요."),
 ("Camila Santos, the owner of Camila’s Bakery: Last Friday, a young man came in.",
  "Camila Santos, 카밀라 빵집의 주인: 지난 금요일, 한 젊은 남자가 들어 왔어요."),
 ("I spoke to him in Spanish, but he didn’t understand me. He spoke only English.",
  "저는 그에게 스페인어로 말했지만, 그는 제 말을 이해하지 못했어요. 그는 영어로만 말했어요."),
 ("We had a lot of different cakes, but he just wanted the smallest one.",
  "우리 가게에는 많은 다른 케이크들이 있었는데, 그는 그냥 가장 작은 것을 원했어요."),
 ("We sold only one cake that day, so I remember him clearly.", "우리는 그날 케이크를 딱 한 개 팔았어요. 그래서 그를 똑똑히 기억해요."),
 ("Oh, he had blue eyes.", "아, 그의 눈은 파란색이었어요."),
 ("Now, look at the information about the suspects.", "이제, 용의자들에 대한 정보를 보자."),
 ("Who threw the cake at the Monalisa?", "누가 ‘모나리자’에게 케이크를 던졌을까?"),
]

PREP = [  # 학교 = 영덕중1 L5 학습지 풀이 · 자습서 = 특급기출 Words · 나머지는 새로 씀
 ("throw", "v.", "던지다", "to send something through the air with your hand",
  "He **threw** the ball to his little sister.", "그는 여동생에게 공을 던졌다."),
 ("eyewitness", "n.", "목격자", "someone who saw a crime or an accident",  # 학교
  "An **eyewitness** told the police about the car accident.", "한 목격자가 경찰에게 그 자동차 사고에 대해 말했다."),
 ("following", "n.", "다음에 말하는 것, 다음에 쓴 것", "the things that come next in a list or a text",
  "Read the **following** and choose the right answer.", "다음을 읽고 알맞은 답을 고르시오."),
 ("criminal", "n.", "범인, 범죄자", "a person who does something against the law, like stealing or hurting others",  # 학교
  "The **criminal** went to prison for ten years.", "그 범죄자는 10년 동안 감옥에 갔다."),
 ("visitor", "n.", "방문객", "a person who comes to see a place or a person",
  "Many **visitors** come to Jeju Island every summer.", "매년 여름 많은 방문객이 제주도에 온다."),
 ("turn around", "phr.", "뒤돌아보다", "to move your body so that you face the other way",
  "She **turned around** when I called her name.", "내가 이름을 부르자 그녀는 뒤돌아보았다."),
 ("in front of", "phr.", "~ 앞에", "close to the face side of something or someone",
  "Let’s meet **in front of** the library at three.", "3시에 도서관 앞에서 만나자."),
 ("wheelchair", "n.", "휠체어", "a seat that moves on round parts, used by people who cannot walk",  # 학교 풀이를 고침
  "My grandfather uses a **wheelchair** after his surgery.", "할아버지는 수술 후에 휠체어를 사용하신다."),
 ("a little", "phr.", "약간, 조금", "a small amount; slightly",
  "This soup is **a little** salty for me.", "이 수프는 나에게 조금 짜다."),
 ("janitor", "n.", "청소부, 관리인", "a person in charge of cleaning and fixing things in a building",  # 학교
  "The **janitor** fixed the broken door in our classroom.", "관리인이 우리 교실의 고장 난 문을 고쳤다."),
 ("run away", "phr.", "도망가다", "to leave a place or person secretly and suddenly",  # 학교
  "The cat **ran away** from the big dog.", "고양이가 큰 개에게서 도망갔다."),
 ("fall off", "phr.", "~에서 떨어지다", "to drop to the ground from a high object",  # 자습서
  "A book **fell off** my desk.", "책 한 권이 내 책상에서 떨어졌다."),
 ("wig", "n.", "가발", "an object with hair on it that someone wears on their head",  # 학교
  "The actor wore a long black **wig** on stage.", "그 배우는 무대에서 길고 검은 가발을 썼다."),
 ("run after", "phr.", "~을 뒤쫓다", "to follow someone quickly to get them",
  "The boy **ran after** the bus, but it left.", "소년은 버스를 뒤쫓았지만 버스는 떠났다."),
 ("catch", "v.", "잡다", "to take and hold a person or thing that is moving",
  "Can you **catch** this ball with one hand?", "이 공을 한 손으로 잡을 수 있니?"),
 ("in fact", "phr.", "사실은", "used to say what is really true",
  "He looks quiet, but **in fact** he talks a lot.", "그는 조용해 보이지만, 사실은 말을 많이 한다."),
 ("guard", "n.", "경비원", "a person whose job is to protect a person, place, or thing from danger or attack",  # 학교
  "A **guard** stands at the gate of the building.", "경비원이 건물 입구에 서 있다."),
 ("scene", "n.", "현장", "the place where something happens",  # 자습서 풀이 앞부분
  "Police cars came to the **scene** of the accident.", "경찰차들이 사고 현장에 왔다."),
 ("piece", "n.", "조각", "a part that is cut or broken from something bigger",
  "Can I have a **piece** of pizza?", "피자 한 조각 먹어도 돼?"),
 ("next to", "phr.", "~ 옆에", "very close to someone or something, at the side",
  "My best friend sits **next to** me in class.", "가장 친한 친구가 수업 시간에 내 옆에 앉는다."),
 ("bakery", "n.", "빵집", "a place where bread and cakes are made or sold",  # 학교
  "The new **bakery** sells fresh bread every morning.", "새 빵집은 매일 아침 신선한 빵을 판다."),
 ("owner", "n.", "주인", "a person who has something",
  "The **owner** of this dog lives next door.", "이 개의 주인은 옆집에 산다."),
 ("understand", "v.", "이해하다", "to know the meaning of something",
  "I don’t **understand** this math problem.", "나는 이 수학 문제를 이해하지 못한다."),
 ("clearly", "adv.", "또렷하게, 분명히", "in a way that is easy to see, hear, or know",
  "Please speak **clearly** so everyone can hear you.", "모두가 들을 수 있도록 또렷하게 말해 주세요."),
 ("suspect", "n.", "용의자", "a person who is believed to be guilty of something",  # 자습서
  "The police asked the **suspect** many questions.", "경찰은 용의자에게 많은 질문을 했다."),
]

WS1 = [
 ("Last Saturday, / someone threw((던지다)) a cake / at the Monalisa / in the Botero Museum / in Bogota, Colombia.",
  "지난 토요일 / 누군가가 케이크를 던졌다 / 모나리자에 / 보테로 박물관에 있는 / 콜롬비아 보고타의"),
 ("There were four eyewitnesses((목격자)). / What did they say?", "네 명의 목격자가 있었다 / 그들은 무엇을 말했을까"),
 ("Read the following((다음에 말하는 것)), / and find the criminal((범인)).", "다음을 읽어라 / 그리고 범인을 찾아라"),
 ("Ann Jones, a visitor((방문객)): / I was looking at the Monalisa, / and someone threw a cake / at the painting.",
  "Ann Jones, 방문객 / 나는 모나리자를 보고 있었다 / 그리고 누군가가 케이크를 던졌다 / 그 그림에"),
 ("I turned around((뒤돌아보다)) / and saw an old man.", "나는 뒤돌아봤다 / 그리고 한 노인을 봤다"),
 ("He was standing / in front of((~ 앞에)) a wheelchair((휠체어)).", "그는 서 있었다 / 휠체어 앞에"),
 ("I’m about 170 cm tall, / and he was a little((조금)) taller / than me.", "나는 키가 약 170 cm이다 / 그리고 그는 조금 더 컸다 / 나보다"),
 ("Carlos Diaz, a janitor((청소부)): / An old man / with gray hair / was running away((도망가다)), / and something fell off((~에서 떨어지다)) / his head.",
  "Carlos Diaz, 청소부 / 한 노인이 / 회색 머리를 한 / 도망가고 있었다 / 그리고 무언가가 떨어졌다 / 그의 머리에서"),
 ("It was his wig((가발)).", "그것은 그의 가발이었다"),
 ("I ran after((~을 뒤쫓다)) him, / but I couldn’t catch((잡다)) him.", "나는 그를 뒤쫓았다 / 하지만 나는 그를 잡을 수 없었다"),
 ("He was faster / than me.", "그는 더 빨랐다 / 나보다"),
 ("In fact((사실은)), / the old man was not old.", "사실은 / 그 노인은 늙지 않았다"),
 ("He was a young man / with long brown hair.", "그는 젊은 남자였다 / 긴 갈색 머리를 한"),
 ("Diego Perez, a guard((경비원)): / I went to the crime scene((범죄 현장)), / and there were pieces((조각)) of cake / all over the painting.",
  "Diego Perez, 경비원 / 나는 범죄 현장에 갔다 / 그리고 케이크 조각들이 있었다 / 그림 곳곳에"),
 ("There was also a wheelchair / near the painting, / and I found a cake box / next to((~ 옆에)) the wheelchair.",
  "휠체어도 있었다 / 그림 근처에 / 그리고 나는 케이크 상자를 발견했다 / 휠체어 옆에서"),
 ("The box was / from Camila’s Bakery((빵집)).", "그 상자는 ~였다 / 카밀라 빵집에서 온"),
 ("Camila Santos, the owner((주인)) of Camila’s Bakery: / Last Friday, / a young man came in.",
  "Camila Santos, 카밀라 빵집의 주인 / 지난 금요일 / 한 젊은 남자가 들어왔다"),
 ("I spoke to him / in Spanish((스페인어)), / but he didn’t understand me. / He spoke only English.",
  "나는 그에게 말했다 / 스페인어로 / 하지만 그는 내 말을 이해하지 못했다 / 그는 영어만 말했다"),
 ("We had a lot of different cakes, / but he just wanted / the smallest one.",
  "우리는 많은 다른 케이크가 있었다 / 하지만 그는 단지 원했다 / 가장 작은 것을"),
 ("We sold only one cake / that day, / so I remember him clearly((또렷하게)).",
  "우리는 케이크를 딱 한 개 팔았다 / 그날 / 그래서 나는 그를 또렷하게 기억한다"),
 ("Oh, he had blue eyes.", "아, 그는 파란 눈을 가지고 있었다"),
 ("Now, / look at the information((정보)) / about the suspects((용의자)).", "이제 / 정보를 보아라 / 용의자들에 대한"),
 ("Who threw the cake / at the Monalisa?", "누가 케이크를 던졌을까 / 모나리자에"),
]

WS2 = [
 ("Last Saturday, someone **threw** a cake at the Monalisa in the Botero **Museum** in Bogota, Colombia.",
  "지난 토요일, 누군가가 콜롬비아 보고타에 있는 보테로 {{박물관}}의 ‘모나리자’에 케이크를 {{던졌}}다."),
 ("There were four **eyewitnesses**. What did they **say**?", "네 명의 {{목격자}}가 있었다. 그들이 뭐라고 {{말했}}을까?"),
 ("Read the **following**, and find the **criminal**.", "{{다음}}을 읽고, {{범인}}을 찾아보자."),
 ("Ann Jones, a **visitor**: I was **looking at** the Monalisa, and someone threw a cake at the **painting**.",
  "Ann Jones, {{방문객}}: 저는 ‘모나리자’를 {{보고}} 있었는데, 누군가가 {{그림}}을 향해 케이크를 던졌어요."),
 ("I **turned around** and saw an **old man**.", "저는 {{뒤를 돌아봤}}고 한 {{노인}}을 봤어요."),
 ("He was **standing** **in front of** a **wheelchair**.", "그는 {{휠체어}} {{앞에}} {{서}} 있었어요."),
 ("I’m **about** 170 cm **tall**, and he was **a little** taller than me.", "저는 {{키}}가 {{약}} 170 cm 정도인데, 그는 저보다 {{조금}} 더 컸어요."),
 ("Carlos Diaz, a **janitor**: An old man with gray hair was **running away**, and something **fell off** his head.",
  "Carlos Diaz, {{청소부}}: 회색 머리의 한 노인이 {{도망가}}고 있었고, 그의 머리에서 뭔가가 {{떨어졌}}어요."),
 ("It was his **wig**.", "그것은 그의 {{가발}}이었어요."),
 ("I **ran after** him, but I couldn’t **catch** him.", "저는 그를 {{뒤쫓았}}지만, {{잡}}지 못했어요."),
 ("He was **faster** than me.", "그는 저보다 {{더 빨랐}}어요."),
 ("**In fact**, the old man was not **old**.", "{{사실}}, 그 노인은 {{나이 든}} 사람이 아니었어요."),
 ("He was a **young** man with long **brown** hair.", "그는 긴 {{갈색}} 머리의 {{젊은}} 남자였어요."),
 ("Diego Perez, a **guard**: I went to the **crime scene**, and there were **pieces** of cake all over the painting.",
  "Diego Perez, {{경비원}}: 저는 {{범죄 현장}}에 갔는데, 그림 곳곳에 케이크 {{조각}}들이 있었어요."),
 ("There was also a wheelchair **near** the painting, and I **found** a cake box **next to** the wheelchair.",
  "그림 {{근처}}에는 휠체어도 있었고, 저는 휠체어 {{옆에}} 있는 케이크 상자를 {{발견했}}어요."),
 ("The box was from Camila’s **Bakery**.", "그 상자는 카밀라 {{빵집}}의 상자였어요."),
 ("Camila Santos, the **owner** of Camila’s Bakery: **Last** Friday, a young man **came in**.",
  "Camila Santos, 카밀라 빵집의 {{주인}}: {{지난}} 금요일, 한 젊은 남자가 {{들어}} 왔어요."),
 ("I spoke to him in **Spanish**, but he didn’t **understand** me. He spoke only English.",
  "저는 그에게 {{스페인어}}로 말했지만, 그는 제 말을 {{이해하}}지 못했어요. 그는 영어로만 말했어요."),
 ("We had a lot of **different** cakes, but he just wanted the **smallest** one.",
  "우리 가게에는 많은 {{다른}} 케이크들이 있었는데, 그는 그냥 {{가장 작은}} 것을 원했어요."),
 ("We **sold** only one cake that day, so I **remember** him **clearly**.",
  "우리는 그날 케이크를 딱 한 개 {{팔았}}어요. 그래서 그를 {{똑똑히}} {{기억해}}요."),
 ("Oh, he had **blue** **eyes**.", "아, 그의 {{눈}}은 {{파란색}}이었어요."),
 ("Now, look at the **information** about the **suspects**.", "이제, {{용의자}}들에 대한 {{정보}}를 보자."),
 ("**Who** **threw** the cake at the Monalisa?", "{{누가}} ‘모나리자’에게 케이크를 {{던졌}}을까?"),
]

AM = "’m (am)"
WS4 = [
 ("Last Saturday, someone ^^(throw)^^ a cake at the Monalisa in the Botero Museum in Bogota, Colombia.", ["threw"]),
 ("There ^^(be)^^ four eyewitnesses. What ^^(do)^^ they ^^(say)^^?", ["were", "did", "say"]),
 ("^^(read)^^ the following, and ^^(find)^^ the criminal.", ["Read", "find"]),
 ("Ann Jones, a visitor: I ^^(look)^^ at the Monalisa, and someone ^^(throw)^^ a cake at the painting.", ["was looking", "threw"]),
 ("I ^^(turn)^^ around and ^^(see)^^ an old man.", ["turned", "saw"]),
 ("He ^^(stand)^^ in front of a wheelchair.", ["was standing"]),
 ("I ^^(be)^^ about 170 cm tall, and he ^^(be)^^ a little taller than me.", [AM, "was"]),
 ("Carlos Diaz, a janitor: An old man with gray hair ^^(run)^^ away, and something ^^(fall)^^ off his head.", ["was running", "fell"]),
 ("It ^^(be)^^ his wig.", ["was"]),
 ("I ^^(run)^^ after him, but I ^^(can’t, catch)^^ him.", ["ran", "couldn’t catch"]),
 ("He ^^(be)^^ faster than me.", ["was"]),
 ("In fact, the old man ^^(be)^^ not old.", ["was"]),
 ("He ^^(be)^^ a young man with long brown hair.", ["was"]),
 ("Diego Perez, a guard: I ^^(go)^^ to the crime scene, and there ^^(be)^^ pieces of cake all over the painting.", ["went", "were"]),
 ("There ^^(be)^^ also a wheelchair near the painting, and I ^^(find)^^ a cake box next to the wheelchair.", ["was", "found"]),
 ("The box ^^(be)^^ from Camila’s Bakery.", ["was"]),
 ("Camila Santos, the owner of Camila’s Bakery: Last Friday, a young man ^^(come)^^ in.", ["came"]),
 ("I ^^(speak)^^ to him in Spanish, but he ^^(don’t, understand)^^ me. He ^^(speak)^^ only English.", ["spoke", "didn’t understand", "spoke"]),
 ("We ^^(have)^^ a lot of different cakes, but he just ^^(want)^^ the smallest one.", ["had", "wanted"]),
 ("We ^^(sell)^^ only one cake that day, so I ^^(remember)^^ him clearly.", ["sold", "remember"]),
 ("Oh, he ^^(have)^^ blue eyes.", ["had"]),
 ("Now, ^^(look)^^ at the information about the suspects.", ["look"]),
 ("Who ^^(throw)^^ the cake at the Monalisa?", ["threw"]),
]

WS5 = [
 ("Last Saturday, someone ^^[throws / threw]^^ a cake at the Monalisa in the Botero Museum ^^[in Bogota, Colombia / in Colombia, Bogota]^^.",
  ["threw", "in Bogota, Colombia"]),
 ("There ^^[was / were]^^ four eyewitnesses. What ^^[they said / did they say]^^?", ["were", "did they say"]),
 ("Read the following, and ^^[find / finds]^^ the criminal.", ["find"]),
 ("Ann Jones, a visitor: I ^^[were / was]^^ looking at the Monalisa, and someone ^^[threw / thrown]^^ a cake at the painting.", ["was", "threw"]),
 ("I turned around and ^^[seen / saw]^^ an old man.", ["saw"]),
 ("He was ^^[standing / stand]^^ in front of a wheelchair.", ["standing"]),
 ("I’m about 170 cm tall, and he was a little ^^[more tall / taller]^^ than me.", ["taller"]),
 ("Carlos Diaz, a janitor: An old man with gray hair ^^[was / were]^^ running away, and something ^^[falled / fell]^^ off his head.", ["was", "fell"]),
 ("It ^^[were / was]^^ his wig.", ["was"]),
 ("I ran after him, but I couldn’t ^^[catch / caught]^^ him.", ["catch"]),
 ("He was ^^[fast / faster]^^ than me.", ["faster"]),
 ("In fact, the old man ^^[did not / was not]^^ old.", ["was not"]),
 ("He was ^^[a / an]^^ young man with long brown hair.", ["a"]),
 ("Diego Perez, a guard: I ^^[went / go]^^ to the crime scene, and there were ^^[piece / pieces]^^ of cake all over the painting.", ["went", "pieces"]),
 ("There ^^[were / was]^^ also a wheelchair near the painting, and I found a cake box next ^^[to / of]^^ the wheelchair.", ["was", "to"]),
 ("The box was from ^^[Camila’s / Camilas]^^ Bakery.", ["Camila’s"]),
 ("Camila Santos, the owner of Camila’s Bakery: ^^[On last Friday / Last Friday]^^, a young man ^^[came / come]^^ in.", ["Last Friday", "came"]),
 ("I spoke to ^^[he / him]^^ in Spanish, but he ^^[doesn’t / didn’t]^^ understand me. He spoke only English.", ["him", "didn’t"]),
 ("We had a lot of different ^^[cakes / cake]^^, but he just wanted the ^^[smaller / smallest]^^ one.", ["cakes", "smallest"]),
 ("We sold only one cake that day, so I remember him ^^[clearly / clear]^^.", ["clearly"]),
 ("Oh, he ^^[has / had]^^ blue eyes.", ["had"]),
 ("Now, ^^[look / looks]^^ at the ^^[informations / information]^^ about the suspects.", ["look", "information"]),
 ("Who ^^[did throw / threw]^^ the cake at the Monalisa?", ["threw"]),
]

WS6 = [
 {"lines": ["Who Threw a Cake at the Monalisa?",
            "Last Saturday, someone **throws** a cake at the Monalisa **in** the Botero Museum **in Bogota, Colombia**. "
            "There **were** four eyewitnesses. What **they said**? **Read** the following, and **find** the criminal."],
  "errors": [{"wrong": "throws", "right": "threw", "reason": "Last Saturday 는 과거 — throw 의 과거형 threw"},
             {"wrong": "they said", "right": "did they say", "reason": "의문사 의문문 어순: 의문사 + did + 주어 + 동사원형"}]},
 {"lines": ["^^Ann Jones, a visitor^^",
            "I **were** looking at the Monalisa, and someone **threw** a cake at the painting. I turned around and **see** an old man. "
            "He was **standing** in front of a wheelchair. I’m **about** 170 cm tall, and he was a little **more taller** than me."],
  "errors": [{"wrong": "were", "right": "was", "reason": "주어 I 의 과거진행형은 was + -ing"},
             {"wrong": "see", "right": "saw", "reason": "turned 와 and 로 이어진 과거 — see 의 과거형 saw"},
             {"wrong": "more taller", "right": "taller", "reason": "taller 가 이미 비교급 — more 를 겹쳐 쓰지 않는다"}]},
 {"lines": ["^^Carlos Diaz, a janitor^^",
            "An old man with gray hair **was** running away, and something **falled** off his head. It **was** his wig. "
            "I ran after him, but I couldn’t **caught** him. He was **faster** than me. In fact, the old man was not old. "
            "He was **a** young man with long brown hair."],
  "errors": [{"wrong": "falled", "right": "fell", "reason": "fall 의 과거형은 fell (불규칙)"},
             {"wrong": "caught", "right": "catch", "reason": "조동사 couldn’t + 동사원형"}]},
 {"lines": ["^^Diego Perez, a guard^^",
            "I **went** to the crime scene, and there **was** pieces of cake all over the painting. There was also a wheelchair **near** "
            "the painting, and I **find** a cake box **next to** the wheelchair. The box was **from** Camila’s Bakery."],
  "errors": [{"wrong": "was", "right": "were", "reason": "there + be 뒤의 주어 pieces 가 복수"},
             {"wrong": "find", "right": "found", "reason": "지난 일 — find 의 과거형 found"}]},
 {"lines": ["^^Camila Santos, the owner of Camila’s Bakery^^",
            "Last Friday, a young man came in. I spoke to **he** in Spanish, but he **didn’t understand** me. He spoke only English. "
            "We had a lot of different **cake**, but he just wanted the smallest one. We sold only one cake that day, so I remember him "
            "**clear**. Oh, he **had** blue eyes.",
            "Now, **looks** at the information about the suspects. Who threw the cake at the Monalisa?"],
  "errors": [{"wrong": "he", "right": "him", "reason": "전치사 to 뒤는 목적격"},
             {"wrong": "cake", "right": "cakes", "reason": "a lot of different + 셀 수 있는 명사 복수"},
             {"wrong": "clear", "right": "clearly", "reason": "동사 remember 를 꾸미는 부사"},
             {"wrong": "looks", "right": "look", "reason": "명령문은 동사원형으로 시작"}]},
]

WS7 = [
 "Last Saturday, (a cake / someone / throw) (in the Botero Museum / at the Monalisa) in Bogota, Colombia.",
 "(four eyewitnesses / there / be). (say / they / what / do)?",
 "(the following / read), and (the criminal / find).",
 "Ann Jones, a visitor: (at the Monalisa / I / look), and (a cake / throw / someone) (the painting / at).",
 "(around / I / turn) and (an old man / see).",
 "(stand / he) (a wheelchair / in front of).",
 "(about 170 cm / I’m / tall), and (taller / he / a little / be) (me / than).",
 "Carlos Diaz, a janitor: (with gray hair / an old man / run / away), and (his head / off / fall / something).",
 "(his wig / be / it).",
 "(him / run / after / I), but (him / can’t / catch / I).",
 "(faster / be / he) (me / than).",
 "In fact, (not / be / old / the old man).",
 "(a young man / be / he) (long brown hair / with).",
 "Diego Perez, a guard: (the crime scene / go / to / I), and (pieces of cake / there / be) (the painting / all over).",
 "(also / a wheelchair / be / there) (the painting / near), and (a cake box / find / I) (the wheelchair / next to).",
 "(be / the box) (Camila’s Bakery / from).",
 "Camila Santos, the owner of Camila’s Bakery: Last Friday, (in / come / a young man).",
 "(him / speak / I / to) (Spanish / in), but (understand / me / don’t / he). (only English / speak / he).",
 "(a lot of / we / have / different cakes), but (want / he / just) (one / the smallest).",
 "(one cake / sell / only / we) (day / that), so (clearly / him / I / remember).",
 "Oh, (blue eyes / have / he).",
 "Now, (the information / look at) (the suspects / about).",
 "(throw / who) (the cake / at the Monalisa)?",
]

WS8_SRC = [  # <…> 가 영작 칸이 된다. <> 를 지우면 원문과 같아야 한다
 (["throw", "cake", "museum"], "Last Saturday, <someone threw a cake at the Monalisa in the Botero Museum in Bogota, Colombia>."),
 (["there", "eyewitness", "say"], "<There were four eyewitnesses>. <What did they say>?"),
 (["read", "following", "criminal"], "<Read the following, and find the criminal>."),
 (["look at", "throw", "painting"], "Ann Jones, a visitor: <I was looking at the Monalisa>, and <someone threw a cake at the painting>."),
 (["turn around", "see", "old man"], "<I turned around and saw an old man>."),
 (["stand", "in front of", "wheelchair"], "<He was standing in front of a wheelchair>."),
 (["about", "tall", "a little", "than"], "<I’m about 170 cm tall>, and <he was a little taller than me>."),
 (["gray hair", "run away", "fall off"], "Carlos Diaz, a janitor: <An old man with gray hair was running away>, and <something fell off his head>."),
 (["it", "wig"], "<It was his wig>."),
 (["run after", "can", "catch"], "<I ran after him>, but <I couldn’t catch him>."),
 (["fast", "than"], "<He was faster than me>."),
 (["in fact", "old"], "<In fact, the old man was not old>."),
 (["young", "with", "brown hair"], "<He was a young man with long brown hair>."),
 (["crime scene", "pieces", "all over"], "Diego Perez, a guard: <I went to the crime scene>, and <there were pieces of cake all over the painting>."),
 (["also", "near", "find", "next to"], "<There was also a wheelchair near the painting>, and <I found a cake box next to the wheelchair>."),
 (["box", "from", "bakery"], "<The box was from Camila’s Bakery>."),
 (["last", "come in"], "Camila Santos, the owner of Camila’s Bakery: <Last Friday, a young man came in>."),
 (["speak", "Spanish", "understand", "only"], "<I spoke to him in Spanish>, but <he didn’t understand me>. <He spoke only English>."),
 (["different", "just", "want", "smallest"], "<We had a lot of different cakes>, but <he just wanted the smallest one>."),
 (["sell", "only", "remember", "clearly"], "<We sold only one cake that day>, so <I remember him clearly>."),
 (["have", "blue eyes"], "Oh, <he had blue eyes>."),
 (["look at", "information", "suspect"], "Now, <look at the information about the suspects>."),
 (["who", "throw"], "<Who threw the cake at the Monalisa>?"),
]
for (en, _), (_, src) in zip(S, WS8_SRC):
    assert src.replace("<", "").replace(">", "") == en, src
WS8 = [(k, re.sub(r"<(.+?)>", lambda m: "{{#%d}}" % len(m.group(1).split()), src)) for k, src in WS8_SRC]

HERE = os.path.dirname(os.path.abspath(__file__))
build(os.path.join(HERE, "영일중1_L5_본문.json"), "Lesson 5 Think like Sherlock Holmes!", "영일중", "1학년",
      S, PREP, WS1, WS2, WS4, WS5, WS6, WS7, WS8)
