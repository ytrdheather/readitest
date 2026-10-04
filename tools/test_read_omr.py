# -*- coding: utf-8 -*-
"""
`read_omr.py` 를 가짜 스캔본으로 시험한다 — 종이·프린터 없이.

  python tools/test_read_omr.py            # 기본 120장
  python tools/test_read_omr.py --n 400 --keep 폴더   # 가짜 스캔본을 남겨 눈으로 볼 때

OMR PDF(`render_omr.py` 산출물)를 그림으로 바꾸고, 정답을 정해 사인펜처럼 칠한 뒤
기울이기 · 뒤집기 · 옆으로 · 흐림 · 잡음 · 어두운 종이 · JPEG 압축을 섞는다.
일부는 일부러 두 칸 칠함 · 흐리게 칠함 · 반만 칠함 · 지운 자국 · 출결번호 한 자리 빠뜨림.

## 합격 기준

  **조용한 오답 0** — review 에 안 올리고 정답과 다르게 읽은 칸이 하나라도 있으면 실패.
  애매하게 만든 칸은 review 로 가면 맞은 것이다. 깨끗한 카드에서 review 가 뜨는 비율도 함께 본다
  (너무 많으면 원장이 손으로 볼 게 늘어 자동 채점의 의미가 없다).
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import read_omr  # noqa: E402
from tools.render_omr import OUT_PDF  # noqa: E402

BASE_DPI = 200


def base_page():
    if not os.path.exists(OUT_PDF):
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_omr.py")], check=True)
    import fitz
    pix = fitz.open(OUT_PDF)[0].get_pixmap(dpi=BASE_DPI, colorspace=fitz.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width).copy()


def mm2px(v):
    return v * BASE_DPI / 25.4


def fill(img, cx, cy, r, kind, rng):
    """(cx, cy) mm 에 사인펜 자국. kind: full / faint / half / erased."""
    x, y = mm2px(cx + rng.uniform(-0.25, 0.25)), mm2px(cy + rng.uniform(-0.25, 0.25))
    rr = mm2px(r) * rng.uniform(1.0, 1.2)
    if kind == "full":
        val = rng.randint(15, 70)
        cv2.ellipse(img, (int(x), int(y)), (int(rr), int(rr * rng.uniform(0.9, 1.15))),
                    rng.uniform(0, 180), 0, 360, val, -1, cv2.LINE_AA)
    elif kind == "faint":                      # 연필처럼 흐림
        cv2.ellipse(img, (int(x), int(y)), (int(rr), int(rr)), 0, 0, 360,
                    rng.randint(165, 190), -1, cv2.LINE_AA)
    elif kind == "half":                       # 위쪽 절반만
        cv2.ellipse(img, (int(x), int(y)), (int(rr), int(rr)), 0, 180, 360, 30, -1, cv2.LINE_AA)
    elif kind == "erased":                     # 지우고 남은 옅은 자국
        cv2.ellipse(img, (int(x), int(y)), (int(rr), int(rr)), 0, 0, 360,
                    rng.randint(205, 225), -1, cv2.LINE_AA)


def make_card(page, card_idx, L, rng, tricky):
    """카드 하나를 칠하고 정답을 낸다. 아래 카드는 y 를 148.5mm 내린다."""
    oy = card_idx * L["card"][1]
    r = L["bubble_d"] / 2
    truth = {"student_id": "".join(str(rng.randint(0, 9)) for _ in range(L["student_id"]["digits"])),
             "set": rng.randint(1, 6), "answers": {}, "expect_review": set()}
    n_q = rng.choice([18, 20, 23, 24])
    for q in range(1, n_q + 1):
        truth["answers"][str(q)] = "" if rng.random() < 0.04 else str(rng.randint(1, 5))
    if truth["answers"][str(n_q)] == "":
        truth["answers"][str(n_q)] = "3"

    # 애매한 칸 (tricky 카드에만)
    tricks = {}
    if tricky:
        qs = rng.sample(range(1, n_q), 3)
        for q, kind in zip(qs, rng.sample(["double", "faint", "half", "erased", "blank_faint"], 3)):
            tricks[str(q)] = kind

    for i, ch in enumerate(truth["student_id"]):
        cx, cy = L["student_id"]["cols"][i][int(ch)]
        fill(page, cx, cy + oy, r, "full", rng)
    if tricky and rng.random() < 0.3:          # 출결번호 한 자리에 두 칸 칠함
        i = rng.randrange(L["student_id"]["digits"])
        other = (int(truth["student_id"][i]) + 3) % 10
        cx, cy = L["student_id"]["cols"][i][other]
        fill(page, cx, cy + oy, r, "full", rng)
        truth["expect_review"].add(f"출결번호 {i + 1}번째 자리")
        truth["student_id"] = truth["student_id"][:i] + "?" + truth["student_id"][i + 1:]
    cx, cy = L["set"]["bubbles"][truth["set"] - 1]
    fill(page, cx, cy + oy, r, "full", rng)

    for q, a in truth["answers"].items():
        cs = L["choices"][q]
        kind = tricks.get(q)
        if a == "":
            continue
        k = int(a) - 1
        if kind == "double":
            j = (k + rng.randint(1, 4)) % 5
            fill(page, cs[k][0], cs[k][1] + oy, r, "full", rng)
            fill(page, cs[j][0], cs[j][1] + oy, r, "full", rng)
            truth["answers"][q] = ",".join(sorted([str(k + 1), str(j + 1)]))
            truth["expect_review"].add(f"{q}번")
        elif kind in ("faint", "half"):
            fill(page, cs[k][0], cs[k][1] + oy, r, kind, rng)
            truth["expect_review"].add(f"{q}번")          # 맞게 읽어도 되지만 review 가 정상
            truth.setdefault("soft", set()).add(q)
        elif kind == "erased":                             # 하나 지우고 다른 걸 칠함
            j = (k + rng.randint(1, 4)) % 5
            fill(page, cs[j][0], cs[j][1] + oy, r, "erased", rng)
            fill(page, cs[k][0], cs[k][1] + oy, r, "full", rng)
            truth.setdefault("soft", set()).add(q)         # review 여도, 아니어도 정답만 맞으면 됨
        elif kind == "blank_faint":                        # 칠하다 만 흔적 — 답은 비었다고 봐야
            fill(page, cs[k][0], cs[k][1] + oy, r, "faint", rng)
            truth["answers"][q] = ""
            truth["expect_review"].add(f"{q}번")
            truth.setdefault("soft", set()).add(q)
        else:
            fill(page, cs[k][0], cs[k][1] + oy, r, "full", rng)
    return truth


def degrade(img, rng):
    """스캐너가 내는 흠. 어떤 것을 넣었는지 이름도 낸다."""
    tags = []
    h, w = img.shape
    if rng.random() < 0.5:                                  # 종이 바탕 회색·대비
        a, b = rng.uniform(0.8, 1.0), rng.uniform(0, 30)
        img = np.clip(img * a + b * (img > 128), 0, 255).astype(np.uint8)
        tags.append("대비")
    ang = rng.uniform(-3, 3)
    scale = rng.uniform(0.75, 1.5)                          # ≈ 150~300dpi
    rot = rng.choice([0, 0, 0, 90, 180, 270])
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, scale)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * cos) + 40, int(h * cos + w * sin) + 40
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    img = cv2.warpAffine(img, M, (nw, nh), borderValue=int(rng.uniform(200, 255)))
    tags.append(f"기울기{ang:+.1f}° 배율{scale:.2f}")
    if rot:
        img = np.ascontiguousarray(np.rot90(img, rot // 90))
        tags.append(f"회전{rot}")
    if rng.random() < 0.5:
        k = rng.choice([3, 5])
        img = cv2.GaussianBlur(img, (k, k), 0)
        tags.append("흐림")
    if rng.random() < 0.5:
        noise = np.random.default_rng(rng.randint(0, 1 << 30)).normal(0, rng.uniform(4, 12), img.shape)
        img = np.clip(img + noise, 0, 255).astype(np.uint8)
        tags.append("잡음")
    if rng.random() < 0.5:
        q = rng.randint(45, 85)
        img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])[1],
                           cv2.IMREAD_GRAYSCALE)
        tags.append(f"JPEG{q}")
    return img, tags


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120, help="가짜 스캔 장 수")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--keep", help="가짜 스캔본을 남길 폴더")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    L = read_omr.load_layout()
    page0 = base_page()
    half = page0.shape[0] // 2
    work = args.keep or tempfile.mkdtemp(prefix="omr_test_")
    os.makedirs(work, exist_ok=True)

    stats = {"cards": 0, "unread": 0, "silent_wrong": 0, "review_missed": 0,
             "clean_cards": 0, "clean_with_review": 0, "id_wrong": 0, "set_wrong": 0}
    failures = []
    for n in range(args.n):
        page = page0.copy()
        tricky = rng.random() < 0.4
        whole = rng.random() < 0.2                       # 자르지 않은 A4 로 넣은 경우
        truths = [make_card(page, 0, L, rng, tricky)]
        if whole:
            truths.append(make_card(page, 1, L, rng, tricky))
            img = page
        else:
            img = page[:half + 2]                        # 위 카드만 (잘라 낸 A5)
        img, tags = degrade(img, rng)
        path = os.path.join(work, f"s{n:03d}.png")
        cv2.imencode(".png", img)[1].tofile(path)

        cards, errors = read_omr.read_paths([path], L)
        stats["cards"] += len(truths)
        if len(cards) != len(truths):
            stats["unread"] += len(truths) - len(cards)
            failures.append(f"s{n:03d} 카드 {len(truths)}장 중 {len(cards)}장 읽음 {tags} {errors}")
            continue
        # 거꾸로 넣은 A4 는 아래 카드가 먼저 읽힌다 — 실제로는 순서가 상관없다. 출결번호로 짝짓는다
        if len(cards) == 2 and sum(a == b for a, b in zip(cards[0]["student_id"], truths[1]["student_id"])) >                 sum(a == b for a, b in zip(cards[0]["student_id"], truths[0]["student_id"])):
            cards = cards[::-1]
        for t, c in zip(truths, cards):
            rev = {r["what"] for r in c["review"]}
            soft = t.get("soft", set())
            if not t["expect_review"] and not soft:
                stats["clean_cards"] += 1
                if rev:
                    stats["clean_with_review"] += 1
            if c["student_id"] != t["student_id"] and "?" not in c["student_id"]:
                stats["id_wrong"] += 1
                failures.append(f"s{n:03d} 출결 {c['student_id']} ≠ {t['student_id']} {tags}")
            if c["set"] != t["set"] and "세트" not in rev:
                stats["set_wrong"] += 1
                failures.append(f"s{n:03d} 세트 {c['set']} ≠ {t['set']} {tags}")
            for q, a in t["answers"].items():
                got = c["answers"].get(q, "")
                if f"{q}번" in rev:
                    continue                              # 사람이 본다 — 틀려도 사고 아님
                if got != a:
                    stats["silent_wrong"] += 1
                    failures.append(f"s{n:03d} {q}번 읽음 {got!r} 정답 {a!r} "
                                    f"(조용한 오답) {tags}")
            for what in t["expect_review"]:
                if what not in rev and not (what.endswith("번") and what[:-1] in soft
                                            and c["answers"].get(what[:-1], "") == t["answers"][what[:-1]]):
                    stats["review_missed"] += 1
                    failures.append(f"s{n:03d} {what} 확인 목록에 안 올라감 {tags}")

    print(json.dumps(stats, ensure_ascii=False, indent=1))
    for f in failures[:40]:
        print("  ·", f)
    ok = stats["silent_wrong"] == 0 and stats["unread"] == 0 and stats["id_wrong"] == 0 \
        and stats["set_wrong"] == 0
    print("합격" if ok else "실패", "— 가짜 스캔본:", work)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
