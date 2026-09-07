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
4. **참과 거짓을 섞습니다.** 한쪽으로 몰리면 아이가 찍습니다. 대략 절반씩.
5. **거짓 문항은 지문을 살짝 비틀어 만듭니다.** 숫자·이름·장소·인과관계·순서를
   바꾸는 식입니다. 지문과 아무 상관 없는 엉뚱한 진술은 변별력이 없습니다.
6. **지문 순서대로 냅니다.** 아이가 지문을 훑으며 풀 수 있게, 근거 문장 번호가
   대체로 커지는 순서로 배열하십시오.
7. 같은 문장을 두 번 이상 근거로 쓰지 마십시오. 한 문장당 한 문항이 원칙입니다.

# 대화문일 때

화자가 누구인지, 누가 무엇을 원하고 제안했는지를 묻습니다. 대화의 흐름(먼저/나중)도
좋은 문항이 됩니다. 화자를 바꿔치기하는 것이 가장 흔한 거짓 문항입니다.
"""

DIALOGUE_EXTRA = """
# 대화문에서는 **표현 바꿔쓰기**를 절반쯤 섞습니다

대화문은 의사소통 기능을 익히는 자료입니다. 내용만 묻지 말고 **같은 뜻의 다른
표현**을 함께 외우게 하십시오. 원장 지시(2026-09-07): 「단순 내용일치 말고,
xxxx 표현은 xxxx 표현으로 바꿀 수 있다, 이런 식으로 비슷한 표현들을 같이 암기할
수 있도록.」

형식은 이렇습니다.

    "How can I get to the Star Stadium?" 은
    "What's the best way to get to the Star Stadium?" 으로 바꿔 쓸 수 있다.   → O

**각 문항의 `type` 을 정확히 정하십시오.**
  · `content`    — 대화 내용을 묻는 것
  · `paraphrase` — 표현을 바꿔 쓸 수 있는지 묻는 것

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


def build_params(title, kind, sentences, n_items):
    body = prompts.number_sentences(sentences)
    dialog = kind == "textbook_dialogue"
    label = "대화문" if dialog else "지문"
    extra = ("\n**바꿔쓰기(`paraphrase`) 문항을 절반쯤 섞으십시오.** "
             f"{n_items}개 중 대략 {n_items // 2}개입니다." if dialog else "")
    user = (f"# {label}: {title}\n\n{body}\n\n"
            f"위 {label}으로 O/X 문항을 **{n_items}개 안팎** 만드십시오.\n"
            f"문장이 {len(sentences)}개이므로 문장 하나당 대략 한 문항입니다.{extra}")
    system = SYSTEM + (DIALOGUE_EXTRA if dialog else "")
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": schema(n_items)}},
        "thinking": {"type": "adaptive"},
    }


def parse(raw, sentences):
    """근거 문장 번호가 지문 범위를 벗어난 문항은 버린다."""
    n = len(sentences)
    kept, rejects = [], []
    used = set()
    for i, it in enumerate(raw.get("items", [])):
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
