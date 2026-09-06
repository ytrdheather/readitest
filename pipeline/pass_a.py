# -*- coding: utf-8 -*-
"""패스 A — 태깅 A(어법) + 태깅 B(논리) + 문항 생성. Opus 5."""
import json
import re

from . import prompts, schemas
from .models import PASS_A_MODEL
from .passage import SpanResolver, sentences_only


def load_masters(rest):
    """마스터를 DB에서 읽는다. 승인된 유형만 문항 생성에 쓴다 (value_approved=true)."""
    grammar = rest.get("/grammar_point?select=code,category,label_ko,is_candidate,note")
    mods = rest.get("/modification_type?select=code,category,label_ko,example_before,example_after")
    qtypes = rest.get("/question_type?select=code,label_ko,option_lang,value_approved,review_tier")
    approved = [q for q in qtypes if q["value_approved"] is True]
    if not approved:
        raise SystemExit("승인된 문항 유형이 없습니다. question_type.value_approved 를 확인하십시오.")
    return {"grammar": grammar, "mods": mods, "qtypes": qtypes, "approved_qtypes": approved}


def _catalogs(m):
    """system 프롬프트에 붙일 카탈로그. 정렬 고정 — 캐시 프리픽스 안정성."""
    return "\n\n".join([
        prompts.render_catalog(
            m["grammar"], ["code", "category", "label_ko"],
            "# 어법 포인트 카탈로그 (grammar_point)\n\n"
            "이 코드 밖으로 나갈 수 없습니다. 자유 텍스트 금지."),
        prompts.render_catalog(
            m["mods"], ["code", "category", "label_ko", "example_before", "example_after"],
            "# 변형 유형 카탈로그 (modification_type)\n\n"
            "교사가 지문을 시험에 낼 때 실제로 쓰는 방법들입니다. "
            "두 학교·두 교사의 기출에서 관측된 것만 들어 있습니다."),
        prompts.render_catalog(
            m["approved_qtypes"], ["code", "label_ko", "option_lang"],
            "# 문항 유형 (question_type) — **원장이 훈련 가치를 승인한 것만**\n\n"
            "여기 없는 유형은 만들지 마십시오.\n\n"
            # 2026-09-06: 예전에는 여기에 「단문 나열형은 반려됐다」고 적혀 있었다.
            # 그날 그 유형이 승인되면서 카탈로그에는 실리는데 지침은 만들지 말라고
            # 하는 모순이 됐다. 승인 상태는 카탈로그가 이미 말해 주므로, 지침은
            # **어떻게 만들어야 하는가**만 말한다.
            "'어법 — 단문 나열형'을 만들 때는 **문장을 지문에서 가져오십시오.** "
            "아이가 이미 읽은 본문 문장을 한 자리만 건드린 것과, 아무 데서나 끌어온 "
            "문장을 나열한 것은 다릅니다. 앞은 훈련이 되고 뒤는 되지 않습니다."),
    ])


def build_params(passage, masters, batch=False):
    """messages.create() 에 그대로 넘길 파라미터."""
    sentences = sentences_only(passage["body_text"])
    system = [
        # ── 캐시 프리픽스: 지침 + 카탈로그. 지문마다 바뀌지 않는다 ──
        {"type": "text", "text": prompts.PASS_A_SYSTEM},
        {"type": "text", "text": _catalogs(masters),
         "cache_control": {"type": "ephemeral"}},
    ]
    schema = schemas.pass_a_schema(
        [g["code"] for g in masters["grammar"]],
        [m["code"] for m in masters["mods"]],
        [q["code"] for q in masters["approved_qtypes"]],
    )
    params = {
        "model": PASS_A_MODEL,
        "max_tokens": 32000,
        "system": system,
        "messages": [{
            "role": "user",
            "content": prompts.pass_a_user(
                passage.get("title") or "(제목 없음)",
                passage.get("source_detail") or "(출처 미상)",
                sentences),
        }],
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        "thinking": {"type": "adaptive"},
    }
    return params


# 화자 표시는 한 낱말이 아닐 수 있다 — 'A man:' 'Dr. Schofield:' 도 화자다.
_SPEAKER = re.compile(r"^[A-Z][A-Za-z.]{0,10}(?: [A-Za-z.]{1,12}){0,2}:\s*")
_MARKUP = re.compile(r"</?u>|[①-⑳ⓐ-ⓩ㉑-㊿]")
_PAREN_OPT = re.compile(r"\(([A-Za-z][A-Za-z' ]{0,20})\)\s*")

def _canon(s, drop_paren=False):
    s = _MARKUP.sub("", s)
    s = _SPEAKER.sub("", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    if drop_paren:                       # '(that) he meets' → 'he meets'
        s = _PAREN_OPT.sub("", s)
    return " ".join(s.split()).strip()


def parse(raw_json, passage):
    """
    모델 출력을 DB 행으로 바꾼다. 여기서 걸러지는 것:
      · 지문에 없는 surface (환각)
      · 위치를 확정할 수 없는 surface
      · 정답 선지가 0개이거나 2개 이상인 문항
      · 존재하지 않는 태그를 가리키는 문항
    """
    body = passage["body_text"]
    r = SpanResolver(body)
    NONE = schemas.NONE

    tags, tag_index_map = [], {}
    for i, t in enumerate(raw_json.get("tags", [])):
        span = r.resolve(t["surface"], t.get("sentence_no"), f"태그 #{i}")
        if not span:
            continue
        tag_index_map[i] = len(tags)
        tags.append({
            "grammar_point_code": t["grammar_point_code"],
            "span_start": span[0], "span_end": span[1],
            "surface": t["surface"],
            "sentence_no": r.sentence_of(span[0]),
            "rationale": t["rationale"],
            "confidence": t["confidence"],
            "applicable_modifications": t.get("applicable_modifications", []),
        })

    n_sent = len(r.sentences)
    logic, seen = [], set()
    for l in raw_json.get("logic", []):
        no = l["sentence_no"]
        if no in seen or not (1 <= no <= n_sent):
            continue
        seen.add(no)
        logic.append({
            "sentence_no": no,
            "role": l["role"],
            "signal": None if l.get("signal") in (NONE, "", None) else l["signal"],
            "is_blank_candidate": l["is_blank_candidate"],
        })
    logic.sort(key=lambda x: x["sentence_no"])
    missing_logic = sorted(set(range(1, n_sent + 1)) - seen)

    # 선지가 '지문 문장의 인용' 인 유형만. 주제·내용일치·빈칸·어구추론의 선지는
    # 원래 새로 쓰는 문장이라 원문과 달라야 정상이다.
    QUOTES_PASSAGE = {"T-GRAMMAR-INLINE", "T-GRAMMAR-USAGE",
                      "T-GRAMMAR-STANDALONE", "T-WRITE-FIX"}
    # 원문과 선지를 견주기 전에 **조판 차이를 걷어낸다.** 2026-09-06 에 32개 지문을
    # 태깅했더니 27건이 걸렸는데 **전부 오탐**이었다. 정답 선지는 하나도 안 걸렸고,
    # 걸린 것은 전부 이런 차이였다:
    #
    #   'B: Excuse me…'  vs  'Excuse me…'      화자 표시 (대화문 선지에는 안 붙인다)
    #   '<u>held</u>'                          밑줄 태그
    #   'ⓐWhat kinds…'                         밑줄 기호
    #   'don’t'  vs  "don't"                   아포스트로피 종류
    #   'people (that) he meets'               교과서의 「생략 가능」 괄호 표기
    #
    # 처음 이 검사를 만들 때(2026-09-01)는 서술형 지문만 봤고 대화문이 없었다.
    # 오탐이 27건이면 검사가 아니라 소음이다 — 진짜 훼손(앞이 잘리거나 낱말이
    # 바뀐 것)만 남기려면 이 차이들을 먼저 지워야 한다.
    SENTENCES = {_canon(s) for _, _, _, s in r.sentences}
    SENTENCES_NOPAREN = {_canon(s, True) for _, _, _, s in r.sentences}

    def verbatim_problem(it):
        """지문 문장을 통째로 옮긴 선지가 정말 원문과 같은지.

        실측 사례(Bicycle 2026-09-01): 발문에 「지문의 문장을 그대로 옮긴」이라 써놓고
        선지 (a) 에서 맨 앞 'Mt.' 를 빠뜨렸다. 어떤 검증도 이걸 못 잡았다.

        **부분 문자열 검사로는 안 잡힌다** — 앞이 잘려도 substring 은 통과한다.
        그래서 규칙을 좁혔다: **완전한 문장처럼 보이는 선지**(대문자로 시작하고
        문장부호로 끝남)는 **지문의 어느 문장과 정확히 같아야 한다.**
        발췌형 선지(소문자로 시작)는 대상이 아니다 — 중간을 잘라 쓰는 게 정상이다.
        오답 선지는 일부러 변형하므로 변형·위반 표시가 있으면 건너뛴다.
        """
        if it.get("question_type_code") not in QUOTES_PASSAGE:
            return []
        bad = []
        for o in it.get("options", []):
            if o.get("via_modification") != NONE or o.get("violates_point_code") != NONE:
                continue
            cand = " ".join(o["body"].split()).strip()
            # 문장 번호 표시가 붙는 관행: "… over it ([6])"
            cand = re.sub(r"\s*\(\[\d+\]\)\s*$", "", cand).strip()
            if len(cand) < 20 or "___" in cand:
                continue
            looks_full = cand[0].isupper() and cand[-1] in ".?!"
            if not looks_full:
                continue
            c1 = _canon(cand)
            if c1 in SENTENCES or _canon(cand, True) in SENTENCES_NOPAREN:
                continue
            bad.append(o["label"])
        return bad

    items, item_rejects = [], []
    for i, it in enumerate(raw_json.get("items", [])):
        opts = it.get("options", [])
        answers = [o for o in opts if o["is_answer"]]
        if opts and len(answers) != 1:
            item_rejects.append((f"문항 #{i} {it['question_type_code']}",
                                 f"정답 선지가 {len(answers)}개"))
            continue
        bad = [o["label"] for o in opts
               if o["is_answer"] and o["violates_point_code"] != NONE
               and it["question_type_code"] not in ("T-GRAMMAR-INLINE", "T-WRITE-FIX")]
        items.append({
            "_verbatim_problem": verbatim_problem(it),
            "question_type_code": it["question_type_code"],
            "grammar_point_code": None if it["grammar_point_code"] == NONE
                                  else it["grammar_point_code"],
            "stem": it["stem"],
            "answer_key": it["answer_key"],
            "explanation": it["explanation"],
            "difficulty": it["difficulty"],
            "option_lang": it["option_lang"],
            "source_tags": [tag_index_map[s] for s in it.get("source_tags", [])
                            if s in tag_index_map],
            "options": [{
                "label": o["label"], "body": o["body"], "is_answer": o["is_answer"],
                "violates_point_code": None if o["violates_point_code"] == NONE
                                       else o["violates_point_code"],
                "via_modification": None if o["via_modification"] == NONE
                                    else o["via_modification"],
                "ordinal": j + 1,
            } for j, o in enumerate(opts)],
            "_answer_violates_point": bad,
        })

    return {
        "passage_id": passage.get("id"),
        "body_text_sha256": passage["body_text_sha256"],
        "tags": tags,
        "logic": logic,
        "items": items,
        "diagnostics": {
            "sentence_count": n_sent,
            "tags_returned": len(raw_json.get("tags", [])),
            "tags_kept": len(tags),
            "span_rejects": [{"where": w, "reason": why, "surface": s}
                             for w, why, s in r.rejects],
            "logic_missing_sentences": missing_logic,
            "items_returned": len(raw_json.get("items", [])),
            "items_kept": len(items),
            "item_rejects": [{"where": w, "reason": why} for w, why in item_rejects],
            "verbatim_problems": [
                {"item": i, "type": x["question_type_code"], "options": x["_verbatim_problem"]}
                for i, x in enumerate(items) if x["_verbatim_problem"]],
        },
    }


def extract_json(message):
    """output_config.format 이 걸려 있으면 첫 text 블록이 유효한 JSON이다."""
    text = next((b.text for b in message.content if b.type == "text"), None)
    if text is None:
        raise SystemExit(f"text 블록이 없습니다. stop_reason={message.stop_reason}")
    return json.loads(text)
