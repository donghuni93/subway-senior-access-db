-- 고령 이용 수요와 승강기 운영 정보를 통합한 서울 지하철 이용 지원 시스템
-- 물리 스키마 (MySQL 8.0, utf8mb4)
-- 실행: mysql --login-path=endb < sql/01_schema.sql
-- 제안서 표 5의 9개 릴레이션을 실제 API 응답에 맞춰 조정하였다. 변경 이유는 design/03_릴레이션스키마.md 참고.

DROP DATABASE IF EXISTS subway_access_db;
CREATE DATABASE subway_access_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE subway_access_db;

-- ① 노선
CREATE TABLE line (
    line_no   TINYINT UNSIGNED NOT NULL,
    line_nm   VARCHAR(10)      NOT NULL,
    PRIMARY KEY (line_no),
    CONSTRAINT ck_line_no CHECK (line_no BETWEEN 1 AND 8)
);

-- ①-2 역사(驛舍): 같은 건물을 쓰는 호선별 역의 묶음.
--      환승역은 승하차·승강기가 한 호선 코드로만 기록되는 경우가 있어(충무로·청구 등) 분석은 역사 단위로 한다.
CREATE TABLE station_complex (
    complex_id  SMALLINT UNSIGNED NOT NULL COMMENT '묶음 안 가장 작은 역번호',
    complex_nm  VARCHAR(30)       NOT NULL,
    PRIMARY KEY (complex_id)
);

-- ② 역 (호선별 역, 환승역은 호선마다 별도 행)
CREATE TABLE station (
    station_no     SMALLINT UNSIGNED NOT NULL COMMENT '역번호 = 역코드(STN_CD)의 정수값, 예: 서울역 1호선 150(0150), 방화 2511',
    fr_code        VARCHAR(10)       NULL COMMENT '외부코드(안내용 역 번호), 예: 서울역 133, 용답 211-1',
    line_no        TINYINT UNSIGNED  NOT NULL,
    station_nm     VARCHAR(30)       NOT NULL,
    lat            DECIMAL(9,6)      NULL,
    lng            DECIMAL(9,6)      NULL,
    platform_type  VARCHAR(10)       NULL COMMENT '승강장 형식(섬식·상대식 등)',
    floors         VARCHAR(10)       NULL COMMENT '역사 층수(예: B2)',
    built_year     SMALLINT UNSIGNED NULL,
    depth_m        DECIMAL(5,2)      NULL COMMENT '정거장 깊이(m). 음수 = 지상보다 높은 고가역(예: 뚝섬 -19.07). 수직 이동 부담은 ABS로 본다',
    complex_id     SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (station_no),
    UNIQUE KEY uk_station_fr_code (fr_code),
    KEY ix_station_line (line_no),
    KEY ix_station_complex (complex_id),
    CONSTRAINT fk_station_line FOREIGN KEY (line_no) REFERENCES line (line_no),
    CONSTRAINT fk_station_complex FOREIGN KEY (complex_id) REFERENCES station_complex (complex_id),
    CONSTRAINT ck_station_depth CHECK (depth_m IS NULL OR depth_m BETWEEN -50 AND 100)
);

-- ③ 환승 (환승 대상에 다른 운영기관 노선이 섞여 있어 대상은 노선명으로 둔다)
CREATE TABLE transfer (
    station_no    SMALLINT UNSIGNED NOT NULL,
    to_line       VARCHAR(20)       NOT NULL COMMENT '환승 노선(예: 4호선, 공항철도)',
    distance_m    SMALLINT UNSIGNED NULL,
    transfer_sec  SMALLINT UNSIGNED NULL,
    PRIMARY KEY (station_no, to_line),
    CONSTRAINT fk_transfer_station FOREIGN KEY (station_no) REFERENCES station (station_no)
);

-- ④ 승강기 (엘리베이터·에스컬레이터)
CREATE TABLE elevator (
    elevator_no  INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    station_no   SMALLINT UNSIGNED NOT NULL,
    kind         CHAR(2)           NOT NULL COMMENT 'EV 엘리베이터, ES 에스컬레이터',
    elevator_nm  VARCHAR(100)      NOT NULL COMMENT 'API 승강기명 (역 안에서 유일)',
    location     VARCHAR(100)      NULL COMMENT '설치 위치',
    section      VARCHAR(20)       NULL COMMENT '운행 구간(예: B1-1F)',
    fclt_no      VARCHAR(10)       NULL COMMENT 'OA-22740 시설번호 (엘리베이터만)',
    PRIMARY KEY (elevator_no),
    UNIQUE KEY uk_elevator_name (station_no, elevator_nm),
    UNIQUE KEY uk_elevator_fclt (fclt_no),
    CONSTRAINT fk_elevator_station FOREIGN KEY (station_no) REFERENCES station (station_no),
    CONSTRAINT ck_elevator_kind CHECK (kind IN ('EV', 'ES'))
);

-- ⑤ 승강기 비가동 이력 (약한 개체: 승강기별 순번)
CREATE TABLE outage (
    elevator_no  INT UNSIGNED     NOT NULL,
    seq          SMALLINT UNSIGNED NOT NULL,
    status       VARCHAR(10)      NOT NULL COMMENT 'API 운행상태 값(예: 보수중)',
    start_at     DATETIME         NOT NULL COMMENT '비가동이 처음 관측된 수집 시각',
    end_at       DATETIME         NULL COMMENT '가동이 다시 관측된 수집 시각, 진행 중이면 NULL',
    start_known  TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1 = 가동 관측 뒤 시작, 0 = 첫 관측에 이미 비가동(실제 시작 모름, 통계 제외)',
    PRIMARY KEY (elevator_no, seq),
    KEY ix_outage_open (end_at),
    CONSTRAINT fk_outage_elevator FOREIGN KEY (elevator_no) REFERENCES elevator (elevator_no) ON DELETE CASCADE,
    CONSTRAINT ck_outage_period CHECK (end_at IS NULL OR end_at > start_at),
    CONSTRAINT ck_outage_start_known CHECK (start_known IN (0, 1))
);

-- ⑥ 승하차 (역·일자·시간대, 전체와 노인)
CREATE TABLE ridership (
    station_no     SMALLINT UNSIGNED NOT NULL,
    ride_date      DATE              NOT NULL,
    hour_slot      TINYINT UNSIGNED  NOT NULL COMMENT '5=06시 이전, 6~23=해당 시각부터 1시간, 24=24시 이후',
    board_all      INT UNSIGNED      NULL,
    alight_all     INT UNSIGNED      NULL,
    board_senior   INT UNSIGNED      NULL,
    alight_senior  INT UNSIGNED      NULL,
    PRIMARY KEY (station_no, ride_date, hour_slot),
    KEY ix_ridership_date (ride_date),
    CONSTRAINT fk_ridership_station FOREIGN KEY (station_no) REFERENCES station (station_no),
    CONSTRAINT ck_ridership_slot CHECK (hour_slot BETWEEN 5 AND 24),
    CONSTRAINT ck_ridership_senior CHECK (
        board_senior IS NULL OR board_all IS NULL OR board_senior <= board_all)
);

-- ⑦ 출입구 임시폐쇄
CREATE TABLE exit_closure (
    closure_id     INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    station_no     SMALLINT UNSIGNED NOT NULL,
    place          VARCHAR(100)      NOT NULL,
    start_date     DATE              NOT NULL,
    end_date       DATE              NULL,
    reason         VARCHAR(100)      NULL,
    detour         VARCHAR(100)      NOT NULL DEFAULT '',
    first_seen_at  DATETIME          NOT NULL COMMENT 'API에서 처음 관측한 수집 시각',
    last_seen_at   DATETIME          NOT NULL COMMENT 'API에서 마지막으로 관측한 수집 시각',
    PRIMARY KEY (closure_id),
    UNIQUE KEY uk_closure (station_no, place, start_date, detour),
    CONSTRAINT fk_closure_station FOREIGN KEY (station_no) REFERENCES station (station_no),
    CONSTRAINT ck_closure_period CHECK (end_date IS NULL OR end_date >= start_date)
);

-- ⑧ 분석 회차와 결과 (군집 분석, 역사 단위)
CREATE TABLE cluster_run (
    run_id       SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_at       DATETIME          NOT NULL,
    k            TINYINT UNSIGNED  NOT NULL COMMENT '군집 수',
    features     VARCHAR(300)      NOT NULL COMMENT '입력 지표 목록',
    silhouette   DECIMAL(5,4)      NULL,
    data_until   DATETIME          NULL COMMENT '사용한 승강기 수집 자료의 마지막 시각',
    PRIMARY KEY (run_id)
);

-- 회차별 군집 이름: cluster_nm은 (run_id, cluster_no)에 종속하므로 결과와 분리한다(3NF)
CREATE TABLE cluster_type (
    run_id        SMALLINT UNSIGNED NOT NULL,
    cluster_no    TINYINT UNSIGNED  NOT NULL,
    cluster_nm    VARCHAR(40)       NOT NULL COMMENT '군집 해석 이름',
    PRIMARY KEY (run_id, cluster_no),
    CONSTRAINT fk_cluster_run FOREIGN KEY (run_id) REFERENCES cluster_run (run_id) ON DELETE CASCADE
);

CREATE TABLE cluster_result (
    run_id        SMALLINT UNSIGNED NOT NULL,
    complex_id    SMALLINT UNSIGNED NOT NULL,
    cluster_no    TINYINT UNSIGNED  NOT NULL,
    priority_rank SMALLINT UNSIGNED NULL COMMENT '우선 관리 순위(1이 가장 높음)',
    priority_score DECIMAL(6,3)     NULL,
    PRIMARY KEY (run_id, complex_id),
    KEY ix_cluster_type (run_id, cluster_no),
    CONSTRAINT fk_cluster_type FOREIGN KEY (run_id, cluster_no) REFERENCES cluster_type (run_id, cluster_no)
        ON DELETE CASCADE,
    CONSTRAINT fk_cluster_complex FOREIGN KEY (complex_id) REFERENCES station_complex (complex_id)
);

-- 집계 테이블(물리 설계상 성능용 파생 데이터): 역사 × 요일구분 × 시간대 평균 이용객.
-- RIDERSHIP 200만 행을 대시보드가 매번 집계하지 않도록 적재 후 한 번 계산해 둔다(src/load_db.py가 다시 계산).
CREATE TABLE ridership_profile (
    complex_id     SMALLINT UNSIGNED NOT NULL,
    day_type       CHAR(2)           NOT NULL COMMENT '평일 또는 주말',
    hour_slot      TINYINT UNSIGNED  NOT NULL,
    avg_all        DECIMAL(9,1)      NULL COMMENT '하루 평균 승차+하차',
    avg_senior     DECIMAL(9,1)      NULL COMMENT '하루 평균 노인 승차+하차',
    n_days         SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (complex_id, day_type, hour_slot),
    CONSTRAINT fk_profile_complex FOREIGN KEY (complex_id) REFERENCES station_complex (complex_id),
    CONSTRAINT ck_profile_day CHECK (day_type IN ('평일', '주말'))
);

-- ⑨ 적재 기록 (수집 스냅샷 1개 = 1행, 파일 적재 1회 = 1행)
CREATE TABLE load_log (
    load_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    source     VARCHAR(30)  NOT NULL,
    run_at     DATETIME     NOT NULL COMMENT '수집 시각(스냅샷) 또는 적재 실행 시각',
    row_cnt    INT UNSIGNED NOT NULL DEFAULT 0,
    result     VARCHAR(10)  NOT NULL,
    message    VARCHAR(300) NULL,
    PRIMARY KEY (load_id),
    UNIQUE KEY uk_load (source, run_at),
    CONSTRAINT ck_load_result CHECK (result IN ('ok', 'error', 'skip'))
);
