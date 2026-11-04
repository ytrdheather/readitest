# -*- coding: utf-8 -*-
"""
선택형 문항의 일반 출제 원리 — 학교 구조(설계도)와 무관하게 어느 시험지에나 걸리는 것.

원장 질문 2026-11-04 「동형모의고사 작성할 때 영어과 문제 출제 원리 같은 것을 지켜서
넣고 있는가?」. 그때까지 32세트 645문항을 세어 보니 프롬프트에 부탁만 하고 검사하지 않았다:

    정답 번호 분포   ①129 ②156 ③157 ④129 ⑤74 — ⑤가 11%
    같은 번호 연속   3번 이상 연속 21곳
    정답만 긴 선지   정답이 눈에 띄게 가장 긴 문항 25개
    부정 발문        「않은·틀린·다른」 188개 중 강조된 것 13개

모델은 정답을 ⑤에 잘 안 두고, 정답 선지를 더 꼼꼼히(길게) 쓴다. 부탁으로는 안 고쳐지므로
**정답 위치는 생성 뒤에 기계로 배치하고**(balance), 나머지는 검사해서 경고한다(check).
부정 발문 강조는 렌더러가 `NEG` 로 한다 (디자인 지침 6).

## 선지를 옮길 수 없는 문항

선지가 지문 속 밑줄 번호를 가리키면 옮기는 순간 정답이 바뀐다. 이런 문항은 정답을 그대로
두고, 옮길 수 있는 문항으로 분포를 맞춘다 — `fixed_reason()`.
"""
import random
import re

CIRC = "①②③④⑤"

# 부정 발문 — 「틀린 것」 「들어갈 수 없는 말」 「일치하지 않는 것」 「쓰임이 다른 것」.
# 뒤에 「것·곳·말…」 이 와야 발문으로 본다 (「다른 사람」 같은 본문 낱말은 건드리지 않는다).
NEG = re.compile(r"(않은|않는|없는|아닌|틀린|어색한|다른)(?=\s*(것|하나|곳|말|문장|낱말|부분|짝|선지))")

_BARE = re.compile(r"^\s*([①②③④⑤]|\[\d\]|\(\d\))\s*$")
_LEAD = re.compile(r"^\s*[①②③④⑤]\s*")
_NUM = re.compile(r"\d+")
_ALL = re.compile(r"^(모두|위의? .*모두|all of the above|none of the above)", re.I)


def fixed_reason(it, mats):
    """선지를 옮기면 안 되는 사유. 옮겨도 되면 None."""
    opts = it.get("options", [])
    if it.get("type") == "T-GRAMMAR-INLINE":
        return "지문 속 밑줄 번호"
    if opts and all(_BARE.match(o) for o in opts):
        return "선지가 번호뿐"
    if re.search(r"(①|\[1\]|\(1\))\s*~", it.get("stem_ko", "")):
        return "발문이 ①~⑤ 위치를 가리킴"
    m = mats.get(it.get("material_id"), {})
    if "①" in m.get("text", "") and "②" in m.get("text", ""):
        return "자료에 ①② 표시"
    nums = [_NUM.search(o) for o in opts]
    if opts and all(nums):
        v = [int(x.group()) for x in nums]
        if v == sorted(v) or v == sorted(v, reverse=True):
            return "숫자 선지는 크기 순"
    if any(_ALL.match(_LEAD.sub("", o)) for o in opts):
        return "「모두」 선지는 끝자리"
    return None


def _strip_labels(opts):
    """선지 앞에 모델이 붙인 「① 」 — 렌더러가 번호를 찍으므로 옮기기 전에 뗀다."""
    if len(opts) == 5 and all(o.lstrip().startswith(CIRC[i]) for i, o in enumerate(opts)):
        return [_LEAD.sub("", o) for o in opts]
    return opts


def _bad_run(seq, i, p):
    """i 자리에 p 를 두면 같은 번호가 3번 이어지는가 (앞뒤로 이미 정해진 것 기준)."""
    g = lambda k: seq[k] if 0 <= k < len(seq) else None      # noqa: E731
    return ((g(i - 2) == g(i - 1) == p) or (g(i - 1) == p == g(i + 1))
            or (p == g(i + 1) == g(i + 2)))


def balance(items, mats, seed):
    """정답 번호를 ①~⑤ 고르게, 같은 번호 3연속 없이 다시 배치한다.

    정답 선지만 목표 자리로 옮기고 오답끼리의 순서는 그대로 둔다 — 출제자가 일부러 둔
    순서(짝 맞춘 어형 조합 등)를 덜 흩뜨린다. 해설(why_ko)의 ①~⑤ 도 같이 고친다.
    돌려주는 것: [(문항 번호, 옛 정답, 새 정답)] — 옮긴 것만.
    """
    rng = random.Random(seed)
    n = len(items)
    target = [n // 5] * 5
    for p in rng.sample(range(5), n % 5):
        target[p] += 1
    movable = [fixed_reason(it, mats) is None for it in items]
    seq = [None if mv else it["answer"] for it, mv in zip(items, movable)]
    left = target[:]
    for a in seq:
        if a:
            left[a - 1] -= 1

    moves = []
    for i, it in enumerate(items):
        if not movable[i]:
            continue
        order = sorted(range(1, 6), key=lambda p: (_bad_run(seq, i, p), -left[p - 1],
                                                    p == seq[i - 1] if i else False,
                                                    rng.random()))
        new = order[0]
        seq[i] = new
        left[new - 1] -= 1
        old = it["answer"]
        it["options"] = _strip_labels(it["options"])
        if new == old:
            continue
        idx = list(range(5))
        idx.insert(new - 1, idx.pop(old - 1))                 # idx[새 자리] = 옛 자리
        it["options"] = [it["options"][k] for k in idx]
        remap = {CIRC[k]: CIRC[j] for j, k in enumerate(idx)}
        it["why_ko"] = "".join(remap.get(ch, ch) for ch in it.get("why_ko", ""))
        it["answer"] = new
        moves.append((it.get("no"), old, new))
    return moves


def check(items, mats=None):
    """(problems, warnings). problems 는 틀린 것이 확실한 것만."""
    problems, warnings = [], []
    n = len(items)
    seq = [it.get("answer") for it in items]
    cnt = [seq.count(p) for p in range(1, 6)]
    if n >= 10 and (max(cnt) - min(cnt) > max(2, n // 5)):
        warnings.append("정답 번호 분포 " + " ".join(f"{CIRC[p]}{cnt[p]}" for p in range(5))
                        + " — 고르지 않음")
    run = 1
    for i in range(1, n):
        run = run + 1 if seq[i] == seq[i - 1] else 1
        if run == 3:
            warnings.append(f"{items[i - 2].get('no')}~{items[i].get('no')}번 정답이 "
                            f"{CIRC[seq[i] - 1]} 로 3번 이상 이어짐")
    for it in items:
        opts = [_LEAD.sub("", o).strip() or o.strip() for o in it.get("options", [])]   # 「①」 뿐인 선지는 그대로
        a = it.get("answer", 0)
        if len({o.lower() for o in opts}) < len(opts):
            problems.append(f"{it.get('no')}번 같은 선지가 두 번 나옴")
        if len(opts) == 5 and 1 <= a <= 5 and not (mats and fixed_reason(it, mats)):
            L = [len(o) for o in opts]
            rest = max(L[:a - 1] + L[a:])
            if L[a - 1] >= 8 and L[a - 1] > rest * 1.25:
                warnings.append(f"{it.get('no')}번 정답 선지만 눈에 띄게 김 "
                                f"({L[a - 1]}자 · 나머지 최장 {rest}자) — 길이로 답이 보임")
    return problems, warnings
