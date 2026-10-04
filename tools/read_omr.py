# -*- coding: utf-8 -*-
"""
동형 모의고사 OMR 스캔본에서 출결번호 · 세트 · 객관식 마킹을 읽는다. (채점은 하지 않는다)

  python tools/read_omr.py                       # Z:\\omr\\inbox 전부 → Z:\\omr\\read\\<시각>\\
  python tools/read_omr.py 스캔.pdf 사진.jpg      # 파일을 직접 줄 때
  python tools/read_omr.py --out 폴더

양식은 `tools/render_omr.py` 가 만들고, 칸 좌표는 `data/omr/omr_layout_v1.json` 에서 읽는다.

## 어떻게 읽나

1. 쪽(PDF)·그림을 회색조로 → 꽉 찬 검은 정사각형(모서리 표식)을 찾는다.
   표식 넷이 카드 하나다. 자르지 않은 A4(카드 둘)면 여덟 개 → 카드 둘로 나눈다.
2. 왼쪽 위 표식 옆의 작은 표식으로 방향을 정한다 — 거꾸로·옆으로 넣어도 된다.
3. 네 표식 중심으로 mm → 픽셀 변환(원근 변환)을 구해 카드를 반듯하게 편다.
4. 원마다 안쪽의 「얼마나 검은가」를 잰다. 빈 원도 인쇄된 숫자 때문에 조금 검다 —
   카드마다 빈 원의 중앙값을 바탕값으로 빼서 비교한다 (사인펜·스캐너 진하기가 달라도 같은 기준).

## 확정하지 않는 것 — `review`

성적표에 틀린 점수가 찍히는 것이 가장 큰 사고다. 그래서 기계가 애매하면 **고르지 않고** 목록으로 뺀다.

  · 한 문항에 두 칸 이상 칠함          → 답 "2,4" + review
  · 덜 칠했거나 지운 자국 같은 진하기   → review (가장 진한 칸을 후보로 적는다)
  · 출결번호 한 자리에 0개·2개 이상     → student_id 에 "?" + review
  · 세트가 0개·2개 이상                 → set None + review
  · 표식 넷을 못 찾음                   → 카드 자체를 못 읽음 (errors)

빈 문항(아무것도 안 칠함)은 review 가 아니라 답 "" — 모르는 문제를 비워 낸 것일 수 있다.
"""
import argparse
import datetime as dt
import glob
import itertools
import json
import math
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUT_PATH = os.path.join(ROOT, "data", "omr", "omr_layout_v1.json")
INBOX = r"Z:\omr\inbox"
READ_ROOT = r"Z:\omr\read"

PX_PER_MM = 8.0          # 펴낸 카드 해상도 (≈ 203dpi)
RENDER_DPI = 200         # PDF 를 그림으로 바꿀 때

# 진하기 판정 — (원 안 검은 비율 − 바탕값) / (1 − 바탕값)
MARKED = 0.45            # 이 이상이면 칠함
FAINT = 0.10             # 이 이상 MARKED 미만이면 애매 (덜 칠함·지운 자국)
# 가짜 스캔 80장 실측 (2026-10-05, 원 안 숫자별 바탕값): 빈 원 최대 0.062 · 칠한 원 최소 0.73.
# 연필처럼 흐리게 칠한 것이 0.15 안팎이라 0.18 에서는 빈칸으로 넘어갔다 → 0.10.
COVER_DELTA = 35         # 종이 흰색보다 이만큼 어두우면 「덮인」 픽셀
COVER_FAINT = 0.6        # 덮임이 이 이상이면 진하기가 낮아도 애매로 본다
# 진짜 스캔본이 들어오면 tools/test_read_omr.py 와 같은 방법으로 다시 잰다.

IMG_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")


def load_layout(path=LAYOUT_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- 입력 ---------------------------------------------------------------------
def _render_pdf(path):
    """PDF 각 쪽을 회색조 그림으로. pypdfium2 먼저, 없으면 PyMuPDF (requirements.txt 와 같은 순서)."""
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(path)
        for i in range(len(doc)):
            pil = doc[i].render(scale=RENDER_DPI / 72).to_pil().convert("L")
            yield i + 1, np.array(pil)
        return
    except ImportError:
        pass
    import fitz
    for i, pg in enumerate(fitz.open(path)):
        pix = pg.get_pixmap(dpi=RENDER_DPI, colorspace=fitz.csGRAY)
        yield i + 1, np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def iter_pages(paths):
    """(파일, 쪽, 회색조 그림) 을 낸다."""
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext == ".pdf":
            for n, img in _render_pdf(p):
                yield p, n, img
        elif ext in IMG_EXT:
            img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_GRAYSCALE)  # 한글 경로
            if img is None:
                yield p, 1, None
            else:
                yield p, 1, img


# --- 표식 찾기 ----------------------------------------------------------------
def find_squares(gray):
    """꽉 찬 검은 정사각형 후보: [(cx, cy, side)]."""
    h, w = gray.shape
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(bw, connectivity=8)
    short = min(h, w)
    out = []
    for i in range(1, n):
        x, y, bw_, bh, area = stats[i]
        side = (bw_ + bh) / 2
        if side < short / 120 or side > short / 12:
            continue
        if not 0.75 < bw_ / bh < 1.33:
            continue
        # 기울어진 정사각형의 bbox 는 커진다 — 최소 외접 사각형으로 채움 비율을 잰다
        comp = (labels[y:y + bh, x:x + bw_] == i).astype(np.uint8)
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        (rw, rh) = cv2.minAreaRect(cnts[0])[1]
        if rw == 0 or rh == 0 or not 0.8 < rw / rh < 1.25:
            continue
        if area / (rw * rh) < 0.88:          # 칠한 원은 ≈ 0.785 — 여기서 걸러진다
            continue
        cx, cy = cents[i]
        out.append((float(cx), float(cy), math.sqrt(rw * rh)))
    return out


def find_cards(gray, L):
    """그림 한 장에서 카드들을 찾는다. [(mm→px 3x3 행렬, 회전 이름)]."""
    sq = find_squares(gray)
    if len(sq) < 4:
        return []
    mk_side = L["marker_size"]
    (tlx, tly), (trx, try_), (blx, bly) = (L["markers"]["tl"], L["markers"]["tr"],
                                           L["markers"]["bl"])
    long_mm, short_mm = trx - tlx, bly - tly
    want_ratio = long_mm / short_mm
    orient_mm = math.dist(L["orient_mark"], L["markers"]["tl"])

    # 큰 표식: 크기가 가장 큰 무리. 작은 표식(방향): 그 절반쯤
    sides = sorted(s for *_, s in sq)
    big_side = sides[-1]
    bigs = [q for q in sq if q[2] > big_side * 0.75]
    smalls = [q for q in sq if 0.3 * big_side < q[2] < 0.75 * big_side]
    if len(bigs) > 12:
        bigs = sorted(bigs, key=lambda q: -q[2])[:12]

    cards, used = [], set()
    cands = []
    for combo in itertools.combinations(range(len(bigs)), 4):
        pts = np.array([bigs[i][:2] for i in combo])
        rect = _as_rectangle(pts)
        if rect is None:
            continue
        a, b, c, d, err = rect          # a-b 긴 변, a-d 짧은 변
        ratio = math.dist(a, b) / math.dist(a, d)
        if abs(ratio - want_ratio) / want_ratio > 0.06 or err > 0.04:
            continue
        # 표식 크기와 카드 크기가 맞아야 한다 (글자 덩어리로 만든 가짜 사각형 거르기)
        px_per_mm = math.dist(a, b) / long_mm
        if abs(np.mean([bigs[i][2] for i in combo]) / px_per_mm - mk_side) > mk_side * 0.35:
            continue
        cands.append((err + abs(ratio - want_ratio), combo, (a, b, c, d), px_per_mm))
    for _, combo, (a, b, c, d), ppm in sorted(cands):
        if used & set(combo):
            continue
        corners = _orient(a, b, c, d, smalls, orient_mm * ppm)
        if corners is None:
            continue
        used |= set(combo)
        tl, tr, br, bl = corners
        src = np.float32([L["markers"]["tl"], L["markers"]["tr"],
                          L["markers"]["br"], L["markers"]["bl"]])
        dst = np.float32([tl, tr, br, bl])
        cards.append(cv2.getPerspectiveTransform(src, dst))
    # 위에서 아래, 왼쪽에서 오른쪽 순서 (자르지 않은 A4 면 위 카드가 먼저)
    cards.sort(key=lambda M: (round((M @ [105, 74, 1])[1] / (M @ [105, 74, 1])[2] / 50),
                              (M @ [105, 74, 1])[0]))
    return cards


def _as_rectangle(pts):
    """네 점이 직사각형이면 (a, b, c, d, 오차) — a→b 가 긴 변, a→d 가 짧은 변, 둘레 순서."""
    c = pts.mean(axis=0)
    order = np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    p = pts[order]
    sides = [np.linalg.norm(p[(i + 1) % 4] - p[i]) for i in range(4)]
    diag = (np.linalg.norm(p[2] - p[0]), np.linalg.norm(p[3] - p[1]))
    if min(sides) == 0:
        return None
    err = (abs(sides[0] - sides[2]) / max(sides[0], sides[2])
           + abs(sides[1] - sides[3]) / max(sides[1], sides[3])
           + abs(diag[0] - diag[1]) / max(diag)) / 3
    if sides[0] < sides[1]:
        p = np.roll(p, -1, axis=0)
    return tuple(map(tuple, p)) + (err,)


def _orient(a, b, c, d, smalls, orient_px):
    """작은 표식이 붙은 모서리를 왼쪽 위로 → (tl, tr, br, bl)."""
    ring = [a, b, c, d]
    best = None
    for i, corner in enumerate(ring):
        for sx, sy, _ in smalls:
            dist = math.dist(corner, (sx, sy))
            if abs(dist - orient_px) < orient_px * 0.45:
                if best is None or dist < best[1]:
                    best = (i, dist, (sx, sy))
    if best is None:
        return None
    i, _, s = best
    tl = np.array(ring[i])
    nxt, prv = np.array(ring[(i + 1) % 4]), np.array(ring[(i - 1) % 4])
    # 작은 표식은 tl → tr (긴 변) 방향에 있다
    long_nb = nxt if np.linalg.norm(nxt - tl) > np.linalg.norm(prv - tl) else prv
    if np.dot(np.array(s) - tl, long_nb - tl) <= 0:
        return None
    short_nb = prv if long_nb is nxt else nxt
    far = np.array(ring[(i + 2) % 4])
    return tuple(tl), tuple(long_nb), tuple(far), tuple(short_nb)


# --- 카드 읽기 ----------------------------------------------------------------
def warp_card(gray, M, L):
    w, h = L["card"]
    S = np.diag([PX_PER_MM, PX_PER_MM, 1.0])
    # 펴낸 그림 픽셀 → mm → 원래 그림 픽셀
    H = M @ np.linalg.inv(S)
    return cv2.warpPerspective(gray, H, (int(w * PX_PER_MM), int(h * PX_PER_MM)),
                               flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA,
                               borderValue=255)


def _bubble_pixels(card, centers, r_mm):
    """원 안쪽(테두리 빼고)의 픽셀들."""
    r = r_mm * PX_PER_MM
    k = int(math.ceil(r)) + 2
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    mask = (xx ** 2 + yy ** 2) <= (r * 0.78) ** 2
    out = []
    for cx, cy in centers:
        x, y = int(round(cx * PX_PER_MM)), int(round(cy * PX_PER_MM))
        patch = card[y - k:y + k + 1, x - k:x + k + 1]
        out.append(patch[mask] if patch.shape == mask.shape else np.full(int(mask.sum()), 255, np.uint8))
    return out


def read_card(card, L):
    r = L["bubble_d"] / 2
    groups = {}
    for q, cs in L["choices"].items():
        groups[("q", q)] = cs
    for i, col in enumerate(L["student_id"]["cols"]):
        groups[("id", i)] = col
    groups[("set", 0)] = L["set"]["bubbles"]

    pix = {k: _bubble_pixels(card, cs, r) for k, cs in groups.items()}
    # 진하기: 0(흰) ~ 1(검은) 연속값 평균
    raw = {k: [float(((255 - p) / 255.0).mean()) for p in ps] for k, ps in pix.items()}
    allv = np.array([v for vs in raw.values() for v in vs])
    base_all = float(np.median(allv))
    full = max(float(np.percentile(allv, 99.5)), base_all + 0.25)   # 칠한 원의 진하기

    # 바탕값은 원 안에 인쇄된 숫자별로 따로 — 「1」 과 「8」 은 잉크 양이 달라 빈 원의 진하기가 다르다.
    # 하나로 빼면 그 차이(≈0.05)에 흐리게 칠한 칸이 묻힌다 (가짜 스캔 시험에서 조용한 오답 6건).
    # 칠한 게 분명한 원은 빼고 잰다 — 「0」 은 출결번호 칸에만 4개라, 출결번호 0070 이면
    # 넷 중 셋이 칠해져 중앙값이 칠한 진하기가 됐다 (칠한 0 을 빈칸으로 읽음). 빈 원이 3개 미만이면 전체 값.
    cut = base_all + 0.3 * (full - base_all)
    by_digit = {}
    for k, vs in raw.items():
        for i, v in enumerate(vs):
            if v < cut:
                by_digit.setdefault(_digit(k, i), []).append(v)
    base = {d: float(np.median(vs)) if len(vs) >= 3 else base_all for d, vs in by_digit.items()}
    norm = {k: [max(0.0, (v - base.get(_digit(k, i), base_all)) / (full - base.get(_digit(k, i), base_all)))
                for i, v in enumerate(vs)] for k, vs in raw.items()}

    # 덮임: 원 안이 종이 흰색에서 벗어난 픽셀 비율. 빈 원은 숫자 획만(≈0.1~0.3), 칠한 원은 거의 1.
    # 연한 회색으로 칠하면 숫자를 덮어 평균 진하기는 빈 원과 비슷한데 덮임은 높다 — 그걸 잡는다.
    white = float(np.median([np.percentile(p, 90) for ps in pix.values() for p in ps]))
    cover = {k: [float((p < white - COVER_DELTA).mean()) for p in ps] for k, ps in pix.items()}

    review, answers = [], {}

    def pick(key):
        vals, cov = norm[key], cover[key]
        marked = [i for i, v in enumerate(vals) if v >= MARKED]
        faint = [i for i, v in enumerate(vals)
                 if v < MARKED and (v >= FAINT or cov[i] >= COVER_FAINT)]
        return marked, faint

    for q in L["choices"]:
        marked, faint = pick(("q", q))
        vals = norm[("q", q)]
        if len(marked) == 1 and not faint:
            answers[q] = str(marked[0] + 1)
        elif len(marked) > 1:
            answers[q] = ",".join(str(i + 1) for i in marked)
            review.append({"what": f"{q}번", "why": "두 칸 이상 칠함", "values": _r(vals)})
        elif faint:
            top = max(faint, key=lambda i: (cover[("q", q)][i], vals[i]))
            answers[q] = ",".join(str(i + 1) for i in marked) if marked else ""
            review.append({"what": f"{q}번", "why": "흐리게 칠했거나 지운 자국",
                           "guess": str(top + 1), "values": _r(vals)})
        else:
            answers[q] = ""

    digits = []
    for i in range(L["student_id"]["digits"]):
        vals = norm[("id", i)]
        marked, faint = pick(("id", i))
        if len(marked) == 1 and not faint:
            digits.append(str(marked[0]))
        else:
            digits.append("?")
            review.append({"what": f"출결번호 {i + 1}번째 자리",
                           "why": "칠한 칸 없음" if not marked and not faint else
                           "두 칸 이상" if len(marked) > 1 else "흐리게 칠함",
                           "values": _r(vals)})
    vals = norm[("set", 0)]
    marked, faint = pick(("set", 0))
    set_no = L["set"]["values"][marked[0]] if len(marked) == 1 and not faint else None
    if set_no is None:
        review.append({"what": "세트", "why": "칠한 칸 없음" if not marked and not faint
                       else "두 칸 이상" if len(marked) > 1 else "흐리게 칠함",
                       "values": _r(vals)})

    # 객관식은 세트마다 문항 수가 달라 뒤쪽 빈칸은 그냥 안 쓴 칸이다 — 마지막 칠한 문항까지만 남긴다
    last = max([int(q) for q, a in answers.items() if a] or [0])
    answers = {q: a for q, a in answers.items() if int(q) <= last}
    return {"student_id": "".join(digits), "set": set_no, "answers": answers,
            "review": review, "baseline": round(base_all, 3)}


def _digit(key, i):
    """원 안에 인쇄된 숫자. 객관식 i → i+1, 출결번호 i → i, 세트 i → i+1."""
    return i if key[0] == "id" else i + 1


def _r(vals):
    return [round(v, 2) for v in vals]


def save_essay_crops(card, L, dest_prefix):
    """서술형 칸을 잘라 PNG 로 — 결과지에 붙이고, 원장이 채점할 때 본다."""
    paths = []
    for es in L["essays"]:
        x0, y0, x1, y1 = (int(v * PX_PER_MM) for v in es["box"])
        p = f"{dest_prefix}_서술{es['n']}.png"
        ok, buf = cv2.imencode(".png", card[y0:y1, x0:x1])
        if ok:
            buf.tofile(p)
            paths.append(p)
    return paths


def read_paths(paths, L, out_dir=None):
    """파일들을 읽어 카드 목록을 낸다. out_dir 를 주면 펴낸 카드·서술형 칸 그림도 남긴다."""
    cards, errors = [], []
    for path, page, gray in iter_pages(paths):
        where = f"{os.path.basename(path)} p{page}"
        if gray is None:
            errors.append({"source": where, "why": "그림을 열 수 없음"})
            continue
        Ms = find_cards(gray, L)
        if not Ms:
            errors.append({"source": where, "why": "모서리 표식 넷을 못 찾음 — 양식이 다르거나 잘림"})
            continue
        for k, M in enumerate(Ms, 1):
            card = warp_card(gray, M, L)
            res = read_card(card, L)
            res["source"] = where + (f" 카드{k}" if len(Ms) > 1 else "")
            if out_dir:
                stem = os.path.join(out_dir, f"{len(cards) + 1:03d}")
                ok, buf = cv2.imencode(".png", card)
                if ok:
                    buf.tofile(stem + "_카드.png")
                res["essay_crops"] = [os.path.basename(p)
                                      for p in save_essay_crops(card, L, stem)]
            cards.append(res)
    return cards, errors


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="*", help=f"파일·폴더 (기본 {INBOX})")
    ap.add_argument("--out", help=f"결과 폴더 (기본 {READ_ROOT}\\<시각>)")
    args = ap.parse_args()

    L = load_layout()
    ins = args.inputs or [INBOX]
    paths = []
    for p in ins:
        if os.path.isdir(p):
            paths += sorted(q for q in glob.glob(os.path.join(p, "*"))
                            if os.path.splitext(q)[1].lower() in IMG_EXT + (".pdf",))
        else:
            paths.append(p)
    if not paths:
        print("읽을 파일이 없습니다:", ", ".join(ins))
        return 1

    out = args.out or os.path.join(READ_ROOT, dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out, exist_ok=True)
    cards, errors = read_paths(paths, L, out)
    result = {"layout_version": L["version"], "read_at": dt.datetime.now().isoformat(timespec="seconds"),
              "files": [os.path.basename(p) for p in paths], "cards": cards, "errors": errors}
    with open(os.path.join(out, "read.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    n_rev = sum(1 for c in cards if c["review"])
    print(f"카드 {len(cards)}장 읽음 · 확인 필요 {n_rev}장 · 못 읽은 쪽 {len(errors)}")
    for c in cards:
        flag = "  ← 확인" if c["review"] else ""
        print(f"  {c['source']:30} 출결 {c['student_id']}  세트 {c['set']}  "
              f"객관식 {len(c['answers'])}문항{flag}")
        for r in c["review"]:
            print(f"      · {r['what']}: {r['why']}" + (f" (후보 {r['guess']})" if r.get("guess") else ""))
    for e in errors:
        print(f"  X {e['source']}: {e['why']}")
    print("결과:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
