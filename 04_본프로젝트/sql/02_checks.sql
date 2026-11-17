-- 적재 후 무결성 점검. 1~6절은 모든 bad 값이 0이어야 정상이다.
-- 7절 '참고'는 점검이 아니라 현황 출력이며 0행이 아닐 수 있다(sql/04_views.sql의 뷰를 쓴다).
-- 실행 순서: 01_schema.sql → load_db.py → 04_views.sql → analysis.py → 이 파일
-- 실행: mysql --login-path=endb subway_access_db < sql/02_checks.sql
USE subway_access_db;

-- 1. 행 수: 비어 있으면 bad = 1. cluster_*는 analysis.py를 실행한 뒤 채워진다.
--    outage·exit_closure는 실제로 0건일 수 있어 판정하지 않는다(bad = 0 고정).
SELECT 'line' AS tbl, COUNT(*) AS n, COUNT(*) = 0 AS bad FROM line
UNION ALL SELECT 'station_complex', COUNT(*), COUNT(*) = 0 FROM station_complex
UNION ALL SELECT 'station', COUNT(*), COUNT(*) = 0 FROM station
UNION ALL SELECT 'transfer', COUNT(*), COUNT(*) = 0 FROM transfer
UNION ALL SELECT 'elevator', COUNT(*), COUNT(*) = 0 FROM elevator
UNION ALL SELECT 'ridership', COUNT(*), COUNT(*) = 0 FROM ridership
UNION ALL SELECT 'ridership_profile', COUNT(*), COUNT(*) = 0 FROM ridership_profile
UNION ALL SELECT 'cluster_run', COUNT(*), COUNT(*) = 0 FROM cluster_run
UNION ALL SELECT 'cluster_type', COUNT(*), COUNT(*) = 0 FROM cluster_type
UNION ALL SELECT 'cluster_result', COUNT(*), COUNT(*) = 0 FROM cluster_result
UNION ALL SELECT 'load_log', COUNT(*), COUNT(*) = 0 FROM load_log
UNION ALL SELECT 'outage', COUNT(*), 0 FROM outage
UNION ALL SELECT 'exit_closure', COUNT(*), 0 FROM exit_closure;

-- 2. 고아 행 (FK가 있으므로 0이어야 함, FK를 끈 채 적재한 경우를 대비한 확인)과 역사 묶음
SELECT 'ridership_orphan' AS chk, COUNT(*) AS bad FROM ridership r LEFT JOIN station s USING (station_no) WHERE s.station_no IS NULL
UNION ALL SELECT 'elevator_orphan', COUNT(*) FROM elevator e LEFT JOIN station s USING (station_no) WHERE s.station_no IS NULL
UNION ALL SELECT 'outage_orphan', COUNT(*) FROM outage o LEFT JOIN elevator e USING (elevator_no) WHERE e.elevator_no IS NULL
UNION ALL SELECT 'cluster_result_orphan', COUNT(*) FROM cluster_result r LEFT JOIN cluster_type t USING (run_id, cluster_no)
          WHERE t.run_id IS NULL
UNION ALL SELECT 'complex_without_station', COUNT(*) FROM station_complex c
          WHERE NOT EXISTS (SELECT 1 FROM station s WHERE s.complex_id = c.complex_id);

-- 3. 값 범위와 비가동 구간
SELECT 'senior_gt_all' AS chk, COUNT(*) AS bad FROM ridership WHERE board_senior > board_all OR alight_senior > alight_all
UNION ALL SELECT 'outage_bad_period', COUNT(*) FROM outage WHERE end_at IS NOT NULL AND end_at <= start_at
UNION ALL SELECT 'closure_bad_period', COUNT(*) FROM exit_closure WHERE end_date < start_date
UNION ALL SELECT 'outage_two_open', COUNT(*) FROM (
    SELECT elevator_no FROM outage WHERE end_at IS NULL GROUP BY elevator_no HAVING COUNT(*) > 1) t
-- 같은 승강기의 두 구간이 겹침 ([start_at, end_at), 진행 중이면 끝이 없음)
UNION ALL SELECT 'outage_overlap', COUNT(*) FROM outage a
          JOIN outage b ON b.elevator_no = a.elevator_no AND b.seq > a.seq
          WHERE b.start_at < COALESCE(a.end_at, '9999-12-31') AND a.start_at < COALESCE(b.end_at, '9999-12-31')
-- 시작을 모르는 구간은 승강기의 첫 구간(seq = 1)이거나 수집 공백 직후(gap_overlap = 1)일 때만 생길 수 있다
-- (규칙: src/preprocess.py outage_intervals, 공백 기준 70분 = GAP_MINUTES = v_collect_gap)
UNION ALL SELECT 'outage_unknown_not_first', COUNT(*) FROM v_outage WHERE start_known = 0 AND seq <> 1 AND gap_overlap = 0;

-- 4. 승하차 완전성: 자료가 있는 역·일자마다 모든 시간대가 있어야 한다.
--    시간대 수는 적재된 값에서 구한다(원천에 따라 1년이 안 되는 역이 있어 일수는 7절에서 따로 본다).
SELECT 'ridership_day_incomplete' AS chk, COUNT(*) AS bad FROM (
    SELECT station_no, ride_date FROM ridership GROUP BY station_no, ride_date
    HAVING COUNT(*) <> (SELECT COUNT(DISTINCT hour_slot) FROM ridership)) t;

-- 5. 집계 테이블(RIDERSHIP_PROFILE)과 원본의 일치
--    5-1 역사별 합계: 평균 × 날 수의 합이 원본 승하차 합과 같아야 한다.
--        평균은 소수 첫째 자리로 반올림되므로 행마다 0.05 × n_days까지의 오차를 허용한다.
--        원본에는 있는데 PROFILE에 없는 역사도 불일치로 센다.
SELECT 'profile_sum_mismatch' AS chk, COUNT(*) AS bad
FROM (
    SELECT s.complex_id,
           SUM(COALESCE(r.board_all, 0) + COALESCE(r.alight_all, 0))       AS raw_all,
           SUM(COALESCE(r.board_senior, 0) + COALESCE(r.alight_senior, 0)) AS raw_senior
    FROM ridership r JOIN station s USING (station_no)
    GROUP BY s.complex_id
) w
LEFT JOIN (
    SELECT complex_id, SUM(avg_all * n_days) AS p_all, SUM(avg_senior * n_days) AS p_senior,
           SUM(n_days) * 0.05 + 1 AS tol
    FROM ridership_profile GROUP BY complex_id
) p USING (complex_id)
WHERE p.complex_id IS NULL OR ABS(p.p_all - w.raw_all) > p.tol OR ABS(p.p_senior - w.raw_senior) > p.tol
--    5-2 n_days 일관성(의도한 비정규화, design/04_정규화.md 6.1절):
--        같은 (역사, 요일구분) 안에서 시간대마다 n_days가 같아야 하고,
UNION ALL SELECT 'profile_n_days_varies', COUNT(*) FROM (
    SELECT complex_id, day_type FROM ridership_profile GROUP BY complex_id, day_type
    HAVING MIN(n_days) <> MAX(n_days)) t
--        평일 n_days + 주말 n_days = 원본에서 그 역사의 자료가 있는 날 수여야 한다.
UNION ALL SELECT 'profile_n_days_total', COUNT(*)
FROM (
    SELECT complex_id, SUM(n_days) AS n
    FROM (SELECT DISTINCT complex_id, day_type, n_days FROM ridership_profile) x
    GROUP BY complex_id
) p
JOIN (
    SELECT s.complex_id, COUNT(DISTINCT r.ride_date) AS n
    FROM ridership r JOIN station s USING (station_no)
    GROUP BY s.complex_id
) w USING (complex_id)
WHERE p.n <> w.n;

-- 6. 분석 회차와 결과
SELECT 'cluster_result_count' AS chk, COUNT(*) AS bad FROM cluster_run u  -- 회차별 결과 행 수가 1 ~ 역사 수
WHERE (SELECT COUNT(*) FROM cluster_result r WHERE r.run_id = u.run_id)
      NOT BETWEEN 1 AND (SELECT COUNT(*) FROM station_complex)
UNION ALL SELECT 'cluster_type_vs_k', COUNT(*) FROM cluster_run u      -- 군집 이름 수 = k
WHERE u.k <> (SELECT COUNT(*) FROM cluster_type t WHERE t.run_id = u.run_id)
UNION ALL SELECT 'cluster_type_empty', COUNT(*) FROM cluster_type t     -- 역사가 하나도 없는 군집
WHERE NOT EXISTS (SELECT 1 FROM cluster_result r WHERE r.run_id = t.run_id AND r.cluster_no = t.cluster_no);

-- 7. 참고 (점검 아님, 0행이 아닐 수 있음)
-- 7-1 자료가 가장 많은 역보다 일수가 적은 역(원천 자체가 일부 기간만 제공: 2026-11-17 기준 321, 2615, 2649, 2753, 2758)
SELECT station_no, COUNT(DISTINCT ride_date) AS n_days
FROM ridership GROUP BY station_no
HAVING COUNT(DISTINCT ride_date) < (SELECT MAX(n) FROM (
    SELECT COUNT(DISTINCT ride_date) AS n FROM ridership GROUP BY station_no) m);

-- 7-2 승강기가 하나도 없는 역 (321·2538은 같은 역사의 다른 호선 역에 기록됨)
SELECT s.station_no, s.station_nm FROM station s LEFT JOIN elevator e USING (station_no) WHERE e.elevator_no IS NULL;

-- 7-3 수집 공백(승강기 스냅샷 간격 70분 초과). 대시보드는 같은 규칙을 db.collect_gap()으로 조회한다.
SELECT prev_at, run_at, gap_min FROM v_collect_gap ORDER BY run_at;

-- 7-4 비가동 구간의 시작 시각 확실성과 수집 공백 겹침
SELECT start_known, gap_overlap, COUNT(*) AS n, SUM(ongoing) AS n_ongoing
FROM v_outage GROUP BY start_known, gap_overlap ORDER BY start_known, gap_overlap;
