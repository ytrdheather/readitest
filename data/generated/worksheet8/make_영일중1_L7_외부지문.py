# -*- coding: utf-8 -*-
"""
영일중1 7과 **외부지문** 워크시트 데이터 (mid-eng-worksheet-8set) — 2026-10-26. 6과 외부지문과 같은 방식.

  원문   data/stage0/passages/영일중1_L7_외부지문_TwoDifferentJobs.json (확정본) — 19문장
         짧은 두 문장(Pilots must understand other people. / Artists must understand themselves.)을 한 문항으로 → 18문항
  해석   학습지에 우리말이 없어 Claude 가 썼다 (6과 외부지문과 같은 원장 승인 범위)
  단어   학습지가 주석을 단 낱말(glossed) 중 14개. 학교 영영풀이가 없어 풀이는 새로 썼다.
         lifestyle · artist 는 같은 어근(life · art)이 풀이에 들어가지 않게 썼다.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import build

S = [
 ("At a restaurant, Jane and Maria talked about their jobs.", "한 식당에서 Jane과 Maria는 그들의 직업에 대해 이야기했다."),
 ("They agreed that there are a few similarities.", "그들은 몇 가지 비슷한 점이 있다는 데 동의했다."),
 ("For both pilots and artists, there is a lot of competition and there are few famous women.", "조종사와 예술가 둘 다 경쟁이 심하고, 유명한 여성이 거의 없다."),
 ("In both jobs, you have to be very strong and sure of yourself.", "두 직업 모두에서 너는 매우 강해야 하고 자신에 대한 확신이 있어야 한다."),
 ("Of course, there are also many differences between the two jobs.", "물론, 두 직업 사이에는 차이점도 많다."),
 ("Pilots and artists have to be strong in different ways.", "조종사와 예술가는 서로 다른 방식으로 강해야 한다."),
 ("Pilots have to stay awake for long hours, and sometimes they have to make important decisions quickly.", "조종사는 오랜 시간 동안 깨어 있어야 하고, 때때로 중요한 결정을 빨리 내려야 한다."),
 ("Artists, however, have to be strong in their ideas about art and life.", "그러나 예술가는 예술과 삶에 대한 자신의 생각이 확고해야 한다."),
 ("People in the two jobs also work in different ways.", "두 직업의 사람들은 일하는 방식도 다르다."),
 ("Pilots usually work with other people, but artists usually work alone.", "조종사는 보통 다른 사람들과 함께 일하지만, 예술가는 보통 혼자 일한다."),
 ("Pilots must understand other people. Artists must understand themselves.", "조종사는 다른 사람들을 이해해야 한다. 예술가는 자기 자신을 이해해야 한다."),
 ("Finally, there is an important difference in lifestyle.", "마지막으로, 생활 방식에 중요한 차이가 있다."),
 ("Pilots travel for their job and are often away from home.", "조종사는 일 때문에 여행을 하고 자주 집을 떠나 있다."),
 ("Artists, however, work at home or in a studio near home.", "그러나 예술가는 집이나 집 근처의 작업실에서 일한다."),
 ("Also, unlike pilots, artists can start and stop working when they want.", "또한, 조종사와 달리 예술가는 원할 때 일을 시작하고 멈출 수 있다."),
 ("Maria said she could never be a pilot because she hates airplanes.", "Maria는 비행기를 싫어해서 절대 조종사는 될 수 없을 거라고 말했다."),
 ("Jane said she could never be an artist because she hates working alone.", "Jane은 혼자 일하는 것을 싫어해서 절대 예술가는 될 수 없을 거라고 말했다."),
 ("There are many things to think about when choosing a job, but what you enjoy should come first.", "직업을 고를 때 생각할 것이 많지만, 네가 즐기는 것이 가장 먼저 와야 한다."),
]

PREP = [
 ("agree", "v.", "동의하다", "to have the same opinion as someone",
  "I **agree** with your idea.", "나는 너의 생각에 동의해."),
 ("similarity", "n.", "비슷한 점, 유사점", "a way in which two things are like each other",
  "There is a **similarity** between the two songs.", "그 두 노래 사이에는 비슷한 점이 있다."),
 ("both A and B", "phr.", "A와 B 둘 다", "the first thing and the second thing together",
  "I like **both cats and dogs**.", "나는 고양이와 개 둘 다 좋아한다."),
 ("competition", "n.", "경쟁, 대회", "a situation in which people try to be more successful than others",
  "There is a lot of **competition** for the prize.", "그 상을 두고 경쟁이 치열하다."),
 ("different", "adj.", "다른", "not the same as something or someone",
  "My sister and I have **different** hobbies.", "언니와 나는 취미가 다르다."),
 ("difference", "n.", "차이(점)", "the way in which two things are not the same",
  "Can you see the **difference** in these two pictures?", "이 두 그림에서 차이점을 찾을 수 있니?"),
 ("stay awake", "phr.", "깨어 있다", "to not fall asleep",
  "I tried to **stay awake** during the long movie.", "나는 긴 영화를 보는 동안 깨어 있으려고 애썼다."),
 ("make a decision", "phr.", "결정을 내리다", "to choose what to do after thinking",
  "You need to **make a decision** by tomorrow.", "너는 내일까지 결정을 내려야 해."),
 ("however", "adv.", "그러나, 하지만", "used to add a fact that is not what you expect after what was said before",
  "The test was hard. **However**, I passed it.", "시험은 어려웠다. 하지만 나는 통과했다."),
 ("alone", "adv.", "혼자", "without any other people",
  "My grandfather lives **alone** in the country.", "할아버지는 시골에서 혼자 사신다."),
 ("lifestyle", "n.", "생활 방식", "the usual way a person spends days, works, and eats",
  "Eating vegetables is part of a healthy **lifestyle**.", "채소를 먹는 것은 건강한 생활 방식의 일부이다."),
 ("be away from", "phr.", "~에서 떨어져 있다, ~을 떠나 있다", "to not be at a place, such as your home, for some time",
  "My dad **is away from** home this week.", "아빠는 이번 주에 집을 떠나 계신다."),
 ("pilot", "n.", "조종사", "a person who flies an airplane",
  "The **pilot** spoke to the passengers before landing.", "조종사는 착륙 전에 승객들에게 말했다."),
 ("artist", "n.", "예술가, 화가", "a person who paints, draws, or makes beautiful things like sculptures",
  "The **artist** painted a picture of the sea.", "그 예술가는 바다 그림을 그렸다."),
]

WS1 = [
 ("At a restaurant, / Jane and Maria talked about their jobs.", "한 식당에서 / Jane과 Maria는 그들의 직업에 대해 이야기했다"),
 ("They agreed((동의하다)) / that there are a few similarities((비슷한 점)).", "그들은 동의했다 / 몇 가지 비슷한 점이 있다는 것에"),
 ("For both pilots and artists, / there is a lot of competition((경쟁)) / and there are few famous women.",
  "조종사와 예술가 둘 다에게 / 많은 경쟁이 있다 / 그리고 유명한 여성은 거의 없다"),
 ("In both jobs, / you have to be very strong / and sure of yourself((자신에 대해 확신하는)).",
  "두 직업 모두에서 / 당신은 매우 강해야 한다 / 그리고 자신에 대해 확신해야 한다"),
 ("Of course, / there are also many differences((차이점)) / between the two jobs.", "물론 / 많은 차이점도 있다 / 두 직업 사이에는"),
 ("Pilots and artists have to be strong / in different ways.", "조종사와 예술가는 강해야 한다 / 서로 다른 방식으로"),
 ("Pilots have to stay awake((깨어 있다)) / for long hours, / and sometimes they have to make important decisions((결정)) / quickly.",
  "조종사는 깨어 있어야 한다 / 오랜 시간 동안 / 그리고 때때로 그들은 중요한 결정을 내려야 한다 / 빠르게"),
 ("Artists, however((그러나)), / have to be strong / in their ideas about art and life.", "그러나 예술가는 / 강해야 한다 / 예술과 삶에 대한 그들의 생각에서"),
 ("People in the two jobs / also work / in different ways.", "두 직업의 사람들은 / 또한 일한다 / 서로 다른 방식으로"),
 ("Pilots usually work with other people, / but artists usually work alone((혼자)).", "조종사는 보통 다른 사람들과 함께 일한다 / 하지만 예술가는 보통 혼자 일한다"),
 ("Pilots must understand other people. / Artists must understand themselves.", "조종사는 다른 사람들을 이해해야 한다 / 예술가는 자기 자신을 이해해야 한다"),
 ("Finally, / there is an important difference / in lifestyle((생활 방식)).", "마지막으로 / 중요한 차이가 있다 / 생활 방식에"),
 ("Pilots travel for their job / and are often away from((~을 떠나 있다)) home.", "조종사는 일 때문에 여행한다 / 그리고 자주 집을 떠나 있다"),
 ("Artists, however, / work at home / or in a studio near home.", "그러나 예술가는 / 집에서 일한다 / 또는 집 근처의 작업실에서"),
 ("Also, / unlike((~와 달리)) pilots, / artists can start and stop working / when they want.", "또한 / 조종사와 달리 / 예술가는 일을 시작하고 멈출 수 있다 / 그들이 원할 때"),
 ("Maria said / she could never be a pilot / because she hates airplanes.", "Maria는 말했다 / 그녀는 결코 조종사가 될 수 없을 것이라고 / 그녀는 비행기를 싫어하기 때문에"),
 ("Jane said / she could never be an artist / because she hates working alone.", "Jane은 말했다 / 그녀는 결코 예술가가 될 수 없을 것이라고 / 그녀는 혼자 일하는 것을 싫어하기 때문에"),
 ("There are many things to think about / when choosing a job, / but what you enjoy / should come first.",
  "생각할 것들이 많다 / 직업을 고를 때 / 하지만 당신이 즐기는 것이 / 가장 먼저 와야 한다"),
]

WS2 = [
 ("At a **restaurant**, Jane and Maria **talked about** their jobs.", "한 {{식당}}에서 Jane과 Maria는 그들의 직업에 대해 {{이야기했}}다."),
 ("They **agreed** that there are a few **similarities**.", "그들은 몇 가지 {{비슷한 점}}이 있다는 데 {{동의했}}다."),
 ("For both pilots and artists, there is a lot of **competition** and there are **few** famous women.", "조종사와 예술가 둘 다 {{경쟁}}이 심하고, 유명한 여성이 {{거의 없}}다."),
 ("In both jobs, you have to be very **strong** and **sure of yourself**.", "두 직업 모두에서 너는 매우 {{강해}}야 하고 {{자신에 대한 확신}}이 있어야 한다."),
 ("Of course, there are also many **differences** between the two jobs.", "물론, 두 직업 사이에는 {{차이점}}도 많다."),
 ("Pilots and artists have to be strong in **different ways**.", "조종사와 예술가는 {{서로 다른 방식}}으로 강해야 한다."),
 ("Pilots have to **stay awake** for long hours, and sometimes they have to make important **decisions** **quickly**.",
  "조종사는 오랜 시간 동안 {{깨어 있}}어야 하고, 때때로 중요한 {{결정}}을 {{빨리}} 내려야 한다."),
 ("Artists, **however**, have to be strong in their **ideas** about art and life.", "{{그러나}} 예술가는 예술과 삶에 대한 자신의 {{생각}}이 확고해야 한다."),
 ("People in the two jobs also **work** in different ways.", "두 직업의 사람들은 {{일하는}} 방식도 다르다."),
 ("Pilots **usually** work with other people, but artists usually work **alone**.", "조종사는 {{보통}} 다른 사람들과 함께 일하지만, 예술가는 보통 {{혼자}} 일한다."),
 ("Pilots must **understand** other people. Artists must understand **themselves**.", "조종사는 다른 사람들을 {{이해해}}야 한다. 예술가는 {{자기 자신}}을 이해해야 한다."),
 ("Finally, there is an important **difference** in **lifestyle**.", "마지막으로, {{생활 방식}}에 중요한 {{차이}}가 있다."),
 ("Pilots **travel** for their job and are often **away from** home.", "조종사는 일 때문에 {{여행을 하}}고 자주 집을 {{떠나 있}}다."),
 ("Artists, however, work at home or in a **studio** **near** home.", "그러나 예술가는 집이나 집 {{근처}}의 {{작업실}}에서 일한다."),
 ("Also, **unlike** pilots, artists can **start and stop** working when they want.", "또한, 조종사와 {{달리}} 예술가는 원할 때 일을 {{시작하고 멈출}} 수 있다."),
 ("Maria said she could **never** be a pilot because she **hates** airplanes.", "Maria는 비행기를 {{싫어해}}서 {{절대}} 조종사는 될 수 없을 거라고 말했다."),
 ("Jane said she could never be an artist because she hates **working alone**.", "Jane은 {{혼자 일하는 것}}을 싫어해서 절대 예술가는 될 수 없을 거라고 말했다."),
 ("There are many things to think about when **choosing** a job, but what you **enjoy** should **come first**.",
  "직업을 {{고를}} 때 생각할 것이 많지만, 네가 {{즐기는}} 것이 {{가장 먼저 와야}} 한다."),
]

WS4 = [
 ("At a restaurant, Jane and Maria ^^(talk)^^ about their jobs.", ["talked"]),
 ("They ^^(agree)^^ that there ^^(be)^^ a few similarities.", ["agreed", "are"]),
 ("For both pilots and artists, there ^^(be)^^ a lot of competition and there ^^(be)^^ few famous women.", ["is", "are"]),
 ("In both jobs, you ^^(have to, be)^^ very strong and sure of yourself.", ["have to be"]),
 ("Of course, there ^^(be)^^ also many differences between the two jobs.", ["are"]),
 ("Pilots and artists ^^(have to, be)^^ strong in different ways.", ["have to be"]),
 ("Pilots ^^(have to, stay)^^ awake for long hours, and sometimes they ^^(have to, make)^^ important decisions quickly.", ["have to stay", "have to make"]),
 ("Artists, however, ^^(have to, be)^^ strong in their ideas about art and life.", ["have to be"]),
 ("People in the two jobs also ^^(work)^^ in different ways.", ["work"]),
 ("Pilots usually ^^(work)^^ with other people, but artists usually ^^(work)^^ alone.", ["work", "work"]),
 ("Pilots ^^(must, understand)^^ other people. Artists ^^(must, understand)^^ themselves.", ["must understand", "must understand"]),
 ("Finally, there ^^(be)^^ an important difference in lifestyle.", ["is"]),
 ("Pilots ^^(travel)^^ for their job and ^^(be)^^ often away from home.", ["travel", "are"]),
 ("Artists, however, ^^(work)^^ at home or in a studio near home.", ["work"]),
 ("Also, unlike pilots, artists ^^(can, start)^^ and ^^(stop)^^ ^^(work)^^ when they ^^(want)^^.", ["can start", "stop", "working", "want"]),
 ("Maria ^^(say)^^ she ^^(could, never, be)^^ a pilot because she ^^(hate)^^ airplanes.", ["said", "could never be", "hates"]),
 ("Jane ^^(say)^^ she ^^(could, never, be)^^ an artist because she ^^(hate)^^ ^^(work)^^ alone.", ["said", "could never be", "hates", "working"]),
 ("There ^^(be)^^ many things ^^(think)^^ about when ^^(choose)^^ a job, but what you ^^(enjoy)^^ ^^(should, come)^^ first.",
  ["are", "to think", "choosing", "enjoy", "should come"]),
]

WS5 = [
 ("At a restaurant, Jane and Maria ^^[talking / talked]^^ about their jobs.", ["talked"]),
 ("They agreed that there ^^[is / are]^^ a few similarities.", ["are"]),
 ("For both pilots and artists, there is a lot of competition and there are ^^[few / little]^^ famous women.", ["few"]),
 ("In both jobs, you have to ^^[being / be]^^ very strong and sure of ^^[yourself / you]^^.", ["be", "yourself"]),
 ("Of course, there are also many ^^[difference / differences]^^ between the two jobs.", ["differences"]),
 ("Pilots and artists have to be strong in ^^[different / difference]^^ ways.", ["different"]),
 ("Pilots have to ^^[stays / stay]^^ awake for long hours, and sometimes they have to make important decisions ^^[quickly / quick]^^.", ["stay", "quickly"]),
 ("Artists, however, have to be strong in ^^[they / their]^^ ideas about art and life.", ["their"]),
 ("People in the two jobs also ^^[work / works]^^ in different ways.", ["work"]),
 ("Pilots ^^[work usually / usually work]^^ with other people, but artists usually work alone.", ["usually work"]),
 ("Pilots must ^^[understands / understand]^^ other people. Artists must understand ^^[themselves / them]^^.", ["understand", "themselves"]),
 ("Finally, there ^^[is / are]^^ an important difference in lifestyle.", ["is"]),
 ("Pilots travel for their job and ^^[is / are]^^ often away from home.", ["are"]),
 ("Artists, however, ^^[works / work]^^ at home or in a studio near home.", ["work"]),
 ("Also, unlike pilots, artists can start and stop ^^[working / to work]^^ when they want.", ["working"]),
 ("Maria said she could never ^^[is / be]^^ a pilot because she ^^[hates / hate]^^ airplanes.", ["be", "hates"]),
 ("Jane said she could never be ^^[a / an]^^ artist because she hates ^^[work / working]^^ alone.", ["an", "working"]),
 ("There are many things ^^[thinking / to think]^^ about when choosing a job, but what you enjoy ^^[should come / should comes]^^ first.", ["to think", "should come"]),
]

WS6 = [
 {"lines": ["Two Different Jobs",
            "At a restaurant, Jane and Maria **talked** about their jobs. They **agreed** that there **is** a few similarities. "
            "For both pilots and artists, there is a lot of **competition** and there are **little** famous women. "
            "In both jobs, you have to **be** very strong and sure of **you**."],
  "errors": [{"wrong": "is", "right": "are", "reason": "There + be 는 뒤 명사(similarities 복수)에 맞춘다"},
             {"wrong": "little", "right": "few", "reason": "셀 수 있는 명사(women) 앞에는 few"},
             {"wrong": "you", "right": "yourself", "reason": "주어 자신을 가리키면 재귀대명사"}]},
 {"lines": ["Of course, there are also many **difference** between the two jobs. Pilots and artists have to be strong in **different** ways. "
            "Pilots have to **stay** awake for long hours, and sometimes they have to make important decisions **quick**. "
            "Artists, **however**, have to be strong in **them** ideas about art and life."],
  "errors": [{"wrong": "difference", "right": "differences", "reason": "many 뒤에는 복수명사"},
             {"wrong": "quick", "right": "quickly", "reason": "동사 make 를 꾸미는 부사"},
             {"wrong": "them", "right": "their", "reason": "명사 ideas 앞 — 소유격"}]},
 {"lines": ["People in the two jobs also **works** in different ways. Pilots **usually work** with other people, but artists usually "
            "work **alone**. Pilots must **understands** other people. Artists must understand **themselves**."],
  "errors": [{"wrong": "works", "right": "work", "reason": "주어 People 은 복수"},
             {"wrong": "understands", "right": "understand", "reason": "조동사 must + 동사원형"}]},
 {"lines": ["Finally, there **are** an important difference in lifestyle. Pilots travel for their job and are often away **from** home. "
            "Artists, however, **works** at home or in a studio near home. Also, unlike pilots, artists can start and stop **working** "
            "when they **want**."],
  "errors": [{"wrong": "are", "right": "is", "reason": "There + be 는 뒤 명사(an important difference 단수)에 맞춘다"},
             {"wrong": "works", "right": "work", "reason": "주어 Artists 는 복수"}]},
 {"lines": ["Maria said she could never **is** a pilot because she **hates** airplanes. Jane said she could never be **a** artist "
            "because she hates **working** alone. There are many things **to think** about when choosing a job, but what you enjoy "
            "should **comes** first."],
  "errors": [{"wrong": "is", "right": "be", "reason": "조동사 could + 동사원형"},
             {"wrong": "a", "right": "an", "reason": "artist 는 모음 소리로 시작"},
             {"wrong": "comes", "right": "come", "reason": "조동사 should + 동사원형"}]},
]

WS7 = [
 "At a restaurant, (talk / Jane and Maria) (their jobs / about).",
 "(agree / they) that (be / there / a few similarities).",
 "For both pilots and artists, (a lot of competition / be / there) and (few famous women / be / there).",
 "In both jobs, (very strong / have to / be / you) and (yourself / sure of).",
 "Of course, (also / be / there / many differences) (the two jobs / between).",
 "(strong / pilots and artists / be / have to) (different ways / in).",
 "(stay / awake / pilots / have to) (long hours / for), and (have to / they / sometimes / make) (quickly / important decisions).",
 "Artists, however, (strong / have to / be) (art and life / their ideas / about / in).",
 "(in the two jobs / people) (in different ways / work / also).",
 "(with other people / usually / pilots / work), but (alone / work / usually / artists).",
 "(other people / understand / must / pilots). (themselves / understand / must / artists).",
 "Finally, (an important difference / be / there) (lifestyle / in).",
 "(for their job / travel / pilots) and (home / often / away from / be).",
 "Artists, however, (at home / work) or (near home / in a studio).",
 "Also, unlike pilots, (start and stop / can / artists / work) (they / want / when).",
 "(say / Maria) (a pilot / could never / be / she) (airplanes / hate / she / because).",
 "(say / Jane) (an artist / could never / be / she) (alone / work / hate / she / because).",
 "(many things / be / there / think about) (a job / choose / when), but (should / come / what you enjoy / first).",
]

WS8 = [
 (["restaurant", "talk about", "jobs"], "At a restaurant, {{#7}}."),
 (["agree", "similarities"], "{{#2}} that {{#5}}."),
 (["both", "competition", "few"], "For both pilots and artists, {{#6}} and {{#5}}."),
 (["have to", "strong", "sure of"], "In both jobs, {{#10}}."),
 (["differences", "between"], "Of course, {{#9}}."),
 (["have to", "strong", "different ways"], "{{#10}}."),
 (["stay awake", "long hours", "make", "decisions"], "{{#8}}, and {{#8}}."),
 (["however", "strong", "ideas"], "Artists, however, {{#11}}."),
 (["people", "also", "different ways"], "{{#10}}."),
 (["usually", "other people", "alone"], "{{#6}}, but {{#4}}."),
 (["must", "understand", "themselves"], "{{#5}}. {{#4}}."),
 (["difference", "lifestyle"], "Finally, {{#7}}."),
 (["travel", "job", "away from"], "{{#11}}."),
 (["however", "studio", "near"], "Artists, however, {{#9}}."),
 (["unlike", "start and stop", "want"], "Also, {{#11}}."),
 (["say", "could never", "pilot", "hate"], "{{#12}}."),
 (["could never", "artist", "work alone"], "{{#13}}."),
 (["think about", "choose", "enjoy", "come first"], "{{#11}}, but {{#6}}."),
]

HERE = os.path.dirname(os.path.abspath(__file__))
build(os.path.join(HERE, "영일중1_L7_외부지문.json"), "Lesson 7 More reading — Two Different Jobs", "영일중", "1학년",
      S, PREP, WS1, WS2, WS4, WS5, WS6, WS7, WS8)
