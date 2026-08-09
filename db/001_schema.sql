-- ===================================================================
--  리디테스트 스키마 v1  (1~2단계 범위)
--  생성 2026-08-09 · 근거: docs/리디테스트_기획서_v0.1.md
--
--  ※ Supabase 웹 화면 → SQL Editor 에 통째로 붙여넣고 Run 하십시오.
--  ※ 여러 번 실행해도 안전합니다 (전부 IF NOT EXISTS / ON CONFLICT).
--
--  0단계에서 확정된 설계만 담았습니다.
--    · 지문 원본(canonical) / 학교별 변형본 분리      §5.5.4
--    · 태깅 A(어법) · 태깅 B(논리구조) 두 축           §7.1.2
--    · 변형 유형 카탈로그 20종                          §5.6
--    · 문항 유형 마스터 + 2층 검수 라우팅               §7.1.1
--    · 반려 사유 9종 (DETACHED_FROM_PASSAGE 포함)       §7.1.2
--    · curriculum_version / textbook 버전 필드          §5.5
--    · RLS — 강사는 승인 문항만                          §5.4
--
--  아직 안 넣은 것 (JSON이 굳지 않아 보류):
--    student / worksheet / attempt / vocab  → 3단계
-- ===================================================================

create extension if not exists "pgcrypto";

-- ===================================================================
-- 0. 사용자 · 역할  (RLS의 기준)
-- ===================================================================

create table if not exists profile (
  user_id     uuid primary key references auth.users(id) on delete cascade,
  role        text not null default 'teacher'
                check (role in ('director','teacher','assistant')),
  display_name text,
  created_at  timestamptz not null default now()
);
comment on table profile is '역할 판정 기준. auth.users 1:1';

create or replace function is_director() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from profile where user_id = auth.uid() and role = 'director');
$$;

create or replace function is_staff() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from profile where user_id = auth.uid());
$$;

-- ===================================================================
-- 1. 마스터 — 어법 포인트
-- ===================================================================

create table if not exists grammar_point (
  code        text primary key,
  category    text not null,
  label_ko    text not null,
  note        text,
  is_candidate boolean not null default false,   -- 기출 대조로 새로 발견된 것
  created_at  timestamptz not null default now()
);
comment on table grammar_point is
  '시스템의 어휘. 태깅·문항·매핑이 전부 이 코드를 참조한다. 자유 텍스트 금지.';

insert into grammar_point (code, category, label_ko, is_candidate) values
  ('VERB_SVA',            '동사',   '주어-동사 수일치 (수식어구가 긴 경우)', false),
  ('VERB_FINITE',         '동사',   '본동사 vs 준동사',                      false),
  ('VERB_TENSE',          '동사',   '시제 일치',                             false),
  ('VERB_MODAL_HAVE_PP',  '동사',   '조동사 + have p.p.',                    false),
  ('VERB_MODAL_USAGE',    '동사',   'have to / must / don''t have to',       true),
  ('VOICE_ACTIVE_PASSIVE','태',     '능동 vs 수동',                          false),
  ('VOICE_PARTICIPLE',    '태',     '현재분사 vs 과거분사',                  false),
  ('NONFIN_TO_VS_GERUND', '준동사', 'to부정사 vs 동명사',                    false),
  ('NONFIN_SUBJECT',      '준동사', '의미상 주어',                           false),
  ('REL_PRON_VS_ADV',     '관계사', '관계대명사 vs 관계부사',                false),
  ('REL_WHAT_VS_THAT',    '관계사', 'what vs that',                          false),
  ('REL_CONTINUOUS',      '관계사', '계속적 용법',                           false),
  ('REL_POSSESSIVE',      '관계사', '소유격 관계대명사 whose',               true),
  ('CONJ_VS_PREP',        '접속',   '접속사 vs 전치사',                      false),
  ('CONJ_PARALLEL',       '접속',   '병렬구조',                              false),
  ('NOUN_CLAUSE_THAT',    '접속',   '명사절 접속사 that (생략 포함)',        true),
  ('NOUN_CLAUSE_IF',      '접속',   '명사절 접속사 if (~인지)',              true),
  ('MOD_ADJ_VS_ADV',      '수식',   '형용사 vs 부사',                        false),
  ('MOD_COMPARATIVE',     '수식',   '비교급·최상급',                         false),
  ('MOD_POSTPOSITIVE',    '수식',   '-thing + 형용사 후치수식',              true),
  ('SENSE_VERB_ADJ',      '수식',   '감각동사 + 형용사 보어',                true),
  ('PRON_AGREEMENT',      '기타',   '대명사 수·격 (its vs it''s)',           false),
  ('PRON_REFLEXIVE',      '기타',   '재귀대명사',                            false),
  ('PRON_INDEFINITE',     '기타',   '부정대명사 (부정문의 anything 등)',     true),
  ('SUBJUNCTIVE',         '기타',   '가정법 시제',                           false),
  ('INVERSION',           '기타',   '도치',                                  false),
  ('IT_CLEFT',            '기타',   'it 가주어 · 강조구문 · 비인칭 it',      false),
  ('SO_SUCH_TOO_ENOUGH',  '기타',   'so/such · too/enough',                  false)
on conflict (code) do nothing;

-- ===================================================================
-- 2. 마스터 — 변형 유형 카탈로그  (§5.6)
--    예측 시스템과 오답 선지 생성기의 근거.
--    서로 다른 두 교사·두 학교 기출에서 관측된 것들.
-- ===================================================================

create table if not exists modification_type (
  code            text primary key,
  category        text not null
                    check (category in ('error_injection','blank_out','reuse','cosmetic')),
  label_ko        text not null,
  example_before  text,
  example_after   text,
  observed_count  int not null default 0,
  created_at      timestamptz not null default now()
);
comment on table modification_type is
  '교사가 지문을 시험에 낼 때 쓰는 변형 방법. 유한하므로 곧 포화한다.';

insert into modification_type (code, category, label_ko, example_before, example_after) values
  ('EI_ACTIVE_TO_PASSIVE_NO_BY','error_injection','능동→수동 전환 후 by 누락','The explosion created a cloud','A cloud was created the explosion'),
  ('EI_INTRANS_PASSIVIZED',     'error_injection','자동사를 수동태로','were killed for food','were died by food'),
  ('EI_PASSIVE_FORM',           'error_injection','수동태 형태 오류','was invented','was inventing'),
  ('EI_PREP_DELETE',            'error_injection','전치사 삭제','forward with their feet','forward their feet'),
  ('EI_PARTICIPLE_FLIP',        'error_injection','과거분사↔현재분사','a goose trapped','a goose trapping'),
  ('EI_GERUND_TO_VERB',         'error_injection','동명사→정동사','while shopping','while shops'),
  ('EI_PARALLEL_BREAK',         'error_injection','병렬 깨기','or saving for','or saves for'),
  ('EI_AGREEMENT',              'error_injection','수일치 오류','but also makes','but also make'),
  ('EI_NONFIN_FORM',            'error_injection','준동사 형태 오류','difficult to understand','difficult understood'),
  ('EI_CAUSATIVE_FORM',         'error_injection','사역동사 뒤 형태 오류','let her enter','let her entered'),
  ('EI_VERB_COMPLEMENT',        'error_injection','동사별 목적보어 규칙 위반','refused to give up','refused giving up'),
  ('EI_REL_ANTECEDENT',         'error_injection','관계사 선행사 불일치','tool which','tool who'),
  ('EI_FUTURE_IN_SUBORD',       'error_injection','시간·조건절에 미래시제','if you compare','if you will compare'),
  ('EI_STRUCT_DELETE',          'error_injection','구문 통째 제거','needed my help to free its baby','needed my help for its baby'),
  ('EI_ADJ_TO_ADV',             'error_injection','형용사↔부사 교체','it looked nice','it looked nicely'),
  ('BO_FORM_CHOICE',            'blank_out','어형을 빈칸으로 만들고 선지 제시','the most widely accepted one','the most widely ___ one'),
  ('BO_WORD_ORDER',             'blank_out','우리말 주고 주어진 단어로 배열','There are many people who fall for','(배열 문제)'),
  ('RU_EXERCISE_OPTIONS',       'reuse','배부 프린트 연습문제 선지를 시험 선지로','배부본 Which is NOT true 선지 4개','시험 문항 선지로 이동'),
  ('CO_SYNONYM',                'cosmetic','어휘 교체 (어법 무관)','moved','touched'),
  ('CO_CONJ_SWAP',              'cosmetic','동의 접속사 교체','While I was relaxing','When I was relaxing'),
  ('CO_SENTENCE_DROP',          'cosmetic','문장 삭제','(배부본의 한 문장)','(시험본에서 제거)')
on conflict (code) do nothing;

-- ===================================================================
-- 3. 마스터 — 문항 유형  (2층 검수의 1층)
--    value_approved: 원장이 '훈련 가치 있음'으로 승인한 유형만 생성한다.
--    review_tier:    fast = 정오만 빠르게 / deep = 정밀 검수 큐로
-- ===================================================================

create table if not exists question_type (
  code            text primary key,
  label_ko        text not null,
  option_lang     text not null default 'na' check (option_lang in ('ko','en','na')),
  value_approved  boolean,                 -- null = 미검수
  approved_at     timestamptz,
  review_tier     text not null default 'fast' check (review_tier in ('fast','deep')),
  tier_reason     text,                    -- S1(연속 판정) / S2(자유 기술)
  note            text
);
comment on table question_type is
  '유형 검수 결과를 담는다. value_approved=false 인 유형은 아예 생성하지 않는다.';

insert into question_type (code, label_ko, option_lang, value_approved, approved_at, review_tier, tier_reason) values
  ('T-GRAMMAR-INLINE','어법 — 지문 통째 밑줄, 틀린 것 있는 대로','na', true,'2026-08-09','fast',null),
  ('T-GRAMMAR-USAGE', '어법 — 쓰임이 다른 것 구별',              'na', true,'2026-08-09','fast',null),
  ('T-VOCAB-CONTEXT', '어휘추론 — 문맥상 부적절한 낱말',          'na', true,'2026-08-09','deep','S1 연속 판정'),
  ('T-PHRASE-INFER',  '어구추론 — 밑줄 어구의 의미',              'ko', true,'2026-08-09','deep','S1 연속 판정'),
  ('T-TOPIC',         '주제찾기',                                 'en', true,'2026-08-09','fast',null),
  ('T-DETAIL',        '내용일치 / 불일치',                        'en', true,'2026-08-09','fast',null),
  ('T-BLANK',         '빈칸추론 (주제문·결론문 자리)',            'en', true,'2026-08-09','fast',null),
  ('T-WRITE-COND',    '서술형 — 조건영작',                        'na', true,'2026-08-09','fast',null),
  ('T-WRITE-FIX',     '서술형 — 오류수정',                        'na', true,'2026-08-09','deep','S2 자유 기술'),
  ('T-GRAMMAR-STANDALONE','어법 — 단문 나열형',                   'na', false,'2026-08-09','fast','지문 비연계로 반려')
on conflict (code) do nothing;

-- ===================================================================
-- 4. 마스터 — 반려 사유 9종
-- ===================================================================

create table if not exists reject_reason (
  code      text primary key,
  label_ko  text not null,
  axis      text not null check (axis in ('correctness','difficulty','duplication','value'))
);

insert into reject_reason (code, label_ko, axis) values
  ('AMBIGUOUS_ANSWER',      '정답이 둘 이상으로 해석 가능', 'correctness'),
  ('WRONG_POINT',           '겨냥한 문법 포인트와 불일치',  'correctness'),
  ('UNNATURAL_ENGLISH',     '영어가 어색함',                'correctness'),
  ('BAD_DISTRACTOR',        '오답 선지가 변별력 없음',      'correctness'),
  ('TOO_EASY',              '난이도 낮음',                  'difficulty'),
  ('TOO_HARD',              '난이도 높음',                  'difficulty'),
  ('OFF_SYLLABUS',          '학교 범위 밖',                 'difficulty'),
  ('DUPLICATE',             '기존 문항과 중복',             'duplication'),
  ('DETACHED_FROM_PASSAGE', '지문 비연계 — 훈련 가치 없음', 'value')
on conflict (code) do nothing;
comment on column reject_reason.axis is
  'value 축은 2026-08-09 신설. 기존 8개는 전부 정오·난이도·중복 축이었다.';

-- ===================================================================
-- 5. 학교 · 교과서 · 시험
-- ===================================================================

create table if not exists textbook (
  id                 uuid primary key default gen_random_uuid(),
  publisher          text not null,
  author             text,
  curriculum_version text not null,          -- '2015개정' | '2022개정'
  grade              int  not null,
  label              text generated always as
                       (publisher || '(' || coalesce(author,'') || ') ' || curriculum_version || ' 중' || grade) stored,
  unique (publisher, author, curriculum_version, grade)
);

insert into textbook (publisher, author, curriculum_version, grade)
values ('동아','윤정미','2022개정',2)
on conflict do nothing;

create table if not exists school (
  id         uuid primary key default gen_random_uuid(),
  name       text not null unique,
  note       text
);

insert into school (name) values ('영덕중'),('영일중'),('청명중'),('태장중')
on conflict (name) do nothing;

create table if not exists exam (
  id           uuid primary key default gen_random_uuid(),
  school_id    uuid not null references school(id) on delete cascade,
  grade        int  not null,
  year         int  not null,
  semester     int  not null check (semester in (1,2)),
  sitting      text not null check (sitting in ('중간','기말')),
  exam_date    date,
  textbook_id  uuid references textbook(id),
  -- 구조는 학교·회차마다 다르다. 예측 축으로 쓰지 않고 관측만 한다. §5.5.4
  mc_count     int,
  essay_count  int,
  total_score  int,
  page_count   int,
  teacher_name text,      -- 기록만. 매년 교체되므로 예측 키 아님. §5.5.2
  unique (school_id, grade, year, semester, sitting)
);

-- ===================================================================
-- 6. 지문 — 원본(canonical)과 학교별 변형본 분리  (§5.5.4 핵심)
--    · 교과서 본문·대화문 : school_id 없음. 4개교가 공유
--    · 배부 외부지문      : 원본은 공유, 학교별로 변형되어 배부됨
-- ===================================================================

create table if not exists passage (
  id                  uuid primary key default gen_random_uuid(),
  kind                text not null
                        check (kind in ('textbook_reading','textbook_dialogue','handout_external','exam_only')),
  title               text,
  textbook_id         uuid references textbook(id),
  textbook_unit       text,                     -- 'Lesson 3'
  source_detail       text,
  body_text           text not null,
  body_text_sha256    text not null,            -- 확정 후 불변. 태깅은 이 해시 기준으로만 유효
  word_count          int,
  transcription_status text not null default 'pending'
                        check (transcription_status in ('pending','disputed','confirmed')),
  transcription_note  text,
  has_handwriting     boolean not null default false,
  scan_file           text,
  scan_page           int,
  distribution_scope  text not null default 'internal_only',   -- 저작권. 계획서 8장
  created_at          timestamptz not null default now(),
  unique (body_text_sha256)
);
comment on column passage.body_text is
  '전사 확정본. 고치려면 새 레코드를 만들 것 — 조용히 고치면 모든 span이 어긋난다.';

create table if not exists passage_variant (
  id             uuid primary key default gen_random_uuid(),
  passage_id     uuid not null references passage(id) on delete cascade,
  school_id      uuid not null references school(id) on delete cascade,
  exam_id        uuid references exam(id),
  body_text      text not null,
  body_text_sha256 text not null,
  handout_ref    text,                    -- '[4-11] More Reading'
  diff_note      text,                    -- 원본 대비 무엇이 달라졌나
  planted_points text[],                  -- ★ 이 학교가 심은 문법 포인트 = 출제 예고 신호
  created_at     timestamptz not null default now(),
  unique (passage_id, school_id)
);
comment on table passage_variant is
  '같은 원본을 학교마다 다르게 손본다. planted_points가 그 학교의 출제 예고. §5.5.4 ③';

-- ===================================================================
-- 7. 태깅 A (어법)  ·  태깅 B (논리 구조)
-- ===================================================================

create table if not exists passage_tag (
  id                  uuid primary key default gen_random_uuid(),
  passage_id          uuid not null references passage(id) on delete cascade,
  grammar_point_code  text not null references grammar_point(code),
  span_start          int  not null,
  span_end            int  not null,
  surface             text not null,
  rationale           text,                    -- 검수 화면에 노출. 원장이 재판단하지 않도록
  confidence          text not null default 'medium' check (confidence in ('high','medium','low')),
  teacher_emphasis    boolean not null default false,   -- 배부본 볼드. 가중치로만 사용 §6.2.2③
  status              text not null default 'pending'
                        check (status in ('pending','approved','rejected')),
  created_at          timestamptz not null default now(),
  check (span_end > span_start)
);
comment on table passage_tag is '태깅 A — 어법 전수 태깅. 어법·오류수정 문항의 근거.';

create table if not exists passage_logic (
  id            uuid primary key default gen_random_uuid(),
  passage_id    uuid not null references passage(id) on delete cascade,
  sentence_no   int not null,
  role          text not null,      -- 도입질문 | 정의 | 원인 | 부정적결과 | 전환 | 해결책 | 주제문 | 결론문
  signal        text,               -- 연결 신호어: Also / not only~but also / To avoid / When
  is_blank_candidate boolean not null default false,   -- 계획서 9장: 빈칸은 주제문·결론문
  note          text,
  unique (passage_id, sentence_no)
);
comment on table passage_logic is
  '태깅 B — 논리 구조. 주제·내용일치·어구추론·빈칸 문항은 전부 여기서 나온다. §7.1.2';

-- ===================================================================
-- 8. 예상 출제 지점  = 태그 × 변형 유형
-- ===================================================================

create table if not exists predicted_item_site (
  id                      uuid primary key default gen_random_uuid(),
  passage_id              uuid not null references passage(id) on delete cascade,
  passage_tag_id          uuid references passage_tag(id) on delete cascade,
  modification_type_code  text not null references modification_type(code),
  rendered_wrong_form     text,          -- 이 지점이 변형되면 어떤 형태가 되는가
  priority                int not null default 0,
  created_at              timestamptz not null default now()
);
comment on table predicted_item_site is
  '"이 교사가 뭘 낼까"가 아니라 "이 지점이 어떻게 변형될 수 있나"를 전부 나열한다. §5.5.2';

-- ===================================================================
-- 9. 문항
-- ===================================================================

create table if not exists item (
  id                  uuid primary key default gen_random_uuid(),
  passage_id          uuid not null references passage(id) on delete cascade,
  question_type_code  text not null references question_type(code),
  grammar_point_code  text references grammar_point(code),
  stem                text not null,
  answer_key          text,
  explanation         text,
  difficulty          text check (difficulty in ('easy','medium','hard')),
  option_lang         text check (option_lang in ('ko','en','na')),
  version             int  not null default 1,
  parent_item_id      uuid references item(id),          -- 수정은 새 버전. 이전 버전 보존
  status              text not null default 'draft'
                        check (status in ('draft','auto_passed','approved','rejected','retired')),
  review_tier         text not null default 'fast' check (review_tier in ('fast','deep')),
  approved_by         uuid references auth.users(id),
  approved_at         timestamptz,
  created_at          timestamptz not null default now()
);
comment on column item.status is
  '강사에게는 approved 만 보인다. RLS로 강제 — 애플리케이션 코드가 아니라 DB 레벨.';

create table if not exists item_option (
  id                  uuid primary key default gen_random_uuid(),
  item_id             uuid not null references item(id) on delete cascade,
  label               text not null,          -- ① ② ③ ...
  body                text not null,
  is_answer           boolean not null default false,
  violates_point_code text references grammar_point(code),      -- 오답이 위반하는 포인트 (정답은 null)
  via_modification    text references modification_type(code),  -- 어떤 변형으로 만들었나
  ordinal             int not null default 0
);
comment on column item_option.violates_point_code is
  '오답 선지는 지정된 포인트 하나만 위반해야 한다. 계획서 7장 품질 원칙.';

create table if not exists item_check (
  id            uuid primary key default gen_random_uuid(),
  item_id       uuid not null references item(id) on delete cascade,
  check_type    text not null
                  check (check_type in ('reverse_solve','option_uniqueness','director_review')),
  passed        boolean,
  model_used    text,
  detail        jsonb,
  reject_reason text references reject_reason(code),
  review_seconds int,                       -- 검수 속도 실측. 게이트 추적용
  reviewed_by   uuid references auth.users(id),
  reviewed_at   timestamptz not null default now()
);
comment on table item_check is
  '반려 사유 분포가 프롬프트 개선의 유일한 신호원. review_seconds로 검수 속도를 추적한다.';

-- ===================================================================
-- 10. 매핑 · 관측
-- ===================================================================

create table if not exists school_grammar_map (
  id                  uuid primary key default gen_random_uuid(),
  school_id           uuid not null references school(id) on delete cascade,
  grade               int  not null,
  textbook_id         uuid not null references textbook(id),   -- 교과서 바뀌면 매핑 무효 §5.5
  textbook_unit       text,
  grammar_point_code  text not null references grammar_point(code),
  is_extension        boolean,                 -- 교과서 범위 초과. 원장이 몸으로 알아낸 것
  evidence_exam_id    uuid references exam(id),
  confidence          text not null default 'medium' check (confidence in ('high','medium','low')),
  note                text,
  updated_by          uuid references auth.users(id),
  updated_at          timestamptz not null default now()
);
comment on table school_grammar_map is
  '학원의 심장. 다만 단원 매핑은 교과서 개정 시 폐기되므로 textbook_id가 필수. §5.5';

create table if not exists exam_observation (
  id                        uuid primary key default gen_random_uuid(),
  exam_id                   uuid not null references exam(id) on delete cascade,
  handout_passage_hit_rate  numeric,     -- 배부 외부지문 중 출제된 비율. 누적 9/9
  textbook_passage_hit_rate numeric,     -- 교과서 본문 중 출제된 비율. 6/6
  grammar_score_share       numeric,     -- 전체 배점 중 어법 비중
  grammar_distribution      jsonb,       -- 포인트별 배점 분포
  note                      text,
  observed_at               timestamptz not null default now(),
  unique (exam_id)
);
comment on table exam_observation is
  'teacher_pattern을 대체. 교사는 매년 바뀌므로 학교×회차 단위로 쌓는다. §5.5.2';

-- ===================================================================
-- 11. 인덱스
-- ===================================================================

create index if not exists idx_passage_textbook   on passage(textbook_id, textbook_unit);
create index if not exists idx_variant_school     on passage_variant(school_id);
create index if not exists idx_tag_passage        on passage_tag(passage_id);
create index if not exists idx_tag_point          on passage_tag(grammar_point_code);
create index if not exists idx_logic_passage      on passage_logic(passage_id);
create index if not exists idx_item_passage       on item(passage_id);
create index if not exists idx_item_status        on item(status) where status = 'approved';
create index if not exists idx_item_queue         on item(status, review_tier) where status = 'auto_passed';
create index if not exists idx_option_item        on item_option(item_id);
create index if not exists idx_check_item         on item_check(item_id);
create index if not exists idx_map_lookup         on school_grammar_map(school_id, grade, textbook_id, textbook_unit);
create index if not exists idx_site_passage       on predicted_item_site(passage_id);

-- ===================================================================
-- 12. RLS — 기본은 거부. 강사는 승인 문항만.
-- ===================================================================

alter table profile             enable row level security;
alter table grammar_point       enable row level security;
alter table modification_type   enable row level security;
alter table question_type       enable row level security;
alter table reject_reason       enable row level security;
alter table textbook            enable row level security;
alter table school              enable row level security;
alter table exam                enable row level security;
alter table passage             enable row level security;
alter table passage_variant     enable row level security;
alter table passage_tag         enable row level security;
alter table passage_logic       enable row level security;
alter table predicted_item_site enable row level security;
alter table item                enable row level security;
alter table item_option         enable row level security;
alter table item_check          enable row level security;
alter table school_grammar_map  enable row level security;
alter table exam_observation    enable row level security;

-- 본인 프로필
drop policy if exists p_profile_self on profile;
create policy p_profile_self on profile for select using (user_id = auth.uid());

-- 원장: 전 테이블 전권
do $$
declare t text;
begin
  foreach t in array array[
    'grammar_point','modification_type','question_type','reject_reason',
    'textbook','school','exam','passage','passage_variant','passage_tag',
    'passage_logic','predicted_item_site','item','item_option','item_check',
    'school_grammar_map','exam_observation'
  ] loop
    execute format('drop policy if exists p_director_all on %I', t);
    execute format(
      'create policy p_director_all on %I for all using (is_director()) with check (is_director())', t);
  end loop;
end $$;

-- 직원(강사·조교): 참조용 마스터는 읽기 가능
do $$
declare t text;
begin
  foreach t in array array[
    'grammar_point','question_type','textbook','school','exam'
  ] loop
    execute format('drop policy if exists p_staff_read on %I', t);
    execute format('create policy p_staff_read on %I for select using (is_staff())', t);
  end loop;
end $$;

-- ★ 핵심: 강사는 승인 문항만 조회. 미승인 행은 존재 자체가 안 보인다.
drop policy if exists p_staff_item_approved on item;
create policy p_staff_item_approved on item
  for select using (is_staff() and status = 'approved');

drop policy if exists p_staff_option_approved on item_option;
create policy p_staff_option_approved on item_option
  for select using (
    is_staff() and exists (
      select 1 from item i where i.id = item_option.item_id and i.status = 'approved'
    )
  );

-- 승인 문항이 딸린 지문만
drop policy if exists p_staff_passage_approved on passage;
create policy p_staff_passage_approved on passage
  for select using (
    is_staff() and exists (
      select 1 from item i where i.passage_id = passage.id and i.status = 'approved'
    )
  );

-- 강사는 문항을 만들 수도 고칠 수도 없다.
-- (insert/update/delete 정책을 아예 만들지 않음 = 거부)
-- 신고는 4단계에서 별도 테이블로.

-- ===================================================================
--  끝. 다음: 002_seed_stage0.sql 로 0단계 JSON을 인제스트.
-- ===================================================================
