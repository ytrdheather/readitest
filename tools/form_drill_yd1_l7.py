# -*- coding: utf-8 -*-
"""
영덕중1 7과 어법 **보충** 드릴의 문항 — make_form_drill.py 가 읽는다 (--unit 영덕중1L7).

원장 2026-11-12 「보충 드릴 만들기」. 범위는 영덕중1 L7 학습지
(data/stage0/comparisons/중1_영덕_L7_학습지.md §3)다. 학교가 교과서보다 넓게 가르쳤다:
to부정사 부사 역할이 목적 + 원인 · 결과 · 형용사 수식, 6과 명사 역할과 쓰임 구별 (Exercise A 4·5·7번),
의문사 when vs 접속사 when (Exercise B 7번), 시간 부사절의 현재시제 (B 6·8번).
본문 태그로 만든 어법 드릴은 본문에 있는 목적 · when · after 만 묻는다.

문장은 학습지 · 특급기출 예문 · 교과서 본문에서 가져오거나 같은 틀로 새로 썼다.
자료 꼴은 form_drill_l7.py 와 같다 (kind build / fill / fix · mix).
"""

P, C, R, A = "목적 (~하기 위해)", "원인 (~해서)", "결과 (~해서 …하다)", "형용사 수식 (~하기에)"
USE = [
    ("We recycle 【to reduce】 waste.", P),
    ("I got up early 【to prepare】 breakfast.", P),
    ("She went to the store 【to buy】 some milk.", P),
    ("【To stay】 healthy, he exercises every day.", P),
    ("I use hand signals 【to calm】 the dog.", P),
    ("He is saving money 【to buy】 a skateboard.", P),
    ("【To capture】 their happy moments, I'm going to use drones.", P),
    ("Jenny ran fast 【to catch】 the train.", P),
    ("We went to the library 【to borrow】 some books.", P),
    ("I turned on the light 【to see】 better.", P),
    ("A lot of people are working hard 【to create】 this movie.", P),
    ("She wore a helmet 【to protect】 herself.", P),
    ("I'm so glad 【to meet】 you.", C),
    ("They were excited 【to see】 the singer in person.", C),
    ("She was happy 【to see】 her friends.", C),
    ("He was sad 【to hear】 the news.", C),
    ("I was surprised 【to find】 the door open.", C),
    ("She was disappointed 【to lose】 the game.", C),
    ("We are sorry 【to hear】 that.", C),
    ("He was pleased 【to get】 a new tablet.", C),
    ("The boy grew up 【to be】 a great musician.", R),
    ("Greg lived 【to be】 ninety.", R),
    ("She grew up 【to be】 a world-famous chef.", R),
    ("My grandmother lived 【to be】 a hundred.", R),
    ("The quiz is fun 【to solve】.", A),
    ("The question was difficult 【to answer】.", A),
    ("This book is easy 【to read】.", A),
    ("The smartphone is expensive 【to buy】.", A),
    ("This river is dangerous 【to swim】 in.", A),
    ("English is not hard 【to learn】.", A),
]

NS, NO, NC = "명사 · 주어 (~하는 것은)", "명사 · 목적어 (~하는 것을)", "명사 · 보어 (~하는 것이다)"
AJ = "형용사 · 앞의 명사를 꾸민다 (~할)"
ROLE = [
    ("I want 【to be】 a sports reporter.", NO),
    ("My job is 【to find】 perfect places for shooting.", NC),
    ("I like 【to travel】.", NO),
    ("【To sleep】 well is important.", NS),
    ("She hopes 【to travel】 the world.", NO),
    ("My dream is 【to help】 children in Africa.", NC),
    ("They decided 【to clean】 the room.", NO),
    ("【To watch】 dramas is fun.", NS),
    ("He doesn't like 【to wake】 up early.", NO),
    ("Our plan is 【to go】 on a trip next summer.", NC),
    ("We need 【to save】 water.", NO),
    ("What do you want 【to do】 after school?", NO),
    ("I have something 【to tell】 you.", AJ),
    ("Do you have a lot of work 【to do】?", AJ),
    ("I need a book 【to read】 on the train.", AJ),
    ("She has no time 【to play】 games.", AJ),
    ("Give me something 【to drink】, please.", AJ),
    ("He has many friends 【to help】 him.", AJ),
    ("We studied hard 【to get】 good grades.", "부사 · 목적"),
    ("He was glad 【to join】 the team.", "부사 · 원인"),
    ("They went to the park 【to walk】 their dog.", "부사 · 목적"),
    ("I stopped working 【to have】 lunch.", "부사 · 목적"),
    ("What should I do 【to improve】 my English?", "부사 · 목적"),
    ("She was very happy 【to see】 her friends.", "부사 · 원인"),
    ("The boy grew up 【to be】 a great scientist.", "부사 · 결과"),
    ("【To create】 a better story, I can change the order of scenes.", "부사 · 목적"),
    ("She came home early 【to see】 her children.", "부사 · 목적"),
    ("We left early 【to avoid】 traffic.", "부사 · 목적"),
    ("This math problem is easy 【to solve】.", "부사 · 형용사 수식"),
    ("He went to the gym 【to exercise】 for an hour.", "부사 · 목적"),
]

Q, J = "의문사 (언제)", "접속사 (~할 때)"
WHEN = [
    ("【When】 did she first meet him?", Q),
    ("【When】 will you be back home?", Q),
    ("【When】 do you usually have dinner?", Q),
    ("【When】 did you hear that he was sick?", Q),
    ("【When】 is your birthday?", Q),
    ("【When】 does the movie start?", Q),
    ("【When】 are you going to shoot the movie?", Q),
    ("【When】 can we meet again?", Q),
    ("【When】 did they arrive at the beach?", Q),
    ("【When】 do you do your homework?", Q),
    ("【When】 he opened the gift, he was surprised.", J),
    ("【When】 I feel tired, I take a nap.", J),
    ("I listen to music 【when】 I'm free.", J),
    ("Max gets too excited 【when】 a lot of people are around.", J),
    ("He loved chocolate 【when】 he was a child.", J),
    ("【When】 he heard the news, he was very excited.", J),
    ("She called me 【when】 she needed help.", J),
    ("I create sound effects in my studio 【when】 recording on location is not easy.", J),
    ("【When】 it rains, don't forget your umbrella.", J),
    ("Did you call me 【when】 I was sleeping?", J),
]

CONJ = [
    ("She smiles ___ she sees her friends. (친구들을 볼 때)", "when"),
    ("She cleaned the kitchen ___ she baked cookies. (쿠키를 구운 후에)", "after"),
    ("We turned off the lights ___ we left. (떠나기 전에)", "before"),
    ("___ I feel tired, I take a nap. (피곤할 때)", "When"),
    ("I read a book ___ I go to bed. (자기 전에)", "before"),
    ("___ Kevin did his homework, he played outside. (숙제를 한 후에)", "After"),
    ("You need to warm up ___ you swim. (수영하기 전에)", "before"),
    ("She called me ___ she needed help. (도움이 필요했을 때)", "when"),
    ("___ he finished his homework, he played a mobile game. (숙제를 끝낸 뒤에)", "After"),
    ("My work begins ___ the shooting is over. (촬영이 끝난 뒤에)", "after"),
    ("___ you leave, close all the windows. (떠나기 전에)", "Before"),
    ("He got better ___ he took the medicine. (약을 먹은 후에)", "after"),
    ("You should be careful ___ you cross the street. (길을 건널 때)", "when"),
    ("Wash your hands ___ you eat. (먹기 전에)", "before"),
    ("___ we saw the cat, it ran away. (고양이를 봤을 때)", "When"),
    ("Let's go out ___ it stops raining. (비가 그친 후에)", "after"),
    ("Brush your teeth ___ you go to bed. (잠자리에 들기 전에)", "before"),
    ("He paints pictures ___ he has free time. (시간이 날 때)", "when"),
    ("___ the game ended, everyone went home. (경기가 끝난 후에)", "After"),
    ("Where did you live ___ you moved here? (이곳으로 이사 오기 전에)", "before"),
]

FIX = [
    ("I'll text you when I 【will finish】 my homework.", "finish"),
    ("When Amy 【will arrive】, we will have dinner.", "arrives"),
    ("After school 【will be】 over, I'll go to the gym.", "is"),
    ("Before I 【will go】 home, I will check my homework.", "go"),
    ("We will start the game after he 【will come】.", "comes"),
    ("Before she 【will cook】 dinner, she will wash the vegetables.", "cooks"),
    ("I will call you when the movie 【will end】.", "ends"),
    ("After it 【will stop】 raining, we will go out.", "stops"),
    ("They went there 【to playing】 soccer.", "to play"),
    ("She went to the library 【borrow】 some books.", "to borrow"),
    ("I was happy 【to met】 my old friend.", "to meet"),
    ("He ran fast 【for catch】 the ball.", "to catch"),
    ("【Stay】 healthy, she does yoga every day.", "To stay"),
    ("We saved money 【to went】 on a trip.", "to go"),
    ("The quiz is fun 【to solves】.", "to solve"),
    ("After I finish my homework, I 【will play】 computer games.", "O"),
    ("When she 【comes】 back, I will tell her the news.", "O"),
    ("I'll lend you this book after I 【finish】 it.", "O"),
    ("He took a shower before he 【went】 to bed.", "O"),
    ("When I 【hear】 that song, I feel happy.", "O"),
    ("Before their guests 【arrived】, they cleaned the house.", "O"),
    ("She 【will wash】 the vegetables before she cooks dinner.", "O"),
    ("We will have a party when Dad 【gets】 home.", "O"),
    ("I hurried 【not to be】 late for my class.", "O"),
    ("She was excited 【to see】 the concert.", "O"),
    ("【To learn】 more, I ask questions.", "O"),
    ("He left early 【to get】 good seats.", "O"),
    ("Greg lived 【to be】 ninety.", "O"),
    ("After the class 【is】 over, we will eat lunch.", "O"),
    ("I use my smartphone 【to take】 pictures.", "O"),
]

BUILD = [
    ("I eat lunch. Then I take two more classes.", "한 문장으로 · After 로 시작", "After I eat lunch, I take two more classes."),
    ("I do my homework. Then I eat dinner.", "한 문장으로 · before 를 가운데에", "I do my homework before I eat dinner."),
    ("I had breakfast, and then I started studying.", "After 로 시작", "After I had breakfast, I started studying."),
    ("He was a child. He loved chocolate then.", "한 문장으로 · When 으로 시작", "When he was a child, he loved chocolate."),
    ("She washed her hands. Then she ate dinner.", "한 문장으로 · Before 로 시작", "Before she ate dinner, she washed her hands."),
    ("I feel tired. I take a nap then.", "한 문장으로 · when 을 가운데에", "I take a nap when I feel tired."),
    ("The game ended. Then everyone went home.", "한 문장으로 · after 를 가운데에", "Everyone went home after the game ended."),
    ("He closed the door. Then he went out.", "한 문장으로 · Before 로 시작", "Before he went out, he closed the door."),
    ("I went to the bakery. I wanted to get some bread.", "한 문장으로 · to부정사", "I went to the bakery to get some bread."),
    ("They are going to the gym. They will exercise for an hour.", "한 문장으로 · to부정사", "They are going to the gym to exercise for an hour."),
    ("She saved money. She wanted to buy a new bike.", "한 문장으로 · to부정사", "She saved money to buy a new bike."),
    ("We want to reduce waste, so we recycle.", "to부정사 · We recycle 로 시작", "We recycle to reduce waste."),
    ("그는 아이들을 보기 위해 집에 일찍 왔다.", "come home early, see his kids", "He came home early to see his kids."),
    ("나는 사진을 찍기 위해 스마트폰을 사용한다.", "use my smartphone, take pictures", "I use my smartphone to take pictures."),
    ("건강을 유지하기 위해 그녀는 매일 요가를 한다.", "To 로 시작 · stay healthy, do yoga", "To stay healthy, she does yoga every day."),
    ("나는 숙제를 끝낼 때 너한테 문자 할게.", "will text, when, finish", "I'll text you when I finish my homework."),
    ("밖에 나가기 전에 네 방을 청소해라.", "clean, before, go out", "Clean your room before you go out."),
    ("그녀는 저녁을 요리하기 전에 채소를 씻을 것이다.", "Before 로 시작 · cook, will wash", "Before she cooks dinner, she will wash the vegetables."),
    ("그들은 그 책을 읽은 후에 독후감을 써야 한다.", "should write a book report, after, read", "They should write a book report after they read the book."),
    ("당신을 만나서 정말 기뻐요.", "so glad, meet", "I'm so glad to meet you."),
]

SECTIONS = [
    {"key": "use", "kind": "fix", "per": 15, "diag": 2, "items": USE, "mix": ["목적", "원인", "결과", "형용사"],
     "head": "밑줄 친 to부정사(부사 역할)의 뜻이 목적 · 원인 · 결과 · 형용사 수식 중 무엇인지 쓰시오",
     "rule": "<b>목적</b> ~하기 위해 (문장 앞에도 온다: To stay healthy, …) / <b>원인</b> 감정 형용사(glad · happy · sad · excited · "
             "surprised · sorry) 뒤, ~해서 / <b>결과</b> grow up · live 뒤, ~해서 …하다 / "
             "<b>형용사 수식</b> easy · hard · difficult · fun · dangerous 뒤, ~하기에"},
    {"key": "role", "kind": "fix", "per": 15, "diag": 2, "items": ROLE, "mix": ["명사", "형용사", "부사"],
     "head": "밑줄 친 to부정사가 명사 · 형용사 · 부사 역할 중 무엇인지 쓰시오",
     "rule": "<b>명사</b> 주어 · 목적어(want · hope · like · decide · need 뒤) · 보어(be동사 뒤) 자리, ~하는 것 / "
             "<b>형용사</b> 명사 바로 뒤에서 꾸민다, ~할 (something to tell) / "
             "<b>부사</b> 빼도 문장이 된다, ~하기 위해 · ~해서 · ~하기에"},
    {"key": "when", "kind": "fix", "per": 10, "diag": 2, "items": WHEN, "mix": ["의문사", "접속사"],
     "head": "밑줄 친 when 이 의문사인지 접속사인지 쓰시오",
     "rule": "<b>의문사</b> 「언제」 — 뒤가 의문문 어순(did she · will you · is your)이고 문장이 하나 / "
             "<b>접속사</b> 「~할 때」 — 뒤가 <b>주어 + 동사</b>이고 문장(절)이 둘. 물음표로 끝나도 접속사일 수 있다."},
    {"key": "conj", "kind": "fill", "per": 10, "diag": 2, "items": CONJ,
     "head": "괄호 안의 우리말에 맞게 when · before · after 중 알맞은 말을 쓰시오",
     "rule": "<b>when</b> ~할 때 · <b>before</b> ~하기 전에 · <b>after</b> ~한 후에. 뒤에 <b>주어 + 동사</b>가 온다. "
             "부사절이 문장 앞에 오면 끝에 <b>콤마(,)</b> — 문장 첫 글자는 대문자로 쓴다."},
    {"key": "fix", "kind": "fix", "per": 15, "diag": 2, "items": FIX, "mix": "OX",
     "head": "밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오",
     "rule": "시간의 부사절(when · before · after 가 이끄는 절)은 뜻이 미래여도 <b>현재시제</b> — will 을 쓰지 않는다 "
             "(주어가 3인칭 단수면 -s). <b>주절</b>은 will 그대로. to부정사는 <b>to + 동사원형</b>, 부정은 not to."},
    {"key": "build", "kind": "build", "per": 10, "diag": 2, "items": BUILD,
     "head": "괄호 안의 지시 · 주어진 말에 따라 한 문장으로 쓰시오",
     "rule": "주어진 말은 알맞은 형태로 바꾼다. 부사절이 앞이면 <b>콤마</b>. 먼저 일어난 일에 <b>after</b>, 나중 일에 <b>before</b>. "
             "목적은 <b>to + 동사원형</b>. 미래의 일이어도 when · before · after 절 안은 현재시제."},
]
