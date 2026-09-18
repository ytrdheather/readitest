# -*- coding: utf-8 -*-
"""
1층 드릴 c — 어휘.

원장 지정(2026-09-05)의 1층 드릴 세 갈래 중 c.
「어휘, 영영어휘 뜻을 잘 암기했는지 확인할 수 있는 드릴」.

## 모델을 부르지 않는다

a(어법)·b(내용 확인)와 달리 **여기서는 API 를 쓰지 않는다.**
학교가 준 단어·뜻·영영풀이·예문이 이미 파일에 있고, 드릴은 그것을 **배열만**
바꾼 것이기 때문이다. 모델을 부르면 없는 뜻을 지어내거나 학교가 준 것과 다른
영영풀이를 쓸 위험만 생긴다 — 시험에 나오는 것은 **학교가 준 그 문장**이다.

## 형식은 학교가 실제로 내는 것을 그대로 쓴다

배부물에서 관측한 다섯 가지다
([어휘 대조](../data/stage0/comparisons/어휘_자습서_학교_대조.md)).

    both      영한 · 한영 양방향       영덕 Warm-Up(30단어 60칸) · 태장 1쪽
    def       영영풀이 → 단어 쓰기      태장 2쪽 · 영일 1·2쪽
    match     영영풀이 ↔ 단어 ↔ 뜻 연결  영덕 Basic A
    cloze     문맥 빈칸 (보기 제시)     태장 1쪽 B · 영덕 Basic B
    phrase    구(句) 채우기            영덕 Basic C

`def` 와 `cloze` 는 **재료가 있는 낱말만** 낼 수 있다. 영영풀이가 없는 낱말을
끼워 넣으려고 지어내지 않는다 — 없으면 그 낱말은 그 형식에서 빠진다.

## 예문 빈칸은 낱말을 지운 자리다

`cloze` 는 학교가 준 예문에서 그 낱말만 지운다. 굴절형(buried, researched)도
지워야 하므로 어간으로 견주어 찾는다. 못 찾으면 **그 문항을 버린다** —
엉뚱한 자리를 지우느니 안 내는 것이 낫다.
"""
import random
import re

# 굴절 어미. 긴 것부터 떼어 어간을 만든다.
_SUFFIX = ("ing", "ies", "ied", "es", "ed", "s")


def stem(w):
    """예문 속 굴절형과 표제어를 같은 자리로 보낸다.

    처음 판에서 `bury→buried` · `continue→continued` · `hide→hiding` 세 개가
    전부 빠졌다. 셋 다 철자가 바뀌는 동사인데, 하필 시험에 잘 나오는 것들이라
    그냥 버릴 수 없었다. 그래서 세 가지를 더 본다 —
    **-ied → -y · 끝의 e 떼기 · 자음 중복 되돌리기.**
    """
    w = w.lower()
    if len(w) > 4 and w.endswith("ied"):          # buried → bury
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("ies"):          # studies → study
        return w[:-3] + "y"
    for s in _SUFFIX:
        if len(w) > len(s) + 2 and w.endswith(s):
            w = w[: -len(s)]
            if len(w) > 2 and w[-1] == w[-2]:     # running → runn → run
                w = w[:-1]
            break
    if len(w) > 3 and w.endswith("e"):            # continue·hide 를 continu·hid 로
        w = w[:-1]
    return w


def blank_example(example, word, mark="__________"):
    """예문에서 그 낱말(굴절형 포함)을 지운다. 못 지우면 None."""
    if not example or not word:
        return None
    if " " in word:                              # 구(句)는 통째로 지운다
        # 표제어가 `be well known for` 인데 예문은 `is well known for` 다.
        # be동사는 문장에 맞춰 변하므로 그 부분을 떼고도 한 번 찾아본다.
        cands = [word]
        if word.lower().startswith("be "):
            cands.append(word[3:])
        for c in cands:
            out, n = re.compile(re.escape(c), re.I).subn(mark, example, count=1)
            if n:
                return out
        return None
    target = stem(word)
    toks = re.findall(r"[A-Za-z']+|[^A-Za-z']+", example)
    for i, t in enumerate(toks):
        if t.isalpha() and stem(t) == target:
            toks[i] = mark
            return "".join(toks)
    return None


def _pick(words, need, rng):
    return [w for w in words if all(w.get(k) for k in need)]


def build(title, words, kinds=("both", "def", "cloze", "match", "phrase"),
          seed=None, phrases=()):
    """드릴 한 부를 만든다. 반환값은 렌더러가 그대로 찍는 형태다."""
    rng = random.Random(seed)
    sec = []

    if "both" in kinds:
        # 양방향. 영덕이 30단어를 60칸으로 내므로 순서를 섞어 두 번 묻는다.
        # 우리말 뜻이 없는 낱말은 **어느 방향으로도 묻지 않는다.** 문제 칸이 비면 못 푸는
        # 문항이고, 정답 칸이 비면 강사가 채점을 못 한다 (영일중1 L7 — 뜻이 손글씨라 47개가 비었다).
        en2ko = [w for w in words if (w.get("ko") or w.get("gloss_ko"))]
        ko2en = list(en2ko)
        rng.shuffle(ko2en)
        sec.append({"kind": "both", "title": "빈칸에 영어는 우리말로, 우리말은 영어로 쓰시오.",
                    "en2ko": [{"word": w["word"], "answer": w.get("ko") or w.get("gloss_ko", "")}
                              for w in en2ko],
                    "ko2en": [{"ko": w.get("ko") or w.get("gloss_ko", ""), "answer": w["word"]}
                              for w in ko2en]})

    have_def = _pick(words, ("def_en",), rng)
    if "def" in kinds and have_def:
        sec.append({"kind": "def", "title": "다음 영영풀이에 알맞은 단어를 쓰시오.",
                    "items": [{"def_en": w["def_en"], "ko": w.get("ko", ""),
                               "answer": w["word"]} for w in have_def]})

    if "match" in kinds and len(have_def) >= 4:
        # 영덕 Basic A 는 4문항 묶음이다. 같은 크기로 여러 묶음을 낸다.
        pool = list(have_def)
        rng.shuffle(pool)
        groups = [pool[i:i + 4] for i in range(0, len(pool) // 4 * 4, 4)]
        sec.append({"kind": "match",
                    "title": "영영풀이에 해당하는 단어와 우리말 뜻을 연결하시오.",
                    "groups": [{"defs": g,
                                "words": rng.sample([x["word"] for x in g], len(g)),
                                "kos": rng.sample([x.get("ko", "") for x in g], len(g))}
                               for g in groups]})

    if "cloze" in kinds:
        items = []
        for w in words:
            blanked = blank_example(w.get("example_en"), w["word"])
            if blanked:
                items.append({"sentence": blanked, "answer": w["word"],
                              "ko": w.get("example_ko", "")})
        if items:
            # 보기는 5개씩 묶어 준다 — 태장·영덕이 그렇게 낸다.
            rng.shuffle(items)
            sec.append({"kind": "cloze",
                        "title": "빈칸에 알맞은 말을 [보기]에서 찾아 쓰시오. (한 번씩만 쓸 것)",
                        "chunks": [items[i:i + 5] for i in range(0, len(items), 5)]})

    if "phrase" in kinds and phrases:
        sec.append({"kind": "phrase", "title": "우리말과 뜻이 같도록 빈칸을 채우시오.",
                    "items": list(phrases)})

    return {"title": title, "sections": sec,
            "n_words": len(words),
            "counts": {s["kind"]: _count(s) for s in sec}}


def _count(s):
    if s["kind"] == "both":
        return len(s["en2ko"]) + len(s["ko2en"])
    if s["kind"] == "match":
        return sum(len(g["defs"]) for g in s["groups"])
    if s["kind"] == "cloze":
        return sum(len(c) for c in s["chunks"])
    return len(s["items"])
