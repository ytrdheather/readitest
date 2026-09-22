# -*- coding: utf-8 -*-
"""
result/ 의 최신 PDF 를 Z: 배포 폴더로 맞춘다.

  python tools/sync_result.py            # 무엇이 다른지만 보여준다
  python tools/sync_result.py --apply

## 왜 필요한가

만드는 곳(`result/`)과 **쓰는 곳**(`Z:`)이 다르다. 원장이 손으로 옮겨 왔는데,
그 뒤에 다시 뽑은 것을 옮기지 않으면 Z: 에 낡은 판이 남는다.

2026-09-23 에 실제로 났다 — 원장이 「태장중2 6과에 외부지문이 안 들어갔다」고 했는데
`result/` 것에는 들어 있었고 Z: 것이 9/17 판이었다. 그때 전수 대조하니 **38개가 낡아 있었다.**
낡은 종이가 아이 손에 가는 것이 이 프로젝트에서 가장 값비싼 실수다.

## 어디로 가나

파일 이름으로 정한다 — 이미 Z: 에 있으면 그 자리로, 없으면 아래 규칙으로.

    …동형모의고사…      Z:\…\중등 내신 동형 모의고사\
    그 밖(자체드릴 등)   Z:\…\중등 내신 대비 교재 정리\자체자료\{N}학년\

덮어쓰기는 **내용이 다를 때만** 한다 (md5). 같은 파일을 다시 쓰지 않는다.
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "result", "readitude")
Z_DRILL = r"Z:/학원파일/내신자료/중등 내신 대비 교재 정리/자체자료"
Z_MOCK = r"Z:/학원파일/내신자료/중등 내신 동형 모의고사"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def index_z():
    """Z: 에 이미 있는 것 — 파일 이름 → 경로. 원장이 정한 자리를 그대로 존중한다."""
    out = {}
    for root in (Z_DRILL, Z_MOCK):
        for dp, _, fn in os.walk(root):
            for f in fn:
                if f.lower().endswith(".pdf"):
                    out.setdefault(f, os.path.join(dp, f))
    return out


def dest_for(name):
    """Z: 에 없던 파일의 자리를 이름에서 정한다."""
    m = re.search(r"중(\d)|(\d)과", name)
    grade = "1" if re.search(r"중1|중1\s", name) else "2"
    if "동형모의고사" in name:
        return os.path.join(Z_MOCK, name)
    return os.path.join(Z_DRILL, f"{grade}학년", name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    zmap = index_z()
    news, stale, same = [], [], 0
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".pdf"):
            continue
        src = os.path.join(SRC, f)
        dst = zmap.get(f) or dest_for(f)
        if not os.path.exists(dst):
            news.append((src, dst))
        elif md5(src) != md5(dst):
            stale.append((src, dst))
        else:
            same += 1

    print(f"■ 같음 {same}개")
    print(f"\n■ Z: 것이 낡음 — 덮어쓸 것 {len(stale)}개")
    for s, d in stale:
        old = time.strftime("%m-%d", time.localtime(os.path.getmtime(d)))
        new = time.strftime("%m-%d", time.localtime(os.path.getmtime(s)))
        print(f"   {os.path.basename(s)[:46]:<48} {old} → {new}")
    print(f"\n■ Z: 에 없음 — 새로 넣을 것 {len(news)}개")
    for s, d in news:
        print(f"   {os.path.basename(s)[:46]:<48} → {os.path.dirname(d).replace(Z_DRILL, 'Z:…자체자료').replace(Z_MOCK, 'Z:…동형')}")

    if not a.apply:
        print("\n   --apply 를 붙이면 실제로 복사합니다. (Z: 의 낡은 판을 덮어씁니다)")
        return
    for s, d in stale + news:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
    print(f"\n   복사 완료 — 덮어씀 {len(stale)} · 새로 넣음 {len(news)}")


if __name__ == "__main__":
    sys.exit(main())
