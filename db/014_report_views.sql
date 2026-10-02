-- ===================================================================
--  014  리디플랜 보고서용 읽기 전용 뷰 (2026-10-02 원장 승인 — 1안)
--
--  ※ Supabase 웹 화면 → SQL Editor 에 통째로 붙여넣고 Run 하십시오.
--  ※ 여러 번 실행해도 안전합니다 (create or replace).
--
--  🔴 이 파일에 DROP / DELETE / TRUNCATE 는 없습니다.
--     create or replace view · revoke · grant 만 있습니다. 기존 테이블·행·정책은 건드리지 않습니다.
--
--  1안: 리디플랜은 publishable(anon) 키로 **이 뷰 두 개만** 읽는다.
--       기반 테이블 RLS 는 그대로(anon 은 0행). service_role 키는 리디플랜에 넣지 않는다.
--
--  security_invoker = false 는 의도된 것이다 — 뷰 소유자 권한으로 기반 테이블을 읽는다.
--  true 로 하면 anon 에게 기반 테이블 select 정책을 열어야 하고, 그러면 note 같은
--  내부 컬럼까지 보인다. Supabase 린터가 「security definer view」 경고를 띄우는 것은 정상.
--
--  근거: docs/리디플랜_연동_데이터조사.md §7·§8
-- ===================================================================

-- -------------------------------------------------------------------
-- 1. 학교 × 학년 × 어법 포인트 출제 이력
--    exam_hit_count  : 기출에서 확인된 시험 수
--    exams_observed  : 그 학교·학년의 DB 에 있는 시험 수(분모)
--    둘을 함께 보여야 「1회 중 1회」를 「단골」로 오독하지 않는다.
--    note 는 넣지 않는다 — 내부 판단 메모가 학부모 리포트로 새면 안 된다.
-- -------------------------------------------------------------------
create or replace view report_school_grammar
with (security_invoker = false)
as
select
  s.name                                              as school_name,
  m.grade,
  tb.label                                            as textbook,
  m.grammar_point_code,
  gp.label_ko                                         as grammar_label_ko,
  gp.category                                         as grammar_category,
  gp.is_candidate                                     as grammar_is_candidate,
  count(distinct m.evidence_exam_id)                  as exam_hit_count,
  (select count(*) from exam e2
    where e2.school_id = m.school_id and e2.grade = m.grade
      and e2.exam_date is not null and e2.exam_date <= current_date)
                                                      as exams_observed,
  count(*) filter (where m.evidence_exam_id is null)  as handout_scope_rows,
  min(e.exam_date)                                    as first_hit_exam_date,
  max(e.exam_date)                                    as last_hit_exam_date,
  string_agg(distinct (e.year || '-' || e.semester || ' ' || e.sitting), ', ')
                                                      as hit_exams,
  string_agg(distinct m.textbook_unit, ', ')          as units,
  max(m.updated_at)                                   as updated_at
from school_grammar_map m
join school        s  on s.id    = m.school_id
join grammar_point gp on gp.code = m.grammar_point_code
left join textbook tb on tb.id   = m.textbook_id
left join exam     e  on e.id    = m.evidence_exam_id
group by s.name, m.school_id, m.grade, tb.label,
         m.grammar_point_code, gp.label_ko, gp.category, gp.is_candidate;

comment on view report_school_grammar is
  '리디플랜 학부모 리포트용 (읽기 전용). 한 행 = 학교×학년×어법포인트. 014_report_views.sql';

-- -------------------------------------------------------------------
-- 2. 시험 일정 — exam_date 가 null 이면 날짜 미정 (예: 영덕중2 2026-2 중간 「10월 둘째 주」)
-- -------------------------------------------------------------------
create or replace view report_exam_schedule
with (security_invoker = false)
as
select
  s.name        as school_name,
  e.grade,
  e.year,
  e.semester,
  e.sitting,
  e.exam_date,
  tb.label      as textbook,
  e.mc_count,
  e.essay_count,
  e.total_score
from exam e
join school s on s.id = e.school_id
left join textbook tb on tb.id = e.textbook_id;

comment on view report_exam_schedule is
  '리디플랜 학부모 리포트용 (읽기 전용). exam_date null = 날짜 미정. 014_report_views.sql';

-- -------------------------------------------------------------------
-- 3. 권한 — Supabase 는 public 스키마의 새 객체에 anon·authenticated 권한을
--    기본으로 준다. 먼저 전부 걷고 anon 에 select 만 다시 준다.
-- -------------------------------------------------------------------
revoke all on report_school_grammar, report_exam_schedule from public, anon, authenticated;
grant select on report_school_grammar, report_exam_schedule to anon;

-- 확인: python tools/check_report_views.py  (anon 키로 뷰 2개가 보이고 기반 테이블은 0행인지)
