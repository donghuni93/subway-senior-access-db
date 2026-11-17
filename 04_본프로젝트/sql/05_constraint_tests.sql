-- 제약조건 위반 테스트: 아래 INSERT는 모두 거부되어야 한다(ERROR가 나와야 정상).
-- 실행: mysql --login-path=endb --force subway_access_db < sql/05_constraint_tests.sql
-- 성공한 문장이 있어도 마지막 ROLLBACK으로 되돌린다.
USE subway_access_db;
START TRANSACTION;

-- T1 FK: 없는 역번호의 승하차
INSERT INTO ridership (station_no, ride_date, hour_slot, board_all, alight_all, board_senior, alight_senior)
VALUES (9999, '2025-01-01', 10, 10, 10, 1, 1);

-- T2 PK: 이미 있는 (역, 일자, 시간대) 중복
INSERT INTO ridership (station_no, ride_date, hour_slot, board_all, alight_all, board_senior, alight_senior)
VALUES (150, '2025-01-01', 10, 10, 10, 1, 1);

-- T3 CHECK: 노인 승차가 전체 승차보다 많음
INSERT INTO ridership (station_no, ride_date, hour_slot, board_all, alight_all, board_senior, alight_senior)
VALUES (150, '2026-01-01', 10, 10, 10, 50, 1);

-- T4 CHECK: 시간대 범위 밖(25)
INSERT INTO ridership (station_no, ride_date, hour_slot, board_all, alight_all, board_senior, alight_senior)
VALUES (150, '2026-01-01', 25, 10, 10, 1, 1);

-- T5 UNSIGNED: 음수 인원
INSERT INTO ridership (station_no, ride_date, hour_slot, board_all, alight_all, board_senior, alight_senior)
VALUES (150, '2026-01-02', 10, -1, 10, 0, 0);

-- T6 CHECK: 비가동 종료가 시작보다 이름
INSERT INTO outage (elevator_no, seq, status, start_at, end_at)
VALUES (1, 999, '보수중', '2026-11-17 10:00:00', '2026-11-17 09:00:00');

-- T7 CHECK: 승강기 종류는 EV·ES만
INSERT INTO elevator (station_no, kind, elevator_nm) VALUES (150, 'WL', '테스트 휠체어리프트');

-- T8 UNIQUE: 같은 역에 같은 이름의 승강기
INSERT INTO elevator (station_no, kind, elevator_nm)
SELECT station_no, kind, elevator_nm FROM elevator WHERE elevator_no = 1;

-- T9 CHECK: 출입구 폐쇄 종료일이 시작일보다 이름
INSERT INTO exit_closure (station_no, place, start_date, end_date, first_seen_at, last_seen_at)
VALUES (150, '테스트 출입구', '2026-12-01', '2026-11-01', NOW(), NOW());

-- T10 FK: 역사(complex)가 없는 역
INSERT INTO station (station_no, line_no, station_nm, complex_id) VALUES (9998, 1, '테스트역', 9998);

-- T11 CHECK: 노선 번호 범위 밖(9호선)
INSERT INTO line (line_no, line_nm) VALUES (9, '9호선');

-- T12 FK + CASCADE 확인용: 부모(역) 삭제는 자식(승하차)이 있으면 거부
DELETE FROM station WHERE station_no = 150;

-- T13 CHECK: 시작 시각 확실성은 0 또는 1
INSERT INTO outage (elevator_no, seq, status, start_at, start_known)
VALUES (1, 998, '보수중', '2026-11-17 10:00:00', 2);

-- T14 FK: 군집 이름(cluster_type)이 없는 (회차, 군집 번호)의 결과
INSERT INTO cluster_result (run_id, complex_id, cluster_no) VALUES (9999, 150, 1);

ROLLBACK;
SELECT 'done' AS constraint_tests;
