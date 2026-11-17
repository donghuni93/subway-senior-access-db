-- 핵심 질의 (질문 1·2·3, 출입구 안내). 사용자 입력은 @변수로 두었고, 대시보드(src/db.py)는 같은 질의를 매개변수(%s)로 실행한다.
-- 실행: mysql --login-path=endb subway_access_db < sql/03_queries.sql   (뷰는 sql/04_views.sql을 먼저 실행)
-- 한계(시간 불일치): 이용 프로필(ridership_profile, 승하차)은 2025년 자료이고 비가동(outage)은 2026년 11월부터
--   수집한 자료다. 비가동과 노인 이용을 잇는 값(Q2-1, Q2-3의 영향 규모)은 '2025년의 같은 요일구분·시간대 평균이
--   올해도 비슷하다'는 가정 위의 추정치이며 실제 영향 인원이 아니다.
-- 비가동 통계(Q2-2~Q2-6)는 시작 시각을 아는 구간(start_known = 1)만 쓴다(Q2-2는 v_complex_outage에서, Q2-1은 현재 상태라 전부). 매시 수집이라 시간은 1시간 단위 근사치다.
USE subway_access_db;

SET @complex_id = 153;       -- 사용자가 고른 역사(종로3가 153·319·2535 → 153). 역명으로 찾을 때는 v_station에서 complex_id를 먼저 확인한다
SET @day_type   = '평일';      -- 평일 / 주말
SET @hour_slot  = 10;          -- 5=06시 이전, 6~23, 24=24시 이후

-- ───────────── 질문 1. 고령 이용 수요는 어느 역, 어느 시간대에 집중되는가?
-- Q1-1 평일 하루 평균 노인 이용(승차+하차)이 많은 역사 상위 15
SELECT c.complex_nm, d.senior_weekday, d.all_weekday, d.senior_pct
FROM v_complex_demand d JOIN station_complex c USING (complex_id)
WHERE d.min_days >= 100
ORDER BY d.senior_weekday DESC
LIMIT 15;

-- Q1-2 노인 비중이 높은 역사 상위 15 (하루 평균 이동 1만 회 이상)
SELECT c.complex_nm, d.senior_pct, d.senior_weekday, d.all_weekday
FROM v_complex_demand d JOIN station_complex c USING (complex_id)
WHERE d.all_weekday >= 10000
ORDER BY d.senior_pct DESC
LIMIT 15;

-- Q1-3 선택한 역의 시간대별 평균 이용과 노인 비중
SELECT p.day_type, p.hour_slot, p.avg_all, p.avg_senior,
       ROUND(100 * p.avg_senior / NULLIF(p.avg_all, 0), 1) AS senior_pct
FROM ridership_profile p
WHERE p.complex_id = @complex_id
ORDER BY p.day_type, p.hour_slot;

-- Q1-4 전체 역사 합계: 시간대별 노인 비중 (노인 이용이 몰리는 시간대)
SELECT day_type, hour_slot, SUM(avg_senior) AS senior, SUM(avg_all) AS total,
       ROUND(100 * SUM(avg_senior) / SUM(avg_all), 1) AS senior_pct
FROM ridership_profile
GROUP BY day_type, hour_slot
ORDER BY day_type, hour_slot;

-- Q1-5 원본 RIDERSHIP 직접 집계 예(월별 노인 이용 추이, 조인·집계)
SELECT DATE_FORMAT(r.ride_date, '%Y-%m') AS ym,
       SUM(r.board_senior + r.alight_senior) AS senior,
       ROUND(100 * SUM(r.board_senior + r.alight_senior) / SUM(r.board_all + r.alight_all), 1) AS senior_pct
FROM ridership r
GROUP BY ym
ORDER BY ym;

-- Q1-6 피크 시간대 집중도: @day_type 하루 노인 이용(승차+하차) 중 가장 많은 3개 시간대의 비중
--      시간대는 20칸(06시 이전·06~23시·24시 이후)이라 고르게 퍼지면 약 15%. 상위 15곳과 선택한 역사를 함께 보인다
WITH ranked AS (
    SELECT complex_id, hour_slot, avg_senior,
           ROW_NUMBER() OVER (PARTITION BY complex_id ORDER BY avg_senior DESC, hour_slot) AS rn,
           SUM(avg_senior) OVER (PARTITION BY complex_id) AS day_senior
    FROM ridership_profile
    WHERE day_type = @day_type
), conc AS (
    SELECT r.complex_id,
           ROUND(100 * SUM(IF(r.rn <= 3, r.avg_senior, 0)) / NULLIF(MAX(r.day_senior), 0), 1) AS top3_share_pct,
           GROUP_CONCAT(IF(r.rn <= 3, r.hour_slot, NULL) ORDER BY r.rn) AS top3_slots,
           ROUND(MAX(r.day_senior), 0) AS senior_day
    FROM ranked r JOIN v_complex_demand d USING (complex_id)
    WHERE d.min_days >= 100
    GROUP BY r.complex_id
), ranked_conc AS (
    SELECT conc.*, RANK() OVER (ORDER BY top3_share_pct DESC) AS conc_rank FROM conc
)
SELECT x.conc_rank, c.complex_nm, x.top3_share_pct, x.top3_slots, x.senior_day,
       x.complex_id = @complex_id AS selected
FROM ranked_conc x JOIN station_complex c USING (complex_id)
WHERE x.conc_rank <= 15 OR x.complex_id = @complex_id
ORDER BY x.conc_rank;

-- Q1-7 평일/주말 비율: 평일 하루 평균 노인 이용 ÷ 주말(공휴일 포함) 하루 평균 노인 이용
--      1보다 크면 평일에 더 몰리는 역사(통근·통원형), 1에 가까우면 주말 나들이 수요도 큰 역사. 상위 15곳과 선택한 역사
WITH ratio AS (
    SELECT complex_id, senior_weekday, senior_weekend,
           ROUND(senior_weekday / NULLIF(senior_weekend, 0), 2) AS weekday_weekend_ratio
    FROM v_complex_demand
    WHERE min_days >= 100
), ranked_ratio AS (
    SELECT ratio.*, RANK() OVER (ORDER BY weekday_weekend_ratio DESC) AS ratio_rank FROM ratio
)
SELECT x.ratio_rank, c.complex_nm, ROUND(x.senior_weekday, 0) AS senior_weekday,
       ROUND(x.senior_weekend, 0) AS senior_weekend, x.weekday_weekend_ratio,
       x.complex_id = @complex_id AS selected
FROM ranked_ratio x JOIN station_complex c USING (complex_id)
WHERE x.ratio_rank <= 15 OR x.complex_id = @complex_id
ORDER BY x.ratio_rank;

-- ───────────── 질문 2. 승강기 비가동은 어디서 얼마나 자주·오래 일어나며, 영향받을 수 있는 고령 이용객은 몇 명인가?
-- Q2-1 현재 비가동 승강기와 해당 시간대 역사 평균 노인 이용(영향 규모 추정치, 실제 이용 인원이 아님)
SELECT n.complex_nm, n.station_nm, n.kind, n.elevator_nm, n.location, n.down_since, n.down_hours,
       p.avg_senior AS senior_at_hour
FROM v_elevator_now n
LEFT JOIN ridership_profile p
       ON p.complex_id = n.complex_id AND p.day_type = @day_type AND p.hour_slot = @hour_slot
WHERE n.status_now <> '사용가능'
ORDER BY (n.kind = 'EV') DESC, p.avg_senior DESC;

-- Q2-2 역사별 비가동 횟수·누적 시간 (수집 기간 기준)
SELECT complex_nm, n_elevator, n_outage, outage_hours, n_down_now,
       ROUND(outage_hours / NULLIF(n_elevator, 0), 2) AS hours_per_elevator
FROM v_complex_outage
WHERE n_outage > 0
ORDER BY outage_hours DESC
LIMIT 20;

-- Q2-3 비가동 1건마다 영향 규모: 비가동 시간 동안 해당 역사의 시간대별 평균 노인 이용 합
--      (비가동 구간을 시간 단위로 펼치기 위해 재귀 CTE 사용). src/db.py complex_exposure와 같은 규칙:
--      시작 시각을 아는 구간만, 마지막 수집 시각에 막 시작한 길이 0 구간은 제외, 재귀 깊이 한도 10000시간
SET SESSION cte_max_recursion_depth = 10000;
WITH RECURSIVE hrs AS (
    SELECT elevator_no, seq, complex_id, start_at AS h, COALESCE(end_at, (SELECT last_at FROM v_collect_period)) AS until_at
    FROM v_outage
    WHERE start_known = 1 AND start_at < COALESCE(end_at, (SELECT last_at FROM v_collect_period))
    UNION ALL
    SELECT elevator_no, seq, complex_id, h + INTERVAL 1 HOUR, until_at FROM hrs WHERE h + INTERVAL 1 HOUR < until_at
)
SELECT o.complex_nm, o.elevator_nm, o.start_at, o.end_at, o.hours,
       ROUND(SUM(p.avg_senior), 0) AS senior_exposed
FROM hrs
JOIN v_outage o ON o.elevator_no = hrs.elevator_no AND o.seq = hrs.seq
LEFT JOIN ridership_profile p
       ON p.complex_id = hrs.complex_id
      AND p.day_type = IF(DAYOFWEEK(hrs.h) IN (1, 7), '주말', '평일')
      AND p.hour_slot = IF(HOUR(hrs.h) < 6, IF(HOUR(hrs.h) = 0, 24, 5), HOUR(hrs.h))
GROUP BY o.complex_nm, o.elevator_nm, o.start_at, o.end_at, o.hours
ORDER BY senior_exposed DESC
LIMIT 20;

-- Q2-4 비가동 지속 시간의 중앙값과 평균 복구 시간(MTTR), 엘리베이터(EV)·에스컬레이터(ES) 따로
--      끝난 구간(ongoing = 0)만 계산한다. 아직 진행 중인 구간은 끝을 모르므로(우측 절단) n_ongoing으로 따로 보이며,
--      긴 비가동이 진행 중이면 중앙값·MTTR은 실제보다 작게 나온다
WITH closed AS (
    SELECT kind, hours,
           ROW_NUMBER() OVER (PARTITION BY kind ORDER BY hours) AS rn,
           COUNT(*) OVER (PARTITION BY kind) AS n
    FROM v_outage
    WHERE start_known = 1 AND ongoing = 0
), stats AS (
    SELECT kind, MAX(n) AS n_closed,
           AVG(IF(rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2)), hours, NULL)) AS median_hours,
           AVG(hours) AS mttr_hours
    FROM closed
    GROUP BY kind
), still_open AS (
    SELECT kind, COUNT(*) AS n_ongoing
    FROM v_outage
    WHERE start_known = 1 AND ongoing = 1
    GROUP BY kind
)
SELECT k.kind, COALESCE(s.n_closed, 0) AS n_closed, ROUND(s.median_hours, 1) AS median_hours,
       ROUND(s.mttr_hours, 1) AS mttr_hours, COALESCE(o.n_ongoing, 0) AS n_ongoing
FROM (SELECT 'EV' AS kind UNION ALL SELECT 'ES') k
LEFT JOIN stats s USING (kind)
LEFT JOIN still_open o USING (kind);

-- Q2-5 승강기 1대당 주간 비가동 빈도(건/대/주), EV·ES 따로: 시작 시각을 아는 비가동 건수 ÷ 승강기 수 ÷ 수집 주 수
--      수집 기간이 짧으면 한두 건이 크게 부풀려지므로 collect_weeks를 같이 본다
SELECT e.kind, COUNT(DISTINCT e.elevator_no) AS n_elevator, COUNT(o.elevator_no) AS n_outage,
       ROUND(TIMESTAMPDIFF(MINUTE, p.first_at, p.last_at) / 60 / 24 / 7, 3) AS collect_weeks,
       ROUND(COUNT(o.elevator_no) / COUNT(DISTINCT e.elevator_no)
             / NULLIF(TIMESTAMPDIFF(MINUTE, p.first_at, p.last_at) / 60 / 24 / 7, 0), 3) AS outages_per_elevator_week
FROM elevator e
CROSS JOIN v_collect_period p
LEFT JOIN outage o ON o.elevator_no = e.elevator_no AND o.start_known = 1
GROUP BY e.kind, p.first_at, p.last_at
ORDER BY e.kind DESC;

-- Q2-6 역사별 승강기 1대당 주간 비가동 빈도(EV·ES 따로). 비가동이 있었던 역사 상위 20과 선택한 역사
SELECT o.complex_nm, o.n_ev, o.n_outage_ev,
       ROUND(o.n_outage_ev / NULLIF(o.n_ev, 0) / w.weeks, 3) AS ev_per_elevator_week,
       o.n_es, o.n_outage - o.n_outage_ev AS n_outage_es,
       ROUND((o.n_outage - o.n_outage_ev) / NULLIF(o.n_es, 0) / w.weeks, 3) AS es_per_elevator_week,
       o.complex_id = @complex_id AS selected
FROM v_complex_outage o
CROSS JOIN (SELECT NULLIF(TIMESTAMPDIFF(MINUTE, first_at, last_at), 0) / 60 / 24 / 7 AS weeks
            FROM v_collect_period) w
WHERE o.n_outage > 0 OR o.complex_id = @complex_id
ORDER BY selected DESC, ev_per_elevator_week DESC, es_per_elevator_week DESC
LIMIT 21;

-- ───────────── 질문 3. 역 유형과 우선 관리 역 (군집 결과는 src/analysis.py가 CLUSTER_RESULT에 저장)
-- Q3-1 군집별 역사 수와 평균 지표
SELECT r.cluster_no, r.cluster_nm, COUNT(*) AS n_complex,
       ROUND(AVG(f.senior_weekday), 0) AS senior_weekday, ROUND(AVG(f.senior_pct), 1) AS senior_pct,
       ROUND(AVG(f.vertical_m), 1) AS vertical_m, ROUND(AVG(f.outage_hours_per_elevator), 2) AS outage_h_per_elev
FROM v_cluster_latest r JOIN v_complex_features f USING (complex_id)
GROUP BY r.cluster_no, r.cluster_nm
ORDER BY r.cluster_no;

-- Q3-2 우선 관리 역사 상위 15
SELECT r.priority_rank, r.complex_nm, r.cluster_nm, r.priority_score,
       f.senior_weekday, f.vertical_m, f.n_ev, f.outage_hours, f.n_down_now
FROM v_cluster_latest r JOIN v_complex_features f USING (complex_id)
ORDER BY r.priority_rank
LIMIT 15;

-- ───────────── 이동 안내. 선택한 역의 폐쇄 출입구와 대체 경로
SELECT x.station_nm, x.line_no, x.place, x.start_date, x.end_date, x.reason, x.detour
FROM v_closure_now x
WHERE x.complex_id = @complex_id;
