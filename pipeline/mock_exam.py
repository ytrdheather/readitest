# -*- coding: utf-8 -*-
"""
3층 동형 모의고사.

원장이 「유형 대비용」 주력으로 지정한 것 (2026-09-06).
「각 학교 기출 유형과 유사한 기출형 문제를 2~3SET 정도 양질로」.

## 구조는 그 학교 것을 그대로 따른다

`data/stage0/mock_exam_blueprint.json` 이 설계도다. 4개교 2026-1 기말 96문항을
전수 분류해 얻은 것이라 **문항 수·서술형 유무·배점·어법을 담는 그릇**이 학교마다 다르다.

    영일  선택 21 + 서술 4(20점)   교사 자작 단락
    청명  선택 25                 단문 나열형 (20점!)
    태장  선택 19 + 서술 4(20점)   긴 외부지문
    영덕  선택 23                 짧은 대화 + 교과서 지문

**구조·형식은 이어지지만 포인트는 단원이 바뀌면 갈린다.** 2026-1 은 L3~L4 였고
이번은 L5·L6 다. 그래서 구조만 따오고 포인트를 새로 얹는다.

## 🔒 교과서 지문을 모델이 다시 쓰지 못하게 한다

이 파일에서 가장 중요한 규칙이다.

지문을 모델에게 「문제에 실으라」고 하면 **받아치면서 한 글자씩 바뀐다.**
그러면 `body_text` 불변(설계원칙 7)이 깨지고, 문항이 가리키는 자리가 어긋나고,
아이가 받는 종이와 교과서가 달라진다.

그래서 **자료(material)를 우리가 번호를 붙여 넣어 주고, 모델은 번호로만 가리킨다.**

    P1 P2 P3 …   우리가 넣은 교과서 지문·대화문·외부지문 — 모델은 **본문을 못 바꾼다**
    T1 T2 …      모델이 새로 쓰는 교사 자작 단락 — 여기만 새 글이 허용된다

`parse()` 가 P 로 시작하는 자료의 본문이 우리가 준 것과 **글자까지 같은지** 대조하고,
다르면 그 세트를 버린다.
"""
import json
import re

from .models import PASS_A_MODEL

SYSTEM = """당신은 중학교 2학년 영어 내신 시험지를 만듭니다.
**특정 학교의 지난 시험지 구조를 그대로 따르는 동형 모의고사**입니다.

## 가장 중요한 규칙 — 지문을 다시 쓰지 마십시오

자료는 `P1` `P2` … 로 번호가 붙어 주어집니다. 문항에서는 **번호로만 가리키십시오.**
지문을 문항 안에 옮겨 적지 마십시오. 한 글자라도 바꾸면 그 세트는 버려집니다.

새 글을 쓸 수 있는 곳은 **교사 자작 단락**뿐입니다. 그때는 `T1` `T2` 처럼
`T` 로 시작하는 번호를 스스로 붙이고 `materials` 에 본문을 담으십시오.

## 구조를 정확히 맞추십시오

주어진 설계도의 **선택형 문항 수 · 서술형 문항 수 · 배점 합계**를 정확히 맞추십시오.
「대략」이 아니라 **정확히**입니다. 숫자가 안 맞으면 버려집니다.

## 어법을 담는 그릇이 학교마다 다릅니다

설계도의 `grammar_vessel` 을 반드시 지키십시오. 같은 어법이라도 그릇이 다르면
아이가 못 풉니다.

  교사 자작 단락   교과서 밖의 짧은 글을 직접 써서 그 안에 밑줄을 칩니다
  단문 나열형      서로 무관한 문장 5개를 ①~⑤ 로 늘어놓고 틀린 것을 고르게 합니다
  긴 외부지문      긴 지문 하나에 밑줄 여럿을 치고 그중 틀린 것을 찾게 합니다
  짧은 대화        짧은 대화 여러 개에 각각 밑줄을 칩니다

## 선택형 문항

`options` 는 **정확히 5개**, `answer` 는 1~5 입니다.
오답은 그럴듯해야 합니다. 아이가 헷갈릴 만한 것이라야 변별이 됩니다.

## 서술형 문항

설계도의 `essay_blueprint` 를 그대로 따르십시오. 필수 어휘·단어 수·노리는 어법이
지정돼 있으면 **문항 지시문에 그 조건을 명시**하고, `answer_en` 에 모범 답을 씁니다.

## 문항 지시문은 우리말입니다

한국 중학교 시험지 그대로입니다. 선지가 영어인 것은 그대로 두십시오.

## `type` 은 아래 12종 중 하나여야 합니다

우리 마스터에 등록된 코드입니다. **한국어로 쓰지 말고 코드를 그대로** 넣으십시오.

  T-GRAMMAR-INLINE       지문·단락 안 밑줄 ①~⑤ 중 어법상 틀린 것
  T-GRAMMAR-STANDALONE   서로 무관한 문장 5개를 늘어놓고 틀린 것 (단문 나열형)
  T-GRAMMAR-USAGE        밑줄 친 말의 쓰임이 나머지와 다른 것
  T-FORM-CHOICE          (A)(B)(C) 괄호 안 어형을 짝지어 고르기
  T-VOCAB-CONTEXT        영영풀이 · 문맥에 맞는 낱말
  T-PHRASE-INFER         지시어·대명사가 가리키는 것 · 함축 의미
  T-TOPIC                주제 · 제목 · 요지
  T-DETAIL               내용 일치 · 불일치 · 언급되지 않은 것 · 세부 정보
  T-BLANK                빈칸에 들어갈 말
  T-WORD-ORDER           단어를 바르게 배열
  T-WRITE-COND           조건 영작 (서술형)
  T-WRITE-FIX            틀린 곳을 찾아 고쳐 쓰기 (서술형)"""


def schema(n_sel, n_essay):
    return {
        "type": "object",
        "properties": {
            "materials": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "kind": {"type": "string",
                                 "enum": ["given", "teacher_paragraph",
                                          "standalone_set", "dialogue_set"]},
                        "title": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["id", "kind", "title", "text"],
                    "additionalProperties": False,
                },
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "no": {"type": "integer"},
                        "material_id": {"type": "string"},
                        "type": {"type": "string", "enum": [
                            "T-GRAMMAR-INLINE", "T-GRAMMAR-STANDALONE",
                            "T-GRAMMAR-USAGE", "T-FORM-CHOICE",
                            "T-VOCAB-CONTEXT", "T-PHRASE-INFER", "T-TOPIC",
                            "T-DETAIL", "T-BLANK", "T-WORD-ORDER",
                            "T-WRITE-COND", "T-WRITE-FIX"]},
                        "points": {"type": "number"},
                        "stem_ko": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "answer": {"type": "integer"},
                        "why_ko": {"type": "string"},
                        "grammar_point": {"type": "string"},
                    },
                    "required": ["no", "material_id", "type", "points",
                                 "stem_ko", "options", "answer", "why_ko"],
                    "additionalProperties": False,
                },
            },
            "essays": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "no": {"type": "integer"},
                        "material_id": {"type": "string"},
                        "points": {"type": "number"},
                        "prompt_ko": {"type": "string"},
                        "given_words": {"type": "array", "items": {"type": "string"}},
                        "word_limit": {"type": "string"},
                        "target_grammar": {"type": "string"},
                        "answer_en": {"type": "string"},
                        "why_ko": {"type": "string"},
                    },
                    "required": ["no", "points", "prompt_ko", "given_words",
                                 "word_limit", "target_grammar", "answer_en", "why_ko"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["materials", "items", "essays"],
        "additionalProperties": False,
    }


def build_params(school, spec, common, materials, points_hint, set_no):
    """materials: [{"id":"P1","title":..,"text":..,"kind":..}] — 우리가 넣는 자료."""
    mat = "\n\n".join(
        f"### {m['id']} · {m['kind']} · {m['title']}\n{m['text']}" for m in materials)

    ess = ""
    if spec.get("essay"):
        ess = "\n\n## 서술형 설계\n\n규칙: " + spec["essay_rule"] + "\n"
        for i, e in enumerate(spec["essay_blueprint"], 1):
            ess += f"  {i}. " + " · ".join(f"{k} {v}" for k, v in e.items()) + "\n"
        ess += (f"\n서술형은 {spec['essay']}문항, 합계 {spec['essay_points']}점입니다.\n"
                "**전치사를 묻는 자리를 하나 넣으십시오** — 원장 지시 2026-09-09: "
                "「서술형에 문제로도 1개 정도는 출제 될 수 있어」. "
                "`get off at ~ Station` · `by subway` 처럼 굳어진 결합이 좋습니다.")

    sig = "\n".join(f"  · {x}" for x in spec["signature"])
    user = f"""# {school} 동형 모의고사 {set_no}세트

## 이 학교의 구조 (2026-1 기말 96문항 전수 분류에서)

  선택형        {spec['selective']}문항
  서술형        {spec.get('essay', 0)}문항 ({spec.get('essay_points', 0)}점)
  총점          {spec['total_points']}점
  어법 그릇     **{spec['grammar_vessel']}**
                {spec['vessel_note']}
  영영풀이      {spec['vocab_items']}문항 {spec['vocab_points']}점
  단문 나열형   {spec.get('standalone', 0)}문항 {spec.get('standalone_points', 0)}점
  어형 고르기   {spec['form_choice']}문항 (T-FORM-CHOICE · 4개교가 딱 1개씩 낸다)

이 학교만의 것:
{sig}

## 이번 범위 어법

{chr(10).join(f"  {k}  {v}" for k, v in common['range_2026_2'].items() if k != 'note')}
      {common['range_2026_2']['note']}

## 배점

{points_hint}

## 자료 — **본문을 옮겨 적지 말고 번호로만 가리키십시오**

`F` 로 시작하는 자료는 지문이 아니라 **참고 정리**입니다 (의사소통 기능 · 유사 표현 · 대답 표현).
문항에 실을 지문이 아니라, 「빈칸에 들어갈 수 **없는** 말」 「바꿔 쓸 수 있는 표현」 같은 문항의
선지를 만들 때 근거로 쓰십시오. 교과서가 인정하는 유사 표현 밖의 것을 정답으로 삼지 마십시오.

{mat}
{ess}

## 내십시오

선택형 **정확히 {spec['selective']}문항**, 서술형 **정확히 {spec.get('essay', 0)}문항**.
배점 합계 **정확히 {spec['total_points']}점**.
교사 자작 단락이나 단문 나열이 필요하면 `T1` `T2` … 로 `materials` 에 새로 담으십시오.
"""
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 32000,
        "system": [{"type": "text", "text": SYSTEM,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "high",
                          "format": {"type": "json_schema",
                                     "schema": schema(spec["selective"],
                                                      spec.get("essay", 0))}},
        "thinking": {"type": "adaptive"},
    }


def _norm(s):
    s = (s or "").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return " ".join(s.split()).strip()


def parse(raw, spec, given, source_mats=None):
    """구조·배점·지문 무결성을 기계로 본다. 어긋난 것은 사유와 함께 돌려준다.

    `given` 은 우리가 넣은 자료 {id: text}. **P 로 시작하는 자료는 글자까지 같아야 한다** —
    모델이 지문을 받아치면서 바꾸는 것을 여기서 잡는다 (설계원칙 7).

    `source_mats` 는 `gather()` 가 만든 자료 목록 그대로. 모델이 응답에서 **교과서 지문을
    아예 빼먹는 일**이 있다 (2026-09-23 영일중1 3세트 — 문항 6·7·10·12·13·19 가 P1~P4 를
    가리키는데 materials 에 P 가 하나도 없었다). 시험지에 실을 지문이 사라지는 것이라
    조용히 넘어가면 안 되고, 원본이 우리 손에 있으니 **여기서 되채운다.**
    """
    problems = []
    mats = {m["id"]: m for m in raw.get("materials", [])}

    refilled = []
    for sm in (source_mats or []):
        if sm["id"] in mats:
            continue
        if not any(it.get("material_id") == sm["id"]
                   for it in raw.get("items", []) + raw.get("essays", [])):
            continue                      # 아무 문항도 안 쓴 자료는 실을 필요 없다
        m = dict(sm)
        mats[m["id"]] = m
        raw.setdefault("materials", []).insert(len(refilled), m)
        refilled.append(m["id"])
    if refilled:
        problems.append("모델이 응답에서 자료 " + "·".join(refilled) +
                        " 를 빼먹어 원본으로 채워 넣음")

    for mid, text in given.items():
        m = mats.get(mid)
        if not m:
            continue                      # 안 쓴 자료는 문제 아니다
        if _norm(m["text"]) != _norm(text):
            problems.append(f"자료 {mid} 의 본문이 원본과 다름 — 모델이 고쳐 썼다")
        elif m["text"] != text:
            # 글자는 같은데 줄바꿈이 달라진 경우. 대화문은 **발화마다 한 줄**이어야
            # 눈에 들어온다(원장 지시 2026-09-07). 조용히 원본으로 되돌린다.
            problems.append(f"자료 {mid} 의 줄바꿈이 달라 원본으로 되돌림")
        # 어느 쪽이든 **원본이 이긴다.** 모델이 받아친 판을 쓰지 않는다 (설계원칙 7).
        m["text"] = text

    items = raw.get("items", [])
    essays = raw.get("essays", [])
    if len(items) != spec["selective"]:
        problems.append(f"선택형 {len(items)}문항 (설계 {spec['selective']})")
    if len(essays) != spec.get("essay", 0):
        problems.append(f"서술형 {len(essays)}문항 (설계 {spec.get('essay', 0)})")

    total = sum(x.get("points", 0) for x in items) + \
        sum(x.get("points", 0) for x in essays)
    if abs(total - spec["total_points"]) > 0.01:
        problems.append(f"배점 합계 {total} (설계 {spec['total_points']})")

    for it in items:
        if len(it.get("options", [])) != 5:
            problems.append(f"{it.get('no')}번 선지 {len(it.get('options', []))}개")
        if not 1 <= it.get("answer", 0) <= 5:
            problems.append(f"{it.get('no')}번 정답 번호 {it.get('answer')}")
        if it.get("material_id") not in mats:
            problems.append(f"{it.get('no')}번이 모르는 자료 {it.get('material_id')} 를 가리킴")

    n_form = sum(1 for x in items if x.get("type") == "T-FORM-CHOICE")
    if n_form != spec["form_choice"]:
        problems.append(f"T-FORM-CHOICE {n_form}문항 (설계 {spec['form_choice']})")

    n_vocab = sum(1 for x in items if x.get("type") == "T-VOCAB-CONTEXT")
    if n_vocab != spec["vocab_items"]:
        problems.append(f"영영풀이 {n_vocab}문항 (설계 {spec['vocab_items']})")

    # 서술형은 **조건을 스스로 어기기 쉽다** — 단어 수를 정해 놓고 답이 그 밖으로
    # 나가거나, 필수 단어를 안 쓰는 일이 생긴다. 다만 여기는 **경고만** 한다:
    #   · 답이 (a)(b) 로 나뉘면 단어 수를 통으로 셀 수 없다
    #   · 필수 단어 `see` 를 `saw` 로 쓰는 것은 **맞는 답**이다 (문제가 과거형을 요구)
    # 그래서 확실히 틀린 것만 problems 에 넣고 나머지는 warnings 로 뺀다.
    warnings = []
    for e in essays:
        ans_en = e.get("answer_en", "")
        if re.search(r"\(\s*[abAB]\s*\)", ans_en):
            continue                      # 나뉜 답은 통으로 못 센다 — (A)(B) 대문자도 (2026-09-17 오탐)
        n = len(re.findall(r"[A-Za-z][A-Za-z'’-]*", ans_en))
        m = re.search(r"(\d+)\s*[~-]\s*(\d+)", e.get("word_limit", ""))
        if m and not int(m.group(1)) <= n <= int(m.group(2)):
            problems.append(f"서술형 {e.get('no')}번 모범답이 {n}단어 "
                            f"(조건 {e.get('word_limit')})")
        low = ans_en.lower()
        miss = [w for w in e.get("given_words", [])
                if w.lower() not in low and w.lower()[:4] not in low]
        if miss:
            warnings.append(f"서술형 {e.get('no')}번 필수 단어가 답에 안 보임 "
                            f"{miss} — 굴절형일 수 있으니 눈으로 확인")

    return {"materials": raw.get("materials", []), "items": items, "essays": essays,
            "diagnostics": {"problems": problems, "warnings": warnings,
                            "n_items": len(items), "n_essays": len(essays),
                            "total_points": total}}
