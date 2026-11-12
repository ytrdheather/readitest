# -*- coding: utf-8 -*-
"""
청명중1 5과(비상 황종배) 어법 **보충** 드릴의 문항 — make_form_drill.py 가 읽는다 (--unit 청명중1L5).

원장 2026-11-12 「형태 드릴 만들기」. 범위는 청명중1 이성규 L5 학습지 6~11쪽
(data/stage0/comparisons/중1_청명_L5_학습지.md §5):
  Grammar 1 동명사 — 주어 · 보어 · 목적어(동사 · 전치사), 동명사만 / to부정사만 / 둘 다 목적어로 쓰는 동사
  Grammar 2 감각동사 + 형용사 — 부사 X, look like + 명사, -ly 로 끝나는 형용사(friendly · lovely · costly · lonely),
            감각동사 look 과 일반동사 look(at · around) 구별
본문 태그로 만든 어법 드릴은 본문에 있는 enjoyed playing · Making a game · looked real 만 묻는다.

문장은 학습지 · 비상 자습서 예문 · 교과서 본문에서 가져오거나 같은 틀로 새로 썼다.
자료 꼴은 form_drill_yd1_l7.py 와 같다 (kind build / fill / fix · mix).
"""

S, C, O, PR = "주어 (~하는 것은)", "보어 (~하는 것이다)", "동사의 목적어 (~하는 것을)", "전치사의 목적어"
ROLE = [
    ("【Making】 a game was hard, but we did it together.", S),
    ("【Riding】 a bike is exciting.", S),
    ("【Drawing】 cartoons is my hobby.", S),
    ("【Reading】 books makes me happy.", S),
    ("【Playing】 the piano is not easy.", S),
    ("【Watching】 movies is fun.", S),
    ("【Learning】 English is important.", S),
    ("【Swimming】 in the sea is dangerous.", S),
    ("My goal is 【speaking】 English well.", C),
    ("My hobby is 【taking】 pictures.", C),
    ("Her job is 【teaching】 children.", C),
    ("John's hobby is 【listening】 to music.", C),
    ("My dream is 【traveling】 around the world.", C),
    ("His plan is 【making】 a new game.", C),
    ("The best part is 【playing】 with my friends.", C),
    ("Her favorite activity is 【dancing】.", C),
    ("I enjoyed 【playing】 the game.", O),
    ("Most people enjoy 【playing】 games.", O),
    ("Maria finished 【cleaning】 her room.", O),
    ("I avoided 【answering】 the question.", O),
    ("James enjoys 【operating】 machines.", O),
    ("He gave up 【eating】 fast food.", O),
    ("Do you mind 【opening】 the window?", O),
    ("She kept 【talking】 about her trip.", O),
    ("I'm good at 【drawing】 cartoons.", PR),
    ("She is interested in 【making】 robots.", PR),
    ("Thank you for 【helping】 me.", PR),
    ("He left without 【saying】 goodbye.", PR),
    ("How about 【going】 to the bookstore?", PR),
    ("I'm not good at 【playing】 games.", PR),
]

# (문장, 답) — 둘 다 되는 동사는 「playing / to play」 처럼 둘 다 써야 정답
VERB = [
    ("I enjoy ___ soccer. (play)", "playing"),
    ("She finished ___ her homework. (do)", "doing"),
    ("He avoided ___ the question. (answer)", "answering"),
    ("Do you mind ___ the door? (close)", "closing"),
    ("They kept ___ for an hour. (talk)", "talking"),
    ("He gave up ___ the piano. (learn)", "learning"),
    ("She practiced ___ the guitar after school. (play)", "playing"),
    ("She denied ___ the cookies. (eat)", "eating"),
    ("I quit ___ fast food. (eat)", "eating"),
    ("Sumin enjoyed ___ the game. (play)", "playing"),
    ("I practice ___ English every day. (speak)", "speaking"),
    ("Jay doesn't enjoy ___ novels. (read)", "reading"),
    ("I want ___ a game maker. (be)", "to be"),
    ("She hopes ___ her friends soon. (see)", "to see"),
    ("We decided ___ a game together. (make)", "to make"),
    ("He plans ___ to Jeju next month. (go)", "to go"),
    ("They promised ___ me. (help)", "to help"),
    ("James wants ___ an engineer in the future. (be)", "to be"),
    ("I expect ___ a lot of reviews. (get)", "to get"),
    ("She refused ___ the answer. (tell)", "to tell"),
    ("He wishes ___ a famous musician. (become)", "to become"),
    ("We need ___ one more stage. (add)", "to add"),
    ("It began ___ cats and dogs. (rain)", "raining / to rain"),
    ("I like ___ books about robots. (read)", "reading / to read"),
    ("She started ___ a story. (write)", "writing / to write"),
    ("They love ___ in the park. (walk)", "walking / to walk"),
    ("He hates ___ early. (get up)", "getting up / to get up"),
    ("We continued ___ the game. (play)", "playing / to play"),
    ("Minwoo began ___ the game. (code)", "coding / to code"),
    ("I like ___ VR games. (play)", "playing / to play"),
]

SENSE = [
    ("The story sounds 【strangely】.", "strange"),
    ("The lemon tastes 【sourly】.", "sour"),
    ("Your puppy looks 【cutely】.", "cute"),
    ("You look 【happily】.", "happy"),
    ("The flower smells 【well】.", "good"),
    ("The cake tastes 【sweetly】.", "sweet"),
    ("This sweater feels 【softly】.", "soft"),
    ("That roller coaster looks 【dangerously】.", "dangerous"),
    ("The moon looks 【brightly】 tonight.", "bright"),
    ("Every character looked 【really】.", "real"),
    ("Our game looked and sounded 【well】.", "good"),
    ("The soup smells 【badly】.", "bad"),
    ("My new teacher looks warm and 【friend】.", "friendly"),
    ("The song sounds 【a lullaby】.", "like a lullaby"),
    ("It feels 【a dream】.", "like a dream"),
    ("You look 【like tired】.", "tired"),
    ("The cloud looks 【a rabbit】.", "like a rabbit"),
    ("This chocolate 【tastes smoothly】.", "tastes smooth"),
    ("The music 【sounds loudly】.", "sounds loud"),
    ("Now our game 【looked greatly】.", "looked great"),
    ("The cookies 【taste】 sweet.", "O"),
    ("This doll feels 【soft】.", "O"),
    ("These shoes look 【new】.", "O"),
    ("It smelled 【terrible】.", "O"),
    ("This stone feels 【hard】.", "O"),
    ("That 【sounds like】 a good idea.", "O"),
    ("She looks 【lovely】 in that dress.", "O"),
    ("The man looks 【friendly】.", "O"),
    ("He 【looks like】 a doctor.", "O"),
    ("The weather 【feels】 warm.", "O"),
]

ADJ, ADV = "형용사 (명사 + -ly)", "부사 (형용사 + -ly)"
LY = [
    ("Lisa is a 【friendly】 girl.", ADJ),
    ("What a 【lovely】 day!", ADJ),
    ("He felt 【lonely】 at the new school.", ADJ),
    ("The bag was very 【costly】.", ADJ),
    ("Thank you for your 【timely】 help.", ADJ),
    ("She has a 【lovely】 smile.", ADJ),
    ("The old man lives a 【lonely】 life.", ADJ),
    ("My neighbors are very 【friendly】.", ADJ),
    ("It was a 【costly】 mistake.", ADJ),
    ("The cat looks 【lovely】.", ADJ),
    ("He ran 【quickly】 to the bus stop.", ADV),
    ("She sang 【softly】.", ADV),
    ("He solved the problem 【easily】.", ADV),
    ("Don't talk 【loudly】 in the library.", ADV),
    ("The boy looked at me 【sadly】.", ADV),
    ("We 【finally】 published the game.", ADV),
    ("I'm 【really】 interested in robots.", ADV),
    ("The turtle walked 【slowly】.", ADV),
    ("She smiled 【happily】.", ADV),
    ("They worked 【quietly】.", ADV),
]

LOOK_S, LOOK_V = "감각동사 (~하게 보이다)", "일반동사 (보다)"
LOOK = [
    ("The children 【looked】 happy at that time.", LOOK_S),
    ("Stella 【looks】 different from others.", LOOK_S),
    ("Every character 【looked】 real.", LOOK_S),
    ("The game maker's section 【looks】 interesting.", LOOK_S),
    ("You 【look】 tired today.", LOOK_S),
    ("Now our game 【looked】 great.", LOOK_S),
    ("That roller coaster 【looks】 dangerous.", LOOK_S),
    ("These shoes 【look】 new.", LOOK_S),
    ("My new teacher 【looks】 warm and friendly.", LOOK_S),
    ("The sky 【looks】 dark.", LOOK_S),
    ("Please 【look】 closely.", LOOK_V),
    ("You should 【look】 over there now.", LOOK_V),
    ("【Look】 at the crowd on the playground.", LOOK_V),
    ("I 【looked】 around the city with my family.", LOOK_V),
    ("【Look】 at that.", LOOK_V),
    ("She 【looked】 at the stars.", LOOK_V),
    ("We 【looked】 for my lost cat.", LOOK_V),
    ("He 【looked】 out the window.", LOOK_V),
    ("【Look】. People are playing a new game over there.", LOOK_V),
    ("They 【looked】 at the map.", LOOK_V),
]

GFIX = [
    ("【Make】 a game was hard.", "Making"),
    ("I enjoyed 【to play】 the game.", "playing"),
    ("She finished 【clean】 her room.", "cleaning"),
    ("I'm good at 【draw】 cartoons.", "drawing"),
    ("I want 【being】 a game maker.", "to be"),
    ("Playing games 【are】 fun.", "is"),
    ("He avoided 【to answer】 the question.", "answering"),
    ("We decided 【making】 a game.", "to make"),
    ("Do you mind 【open】 the window?", "opening"),
    ("She is interested in 【make】 robots.", "making"),
    ("My hobby is 【take】 pictures.", "taking"),
    ("He gave up 【to eat】 fast food.", "eating"),
    ("They hope 【winning】 the game.", "to win"),
    ("【Read】 books is my hobby.", "Reading"),
    ("【Making】 a game was hard.", "O"),
    ("She likes 【to read】 comic books.", "O"),
    ("It began 【raining】.", "O"),
    ("Thank you for 【helping】 me.", "O"),
    ("My goal is 【to speak】 English well.", "O"),
    ("Riding a bike 【is】 exciting.", "O"),
]

BUILD = [
    ("게임을 만드는 것은 힘들었다.", "make, a game, hard", "Making a game was hard."),
    ("자전거를 타는 것은 신난다.", "ride, a bike, exciting", "Riding a bike is exciting."),
    ("나는 그 게임을 하는 것을 즐겼다.", "enjoy, play, the game", "I enjoyed playing the game."),
    ("그녀는 방 청소하는 것을 끝냈다.", "finish, clean, her room", "She finished cleaning her room."),
    ("나는 만화를 잘 그린다.", "be good at, draw, cartoons", "I'm good at drawing cartoons."),
    ("내 취미는 사진을 찍는 것이다.", "hobby, take, pictures", "My hobby is taking pictures."),
    ("나는 미래에 게임 제작자가 되고 싶다.", "want, be, a game maker, in the future", "I want to be a game maker in the future."),
    ("수진은 로봇을 만드는 것에 관심이 있다.", "Sujin, be interested in, make", "Sujin is interested in making robots."),
    ("영어를 배우는 것은 중요하다.", "learn, English, important", "Learning English is important."),
    ("비가 오기 시작했다. (동명사로)", "begin, rain", "It began raining."),
    ("모든 캐릭터는 진짜처럼 보였다.", "every, character, look, real", "Every character looked real."),
    ("그 꽃은 좋은 냄새가 난다.", "the flower, smell, good", "The flower smells good."),
    ("이 과일은 달콤한 맛이 난다.", "this fruit, taste, sweet", "This fruit tastes sweet."),
    ("날씨가 따뜻하게 느껴진다.", "the weather, feel, warm", "The weather feels warm."),
    ("그 드레스는 아름다워 보인다.", "the dress, look, beautiful", "The dress looks beautiful."),
    ("그 노래는 자장가처럼 들린다.", "the song, sound, a lullaby", "The song sounds like a lullaby."),
    ("그것은 꿈처럼 느껴진다.", "it, feel, a dream", "It feels like a dream."),
    ("우리 게임은 좋게 보였고 좋게 들렸다.", "our game, look, sound, good", "Our game looked and sounded good."),
    ("그 이야기는 이상하게 들린다.", "the story, sound, strange", "The story sounds strange."),
    ("나의 새 선생님은 따뜻하고 친절해 보이신다.", "my new teacher, look, warm, friendly", "My new teacher looks warm and friendly."),
]

SECTIONS = [
    {"key": "role", "kind": "fix", "per": 15, "diag": 2, "items": ROLE, "mix": ["주어", "보어", "동사의", "전치사"],
     "head": "밑줄 친 동명사가 주어 · 보어 · 동사의 목적어 · 전치사의 목적어 중 무엇인지 쓰시오",
     "rule": "동명사 = <b>동사원형 + -ing</b>, 「~하기 · ~하는 것」. <b>주어</b> 문장 맨 앞, <b>단수</b> 취급(Making a game <b>was</b>) / "
             "<b>보어</b> be동사 뒤 (My goal is speaking …) / <b>동사의 목적어</b> enjoy · finish · avoid · mind · keep · give up 뒤 / "
             "<b>전치사의 목적어</b> at · in · for · about · without 뒤 — 전치사 뒤에는 to부정사를 못 쓴다."},
    {"key": "verb", "kind": "fill", "per": 15, "diag": 2, "items": VERB,
     "head": "괄호 안의 동사를 알맞은 형태로 쓰시오 (둘 다 되면 둘 다 쓰시오)",
     "rule": "<b>동명사만</b> enjoy · finish · avoid · keep · deny · mind · quit · stop · give up · practice / "
             "<b>to부정사만</b> want · wish · hope · expect · decide · plan · promise · refuse · need / "
             "<b>둘 다</b> begin · start · continue · hate · love · like"},
    {"key": "gfix", "kind": "fix", "per": 10, "diag": 2, "items": GFIX, "mix": "OX",
     "head": "밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오 (동명사 · to부정사)",
     "rule": "주어 자리 동사원형 ✕ → <b>-ing</b> 또는 To ~ · 동명사 주어는 <b>단수 동사</b> · 전치사 뒤는 <b>-ing</b> · "
             "enjoy · finish · avoid · mind · give up 뒤 -ing / want · hope · decide 뒤 to + 동사원형"},
    {"key": "sense", "kind": "fix", "per": 15, "diag": 2, "items": SENSE, "mix": "OX",
     "head": "밑줄 친 부분이 맞으면 O, 틀리면 고쳐 쓰시오 (감각동사)",
     "rule": "감각동사 look · sound · smell · taste · feel 뒤에는 <b>형용사</b> — 「~하게」 로 해석돼도 부사(-ly)를 쓰지 않는다 "
             "(look happily ✕ · smell well ✕ → smell good). 뒤에 <b>명사</b>가 오면 <b>like</b> + 명사 (sounds like a lullaby). "
             "like 뒤에 형용사는 ✕ (look like tired ✕)."},
    {"key": "ly", "kind": "fix", "per": 10, "diag": 2, "items": LY, "mix": ["형용사", "부사"],
     "head": "밑줄 친 -ly 단어가 형용사인지 부사인지 쓰시오",
     "rule": "<b>형용사 + -ly = 부사</b> quickly · sadly · softly · easily · loudly · finally · really / "
             "<b>명사 + -ly = 형용사</b> friendly · lovely · lonely · costly · timely — 감각동사 뒤에 올 수 있다 (looks friendly)."},
    {"key": "look", "kind": "fix", "per": 10, "diag": 2, "items": LOOK, "mix": ["감각", "일반"],
     "head": "밑줄 친 look 이 감각동사(~하게 보이다)인지 일반동사(보다)인지 쓰시오",
     "rule": "<b>감각동사</b> 뒤에 <b>형용사</b>가 와서 주어의 상태를 말한다 (looked happy) / "
             "<b>일반동사</b> look at · look around · look for · look out, 혹은 뒤에 부사(closely · over there) — 「보다」."},
    {"key": "build", "kind": "build", "per": 10, "diag": 2, "items": BUILD,
     "head": "우리말과 같도록 주어진 말을 이용해 영어로 쓰시오",
     "rule": "주어진 말은 알맞은 형태로 바꾼다. 동명사 주어는 <b>단수 동사</b>. 감각동사 뒤 <b>형용사</b>, 명사면 <b>like</b> + 명사. "
             "시제는 우리말을 따른다."},
]
