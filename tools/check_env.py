# -*- coding: utf-8 -*-
"""
.env 연결 점검 — 키 '값'은 절대 출력하지 않는다.
출력하는 것: 존재 여부, 접두사 형식, 길이, 연결 성공/실패뿐.
"""
import json
import os
import sys
import urllib.error
import urllib.request

# Windows 콘솔이 cp949라 한글·기호에서 깨진다. utf-8로 고정.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")

EXPECT = {
    "SUPABASE_URL": "https://",
    "SUPABASE_ANON_KEY": "sb_publishable_",
    "SUPABASE_SERVICE_ROLE_KEY": "sb_secret_",
    "ANTHROPIC_API_KEY": "sk-ant-",
}
PLACEHOLDER = "여기에_붙여넣기"


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def get(url, headers, timeout=20):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def main():
    print("=" * 58)
    print(" .env 점검  (키 값은 출력되지 않습니다)")
    print("=" * 58)

    if not os.path.exists(ENV_PATH):
        print("  X  .env 파일이 없습니다:", ENV_PATH)
        return 1

    env = load_env(ENV_PATH)
    ok = True

    print("\n[1] 값 채움 여부")
    for key, prefix in EXPECT.items():
        v = env.get(key, "")
        if not v:
            print(f"  X  {key:28} 비어 있음")
            ok = False
        elif PLACEHOLDER in v:
            print(f"  X  {key:28} 안내문구가 그대로 남아 있음")
            ok = False
        elif not v.startswith(prefix):
            print(f"  !  {key:28} 형식이 예상과 다름 (기대: {prefix}...)  길이 {len(v)}")
        else:
            print(f"  O  {key:28} 채워짐  ({prefix}... , 길이 {len(v)})")

    if not ok:
        print("\n채우지 않은 항목이 있어 연결 점검은 건너뜁니다.")
        return 1

    print("\n[2] Supabase 연결")
    url = env["SUPABASE_URL"].rstrip("/")
    # 주의 1) 새 형식 키(sb_publishable_ / sb_secret_)는 JWT가 아니다.
    #        Authorization: Bearer 로 보내면 JWT 파싱 실패로 401. apikey 헤더만 쓴다.
    # 주의 2) /rest/v1/ 루트는 DB 스키마 전체를 노출하므로 Supabase가
    #        publishable key에는 막아 둔다("Secret API key required").
    #        키가 죽은 게 아니므로 키별로 맞는 엔드포인트로 확인해야 한다.
    checks = (
        ("publishable", env["SUPABASE_ANON_KEY"], "/auth/v1/health", "공개 엔드포인트"),
        ("secret     ", env["SUPABASE_SERVICE_ROLE_KEY"], "/rest/v1/", "스키마 루트"),
    )
    for label, key, endpoint, what in checks:
        try:
            status, _ = get(f"{url}{endpoint}", {"apikey": key})
            print(f"  O  {label}  HTTP {status}  연결 성공  ({what})")
        except urllib.error.HTTPError as e:
            print(f"  X  {label}  HTTP {e.code}  {'키가 거부됨' if e.code in (401, 403) else e.reason}")
            ok = False
        except Exception as e:
            print(f"  X  {label}  연결 실패: {type(e).__name__}")
            ok = False

    print("\n[3] Anthropic 연결  (모델 목록 조회 — 토큰 과금 없음)")
    try:
        status, body = get(
            "https://api.anthropic.com/v1/models?limit=3",
            {"x-api-key": env["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
        )
        ids = [m["id"] for m in json.loads(body).get("data", [])]
        print(f"  O  HTTP {status}  연결 성공")
        print(f"     사용 가능 모델 예시: {', '.join(ids) or '(없음)'}")
    except urllib.error.HTTPError as e:
        print(f"  X  HTTP {e.code}  {'키가 거부됨' if e.code == 401 else e.reason}")
        ok = False
    except Exception as e:
        print(f"  X  연결 실패: {type(e).__name__}")
        ok = False

    print("\n" + "=" * 58)
    print(" 결과:", "전부 정상 — 1단계 시작 가능" if ok else "문제 있음 — 위 X 항목 확인 필요")
    print("=" * 58)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
