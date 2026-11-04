# -*- coding: utf-8 -*-
"""
동형 모의고사 선지 유일성 검증 — 기획서 §6.2 「패스 C」 를 동형에 붙인 것 (2026-11-04).

출제자(생성 모델)는 정답을 알고 문항을 쓰므로 **다른 선지도 답이 되는 것**을 못 본다.
영덕중2 7세트 19번 복수정답은 원장 검수에서야 잡혔다(2026-10-06). 그래서 정답을
**알려주지 않고** 다른 호출이 시험지를 풀게 하고, 선지 다섯 개를 하나하나 「이것도 답이
될 수 있는가」 판정하게 한다.

    정답이 아닌 선지가 답이 될 수 있다   → 복수정답 의심
    정해 둔 정답이 답이 될 수 없다       → 정답 오류 의심
    고른 답이 정해 둔 정답과 다르다     → 발문·근거 모호 의심

걸린 문항은 **버리지 않고** `diagnostics.review_needed` 에 남긴다 — 정답지 맨 위에
「검수 필요」 로 찍혀 원장이 그 문항만 보면 된다 (기획서 §7.1.1 문항 검수).

모델: 패스 C 설계는 Haiku 였지만 드릴 검증(`drill_grammar.build_verify_params`)과 같이
생성 모델로 한 번에 묻는다. 어법 판정이 「문법적으로 옳은가」 라 저가 모델은 함정 선지에서
흔들리고, 시험지 한 벌을 한 호출로 보면 문항마다 지문을 다시 넣지 않아도 된다.
"""
import re

from .models import PASS_A_MODEL

CIRC = "①②③④⑤"

SYSTEM = """당신은 중학교 영어 내신 시험지를 **처음 받아 보는 검토 교사**입니다.
출제자가 정한 정답은 알려주지 않습니다. 문항마다 다음을 하십시오.

1. 그냥 풀어서 답을 하나 고르십시오 (`chosen`, 1~5).
2. 선지 다섯 개를 **하나하나 따로** 판정하십시오:
   > 이 선지가 이 발문의 정답이 될 수 있는 해석이 존재하는가?
   문법적으로 옳거나(「틀린 것」을 묻는 문항이면 틀렸거나), 문맥상 성립하거나,
   발문을 다르게 읽으면 답이 될 수 있으면 `could_be_answer` 를 true 로 하십시오.
3. 답이 둘 이상이거나, 하나도 없거나, 근거가 지문에 없거나, 발문이 모호하면
   `note_ko` 에 한 문장으로 적으십시오. 문제없으면 빈 문자열.

**true 를 주저하지 마십시오.** 이상한 문항을 걸러내는 것이 목적입니다.
다섯 개 전부에 판정을 내리십시오."""


def schema():
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "no": {"type": "integer"},
                        "chosen": {"type": "integer"},
                        "verdicts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "option": {"type": "integer"},
                                    "could_be_answer": {"type": "boolean"},
                                    "why": {"type": "string"},
                                },
                                "required": ["option", "could_be_answer", "why"],
                                "additionalProperties": False,
                            },
                        },
                        "note_ko": {"type": "string"},
                    },
                    "required": ["no", "chosen", "verdicts", "note_ko"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def build_params(title, materials, items):
    """정답·해설을 빼고 시험지에 찍히는 것만 넘긴다."""
    mats = {m["id"]: m for m in materials}
    used = []
    for it in items:
        for mid in [it.get("material_id")] + re.findall(r"\[([PT]\d+)\]", it.get("stem_ko", "")):
            if mid in mats and mid not in used:
                used.append(mid)
    parts = [f"### {mid} · {mats[mid]['title']}\n{mats[mid]['text']}" for mid in used]
    qs = []
    for it in items:
        opts = "\n".join(f"  {CIRC[i]} {o}" for i, o in enumerate(it.get("options", [])[:5]))
        qs.append(f"{it['no']}. [{it.get('material_id', '')}] {it['stem_ko']}\n{opts}")
    user = (f"# {title}\n\n## 자료\n\n" + "\n\n".join(parts)
            + f"\n\n## 선택형 {len(items)}문항\n\n" + "\n\n".join(qs))
    return {
        "model": PASS_A_MODEL,
        "max_tokens": 32000,
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": schema()}},
        "thinking": {"type": "adaptive"},
    }


def apply(items, raw):
    """걸린 문항 목록 [{no, kind, note}]. 판정이 없는 문항도 「판정 누락」 으로 남긴다."""
    got = {r.get("no"): r for r in raw.get("items", [])}
    flagged = []
    for it in items:
        r = got.get(it["no"])
        if not r:
            flagged.append({"no": it["no"], "kind": "판정 누락", "note": ""})
            continue
        key = it["answer"]
        yes = sorted(v["option"] for v in r.get("verdicts", []) if v.get("could_be_answer"))
        why = {v["option"]: v.get("why", "") for v in r.get("verdicts", [])}
        others = [p for p in yes if p != key]
        if key not in yes:                # 정해 둔 정답이 답이 못 된다 — 다른 게 답이면 그것도 적는다
            flagged.append({"no": it["no"], "kind": "정답 오류 의심",
                            "note": f"{CIRC[key - 1]} {why.get(key, '')}"
                                    + "".join(f" / 대신 {CIRC[p - 1]} {why.get(p, '')}" for p in others)})
        elif others:
            flagged.append({"no": it["no"], "kind": "복수정답 의심",
                            "note": " / ".join(f"{CIRC[p - 1]} {why.get(p, '')}" for p in others)})
        elif r.get("chosen") != key:
            flagged.append({"no": it["no"], "kind": "풀이 불일치",
                            "note": f"검토자는 {CIRC[r['chosen'] - 1] if 1 <= r.get('chosen', 0) <= 5 else '?'} 를 골랐다. "
                                    + r.get("note_ko", "")})
        elif r.get("note_ko", "").strip():
            flagged.append({"no": it["no"], "kind": "검토 메모", "note": r["note_ko"].strip()})
    return flagged
