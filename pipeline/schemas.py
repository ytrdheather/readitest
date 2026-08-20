# -*- coding: utf-8 -*-
"""
구조화 출력 스키마 (기획서 §6.3 원칙 4 「구조화 출력 강제」).

두 가지를 스키마 레벨에서 못 하게 막는다:

  1. **마스터에 없는 코드** — grammar_point·modification_type·question_type 을 enum 으로
     박아 넣는다. 자유 텍스트로 새 코드를 지어내는 게 구조적으로 불가능해진다.
  2. **승인되지 않은 유형** — question_type.value_approved = true 인 것만 enum 에 들어간다.
     T-GRAMMAR-STANDALONE(단문 나열형)은 반려됐으므로 애초에 생성될 수 없다.

**char offset 은 모델에게 시키지 않는다.** 모델은 `surface`(원문 그대로의 문자열)와
`sentence_no` 만 내고, span_start/span_end 는 파이썬이 body_text 에서 찾아 계산한다.
LLM 의 문자 오프셋 계산은 조용히 한두 칸씩 밀리는데, 이 프로젝트에서 그건
가장 잡기 어려운 종류의 버그다 (설계원칙 7). 부수 효과로 환각 탐지가 공짜로 딸려온다 —
지문에 없는 surface 를 냈으면 그 자리에서 걸린다.

NONE 센티널: JSON Schema 에서 enum + null 조합이 지저분해서, "없음"은 문자열 "NONE" 으로
받고 파이썬에서 None 으로 바꾼다.
"""

NONE = "NONE"

CONFIDENCE = ["high", "medium", "low"]
DIFFICULTY = ["easy", "medium", "hard"]
OPTION_LANG = ["ko", "en", "na"]


def _enum_or_none(codes):
    return {"type": "string", "enum": sorted(codes) + [NONE]}


def pass_a_schema(grammar_codes, mod_codes, qtype_codes):
    """패스 A — 태깅 A + 태깅 B + 문항. 세 축을 한 번에 낸다 (기획서 §6.2)."""
    gp = {"type": "string", "enum": sorted(grammar_codes)}
    return {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "description": "태깅 A — 어법 전수 태깅. 빠뜨리는 것보다 넘치는 게 낫다.",
                "items": {
                    "type": "object",
                    "properties": {
                        "sentence_no": {"type": "integer"},
                        "surface": {
                            "type": "string",
                            "description": "지문에서 **글자 그대로** 잘라낸 연속된 문자열. "
                                           "고치거나 줄이거나 요약하지 말 것. 찾을 수 없으면 버려진다.",
                        },
                        "grammar_point_code": gp,
                        "rationale": {
                            "type": "string",
                            "description": "왜 이게 출제 지점인가. 원장이 재판단하지 않아도 되게 쓴다.",
                        },
                        "confidence": {"type": "string", "enum": CONFIDENCE},
                        "applicable_modifications": {
                            "type": "array",
                            "items": {"type": "string", "enum": sorted(mod_codes)},
                            "description": "이 지점에 기계적으로 적용 가능한 변형 유형.",
                        },
                    },
                    "required": ["sentence_no", "surface", "grammar_point_code",
                                 "rationale", "confidence", "applicable_modifications"],
                    "additionalProperties": False,
                },
            },
            "logic": {
                "type": "array",
                "description": "태깅 B — 문장별 논리 역할. 모든 문장에 하나씩, 빠짐없이.",
                "items": {
                    "type": "object",
                    "properties": {
                        "sentence_no": {"type": "integer"},
                        "role": {
                            "type": "string",
                            "description": "도입질문 / 정의 / 범위 / 원인 / 부정적결과 / 전환 / "
                                           "해결책 / 결과요약 / 주제문 / 결론문 등",
                        },
                        "signal": {"type": "string", "description": "연결 신호어. 없으면 NONE."},
                        "is_blank_candidate": {
                            "type": "boolean",
                            "description": "빈칸 후보. 거의 항상 주제문·결론문·요약문만 true.",
                        },
                    },
                    "required": ["sentence_no", "role", "signal", "is_blank_candidate"],
                    "additionalProperties": False,
                },
            },
            "items": {
                "type": "array",
                "description": "문항. 전부 지문 문맥 안에서 판단하게 만든다 (P-PASSAGE-EMBEDDED).",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_type_code": {"type": "string", "enum": sorted(qtype_codes)},
                        "grammar_point_code": _enum_or_none(grammar_codes),
                        "stem": {"type": "string", "description": "발문. 지문 발췌를 포함해도 된다."},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "body": {"type": "string"},
                                    "is_answer": {"type": "boolean"},
                                    "violates_point_code": {
                                        **_enum_or_none(grammar_codes),
                                        "description": "이 선지가 위반하는 포인트. **하나만.** "
                                                       "위반이 없으면 NONE.",
                                    },
                                    "via_modification": {
                                        **_enum_or_none(mod_codes),
                                        "description": "어떤 변형으로 만들었나. 원문 그대로면 NONE.",
                                    },
                                },
                                "required": ["label", "body", "is_answer",
                                             "violates_point_code", "via_modification"],
                                "additionalProperties": False,
                            },
                        },
                        "answer_key": {"type": "string"},
                        "explanation": {"type": "string"},
                        "difficulty": {"type": "string", "enum": DIFFICULTY},
                        "option_lang": {"type": "string", "enum": OPTION_LANG},
                        "source_tags": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "겨냥한 태그의 sentence_no 가 아니라 tags 배열의 0-기반 인덱스.",
                        },
                    },
                    "required": ["question_type_code", "grammar_point_code", "stem", "options",
                                 "answer_key", "explanation", "difficulty", "option_lang",
                                 "source_tags"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["tags", "logic", "items"],
        "additionalProperties": False,
    }


def pass_b_schema():
    """패스 B — 역방향 검증. 정답을 절대 프롬프트에 넣지 않는다 (기획서 §6.2)."""
    return {
        "type": "object",
        "properties": {
            "chosen_label": {"type": "string", "description": "고른 선지의 라벨. 서술형이면 답 문자열."},
            "reasoning": {"type": "string", "description": "왜 그렇게 골랐는지 한두 문장."},
            "confident": {
                "type": "boolean",
                "description": "답이 하나로 확정되면 true. 둘 이상 가능하거나 근거가 모호하면 false.",
            },
        },
        "required": ["chosen_label", "reasoning", "confident"],
        "additionalProperties": False,
    }


def pass_c_schema():
    """패스 C — 선지 유일성. 오답 선지 하나하나를 따로 판정한다."""
    return {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "could_be_answer": {
                            "type": "boolean",
                            "description": "이 선지가 정답이 될 수 있는 해석이 존재하는가.",
                        },
                        "why": {"type": "string"},
                    },
                    "required": ["label", "could_be_answer", "why"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["verdicts"],
        "additionalProperties": False,
    }
