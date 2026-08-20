# -*- coding: utf-8 -*-
""".env 로더. 값은 반환만 하고 출력하지 않는다 (CLAUDE.md 규칙 1·2)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")


def load_env(path=ENV_PATH):
    env = {}
    if not os.path.exists(path):
        raise SystemExit(
            f".env 가 없습니다: {path}\n"
            "  원장이 직접 만듭니다:  copy .env.example .env\n"
            "  확인:  python tools/check_env.py"
        )
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def require(env, *keys):
    missing = [k for k in keys if not env.get(k)]
    if missing:
        raise SystemExit(f".env 에 값이 비어 있습니다: {', '.join(missing)}")
    return [env[k] for k in keys]
