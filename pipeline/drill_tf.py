# -*- coding: utf-8 -*-
"""
1층 드릴 b — 내용일치 T/F.

원장 지정(2026-09-05)의 1층 드릴 세 갈래 중 b. 「지문별·대화문별 T/F 로 내용 숙지 확인」.

## 분량

원장: 「대부분 본문 하나에는 거의 20~30개 사이가 나오게 배치하는 게 좋지 싶다.」
→ **문장 하나당 대략 한 문항.** 클로드가 처음 제안한 「문장 수의 0.6~0.8배, 최대 12」는
   너무 성글었다.

## 「본문 하나」는 문단이 아니라 **한 편**이다

DB 에는 `Street Art in London-1~4` 로 문단이 나뉘어 있다. 드릴은 그것을 **합쳐서**
한 편으로 다룬다 — 아이가 받는 학습지의 단위가 그것이고, 문단 하나(2문장)로는
드릴이 성립하지 않는다. 지문 레코드는 그대로 두고 여기서만 묶는다.

## 근거 문장을 반드시 가리킨다

각 문항은 `evidence_sentences` 로 지문의 몇 번 문장을 근거로 삼았는지 낸다.
이유 두 가지:

  · **정답을 검증할 수 있다.** 근거 문장을 읽으면 T/F 판정이 맞는지 사람이 30초에 본다.
  · **해설이 공짜로 나온다.** 틀린 아이에게 「본문 몇 번 문장을 보라」고 할 수 있다.

지문에 없는 내용을 근거로 든 문항은 여기서 걸린다 — 태깅에서 surface 로 환각을
잡는 것과 같은 장치다 (설계원칙 7).
"""
import re

from . import prompts
from .models import PASS_A_MODEL

SYSTEM = """\
당신은 중학교 2학년 영어 내신 학습지를 만듭니다.

# 하는 일

지문을 읽고 **내용일치 O/X 문항**을 만듭니다. 아이가 지문을 제대로 읽었는지
확인하는 것이 목적입니다. 어법이 아니라 **내용**을 묻습니다.

# 지켜야 할 것

1. **문항은 한국어로 씁니다.** 중2가 읽고 바로 판단할 수 있는 문장으로.
2. **지문에 있는 것만 묻습니다.** 지문으로 판단할 수 없는 것(상식·추측)은 문항이
   될 수 없습니다. 「알 수 없음」이 정답인 문항도 만들지 마십시오.
3. **근거 문장을 반드시 답니다.** `evidence_sentences` 에 그 문항의 근거가 되는
   문장 번호를 넣습니다. 두 문장을 합쳐야 판단되면 둘 다 넣습니다.
4. **거짓(X) 문항 개수를 사용자 지시대로 정확히 맞추십시오.**
   「대략 절반씩」이나 「45% 안팎」이라고만 하면 참(O)이 65~75% 로 몰립니다 —
   두 번 재서 확인한 결과입니다. 그래서 **개수를 숫자로 지정**합니다.
   만들고 나서 X 가 몇 개인지 **세어 보고**, 모자라면 O 문항 몇 개를 X 로 바꾸십시오.
   O 가 많으면 아이가 다 O 로 찍고 절반을 맞힙니다.
5. **거짓 문항은 지문을 살짝 비틀어 만듭니다.** 숫자·이름·장소·인과관계·순서를
   바꾸는 식입니다. 지문과 아무 상관 없는 엉뚱한 진술은 변별력이 없습니다.
6. **지문 순서대로 냅니다.** 아이가 지문을 훑으며 풀 수 있게, 근거 문장 번호가
   대체로 커지는 순서로 배열하십시오.
7. 같은 문장을 두 번 이상 근거로 쓰지 마십시오. 한 문장당 한 문항이 원칙입니다.

# 대화문일 때

화자가 누구인지, 누가 무엇을 원하고 제안했는지를 묻습니다. 대화의 흐름(먼저/나중)도
좋은 문항이 됩니다. 화자를 바꿔치기하는 것이 가장 흔한 거짓 문항입니다.
"""

CONTENT_ONLY = """
# 이 세트는 **내용 확인만** 합니다

표현 바꿔쓰기 문항은 만들지 마십시오. 그건 따로 만듭니다. 여기서는 **지문의 모든
문장을 빠짐없이** 확인하는 것이 목적입니다 — 한 문장도 건너뛰지 마십시오.
모든 문항의 `type` 은 `content` 입니다.
"""

DIALOGUE_EXTRA = """
# 이 세트는 **표현 바꿔쓰기만** 합니다

대화문은 의사소통 기능을 익히는 자료입니다. **같은 뜻의 다른 표현**을 함께 외우게
하는 것이 목적입니다. 원장 지시(2026-09-07): 「단순 내용일치 말고, xxxx 표현은
xxxx 표현으로 바꿀 수 있다, 이런 식으로 비슷한 표현들을 같이 암기할 수 있도록.」

**내용 확인 문항은 만들지 마십시오.** 그건 앞 세트에서 이미 다 했습니다.
모든 문항의 `type` 은 `paraphrase` 입니다.

형식은 이렇습니다.

    "How can I get to the Star Stadium?" 은
    "What's the best way to get to the Star Stadium?" 으로 바꿔 쓸 수 있다.   → O

## 바꿔쓰기 문항을 만들 때 지켜야 할 것

1. **원문 표현은 대화에 있는 그대로** 씁니다. 지어내지 마십시오.
2. **바꾼 표현은 중학교 2학년이 쓰는 것**으로. 교과서·자습서에 나오는 표현이
   가장 좋습니다. 사전에만 있는 어려운 표현은 쓰지 마십시오.
3. **거짓 문항은 「헷갈릴 만한 것」으로** 만듭니다. 같은 화제 안에서 기능이
   **다른** 표현을 붙이는 것이 좋습니다.
       "How long will it take?" 를 "How can I get there?" 로 바꿀 수 있다 → X
         (하나는 소요 시간, 하나는 교통수단을 묻는다)
   전혀 엉뚱한 표현을 붙이면 아이가 생각하지 않고 찍습니다.
4. **`why_ko` 에 왜 되는지/왜 안 되는지를 씁니다.** 거짓 문항이면 두 표현이
   각각 무엇을 묻는지 밝히십시오. 아이가 정답지를 보고 **바른 표현을 외우게**
   하는 것이 목적입니다.
5. `evidence_sentences` 에는 **원문 표현이 있는 발화 번호**를 넣습니다.
"""


def schema(n_items):   # noqa: ARG001 — 개수는 프롬프트가 통제한다
    return {
        "type": "object",
        "properties": {
            # 배열 길이를 스키마로 못 막는다 — API 가 minItems 를 0/1 만 받는다.
            # 개수는 프롬프트로 통제하고, 여기서는 모양만 강제한다.
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["content", "paraphrase"],
                                 "description": "content=내용 확인 · paraphrase=표현 바꿔쓰기"},
                        "statement_ko": {"type": "string",
                                         "description": "한국어 진술. 아이가 O/X 를 판단한다"},
                        "answer": {"type": "string", "enum": ["O", "X"]},
                        "evidence_sentences": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "근거가 되는 지문 문장 번호"},
                        "why_ko": {"type": "string",
                                   "description": "X 인 이유 또는 O 인 근거. 한 문장"},
                    },
                    "required": ["type", "statement_ko", "answer",
                                 "evidence_sentences", "why_ko"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def build_params(title, kind, sentences, n_items, mode="content"):
    """mode: content = 내용 확인 (지문 전 문장) · paraphrase = 표현 바꿔쓰기

    원장 지시(2026-09-07): 「바꿔쓰기 없이 전체 내용을 확인하는 거 100% 낸 이후에
    바꿔쓰기를 추가로 내도록.」 두 세트를 한 번에 만들면 내용 확인이 성글어진다 —
    실제로 섞어 만들었더니 25문장 중 내용 확인이 14개뿐이었다.
    """
    body = prompts.number_sentences(sentences)
    label = "대화문" if kind == "textbook_dialogue" else "지문"
    if mode == "paraphrase":
        ask = (f"위 {label}에 나온 표현으로 **바꿔쓰기** O/X 문항을 "
               f"**{n_items}개 안팎** 만드십시오.\n\n"
               f"**그중 {round(n_items * 0.45)}개는 정답이 X 여야 합니다.**")
        system = SYSTEM + DIALOGUE_EXTRA
    else:
        ask = (f"위 {label}으로 **내용 확인** O/X 문항을 **{n_items}개 안팎** "
               f"만드십시오.\n문장이 {len(sentences)}개입니다. "
               f"**모든 문장을 빠짐없이** 확인하십시오.\n\n"
               f"**그중 {round(n_items * 0.45)}개는 정답이 X 여야 합니다.** "
               f"다 만든 뒤 X 개수를 세어 확인하십시오.")
        system = SYSTEM + CONTENT_ONLY
    user = f"# {label}: {title}\n\n{body}\n\n{ask}"
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": schema(n_items)}},
        "thinking": {"type": "adaptive"},
    }


_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+")


def clean_text(s):
    """모델이 낸 JSON 이스케이프가 제어문자로 풀린 자리를 지운다.

    실제로 한 번 났다 — `why_ko` 가 `\\bcdots 둘 다 …` 로 와서 JSON 파서가
    `\\b` 를 0x08 로 풀었고, 인쇄물에는 「cdots」 라는 글자가 남았다.
    빈도는 낮지만 강사 손에 가는 종이라 여기서 막는다.
    """
    if not isinstance(s, str):
        return s
    return " ".join(_CTRL.sub(" ", s).split()).strip()


def parse(raw, sentences):
    """근거 문장 번호가 지문 범위를 벗어난 문항은 버린다."""
    n = len(sentences)
    kept, rejects = [], []
    used = set()
    for i, it in enumerate(raw.get("items", [])):
        for k in ("statement_ko", "statement_en", "why_ko"):
            if k in it:
                it[k] = clean_text(it[k])
        ev = [e for e in it["evidence_sentences"] if 1 <= e <= n]
        if not ev:
            rejects.append((i, f"근거 문장 번호가 범위 밖 {it['evidence_sentences']}"))
            continue
        it["evidence_sentences"] = ev
        it["_evidence_text"] = [sentences[e - 1] for e in ev]
        it["_repeat"] = bool(set(ev) & used)      # 같은 문장을 또 썼나 — 버리진 않고 표시만
        used |= set(ev)
        kept.append(it)
    kept.sort(key=lambda x: min(x["evidence_sentences"]))
    kinds = {}
    for x in kept:
        kinds[x.get("type", "content")] = kinds.get(x.get("type", "content"), 0) + 1
    return {"items": kept,
            "diagnostics": {"returned": len(raw.get("items", [])), "kept": len(kept),
                            "by_type": kinds,
                            "rejects": rejects,
                            "answer_balance": {
                                "O": sum(1 for x in kept if x["answer"] == "O"),
                                "X": sum(1 for x in kept if x["answer"] == "X")},
                            "sentences_covered": len(used), "sentence_count": n,
                            "repeated": sum(1 for x in kept if x["_repeat"])}}


# ═══════════════════════════════════════════════════════════════════
#  영어판 — 같은 문항을 영어 진술로 (원장 지시 2026-09-07)
#
#  「한국어로 한 것을 1차로 본 후에 1주일 뒤에 영어로 한 것을 다시 보라고 하면
#   완전학습이 되잖아.」
#
#  그래서 **새로 만들지 않고 옮긴다.** 문항이 달라지면 「같은 것을 다시」가 아니라
#  「다른 것을 또」가 되고, 간격 반복의 값이 사라진다. 정답과 근거 문장은 그대로 두고
#  진술만 영어로 쓴다.
#
#  실물 근거: 영일중 「L5. The Street as a Canvas — Fact Check」 20문항이 영어다.
#  기출도 영어 선지를 쓴다 (청명 21 · 태장 9 내용일치).
# ═══════════════════════════════════════════════════════════════════

EN_SYSTEM = """\
You write True/False statements for Korean middle-school students (Grade 8, age 14).

# Your task

You are given Korean True/False statements about an English passage. **Rewrite each one
as an English statement** that means exactly the same thing.

# Rules

1. **Keep the answer identical.** If the Korean statement is false, the English one must
   be false for the same reason. Do not fix, soften, or change what is being claimed.
2. **Do not copy the passage sentence.** Reword it. If a student can match the statement
   to a passage sentence word-for-word, they answer without reading.
   Passage:   `we are going to see some well-known street artworks in London`
   Statement: `This tour takes people to see famous street art in the city of London.`
3. **Use vocabulary a Grade 8 Korean student knows.** Words from the passage and its
   word list are best. Avoid words that need a dictionary.
4. **Keep it to one sentence** where possible. Two short sentences are acceptable when
   the Korean statement joins two facts.
5. For false statements, the wrong part must be **visible in the English** — a changed
   name, number, place, or relationship. Do not make it false by leaving something out.

Return one English statement per input item, in the same order, keyed by `index`.
"""


def en_schema():
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "1부터. 입력 순서"},
                        "statement_en": {"type": "string"},
                    },
                    "required": ["index", "statement_en"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def build_en_params(title, sentences, items):
    body = prompts.number_sentences(sentences)
    lines = "\n".join(
        f'{i}. [{it["answer"]}] {it["statement_ko"]}  '
        f'(근거 문장 {", ".join(map(str, it["evidence_sentences"]))})'
        for i, it in enumerate(items, 1))
    user = (f"# Passage: {title}\n\n{body}\n\n"
            f"# Korean statements to rewrite in English ({len(items)})\n\n{lines}")
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": EN_SYSTEM,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": en_schema()}},
        "thinking": {"type": "adaptive"},
    }


def merge_en(items, raw):
    """영어 진술을 한국어 문항에 붙인다. 빠진 것은 표시하고 넘어간다."""
    by_i = {x["index"]: x["statement_en"] for x in raw.get("items", [])}
    missing = []
    for i, it in enumerate(items, 1):
        en = by_i.get(i)
        if not en:
            missing.append(i)
            continue
        it["statement_en"] = clean_text(en)
    return missing
