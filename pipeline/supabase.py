# -*- coding: utf-8 -*-
"""Supabase PostgREST 최소 클라이언트. service role 키를 쓰므로 RLS를 우회한다."""
import json
import urllib.error
import urllib.parse
import urllib.request

from .env import load_env, require


def q(v):
    return urllib.parse.quote(str(v), safe="")


class Rest:
    def __init__(self, env=None):
        env = env or load_env()
        url, key = require(env, "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
        self.url = url.rstrip("/") + "/rest/v1"
        self.key = key

    def _call(self, method, path, body=None, prefer=None):
        h = {"apikey": self.key, "Authorization": f"Bearer {self.key}",
             "Content-Type": "application/json", "Accept": "application/json"}
        if prefer:
            h["Prefer"] = prefer
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else []
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise SystemExit(f"\n  X  {method} {path} → HTTP {e.code}\n     {detail}")

    def get(self, path, page=1000):
        """PostgREST 는 한 번에 최대 1000행만 준다. **끝까지 이어서 읽는다.**

        2026-09-23: passage_tag 가 1060행이 되자 도구들이 앞 1000행만 보고
        「이 지문은 이미 태그가 있다/없다」를 잘못 판정했다. 태장 Hulbert 태그 19개가
        실제로는 들어가 있는데 0개로 보였다. 조용히 틀리는 종류라 여기서 막는다.
        """
        if "offset=" in path:
            return self._call("GET", path)          # 호출자가 직접 페이지를 잡은 경우
        out, off = [], 0
        while True:
            sep = "&" if "?" in path else "?"
            chunk = self._call("GET", f"{path}{sep}offset={off}&limit={page}")
            out += chunk
            if len(chunk) < page:
                return out
            off += page

    def insert(self, table, rows, on_conflict=None):
        if not rows:
            return []
        path = f"/{table}"
        prefer = "return=representation"
        if on_conflict:
            path += f"?on_conflict={on_conflict}"
            prefer += ",resolution=merge-duplicates"
        return self._call("POST", path, rows, prefer)

    def patch(self, table, query, values):
        return self._call("PATCH", f"/{table}?{query}", values, "return=representation")

    def delete(self, table, query):
        return self._call("DELETE", f"/{table}?{query}", prefer="return=representation")
