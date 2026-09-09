# -*- coding: utf-8 -*-
"""
1층 드릴 a — 어법 확인.

원장 지정(2026-09-05)의 1층 드릴 세 갈래 중 a.
「진짜로 기초적 어법확인을 위한 **맞는 표현 틀린 표현**, 혹은 맞는 어법 틀린 어법
확인형 드릴」.

## 재료는 이미 붙어 있는 태그다

`passage_tag` 317개(L5·L6 전 지문)에 `surface`(본문 그대로)와 `rationale`이 있고,
**rationale 이 틀린 형태까지 직접 적어 놨다.**

    [MOD_ADJ_VS_ADV] 'internationally famous'
      형용사 famous를 수식하므로 부사 internationally가 맞다.
      **international famous** 처럼 형용사로 바꾼 오답을 심기 쉬운 자리.

## 그런데 모델을 부른다 — 규칙으로 뽑으면 위험하다

어휘 드릴(`drill_vocab.py`)은 모델을 안 불렀다. 재료가 이미 **구조화**돼 있었기
때문이다. 여기는 다르다 — 틀린 형태가 **한국어 산문 속에** 있다.
정규식으로 캐내면 「틀렸다고 낸 것이 사실은 맞는 표현」인 사고가 난다.
어법 드릴에서 그것은 아이에게 틀린 것을 가르치는 일이라 되돌릴 수 없다.

그래서 **산문 → 구조**의 한 걸음만 모델에 맡기고, 나온 것을 기계로 검증한다.

## 검증이 이 파일의 핵심이다

  · `correct` 는 `surface` 와 **글자까지 같아야 한다** (설계원칙 7의 연장)
  · `wrong` 은 `correct` 와 달라야 하고, 서로도 달라야 한다
  · `wrong` 을 넣은 문장이 원문과 같으면 버린다 — 바뀐 게 없다는 뜻이다
  · `wrong` 이 본문 어딘가에 그대로 있으면 **의심**하고 버린다.
    본문에 있는 표현을 「틀렸다」고 하면 아이가 혼란스럽다

하나라도 어긋나면 그 문항을 **버린다.** 적게 내는 것이 틀리게 내는 것보다 낫다.
"""
import re

from . import prompts
from .models import PASS_A_MODEL

SYSTEM = """당신은 중학교 2학년 영어 내신을 준비시키는 교사입니다.
본문에서 뽑아 둔 **어법 포인트**마다, 학교 시험이 실제로 심는 **틀린 형태**를 답니다.

## 무엇을 만드는가

각 포인트에 대해:

  correct  본문에 있는 그대로의 표현 — **한 글자도 바꾸지 마십시오**
  wrong    그 자리에 들어갈 법한 **틀린** 형태 1~3개
  why_ko   왜 correct 가 맞고 wrong 이 틀린지 한 줄 (중2가 읽을 말로)

## 틀린 형태를 고르는 기준

1. **그 자리에서 실제로 틀려야 합니다.** 다른 문맥에서 쓰일 수 있는 표현이라도
   이 문장에서 틀리면 됩니다. 그러나 이 문장에서도 맞는 표현이면 **절대 안 됩니다.**
2. **그럴듯해야 합니다.** 아이가 헷갈릴 만한 것이라야 훈련이 됩니다.
   `internationally famous` 의 오답은 `international famous` 이지 `banana famous` 가
   아닙니다.
3. **주어진 근거(rationale)에 적힌 오답을 우선 씁니다.** 태깅할 때 이미 판단한
   것이라 그것이 가장 정확합니다. 근거에 없으면 그때 새로 만듭니다.
4. 철자만 틀린 것(`famouss`)은 어법이 아니라 철자입니다. 내지 마십시오.

## 개수

포인트 하나에 **wrong 을 2개** 다는 것을 기본으로 하십시오.
확실한 오답이 하나뿐이면 1개만 답니다. 억지로 채우지 마십시오.

## correct 는 복사입니다

`surface` 를 그대로 옮기십시오. 대문자·아포스트로피·괄호까지 같아야 합니다.
다듬거나 고치면 그 문항은 버려집니다."""


def schema():
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tag_id": {"type": "string"},
                        "correct": {"type": "string"},
                        "wrong": {"type": "array", "items": {"type": "string"}},
                        "why_ko": {"type": "string"},
                    },
                    "required": ["tag_id", "correct", "wrong", "why_ko"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def build_params(title, body, tags):
    """지문 한 편의 태그를 한 번에 처리한다."""
    lines = []
    for t in tags:
        lines.append(f"- tag_id: {t['id']}\n"
                     f"  포인트: {t['grammar_point_code']}\n"
                     f"  surface: {t['surface']}\n"
                     f"  근거: {t['rationale']}")
    user = (f"# 지문: {title}\n\n{body}\n\n"
            f"# 어법 포인트 {len(tags)}개\n\n" + "\n".join(lines) +
            f"\n\n위 {len(tags)}개 **전부**에 대해 correct·wrong·why_ko 를 내십시오. "
            f"tag_id 를 그대로 옮겨 짝을 맞추십시오.")
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": SYSTEM,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": schema()}},
        "thinking": {"type": "adaptive"},
    }


def _norm(s):
    """따옴표 모양 차이만 흡수한다. 그 밖의 차이는 진짜 차이로 본다."""
    return (s.replace("’", "'").replace("‘", "'")
             .replace("“", '"').replace("”", '"').strip())


def _appears_elsewhere(w, body, span_start, span_end, correct):
    """그 오답이 본문 **다른 자리에 멀쩡히 쓰이고 있는지** 본다.

    처음 판은 `w in body` 로 봤는데 이게 틀렸다. `by spraying` 의 오답 `by spray`
    는 정답의 앞부분이라 당연히 본문에 있다 — 그런데 「본문에 실재하므로 오답으로
    못 쓴다」고 21개를 버렸다. **-s · -ly · -ing · to 를 빠뜨리는 것이 가장 흔한
    오답 유형인데 그것만 골라 버린 셈이다.**

    그래서 두 가지를 고쳤다.
      · 오답이 정답의 **부분 문자열**이면 검사하지 않는다 (누락형 오답)
      · 그 밖에는 **자기 자리를 뺀 본문**에서 낱말 경계로 찾는다
    """
    if not w or len(w) <= 3:
        return False
    if w in correct:
        return False
    rest = body[:span_start] + "\x00" + body[span_end:]
    return re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", rest) is not None


def parse(raw, tags, body):
    """검증을 통과한 것만 남긴다. 사유를 함께 돌려준다."""
    by_id = {t["id"]: t for t in tags}
    kept, rejects = [], []
    for it in raw.get("items", []):
        t = by_id.get(it.get("tag_id"))
        if not t:
            rejects.append((it.get("tag_id"), "모르는 tag_id"))
            continue
        if _norm(it.get("correct", "")) != _norm(t["surface"]):
            rejects.append((t["surface"], f"correct 가 본문과 다름: {it.get('correct')!r}"))
            continue

        good = []
        for w in it.get("wrong", []):
            w = w.strip()
            if not w:
                continue
            if _norm(w) == _norm(t["surface"]):
                rejects.append((t["surface"], f"wrong 이 정답과 같음: {w!r}"))
                continue
            if w in good:
                continue
            if _appears_elsewhere(w, body, t["span_start"], t["span_end"], t["surface"]):
                rejects.append((t["surface"], f"wrong 이 본문에 실재함: {w!r}"))
                continue
            good.append(w)
        if not good:
            rejects.append((t["surface"], "쓸 수 있는 wrong 이 없음"))
            continue

        kept.append({"tag_id": t["id"], "point": t["grammar_point_code"],
                     "span_start": t["span_start"], "span_end": t["span_end"],
                     "correct": t["surface"], "wrong": good[:3],
                     "why_ko": (it.get("why_ko") or "").strip(),
                     "rationale": t["rationale"]})
    return {"items": kept,
            "diagnostics": {"returned": len(raw.get("items", [])),
                            "kept": len(kept), "given": len(tags),
                            "rejects": rejects}}


_WS = re.compile(r"\s+")


def in_sentence(body, span_start, span_end, sentences):
    """스팬이 걸린 문장을 찾아 (문장번호, 문장) 으로 돌려준다.

    `sentences` 는 `pipeline.passage.split_sentences(body)` 결과다 —
    드릴 b·학습지와 **같은 번호**를 쓰기 위해서다.
    """
    for no, s, e, text in sentences:
        if s <= span_start and span_end <= e:
            return no, text
    return None, None


# ═══════════════════════════════════════════════════════════════════
#  검증 한 걸음 더 — 「그 오답이 정말 틀렸는가」
#
#  실물을 뽑아 보고 찾았다. `How long will it take?` 의 오답으로 나온
#  `How long will that take?` 는 **문법적으로 멀쩡한 문장**이다. 뜻만 다르다.
#  그런데 B절은 「밑줄 친 부분이 어법상 틀렸습니다」라고 단정한다 —
#  맞는 문장을 틀렸다고 가르치는 셈이 된다.
#
#  parse() 의 검사는 구조만 본다(정답과 같은가 · 본문에 있는가). 「영어로서
#  틀렸는가」는 구조로 알 수 없어서 한 걸음을 더 둔다. 출력이 짧아 값이 싸다.
# ═══════════════════════════════════════════════════════════════════

VERIFY_SYSTEM = """당신은 영어 어법 문항을 검수합니다.

문장과 그 안의 **밑줄 자리**, 그리고 거기에 넣을 「틀린 형태」 후보를 받습니다.
후보를 넣었을 때 그 문장이 **영어로서 틀린지** 판정하십시오.

judgement 값:

  wrong   넣으면 문장이 어법상 **틀린다**. 문항으로 써도 좋다
  ok      넣어도 **맞는 영어**다. 뜻만 달라질 뿐이다 → 문항으로 쓰면 안 된다
  odd     문법은 되지만 매우 어색하거나 뜻이 통하지 않는다 → 쓰지 않는다

## 주의

`How long will it take?` → `How long will that take?` 는 **ok** 입니다.
that 도 주어로 쓸 수 있어 문장이 성립합니다. 뜻이 달라질 뿐입니다.

`How long will it take?` → `How long will it takes?` 는 **wrong** 입니다.
조동사 뒤에 3인칭 단수형이 올 수 없습니다.

전치사가 바뀌어 그 자리에서 쓰이지 않는 결합이 되면 **wrong** 입니다.
(`get off at the station` → `get off in the station`)

판정만 하십시오. 고치지 마십시오."""


def verify_schema():
    return {
        "type": "object",
        "properties": {
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tag_id": {"type": "string"},
                        "candidate": {"type": "string"},
                        "judgement": {"type": "string",
                                      "enum": ["wrong", "ok", "odd"]},
                        "note_ko": {"type": "string"},
                    },
                    "required": ["tag_id", "candidate", "judgement", "note_ko"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["checks"],
        "additionalProperties": False,
    }


def build_verify_params(title, items):
    lines = []
    for it in items:
        for w in it["wrong"]:
            lines.append(f"- tag_id: {it['tag_id']}\n"
                         f"  문장: {it['sentence']}\n"
                         f"  원래 표현: {it['correct']}\n"
                         f"  후보: {w}")
    user = (f"# {title}\n\n아래 후보 {len(lines)}개를 각각 판정하십시오. "
            f"같은 tag_id 가 여러 번 나올 수 있으니 candidate 까지 함께 돌려주십시오.\n\n"
            + "\n".join(lines))
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": VERIFY_SYSTEM,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": verify_schema()}},
        "thinking": {"type": "adaptive"},
    }


def apply_verify(items, raw):
    """`wrong` 이라 판정된 것만 남긴다. 하나도 안 남은 문항은 버린다."""
    verdict = {}
    for c in raw.get("checks", []):
        verdict[(c.get("tag_id"), _norm(c.get("candidate", "")))] = (
            c.get("judgement"), c.get("note_ko", ""))
    kept, dropped = [], []
    for it in items:
        good, bad = [], []
        for w in it["wrong"]:
            j, note = verdict.get((it["tag_id"], _norm(w)), (None, ""))
            if j == "wrong":
                good.append(w)
            else:
                bad.append((w, j or "판정없음", note))
        if good:
            it["wrong"] = good
            if bad:
                it["verify_dropped"] = [{"wrong": w, "judgement": j, "note_ko": n}
                                        for w, j, n in bad]
            kept.append(it)
        else:
            dropped.append((it["correct"], "모든 오답이 실은 맞는 표현이라 버림: "
                            + ", ".join(f"{w}({j})" for w, j, _ in bad)))
    return kept, dropped
