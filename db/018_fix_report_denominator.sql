-- ===================================================================
--  018  report_school_grammar 분모 수정 (2026-10-03)
--
--  ※ Supabase SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전합니다.
--  🔴 DROP / DELETE / TRUNCATE 없음. create or replace view 한 건뿐입니다.
--     컬럼 이름·순서가 014 와 같으므로 기존 grant(anon select)는 그대로 유지됩니다.
--
--  왜: 014 는 분모(exams_observed)를 「이미 치른 시험」으로 셌다. 그런데 2026-2 중간
--  (영일 9/29 · 청명 9/30 · 태장 10/1)은 치렀지만 아직 기출 분석을 넣지 않았다.
--  그래서 check_report_views 에서 영일·청명·태장이 전부 「1/2회」로 나왔다 —
--  리포트에 「두 번 중 한 번 냈다」고 잘못 나갈 뻔했다.
--  분모는 **분석을 끝낸 시험** = `exam_observation` 행이 있는 시험으로 센다.
--  기출을 분석해 적재할 때 exam_observation 을 함께 넣어야 분모가 늘어난다.
-- ===================================================================

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
      and exists (select 1 from exam_observation o where o.exam_id = e2.id))
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
  '리디플랜 학부모 리포트용 (읽기 전용). 한 행 = 학교×학년×어법포인트. 분모 = exam_observation 있는 시험. 018';
