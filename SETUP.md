# 새 컴퓨터에서 시작하기

학원 컴퓨터에서 처음 받아 쓸 때의 순서. **5~10분**이면 된다.

---

## 1. 받기

```bash
git clone https://github.com/ytrdheather/readitest.git
cd readitest
```

## 2. 파이썬 의존성

```bash
pip install -r requirements.txt
```

## 3. 🔴 `.env` 만들기 — **키는 새로 발급한다**

```bash
copy .env.example .env
```

그 다음 `.env` 를 메모장으로 열어 값 4개를 채운다.

### 🔑 먼저 알아야 할 것 — **API 키는 여러 개 만들 수 있다**

API 키는 계정 비밀번호가 아니다. **한 계정에 여러 개를 만들 수 있고, 전부 같은
데이터에 접근한다.** 다른 것은 이름표뿐이다.

```
Anthropic 계정 하나
├── 키 "home"      ← 집 컴퓨터
├── 키 "academy"   ← 학원 컴퓨터
└── 키 "laptop"    ← 나중에 노트북 쓰면
```

도어락 카드키와 같다. 여러 장 만들어 두고, 한 장 잃어버리면 그 장만 등록 해제한다.

**그래서 좋은 점**

- **하나만 죽일 수 있다.** 학원 PC 를 조교가 쓰게 되면 `academy` 키만 폐기한다.
  집은 그대로 돌아간다. 같은 키를 양쪽에 쓰면 한쪽 때문에 양쪽이 다 멈춘다
- **어느 쪽에서 났는지 안다.** 콘솔에서 키별로 사용량이 보인다
- 노트북을 잃어버려도 그 키만 없애면 끝이다

### 그러니 키를 복사해 오지 말고 **새로 만든다**

카톡·메일로 옮기지 않는 이유는 「카톡이 위험해서」가 아니다. **옮길 이유가 없기
때문이다** — 새로 만드는 데 30초다. 그리고 옮기면 이런 일이 생긴다.

- **사본이 어디까지 퍼졌는지 모르게 된다.** 카톡은 폰·PC·태블릿에 동기화되고
  서버에도 남는다. 메일은 보낸편지함·받은편지함 양쪽에 남는다. 나중에 지워도
  백업에 남았는지 알 수 없다. 키는 문제가 생기면 즉시 폐기해야 하는데, 어디에
  사본이 있는지 모르면 폐기해도 안심이 안 된다
- **계정 하나가 뚫리면 키도 같이 간다.** 학원 공용 PC 에 카톡을 켜 두면 그
  컴퓨터에도 캐시가 남는다
- **`SUPABASE_SERVICE_ROLE_KEY` 는 특히 그렇다.** 이 키는 **RLS 를 무시한다.**
  「강사는 승인 문항만」을 DB 차원에서 막아 둔 것이 설계원칙 8인데, 이 키를 쥔
  쪽은 그걸 통째로 우회해 DB 전체를 읽고 쓴다. 앞으로 학생 이름·성적이 들어갈
  테이블이다
- **샜는지 안 샜는지 알 수 없다.** Anthropic 은 요금 청구서로 알게 되지만
  Supabase 는 그마저도 없다

| 값 | 어디서 | 비고 |
|---|---|---|
| `SUPABASE_URL` | Supabase → 프로젝트 → Settings → API Keys → **Project URL** | **공개 값. 그대로 복사해도 된다** |
| `SUPABASE_ANON_KEY` | 같은 화면 → **Publishable key** | **공개 값. 그대로 복사해도 된다** (`sb_publishable_`) |
| `SUPABASE_SERVICE_ROLE_KEY` | 같은 화면 → **Create new secret key** (이름 `academy`) | 🔴 **새로 만든다** (`sb_secret_`) |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys → **Create Key** (이름 `academy`) | 🔴 **새로 만든다.** 만든 직후 한 번만 보인다 |

> **넷 중 새로 만드는 것은 아래 둘뿐이다.** 위의 둘은 원래 공개되는 값이라
> 그대로 옮겨도 상관없다.

> ⚠️ **클로드에게 `.env` 를 만들어 달라고 하지 말 것.** 편집 도구로 그 파일을
> 건드리면 이후 원장이 값을 고칠 때마다 키 전체가 대화창에 밀려 들어간다.
> 2026-08-09 에 이 사고가 두 번 났고 키를 두 번 교체했다 (CLAUDE.md 규칙 1).

## 4. 확인

```bash
python tools/check_env.py
```

키 4개가 연결되는지만 본다. **값은 화면에 찍히지 않는다.**
연결이 안 되면 어디서 막혔는지 보는 도구가 따로 있다:

```bash
python tools/diag_supabase.py
```

> Supabase 무료 요금제는 **7일 놀면 프로젝트가 잠든다.** 증상은
> 「DNS 에서 프로젝트 주소가 사라짐」이다. 대시보드에서 **Restore** 를 누르면 된다.

```bash
python tools/check_schema.py
```

테이블·마스터·미승인 후보 코드를 찍는다. 여기까지 나오면 준비 끝이다.

## 5. 원본 자료 — 저장소에 **없다**

스캔본과 교과서 PDF 는 git 에 올라가지 않는다 (학생 이름·손글씨가 들어 있다,
CLAUDE.md 규칙 3). 저장소에는 **전사된 JSON 만** 있다.

원본 위치는 [`data/sources.md`](data/sources.md) 에 적혀 있다. 요약하면:

```
기출     Z:\학원파일\내신자료\⚫ 학교별 내신 시험지 ⚫\<학교명>\
배부물   Z:\학원파일\내신자료\❤ 스캔자료\<학년도 학기> 학교 프린트 모음\
교과서   Z:\학원파일\내신자료\중2 동아 윤정미 (22년 개정)\
```

> **Z: 드라이브가 잡혀 있어야 한다.** 학원 컴퓨터면 NAS 가 같은 망에 있으니
> 집보다 잘 될 것이다. 드라이브 문자가 다르면 명령의 경로만 바꾸면 된다.
>
> 자습서(`L5.pdf` · `l6.pdf`)는 집에서는 `Downloads` 에 두고 썼다. 학원에서는
> Z: 의 교과서 폴더에서 바로 읽으면 된다 — 도구는 경로를 인자로 받는다.

## 6. 클로드로 이어서 작업

프로젝트 폴더에서 클로드를 열면 [`CLAUDE.md`](CLAUDE.md) 가 자동으로 읽힌다.
그 다음 이 순서로 읽으라고 되어 있다:

```
STATUS.md  →  docs/리디테스트_기획서_v0.1.md
```

**[`STATUS.md`](STATUS.md) 맨 위에 「오늘 먼저 할 것」이 적혀 있다.**
[`HANDOFF.md`](HANDOFF.md) 1번은 가장 중요한 원칙이다.

---

## 자주 쓰는 명령

```bash
python tools/check_env.py         # 키 연결 (값 출력 안 함)
python tools/check_schema.py      # 테이블 · 마스터 · 미승인 후보
python tools/check_ingest.py      # 적재된 값 검증 (해시·스팬·정답·RLS)
python tools/make_review_sheet.py # 전사 확인지 다시 만들기
python -m pipeline.run list       # DB 의 지문 목록
```

> `db/002_ingest.py --reset` 은 **DELETE 를 실행한다.** `--reset` 없이는 돌지 않고
> 이미 있는 행은 건너뛴다 (CLAUDE.md 규칙 4).

## 막히면

| 증상 | 볼 것 |
|---|---|
| Supabase 연결 안 됨 | `python tools/diag_supabase.py` — DNS/TCP/TLS/HTTP 중 어디서 막혔는지 |
| 프로젝트 주소가 DNS 에 없음 | 7일 방치로 잠든 것. 대시보드에서 Restore |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Z: 경로 없음 | NAS 연결 확인. 드라이브 문자가 다르면 명령의 경로를 바꾼다 |
