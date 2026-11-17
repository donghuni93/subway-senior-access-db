-- 대시보드·분석이 공통으로 쓰는 뷰
-- 실행: mysql --login-path=endb subway_access_db < sql/04_views.sql  (다시 실행해도 됨)
USE subway_access_db;

-- 수집 기간: 승강기 가동현황 스냅샷의 처음·마지막 수집 시각
CREATE OR REPLACE VIEW v_collect_period AS
SELECT MIN(run_at) AS first_at, MAX(run_at) AS last_at, COUNT(*) AS n_snapshots
FROM load_log
WHERE source = 'elevator_status' AND result = 'ok';

-- 수집 공백: 승강기 가동현황 스냅샷 간격이 70분을 넘는 구간(PC 꺼짐 등). 이 구간의 상태 변화는 관측되지 않았다
-- 70분은 src/preprocess.py의 GAP_MINUTES와 같은 값이어야 한다(공백 직후 시작한 비가동 구간은 start_known = 0).
CREATE OR REPLACE VIEW v_collect_gap AS
SELECT prev_at, run_at, TIMESTAMPDIFF(MINUTE, prev_at, run_at) AS gap_min
FROM (
    SELECT run_at, LAG(run_at) OVER (ORDER BY run_at) AS prev_at
    FROM load_log WHERE source = 'elevator_status' AND result = 'ok'
) t
WHERE TIMESTAMPDIFF(MINUTE, prev_at, run_at) > 70;

-- 역 + 역사 + 노선
CREATE OR REPLACE VIEW v_station AS
SELECT s.station_no, s.station_nm, s.line_no, l.line_nm, s.complex_id, c.complex_nm,
       s.fr_code, s.lat, s.lng, s.platform_type, s.floors, s.built_year, s.depth_m
FROM station s
JOIN line l USING (line_no)
JOIN station_complex c USING (complex_id);

-- 승강기 현재 상태: 마지막 수집 시각에 비가동 구간이 열려 있으면(end_at IS NULL) 비가동
CREATE OR REPLACE VIEW v_elevator_now AS
SELECT e.elevator_no, e.kind, e.elevator_nm, e.location, e.section,
       v.station_no, v.station_nm, v.line_no, v.complex_id, v.complex_nm,
       o.status AS down_status, o.start_at AS down_since,
       IF(o.elevator_no IS NULL, '사용가능', o.status) AS status_now,
       ROUND(TIMESTAMPDIFF(MINUTE, o.start_at, p.last_at) / 60, 1) AS down_hours,
       o.start_known AS down_start_known  -- 0이면 down_since는 비가동을 처음 확인한 시각이고 실제 시작은 더 이르다
FROM elevator e
JOIN v_station v USING (station_no)
CROSS JOIN v_collect_period p
LEFT JOIN outage o ON o.elevator_no = e.elevator_no AND o.end_at IS NULL;

-- 비가동 구간별 지속 시간(진행 중이면 마지막 수집 시각까지). 매시 수집이라 1시간 단위 근사치
-- start_known = 0: 첫 관측에 이미 비가동이었거나 수집 공백·응답 누락 직후 비가동이 처음 보여 실제 시작을 모름
--                  (hours는 하한값). 통계에서는 제외한다.
-- gap_overlap = 1: 구간 안이나 시작·종료 직전에 수집 공백(v_collect_gap)이 있어 시각이 공백 길이만큼 부정확할 수 있음
CREATE OR REPLACE VIEW v_outage AS
SELECT o.elevator_no, o.seq, o.status, o.start_at, o.end_at,
       e.kind, e.elevator_nm, e.location, v.station_no, v.station_nm, v.line_no, v.complex_id, v.complex_nm,
       ROUND(TIMESTAMPDIFF(MINUTE, o.start_at, COALESCE(o.end_at, p.last_at)) / 60, 1) AS hours,
       o.end_at IS NULL AS ongoing,
       o.start_known,
       EXISTS (SELECT 1 FROM v_collect_gap g
               WHERE g.run_at >= o.start_at AND g.prev_at < COALESCE(o.end_at, p.last_at)) AS gap_overlap
FROM outage o
JOIN elevator e USING (elevator_no)
JOIN v_station v USING (station_no)
CROSS JOIN v_collect_period p;

-- 역사별 비가동 통계(질문 2). n_outage·outage_hours와 _ev 지표는 시작 시각을 아는 구간(start_known = 1)만 센다.
-- n_down_now는 현재 상태이므로 시작 시각과 관계없이 진행 중인 구간을 모두 센다.
CREATE OR REPLACE VIEW v_complex_outage AS
SELECT c.complex_id, c.complex_nm,
       COUNT(DISTINCT e.elevator_no)                         AS n_elevator,
       COUNT(DISTINCT IF(e.kind = 'EV', e.elevator_no, NULL)) AS n_ev,
       COUNT(DISTINCT IF(e.kind = 'ES', e.elevator_no, NULL)) AS n_es,
       COUNT(IF(o.start_known = 1, o.elevator_no, NULL))      AS n_outage,
       COALESCE(SUM(IF(o.start_known = 1, o.hours, 0)), 0)   AS outage_hours,
       COALESCE(SUM(o.ongoing), 0)                           AS n_down_now,
       COUNT(IF(o.start_known = 0, o.elevator_no, NULL))      AS n_outage_unknown_start,
       COUNT(IF(o.start_known = 1 AND e.kind = 'EV', o.elevator_no, NULL))    AS n_outage_ev,
       COALESCE(SUM(IF(o.start_known = 1 AND e.kind = 'EV', o.hours, 0)), 0) AS outage_hours_ev
FROM station_complex c
JOIN station s USING (complex_id)
LEFT JOIN elevator e ON e.station_no = s.station_no
LEFT JOIN v_outage o ON o.elevator_no = e.elevator_no
GROUP BY c.complex_id, c.complex_nm;

-- 역사별 고령 수요(질문 1·3): 하루 평균(시간대 합), 노인 비중, 오전 9~16시 노인 집중도
CREATE OR REPLACE VIEW v_complex_demand AS
SELECT complex_id,
       SUM(IF(day_type = '평일', avg_senior, 0))                                AS senior_weekday,
       SUM(IF(day_type = '평일', avg_all, 0))                                   AS all_weekday,
       SUM(IF(day_type = '주말', avg_senior, 0))                                AS senior_weekend,
       ROUND(100 * SUM(avg_senior) / NULLIF(SUM(avg_all), 0), 1)                 AS senior_pct,
       MIN(n_days)                                                             AS min_days
FROM ridership_profile
GROUP BY complex_id;

-- 역사별 분석 지표(질문 3 군집 입력)
CREATE OR REPLACE VIEW v_complex_features AS
SELECT c.complex_id, c.complex_nm,
       COUNT(DISTINCT s.line_no)                       AS n_lines,
       MAX(ABS(s.depth_m))                             AS vertical_m,
       MAX(s.depth_m < 0)                              AS elevated,
       AVG(s.lat) AS lat, AVG(s.lng) AS lng,
       d.senior_weekday, d.all_weekday, d.senior_pct, d.min_days,
       (SELECT MAX(t.transfer_sec) FROM transfer t JOIN station s2 USING (station_no)
         WHERE s2.complex_id = c.complex_id)          AS max_transfer_sec,
       o.n_elevator, o.n_ev, o.n_es, o.n_outage, o.outage_hours, o.n_down_now,
       ROUND(o.outage_hours / NULLIF(o.n_elevator, 0), 2) AS outage_hours_per_elevator,
       o.n_outage_unknown_start, o.n_outage_ev, o.outage_hours_ev,
       ROUND(o.outage_hours_ev / NULLIF(o.n_ev, 0), 2) AS outage_hours_per_ev
FROM station_complex c
JOIN station s USING (complex_id)
LEFT JOIN v_complex_demand d USING (complex_id)
LEFT JOIN v_complex_outage o USING (complex_id)
GROUP BY c.complex_id, c.complex_nm, d.senior_weekday, d.all_weekday, d.senior_pct, d.min_days,
         o.n_elevator, o.n_ev, o.n_es, o.n_outage, o.outage_hours, o.n_down_now,
         o.n_outage_unknown_start, o.n_outage_ev, o.outage_hours_ev;

-- 현재 게시 중인 출입구 폐쇄(마지막 출입구 수집에서도 관측되었고 종료일이 지나지 않은 건)
CREATE OR REPLACE VIEW v_closure_now AS
SELECT x.closure_id, v.station_no, v.station_nm, v.line_no, v.complex_id, v.complex_nm,
       x.place, x.start_date, x.end_date, x.reason, x.detour
FROM exit_closure x
JOIN v_station v USING (station_no)
WHERE x.last_seen_at = (SELECT MAX(run_at) FROM load_log WHERE source = 'exit_closure' AND result = 'ok')
  AND (x.end_date IS NULL OR x.end_date >= CURDATE());

-- 최신 군집 분석 결과 (군집 이름은 cluster_type에서 조인)
CREATE OR REPLACE VIEW v_cluster_latest AS
SELECT r.run_id, r.complex_id, c.complex_nm, r.cluster_no, t.cluster_nm, r.priority_rank, r.priority_score
FROM cluster_result r
JOIN cluster_type t USING (run_id, cluster_no)
JOIN station_complex c USING (complex_id)
WHERE r.run_id = (SELECT MAX(run_id) FROM cluster_run);
