# -*- coding: utf-8 -*-
"""
모델 선택과 비용 계산. 기획서 §6.5 「모델 분리」 — 생성은 강한 모델, 검증은 저가 모델.

단가는 2026-08 기준이며 **바뀔 수 있다.** 실측 청구액과 어긋나면 여기를 고치고
기획서 §6.5 표도 함께 갱신할 것. 추정치를 실측인 척 남기지 않는다.
"""
import anthropic

from .env import load_env, require

# 기획서 §6.2 의 모델 배정
PASS_A_MODEL = "claude-opus-5"    # 태깅 + 문항 생성
PASS_B_MODEL = "claude-haiku-4-5"  # 역방향 검증
PASS_C_MODEL = "claude-haiku-4-5"  # 선지 유일성

# 1M 토큰당 USD
PRICING = {
    "claude-opus-5":   {"in": 5.00, "out": 25.00, "cache_min": 512},
    "claude-sonnet-5": {"in": 3.00, "out": 15.00, "cache_min": 1024},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "cache_min": 4096},
}

BATCH_DISCOUNT = 0.5    # 배치 API는 입·출력 전부 절반
CACHE_READ_MULT = 0.1   # 캐시 읽기 = 입력 단가의 0.1배
CACHE_WRITE_MULT = 1.25  # 캐시 쓰기(5분 TTL) = 입력 단가의 1.25배

USD_KRW = 1400  # 기획서 §6.5 가정. 표시용일 뿐 판단 근거로 쓰지 말 것


def client(env=None):
    env = env or load_env()
    (key,) = require(env, "ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=key)


class Cost:
    """usage 를 누적해 실비를 계산한다. 추정이 아니라 응답이 보고한 토큰 기준."""

    def __init__(self):
        self.rows = []

    def add(self, label, model, usage, batch=False):
        p = PRICING[model]
        rate = BATCH_DISCOUNT if batch else 1.0
        cin = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cread = getattr(usage, "cache_read_input_tokens", 0) or 0
        uin = usage.input_tokens or 0
        out = usage.output_tokens or 0
        usd = rate / 1e6 * (
            uin * p["in"]
            + cin * p["in"] * CACHE_WRITE_MULT
            + cread * p["in"] * CACHE_READ_MULT
            + out * p["out"]
        )
        self.rows.append({
            "label": label, "model": model, "batch": batch,
            "input": uin, "cache_write": cin, "cache_read": cread,
            "output": out, "usd": usd,
        })
        return usd

    @property
    def total_usd(self):
        return sum(r["usd"] for r in self.rows)

    def report(self):
        if not self.rows:
            return "  (호출 없음)"
        w = max(len(r["label"]) for r in self.rows)
        lines = [
            f"  {'구간'.ljust(w)}  {'모델':16} {'입력':>7} {'캐시W':>7} {'캐시R':>7} {'출력':>7}  {'USD':>9}"
        ]
        for r in self.rows:
            lines.append(
                f"  {r['label'].ljust(w)}  {r['model']:16} {r['input']:>7} "
                f"{r['cache_write']:>7} {r['cache_read']:>7} {r['output']:>7}  ${r['usd']:>8.4f}"
            )
        lines.append(f"\n  합계 ${self.total_usd:.4f}  (≈ {self.total_usd * USD_KRW:,.0f}원)")

        # 캐시가 조용히 안 걸리는 경우를 잡는다 — Haiku 4.5 는 최소 4,096 토큰
        for r in self.rows:
            if r["cache_write"] == 0 and r["cache_read"] == 0:
                lines.append(
                    f"  ! {r['label']}: 캐시 미적용. {r['model']} 최소 캐시 길이는 "
                    f"{PRICING[r['model']]['cache_min']:,}토큰 — 프리픽스가 짧으면 조용히 안 걸린다."
                )
        return "\n".join(lines)
