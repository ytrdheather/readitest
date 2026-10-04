# -*- coding: utf-8 -*-
"""
영덕중1 5·6과 4~6세트 — 3번·12번(「문맥상 어색한 낱말」)을 다른 유형 · 더 어려운 문항으로 바꾼다.

  python tools/revise_yd1_vocab_items.py           # 미리보기
  python tools/revise_yd1_vocab_items.py --apply   # 반영 (원래 문항·자료는 revised_from 에 남김)

원장 2026-10-04: 「2개를 다른 유형으로 바꾸자. 난이도를 좀 높인 문제로」.
설계는 영영풀이 2(십자말 + 공통 빈칸)인데 모델이 「문맥상 어색한 낱말」 2개를 더 넣어 4개였다.
게다가 4세트 3번과 5세트 12번이 둘 다 「플래시 → 색이 밝아진다/강해진다」 로 같은 지점이었다.

바꾸는 꼴 — 범위(L5 There was/were · must not/don't have to · 비교급·최상급, L6 to부정사 · 접속사 that) 안에서만:
  · 어법 개수 / 틀린 것끼리 짝 (T-GRAMMAR-INLINE) — 영덕 2025 11번 「밑줄 중 맞는 것」 그릇
  · that 의 쓰임 구별 (T-GRAMMAR-USAGE) — 접속사 that 넷 + 지시대명사 하나
  · 내용 일치·불일치 (T-DETAIL) — 본문 표현을 살짝 바꾼 함정 선지

같은 자료를 쓰는 다른 문항(4세트 8·13번, 5·6세트 8번)이 기대는 문장은 남겼다.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK = os.path.join(ROOT, "data", "generated", "mock")
NOTE = " [유형 교체 2026-10-04 — 원래 「문맥상 어색한 낱말」]"
COUNT = ["1개", "2개", "3개", "4개", "5개"]

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REV = {
    # ───────────── 4세트 ─────────────
    (4, 3): {
        "mat": ("T3", "Our class visited the City Art Museum last Friday. Before we went inside, the guide "
                "explained the rules. First, we ⓐmust not touching any of the paintings, because the oil on "
                "our hands can damage them. Second, we have to keep our voices low, but we ⓑdon’t have to be "
                "completely silent. Third, flash photos are not allowed, because strong light can make the "
                "colors of old paintings weaker. ⓒThere were many old paintings in the first room, and the "
                "oldest one was ⓓmore old than the museum building itself. Finally, the guide said ⓔthat "
                "food and drinks must stay outside."),
        "item": {"type": "T-GRAMMAR-INLINE", "points": 5,
                 "stem_ko": "[T3]의 밑줄 친 ⓐ~ⓔ 중 어법상 옳은 것의 개수는?",
                 "options": COUNT, "answer": 3,
                 "grammar_point": "VERB_MODAL_USAGE · MOD_COMPARATIVE · NOUN_CLAUSE_THAT",
                 "why_ko": "옳은 것은 ⓑ don’t have to(~할 필요 없다) · ⓒ There were + 복수(many old paintings) · "
                           "ⓔ 접속사 that 의 3개. ⓐ 조동사 뒤에는 동사원형 → must not touch. "
                           "ⓓ old 의 비교급은 older → more old 는 틀림."}},
    (4, 12): {
        "mat": ("T7", "Why do people throw food at famous paintings?\n"
                "In 2022, two young visitors threw tomato soup at a Van Gogh painting in London. A few months "
                "earlier, a man threw a cake at the Mona Lisa in Paris. People soon learned ①that strong glass "
                "protected both paintings, and the news traveled around the world in just a few hours.\n"
                "The attackers were not thieves. Most of them were climate activists. They believed ②that a "
                "famous painting was the fastest way to get attention. One of them said, “Art is important, "
                "but our planet is more important.”\n"
                "Many people do not agree with them. They say ③that hurting art never helps the Earth. "
                "④That is why museums now check visitors’ bags more carefully than before, and some of them "
                "do not allow any food inside. Many people hope ⑤that the debate will end soon, but it is "
                "still hot."),
        "item": {"type": "T-GRAMMAR-USAGE", "points": 5,
                 "stem_ko": "[T7]의 밑줄 친 ①~⑤ 중 that 의 쓰임이 나머지 넷과 다른 것은?",
                 "options": ["①", "②", "③", "④", "⑤"], "answer": 4,
                 "grammar_point": "NOUN_CLAUSE_THAT",
                 "why_ko": "①②③⑤ 는 learned · believed · say · hope 의 목적어가 되는 절을 이끄는 접속사 that "
                           "(생략 가능). ④ 는 앞 문장 내용을 가리키는 지시대명사 That(「그것이 ~한 이유다」)이라 "
                           "생략할 수 없다."}},
    # ───────────── 5세트 ─────────────
    (5, 3): {
        "mat": ("T3", "Last month, our school started a zero-waste campaign. At first, ⓐthere was hundreds of "
                "plastic cups in the trash cans every week. Now, almost every student ⓑdecides to bring a "
                "reusable bottle from home. The school also put a recycling machine next to the gym, and we "
                "ⓒdon’t have to pay to use it. But students ⓓmust not putting dirty bottles into the machine. "
                "Since the campaign started, our school’s trash is getting ⓔsmaller and smaller."),
        "item": {"type": "T-GRAMMAR-INLINE", "points": 5,
                 "stem_ko": "[T3]의 밑줄 친 ⓐ~ⓔ 중 어법상 틀린 것끼리 짝지은 것은?",
                 "options": ["ⓐ, ⓑ", "ⓐ, ⓓ", "ⓑ, ⓒ", "ⓒ, ⓔ", "ⓓ, ⓔ"], "answer": 2,
                 "grammar_point": "VERB_MODAL_USAGE · NONFIN_TO_ROLE",
                 "why_ko": "ⓐ hundreds of plastic cups 는 복수 → there were. ⓓ 조동사 뒤 동사원형 → must not put. "
                           "ⓑ decide 는 to부정사를 목적어로 쓰고 주어 every student 는 단수라 decides 가 맞다. "
                           "ⓒ don’t have to(~할 필요 없다) · ⓔ 비교급 and 비교급(점점 더 ~한)은 옳다."}},
    (5, 12): {
        "mat": ("T7", "Have you ever heard a guard say, \"Please don't touch\"? Museums have many rules, and most "
                "of them are there to protect the artworks. Our hands always have a little oil and dirt on them. "
                "One touch leaves a very small mark, but thousands of touches can damage a painting forever. "
                "Light is another problem. Strong light, like a camera flash, slowly makes the colors of an old "
                "painting weaker, so most museums do not allow flash photography. Food and drinks are also "
                "dangerous. A drop of juice can stay on a wooden frame for years, and sweet food brings insects. "
                "So the next time you visit a museum, remember: the rules are not there to make your visit "
                "boring. They are there to keep art safe for the next hundred years."),
        "item": {"type": "T-DETAIL", "points": 5,
                 "stem_ko": "[T7]의 내용과 일치하는 것은?",
                 "options": ["One touch can damage a painting forever.",
                             "Strong light can slowly change the colors of an old painting.",
                             "Sweet food is dangerous because it can break a wooden frame.",
                             "A drop of juice disappears from a frame in a few days.",
                             "Museum rules are there to make visits more exciting."],
                 "answer": 2,
                 "why_ko": "② 강한 빛이 오래된 그림의 색을 서서히 약하게 만든다 — 일치. "
                           "① 한 번 만지면 아주 작은 자국만 남고, 수천 번이 그림을 영원히 망친다(one 과 thousands 바꿔치기). "
                           "③ 단 음식은 벌레를 부른다(틀을 부수는 것이 아님). ④ 주스 한 방울은 몇 년 동안 남는다. "
                           "⑤ 규칙은 지루하게 하려는 것이 아니라 예술품을 지키려는 것 — 흥미와는 무관."}},
    # ───────────── 6세트 ─────────────
    (6, 3): {
        "mat": ("T3", "Last Monday, something strange happened at the city library. Someone drew a big heart on "
                "the back of an old map. ⓐThere was two eyewitnesses. Mina, a student, said, “The person was "
                "a little ⓑshorter than me, and I am 160 cm tall.” Mr. Han, a librarian, ran after the person "
                "but couldn’t catch him. “He was ⓒmuch faster than me. He was ⓓthe most fast runner in the "
                "library that day,” Mr. Han said. The police decided ⓔto check the CCTV."),
        "item": {"type": "T-GRAMMAR-INLINE", "points": 5,
                 "stem_ko": "[T3]의 밑줄 친 ⓐ~ⓔ 중 어법상 옳은 것의 개수는?",
                 "options": COUNT, "answer": 3,
                 "grammar_point": "MOD_COMPARATIVE · NONFIN_TO_ROLE",
                 "why_ko": "옳은 것은 ⓑ 비교급 shorter than · ⓒ much 는 비교급을 강조(훨씬) · ⓔ decide 는 "
                           "to부정사를 목적어로 쓴다 — 3개. ⓐ two eyewitnesses 는 복수 → There were. "
                           "ⓓ fast 의 최상급은 the fastest."}},
    (6, 12): {
        "mat": ("T7", "Do you throw away a chair when one leg breaks? In many cities, there is a better choice: "
                "a repair café. At a repair café, people bring broken things and fix them with the help of "
                "volunteers. You don’t have to pay for the help. You only need to bring your broken item and a "
                "little patience. The first repair café opened in Amsterdam in 2009, and now there are more "
                "than two thousand of them around the world. Repair cafés reduce waste, and they also teach "
                "useful skills. Many visitors say that fixing an old thing is more exciting than buying a new "
                "one. Things also last longer when we take care of them, so your old bag may stay with you for "
                "many years. Why don’t you give your old things a second life this weekend?"),
        "item": {"type": "T-DETAIL", "points": 5,
                 "stem_ko": "[T7]의 내용과 일치하지 않는 것은?",
                 "options": ["리페어 카페에서는 자원봉사자의 도움을 받아 물건을 고친다.",
                             "리페어 카페에서 도움을 받는 데 돈을 낼 필요가 없다.",
                             "첫 리페어 카페는 2009년 암스테르담에서 문을 열었다.",
                             "현재 전 세계의 리페어 카페는 2,000개가 채 되지 않는다.",
                             "많은 방문객은 낡은 물건을 고치는 것이 새것을 사는 것보다 더 흥미롭다고 말한다."],
                 "answer": 4,
                 "why_ko": "본문은 more than two thousand(2,000개가 넘는다)라고 했다 — ④ 불일치. "
                           "① with the help of volunteers ② don’t have to pay(낼 필요 없다 — must not 과 구별) "
                           "③ 2009 · Amsterdam ⑤ more exciting than buying a new one 은 일치."}},
}


def main():
    apply = "--apply" in sys.argv
    for n in sorted({k[0] for k in REV}):
        p = os.path.join(MOCK, f"중1_영덕중_{n}세트.json")
        d = json.load(io.open(p, encoding="utf-8"))
        mats = {m["id"]: m for m in d["materials"]}
        for it in d["items"]:
            r = REV.get((n, it["no"]))
            if not r:
                continue
            if "revised_from" in it:
                print(f"  {n}세트 {it['no']}번  이미 바꿈 — 건너뜀")
                continue
            mid, text = r["mat"]
            m = mats[mid]
            it["revised_from"] = {k: it.get(k) for k in
                                  ("type", "stem_ko", "options", "answer", "why_ko", "grammar_point")}
            it["revised_from"]["material_text"] = m["text"]
            m["text"] = text
            it.update(r["item"])
            it["why_ko"] += NOTE
            print(f"  {n}세트 {it['no']}번  → {it['type']} · {it['stem_ko'][:40]} · 정답 {it['answer']}")
        if apply:
            n_vocab = sum(1 for x in d["items"] if x["type"] == "T-VOCAB-CONTEXT")
            d["diagnostics"]["problems"] = [x for x in d["diagnostics"]["problems"] if "영영풀이" not in x]
            print(f"     영영풀이 {n_vocab}문항")
            with io.open(p, "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
    print("\n  반영함" if apply else "\n  [미리보기] 반영하려면 --apply")


if __name__ == "__main__":
    main()
