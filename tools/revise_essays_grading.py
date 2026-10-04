# -*- coding: utf-8 -*-
"""
서술형을 채점 친화형으로 고친다 — 원장 2026-10-04.

  python tools/revise_essays_grading.py          # 무엇이 바뀌는지 미리보기
  python tools/revise_essays_grading.py --apply  # JSON 에 반영 (원래 문항은 revised_from 에 남김)

원장: 「서술형 답 채점이 너무 힘들게 줄줄이 줄글을 쓰도록 되어 있어. 모두 영작을 시킨 다음에
특정 번째 단어를 써라든가 채점 친화적인 방법으로. 채점이 길어야 한 줄에 그치거나 몇 개
단어를 쓰게. 이미 그렇게 되어 있는 것은 놔두고 아닌 것들만.」

세 가지 꼴로만 바꾼다:
  · 영작 → 「완성한 문장의 ○번째 단어」 만 쓴다. 위치는 **노리는 어법이 걸린 자리**로 고른다
    (관계대명사 · 과거형 · 지각동사 목적보어 형태 · so~that 앞 be동사 시제)
  · 본문 질문에 답하기 → 문장 틀을 주고 **빈칸 몇 단어**만 쓴다
  · 단문 나열 고쳐 쓰기 → 문장 전체가 아니라 「기호 / 틀린 단어 → 고친 단어」

손대지 않은 것: 중1 논술 3(빈칸 2~3단어) · 4(틀린 것 → 고친 것) · 중2 5·6세트 22번(한 줄 6단어).
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK = os.path.join(ROOT, "data", "generated", "mock")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

NOTE = " [채점형 수정 2026-10-04]"

# 영작 → ○번째 단어. 공통 안내.
POS_STEM = "다음 우리말을 <조건>에 맞게 영작할 때, {pos} 단어를 쓰시오."
POS_COND = "답안에는 지정된 순서의 단어만 쓸 것 (문장 전체를 쓰지 말 것)"
COUNT_COND = "단어 수는 띄어쓰기 기준으로 센다"
FIX_STEM = "{mid}의 ①~⑤ 중 어법상 틀린 문장 2개를 골라 기호를 쓰고, 틀린 부분을 바르게 고쳐 쓰시오."
FIX_CONDS = ["틀린 부분만 「틀린 말 → 고친 말」로 쓸 것 (문장 전체를 다시 쓰지 말 것)",
             "한 문장에서 한 군데만 고칠 것"]
FIX_SLOTS = ["(a) 기호 ___ : ______ → ______", "(b) 기호 ___ : ______ → ______"]


def pos_label(ns):
    return "·".join(f"{n}번째" for n in ns)


def pos_item(ns, words, keep_conds, extra_conds=()):
    """ns: 위치, words: 그 위치의 정답 단어."""
    return {
        "prompt_ko": POS_STEM.format(pos=pos_label(ns)),
        "conditions": list(keep_conds) + list(extra_conds) + [COUNT_COND, POS_COND],
        "answer_slots": [f"{n}번째 단어: ________" for n in ns],
        "answer_en_words": [f"{n}번째: {w}" for n, w in zip(ns, words)],
    }


# 학교 파일 · 문항 번호 → 바꿀 내용.
# conditions 는 원 문항 것을 살리되(형태 변형·어법 지정), 「몇 단어로」 는 word_limit 이 맡는다.
REV = {
    # ───────────── 영덕중2 4세트 ─────────────
    ("영덕중_4세트", 19): dict(pos_item(
        [3, 6, 7], ["that (which 도 정답)", "wrote", "surprised"],
        ["목적격 관계대명사 that(또는 which)을 반드시 사용할 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것", "과거시제로 쓸 것"],
        ["Dr. Schofield 는 두 단어로 센다"]),
        full="The article that Dr. Schofield wrote surprised the (whole) world."),
    ("영덕중_4세트", 20): dict(pos_item(
        [2, 5], ["saw", "singing"],
        ["지각동사와 목적격보어를 사용할 것 (진행 중인 동작을 살릴 것)",
         "P1에 나온 표현을 세 단어 이상 연속으로 그대로 쓰지 말 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것"]),
        full="We saw a boy singing in the playground."),
    ("영덕중_4세트", 21): dict(pos_item(
        [3, 8], ["was", "made"],
        ["완전한 한 문장으로 쓸 것", "주어진 단어를 모두 사용하되 시제에 맞게 형태를 바꿀 것",
         "단어를 추가하거나 빼지 말 것"]),
        full="The test was so difficult that I made many mistakes.",
        prompt_ko="주어진 단어를 모두 사용하여 <조건>에 맞는 한 문장을 만들 때, 3번째·8번째 단어를 쓰시오."),
    ("영덕중_4세트", 22): {
        "prompt_ko": "P1과 P3의 내용에 맞게 다음 질문에 대한 답을 완성하시오.",
        "context": "(a) Q: What did Dr. Schofield do in Korea in 1916?\n"
                   "    A: He ______________ medicine in Korea.\n"
                   "(b) Q: How can the girl get to the Dream Zoo?\n"
                   "    A: She can get there ______________.",
        "conditions": ["(a)는 '~하곤 했다'의 뜻이 되도록 used to 를 사용하여 빈칸을 3단어로 쓸 것",
                       "(b)는 알맞은 전치사를 포함하여 빈칸을 2단어로 쓸 것",
                       "본문에 나온 단어만 사용할 것"],
        "answer_slots": ["(a) ______________", "(b) ______________"],
        "answer_en_words": ["(a) used to teach", "(b) by bus (by subway 도 정답)"],
        "given_words": [], "word_limit": "(a) 3단어 · (b) 2단어",
    },
    ("영덕중_4세트", 23): {"fix": "T9", "answer_en_words": [
        "(a) ② going → go", "(b) ③ played → play (playing 도 정답)"]},

    # ───────────── 영덕중2 5세트 ─────────────
    ("영덕중_5세트", 19): dict(pos_item(
        [3, 5, 7], ["that", "saw", "carries"],
        ["목적격 관계대명사 that을 반드시 사용할 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것", "주절의 동사는 현재시제로 쓸 것"]),
        full="The painting that I saw yesterday carries a social message."),
    ("영덕중_5세트", 20): dict(pos_item(
        [2, 4, 5], ["heard", "children", "shouting"],
        ["지각동사의 목적격보어로 현재분사를 쓸 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것",
         "P3에 나온 세 단어 이상 연속된 표현을 그대로 옮겨 쓰지 말 것"]),
        full="We heard the children shouting on the bus."),
    ("영덕중_5세트", 21): dict(pos_item(
        [2, 7], ["was", "saved"],
        ["완전한 한 문장으로 쓸 것", "과거시제로 쓸 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것"]),
        full="He was so brave that he saved the children.",
        prompt_ko="주어진 단어를 모두 사용하여 <조건>에 맞는 한 문장을 만들 때, 2번째·7번째 단어를 쓰시오."),
    ("영덕중_5세트", 23): {"fix": "T11", "answer_en_words": [
        "(a) ② to cross → cross (crossing 도 정답)", "(b) ④ such → so"]},

    # ───────────── 영덕중2 6세트 ─────────────
    ("영덕중_6세트", 19): dict(pos_item(
        [3, 5, 7], ["which (that 도 정답)", "borrowed", "was"],
        ["목적격 관계대명사(which 또는 that)를 반드시 사용할 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿔 쓸 것", "과거시제로 쓸 것"]),
        full="The book which I borrowed yesterday was very interesting."),
    ("영덕중_6세트", 20): dict(pos_item(
        [2, 5], ["saw", "dancing"],
        ["지각동사를 사용하여 한 문장으로 쓸 것", "목적격보어로 현재분사(-ing)를 쓸 것",
         "[참고 문장]에서 세 단어 이상을 연속해 그대로 옮겨 쓰지 말 것",
         "주어진 단어를 모두 사용하되 필요하면 형태를 바꿔 쓸 것"]),
        full="I saw the boy dancing on the stage."),
    ("영덕중_6세트", 21): dict(pos_item(
        [3, 8], ["was", "couldn't"],
        ["so ~ that 구문을 사용할 것", "주어진 단어를 모두 사용하되 필요하면 형태를 바꿀 것",
         "과거시제의 완전한 한 문장으로 쓸 것"],
        ["couldn't 처럼 줄여 쓴 말은 한 단어로 센다"]),
        full="The box was so heavy that I couldn't move it.",
        prompt_ko="주어진 단어를 모두 사용하여 <조건>에 맞는 한 문장을 만들 때, 3번째·8번째 단어를 쓰시오."),
    ("영덕중_6세트", 23): {"fix": "T10", "answer_en_words": [
        "(a) ② to run → run (running 도 정답)", "(b) ⑤ such → so"]},

    # ───────────── 영덕중1 5과 1세트 ─────────────
    ("중1_영덕중_1세트", 1): {
        "prompt_ko": "[T10]의 대화를 읽고, 질문에 대한 답이 되도록 빈칸에 알맞은 말을 쓰시오.",
        "context": "(1) Q: Where do Tom and Mina get off?\n"
                   "    A: They get off ______________.\n"
                   "(2) Q: What will Mina do after she sees the Monalisa?\n"
                   "    A: She will draw a picture of it after ______________ the Monalisa.\n"
                   "(3) Q: What does Mina want to be?\n"
                   "    A: She wants to be a painter ______________.",
        "conditions": ["빈칸 단어 수: (1) 3단어 · (2) 2단어 · (3) 4단어",
                       "주어는 대명사로 쓸 것",
                       "시간을 나타내는 말(after, when) 뒤의 시제에 주의할 것"],
        "answer_slots": ["(1) ______________", "(2) ______________", "(3) ______________"],
        "answer_en_words": ["(1) at Central Station", "(2) she sees", "(3) when she grows up"],
        "given_words": [], "word_limit": "",
    },
    ("중1_영덕중_1세트", 2): {
        "prompt_ko": "[T5]를 읽고, 질문에 대한 답이 되도록 빈칸에 본문의 표현을 써서 완성하시오.",
        "context": "(1) Q: What is a Foley artist in charge of?\n"
                   "    A: A Foley artist is ______________ the sounds in a movie.\n"
                   "(2) Q: What does a Foley artist create with simple things?\n"
                   "    A: A Foley artist ______________ with simple things.",
        "conditions": ["빈칸 단어 수: (1) 3단어 · (2) 3단어",
                       "주어에 맞게 동사의 형태를 바꿀 것"],
        "answer_slots": ["(1) ______________", "(2) ______________"],
        "answer_en_words": ["(1) in charge of", "(2) creates sound effects"],
        "given_words": ["be in charge of", "create sound effects"], "word_limit": "",
    },
    # ───────────── 영덕중1 5과 2세트 ─────────────
    ("중1_영덕중_2세트", 1): {
        "prompt_ko": "[논술형 1] T7의 인터뷰를 읽고, 질문에 대한 답이 되도록 빈칸에 알맞은 말을 쓰시오.",
        "context": "(1) Q: How will Minji go to the City Art Center?\n"
                   "    A: She will go there ______________.\n"
                   "(2) Q: Where will she get off?\n"
                   "    A: She will get off ______________.\n"
                   "(3) Q: What does Minji want to be in the future?\n"
                   "    A: She wants to be a sound designer ______________.",
        "conditions": ["빈칸 단어 수: (1) 2단어 · (2) 3단어 · (3) 4단어",
                       "알맞은 전치사를 포함할 것",
                       "(3)은 when 이 이끄는 시간 부사절로 쓰고 시제에 주의할 것"],
        "answer_slots": ["(1) ______________", "(2) ______________", "(3) ______________"],
        "answer_en_words": ["(1) by subway", "(2) at Central Station", "(3) when she grows up"],
        "given_words": [], "word_limit": "",
    },
    ("중1_영덕중_2세트", 2): {
        "prompt_ko": "[논술형 2] T1을 읽고, 질문에 대한 답이 되도록 빈칸에 본문의 표현을 써서 완성하시오. (각 2점)",
        "context": "(1) Q: What is a Foley artist in charge of?\n"
                   "    A: A Foley artist is a person who is ______________ all the sounds in a film.\n"
                   "(2) Q: What do Foley artists create sound effects with?\n"
                   "    A: Foley artists ______________ with simple things around them.",
        "conditions": ["빈칸 단어 수: (1) 3단어 · (2) 3단어"],
        "answer_slots": ["(1) ______________", "(2) ______________"],
        "answer_en_words": ["(1) in charge of", "(2) create sound effects"],
        "given_words": ["be in charge of", "create sound effects"], "word_limit": "",
    },
    # ───────────── 영덕중1 5과 3세트 ─────────────
    ("중1_영덕중_3세트", 1): {
        "prompt_ko": "[T11]의 대화를 읽고, 질문에 대한 답이 되도록 빈칸에 알맞은 말을 쓰시오.",
        "context": "(1) Q: What does Minji want to be when she grows up?\n"
                   "    A: She wants to be ______________.\n"
                   "(2) Q: When will Minji take the sound class?\n"
                   "    A: She will take it ______________ this Friday.\n"
                   "(3) Q: How will Minji get to the museum?\n"
                   "    A: She will go ______________ and get off ______________.",
        "conditions": ["빈칸 단어 수: (1) 3단어 · (2) 3단어 · (3) 앞 빈칸 2단어, 뒤 빈칸 3단어",
                       "(2)는 after 가 이끄는 시간 부사절로 쓰고 시제에 주의할 것",
                       "(3)은 알맞은 전치사를 포함할 것"],
        "answer_slots": ["(1) ______________", "(2) ______________",
                         "(3) ________ / ______________"],
        "answer_en_words": ["(1) a Foley artist", "(2) after school ends",
                            "(3) by subway / at Sinsa Station"],
        "given_words": [], "word_limit": "",
    },
    ("중1_영덕중_3세트", 2): {
        "prompt_ko": "[T7]을 읽고, 질문에 대한 답이 되도록 빈칸에 본문의 표현을 써서 완성하시오.",
        "context": "(1) Q: What is a Foley artist in charge of?\n"
                   "    A: She is ______________ every small sound in a movie.\n"
                   "(2) Q: What does Mina Park do for films?\n"
                   "    A: She ______________ for films.",
        "conditions": ["빈칸 단어 수: (1) 3단어 · (2) 3단어",
                       "주어에 맞게 동사의 형태를 바꿀 것"],
        "answer_slots": ["(1) ______________", "(2) ______________"],
        "answer_en_words": ["(1) in charge of", "(2) creates sound effects"],
        "given_words": ["be in charge of", "create sound effects"], "word_limit": "",
    },
    # ───────────── 영일중1 1·3세트 (2026-10-04 2차 — 아직 시험 안 본 학교) ─────────────
    # 21·23·24 는 이미 빈칸 4~7단어 한 줄이라 그대로. 22 만 8~9단어 문장이었다.
    ("중1_영일중_1세트", 22): {
        "prompt_ko": "다음은 지호의 일기 중 일부이다. 우리말과 같은 뜻이 되도록 빈칸에 알맞은 말을 쓰시오.",
        "context": "Tomorrow I have a piano lesson at nine.\n"
                   "(내가 지하철을 타고 가면, 나는 일찍 도착할 것이다.)\n"
                   "→ When I (A)______________, I (B)______________ early.",
        "conditions": ["(A)는 by subway 를 사용하여 3단어로 쓸 것",
                       "(B)는 will 을 사용하여 2단어로 쓸 것",
                       "시간을 나타내는 부사절의 시제에 유의할 것"],
        "answer_slots": ["(A) ______________", "(B) ______________"],
        "answer_en_words": ["(A) go by subway", "(B) will arrive"],
        "given_words": ["by subway", "will", "arrive"], "word_limit": "(A) 3단어 · (B) 2단어",
    },
    ("중1_영일중_3세트", 22): {
        "prompt_ko": "다음은 민호가 쓴 일기의 일부이다. 우리말과 같은 뜻이 되도록 빈칸 (A)~(C)에 알맞은 말을 쓰시오.",
        "context": "Tomorrow, my family will go to the science museum by subway.\n"
                   "We will get off (A)________ Sadang Station.\n"
                   "When we (B)______________, I (C)______________ pictures.\n"
                   "(→ 우리가 그곳에 도착하면, 나는 사진을 찍을 것이다.)",
        "conditions": ["(A)는 알맞은 전치사 1단어로 쓸 것",
                       "(B)는 get, there 를 사용하여 2단어로 쓸 것",
                       "(C)는 will, take 를 사용하여 2단어로 쓸 것",
                       "시간을 나타내는 부사절의 시제에 유의할 것"],
        "answer_slots": ["(A) ________", "(B) ______________", "(C) ______________"],
        "answer_en_words": ["(A) at", "(B) get there", "(C) will take"],
        "given_words": [], "word_limit": "(A) 1단어 · (B) 2단어 · (C) 2단어",
    },
}


def apply_one(e, r):
    before = {k: e.get(k) for k in ("prompt_ko", "context", "conditions", "given_words",
                                    "word_limit", "answer_en")}
    if "fix" in r:
        e["prompt_ko"] = FIX_STEM.format(mid=r["fix"])
        e["context"] = ""
        e["conditions"] = list(FIX_CONDS)
        e["answer_slots"] = list(FIX_SLOTS)
        e["given_words"] = []
        e["word_limit"] = ""
    else:
        for k in ("prompt_ko", "context", "conditions", "answer_slots", "given_words", "word_limit"):
            if k in r:
                e[k] = r[k]
    ans = "\n".join(r["answer_en_words"])
    if r.get("full"):
        ans += f"\n(완성 문장: {r['full']})"
    e["answer_en"] = ans
    e["why_ko"] = (e.get("why_ko") or "") + NOTE
    e.setdefault("revised_from", before)


def main():
    apply = "--apply" in sys.argv
    files = sorted({f for f, _ in REV})
    for f in files:
        p = os.path.join(MOCK, f + ".json")
        d = json.load(io.open(p, encoding="utf-8"))
        for e in d["essays"]:
            r = REV.get((f, e["no"]))
            if not r:
                print(f"  {f} {e['no']}번  그대로 둠")
                continue
            if "revised_from" in e:
                print(f"  {f} {e['no']}번  이미 수정됨 — 건너뜀")
                continue
            apply_one(e, r)
            print(f"  {f} {e['no']}번  → {e['answer_en'].splitlines()[0]} …")
        if apply:
            with io.open(p, "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
    print("\n  반영함" if apply else "\n  [미리보기] 반영하려면 --apply")


if __name__ == "__main__":
    main()
