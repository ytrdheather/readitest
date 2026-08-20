# -*- coding: utf-8 -*-
"""
Supabase 연결 진단 — check_env.py가 'URLError'만 뱉을 때 원인을 좁힌다.

DNS → TCP 443 → TLS → HTTP 순서로 하나씩 짚어서, 실패가
  · 프로젝트 일시정지(무료 플랜 7일 미사용 → 자동 pause)   = DNS는 되고 HTTP 5xx/타임아웃
  · 네트워크·방화벽                                        = TCP 실패
  · URL 오타                                               = DNS 실패
  · 키 문제                                                = HTTP 401/403
중 무엇인지 구분되게 한다.

키 값도 프로젝트 ref도 출력하지 않는다. 호스트는 마지막 마디만 보여준다.
"""
import os
import socket
import ssl
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")


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


def main():
    print("=" * 62)
    print(" Supabase 연결 진단  (키·프로젝트 ref는 출력되지 않습니다)")
    print("=" * 62)

    env = load_env(ENV_PATH)
    url = env.get("SUPABASE_URL", "").rstrip("/")
    if not url:
        print("  X  SUPABASE_URL이 비어 있습니다.")
        return 1

    host = url.split("//", 1)[-1].split("/")[0]
    print(f"  호스트: ***{host[-14:]}  (길이 {len(host)})")

    # 1. DNS
    try:
        socket.gethostbyname(host)
        print("  O  DNS 조회 성공")
    except Exception as e:
        print(f"  X  DNS 조회 실패: {type(e).__name__}")
        print("     → SUPABASE_URL 오타이거나, 프로젝트가 삭제됐을 수 있습니다.")
        return 1

    # 2. TCP
    try:
        socket.create_connection((host, 443), timeout=10).close()
        print("  O  TCP 443 연결 성공")
    except Exception as e:
        print(f"  X  TCP 443 연결 실패: {type(e).__name__}: {e}")
        print("     → 방화벽·프록시·백신이 막고 있을 가능성.")
        return 1

    # 3. TLS
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                pass
        print("  O  TLS 핸드셰이크 성공")
    except Exception as e:
        print(f"  X  TLS 실패: {type(e).__name__}: {e}")
        print("     → 인증서 검증 문제(백신 SSL 검사 등).")
        return 1

    # 4. HTTP — 실제 테이블을 secret 키로 조회한다.
    #    /rest/v1/ 루트는 secret 키만 받으므로 publishable 키로 찌르면 401이 뜬다.
    #    그건 프로젝트 문제가 아니라 엔드포인트 규칙이므로 오진이 된다.
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    try:
        req = urllib.request.Request(
            url + "/rest/v1/school?select=name&limit=1",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"  O  HTTP {r.status} — REST 응답 정상")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read()[:200].decode("utf-8", "replace")
        print(f"  !  HTTP {e.code} — 연결은 되나 거부됨")
        print(f"     응답: {body}")
        if e.code in (401, 403):
            print("     → 키가 만료·폐기됐을 수 있습니다. Supabase → Settings → API Keys.")
        return 1
    except urllib.error.URLError as e:
        print(f"  X  HTTP 실패: {type(e).__name__} / reason={type(e.reason).__name__}: {e.reason}")
        print("     → DNS·TCP·TLS가 다 됐는데 여기서 막히면 프로젝트 일시정지(pause)가 유력합니다.")
        print("       Supabase 대시보드에서 프로젝트가 Paused인지 확인하고 Restore 하십시오.")
        return 1
    except Exception as e:
        print(f"  X  HTTP 실패: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
