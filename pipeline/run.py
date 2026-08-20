# -*- coding: utf-8 -*-
"""
생성 파이프라인 CLI.

  python -m pipeline.run list
  python -m pipeline.run pass-a --passage impulse --dry-run   # 호출 안 함. 프롬프트만 확인
  python -m pipeline.run pass-a --passage impulse --count     # 토큰 수만 (과금 없음)
  python -m pipeline.run pass-a --passage impulse --run       # 실제 호출 (동기)
  python -m pipeline.run pass-a --all --batch                 # 배치 제출 (단가 50%)
  python -m pipeline.run collect --batch-id msgbatch_...      # 배치 결과 수거

결과는 data/generated/<passage>.pass_a.json 에 떨어진다. DB에는 아직 넣지 않는다 —
평가를 먼저 통과해야 한다 (tools/eval_pass_a.py).
"""
import argparse
import json
import os
import sys
import time

from . import pass_a
from .env import load_env
from .models import PASS_A_MODEL, Cost, client
from .supabase import Rest

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "generated")


def slug(passage):
    return (passage.get("title") or passage["id"])[:40].replace("/", "_").replace(" ", "_")


def fetch_passages(rest, needle=None):
    rows = rest.get("/passage?select=id,title,source_detail,body_text,body_text_sha256,"
                    "kind,textbook_unit,word_count&order=title")
    if needle:
        low = needle.lower()
        rows = [p for p in rows
                if low in (p["title"] or "").lower() or low in p["id"].lower()]
    return rows


def save(passage, result):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{slug(passage)}.pass_a.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def show_diagnostics(result):
    d = result["diagnostics"]
    print(f"    태그  {d['tags_kept']}/{d['tags_returned']} 유지"
          f"   논리 {len(result['logic'])}/{d['sentence_count']} 문장"
          f"   문항 {d['items_kept']}/{d['items_returned']} 유지")
    for r in d["span_rejects"]:
        print(f"    ! 스팬 버림 [{r['where']}] {r['reason']}: {r['surface'][:50]!r}")
    if d["logic_missing_sentences"]:
        print(f"    ! 논리태깅 누락 문장: {d['logic_missing_sentences']}")
    for r in d["item_rejects"]:
        print(f"    ! 문항 버림 [{r['where']}] {r['reason']}")
    bad = [i for i in result["items"] if i["_answer_violates_point"]]
    if bad:
        print(f"    ! 정답 선지에 violates_point_code 가 붙은 문항 {len(bad)}건 (확인 필요)")


# ═══════════════════════════════════════════════════════════════════

def cmd_list(args):
    rest = Rest()
    for p in fetch_passages(rest):
        print(f"  {p['title'] or '(무제)':38} {p['word_count'] or 0:>4}단어  "
              f"{p['kind']:18} {p['source_detail'] or ''}")


def cmd_pass_a(args):
    env = load_env()
    rest = Rest(env)
    masters = load_masters_cached(rest)
    passages = fetch_passages(rest, None if args.all else args.passage)
    if not passages:
        raise SystemExit("해당하는 지문이 없습니다. `python -m pipeline.run list` 로 확인하십시오.")

    print(f"[대상 지문 {len(passages)}개]")
    for p in passages:
        print(f"  · {p['title']}  {p['word_count']}단어")
    print(f"\n[마스터] 어법 {len(masters['grammar'])} · 변형 {len(masters['mods'])} · "
          f"승인 유형 {len(masters['approved_qtypes'])}/{len(masters['qtypes'])}")

    built = [(p, pass_a.build_params(p, masters, batch=args.batch)) for p in passages]

    if args.dry_run:
        p, params = built[0]
        sys_chars = sum(len(b["text"]) for b in params["system"])
        print(f"\n[DRY RUN] 호출하지 않습니다.")
        print(f"  모델        {params['model']}")
        print(f"  system      {sys_chars:,}자 (캐시 프리픽스 포함)")
        print(f"  user        {len(params['messages'][0]['content']):,}자")
        print(f"  schema      {len(json.dumps(params['output_config']['format']['schema'])):,}자")
        print(f"  effort      {params['output_config']['effort']}")
        print(f"\n--- system 앞 1200자 ---\n{params['system'][0]['text'][:1200]}")
        print(f"\n--- user ---\n{params['messages'][0]['content'][:900]}")
        return

    api = client(env)

    if args.count:
        print()
        for p, params in built:
            n = api.messages.count_tokens(
                model=params["model"], system=params["system"],
                messages=params["messages"])
            print(f"  {p['title']:38} 입력 {n.input_tokens:,} 토큰")
        return

    if args.batch:
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
        batch = api.messages.batches.create(requests=[
            Request(custom_id=f"pass-a::{p['id']}",
                    params=MessageCreateParamsNonStreaming(**params))
            for p, params in built])
        print(f"\n[배치 제출] {batch.id}  상태 {batch.processing_status}")
        print(f"  수거:  python -m pipeline.run collect --batch-id {batch.id}")
        with open(os.path.join(OUT_DIR if os.path.isdir(OUT_DIR) else ROOT,
                               "last_batch.txt"), "w") as f:
            f.write(batch.id)
        return

    cost = Cost()
    print()
    for p, params in built:
        print(f"  [{p['title']}] 호출 중…", flush=True)
        with api.messages.stream(**params) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            print(f"    X 거부됨: {msg.stop_details}")
            continue
        cost.add(p["title"] or p["id"], params["model"], msg.usage, batch=False)
        result = pass_a.parse(pass_a.extract_json(msg), p)
        show_diagnostics(result)
        print(f"    → {save(p, result)}")
    print(f"\n[비용]\n{cost.report()}")


def cmd_collect(args):
    env = load_env()
    api, rest = client(env), Rest(env)
    bid = args.batch_id
    while True:
        batch = api.messages.batches.retrieve(bid)
        if batch.processing_status == "ended":
            break
        print(f"  대기 중… {batch.processing_status} "
              f"(처리 {batch.request_counts.processing})", flush=True)
        time.sleep(30)
    print(f"[배치 종료] 성공 {batch.request_counts.succeeded} · "
          f"실패 {batch.request_counts.errored} · 만료 {batch.request_counts.expired}")

    by_id = {p["id"]: p for p in fetch_passages(rest)}
    cost = Cost()
    for res in api.messages.batches.results(bid):
        pid = res.custom_id.split("::", 1)[1]
        p = by_id.get(pid)
        if res.result.type != "succeeded":
            print(f"  X {pid} {res.result.type}")
            continue
        msg = res.result.message
        cost.add((p or {}).get("title") or pid, msg.model, msg.usage, batch=True)
        result = pass_a.parse(pass_a.extract_json(msg), p)
        print(f"  [{p['title']}]")
        show_diagnostics(result)
        print(f"    → {save(p, result)}")
    print(f"\n[비용]\n{cost.report()}")


_masters = None


def load_masters_cached(rest):
    global _masters
    if _masters is None:
        _masters = pass_a.load_masters(rest)
    return _masters


def main():
    ap = argparse.ArgumentParser(prog="pipeline.run")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="DB의 지문 목록").set_defaults(fn=cmd_list)

    a = sub.add_parser("pass-a", help="태깅 A/B + 문항 생성")
    a.add_argument("--passage", help="제목·id 부분 일치")
    a.add_argument("--all", action="store_true", help="DB의 모든 지문")
    a.add_argument("--dry-run", action="store_true", help="호출하지 않고 프롬프트만 확인")
    a.add_argument("--count", action="store_true", help="토큰 수만 센다 (과금 없음)")
    a.add_argument("--run", action="store_true", help="동기 호출")
    a.add_argument("--batch", action="store_true", help="배치 제출 (단가 50%%)")
    a.set_defaults(fn=cmd_pass_a)

    c = sub.add_parser("collect", help="배치 결과 수거")
    c.add_argument("--batch-id", required=True)
    c.set_defaults(fn=cmd_collect)

    args = ap.parse_args()
    if args.cmd == "pass-a" and not (args.passage or args.all):
        ap.error("--passage 또는 --all 중 하나가 필요합니다")
    if args.cmd == "pass-a" and not (args.dry_run or args.count or args.run or args.batch):
        ap.error("--dry-run / --count / --run / --batch 중 하나를 고르십시오")
    args.fn(args)


if __name__ == "__main__":
    main()
