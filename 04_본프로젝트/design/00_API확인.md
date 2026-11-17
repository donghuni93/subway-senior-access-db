# API 확인 결과 (2026-11-17 01시 실제 호출)

수집기: `src/collect.py`, 원본: `data/snapshots/{source}/YYYYMMDD_HHMM.json.gz`, 수집 기록: `data/snapshots/collect_log.csv`

## 1. 수집 대상 3종

| source | 데이터셋 | 서비스명 | 건수 | 응답 형식 |
|---|---|---|---|---|
| elevator_status | OA-15994 교통약자 이용시설 승강기 가동현황 | `SeoulMetroFaciInfo` | 2,809 | 서울 열린데이터 형식 (`{서비스명: {list_total_count, RESULT, row}}`) |
| elevator_ev | OA-22740 교통약자이용정보 엘리베이터 현황 | `getWksnElvtr` | 871 | 공공데이터포털 형식 (`{response: {header, body: {items: {item}, totalCount}}}`) |
| exit_closure | OA-22122 출입구 임시폐쇄 공사현황 | `TbSubwayLineDetail` | 8 | 서울 열린데이터 형식 |

세 소스 모두 매시 정각에 수집한다. 출입구 폐쇄는 제안서에서 "매일"로 계획했으나 8건뿐이어서 같은 작업에서 함께 받는다. 하루 1회 값이 필요하면 적재 단계에서 하루의 첫 스냅샷만 쓰면 된다.

## 2. OA-15994 `SeoulMetroFaciInfo` (승강기 전체)

필드: `STN_CD`(역코드 4자리), `STN_NM`(역명, 환승역은 "서울역(1)"처럼 호선 표기), `ELVTR_NM`(승강기명), `OPR_SEC`(운행구간, 예: B1-1F), `INSTL_PSTN`(설치위치), `USE_YN`(운행상태), `ELVTR_SE`(종류)

- 종류: ES 에스컬레이터 1,884 / EV 엘리베이터 866 / WL 휠체어리프트 41 / MW 무빙워크 18. 제안서 범위(엘리베이터·에스컬레이터)에 맞춰 WL·MW는 적재 시 제외한다.
- 운행상태 값: `사용가능` 2,733 / `보수중` 76 (11/17 01시 기준)
- 역: 274개 `STN_CD`
- **승강기 ID 필드가 없다.** (`STN_CD`, `ELVTR_NM`) 조합이 2,809건에서 중복 없이 유일하므로 이것을 자연키로 쓴다. ELEVATOR 테이블에는 대리키 `elevator_no`를 두고 이 조합에 UNIQUE를 건다. 승강기명이 바뀌면 다른 승강기로 보이는 위험이 있어, 수집 기간 중 이름 변경 여부를 적재 단계에서 점검한다.
- 비가동 판단: `USE_YN = '보수중'`. 보수중이 고장인지 계획 점검인지는 이 API로 구분할 수 없다.

## 3. OA-22740 `getWksnElvtr` (엘리베이터만)

필드: `fcltNo`(시설번호), `fcltNm`, `lineNm`(호선), `stnCd`(역코드), `stnNm`, `stnNo`(역번호), `crtrYmd`(기준일자), `mngNo`, `vcntEntrcNo`(근접 출입구), `dtlPstn`(상세위치), 시작·종료층, `pscpNope`(정원), `pscpWht`(정원중량), `elvtrSn`(승강기 일련번호), `oprtngSitu`(가동현황)

- 1~8호선 273개 역, 871대
- `fcltNo`는 871건 모두 유일하다. `elvtrSn`은 2건 중복(`0077-428`, `0077-876`)이 있어 키로 쓰지 않는다.
- 가동현황 값: `M` 860 / `S` 6 / 빈 값 5. [확인 필요] M·S의 뜻(정상·중지로 추정)을 데이터셋 설명 페이지에서 확인한다.
- **`stnCd`와 `stnNo`가 한 행에 함께 있다.** 역코드(승강기·`getStnPsgr` 계열) ↔ 역번호(승하차 파일 계열) 대응표(1-3)를 만들 때 이 API를 출발점으로 쓴다.
- OA-15994의 EV 866대와 이 API의 871대를 역코드·위치로 대조하면 엘리베이터 상태를 교차 검증할 수 있다.

## 4. OA-22122 `TbSubwayLineDetail` (출입구 임시폐쇄)

필드: `LINE`(호선), `SBWY_STNS_NM`(역명), `CLSG_PLC`(폐쇄 장소), `BGNG_YMD`·`END_YMD`(시작·종료일, "2026-07-13 00:00:00.0" 형식), `CLSG_RSN`(사유), `RPLC_PATH`(대체 경로)

- 역코드가 없고 역명만 있다. 역명이 잘린 값("건대입구(")도 있어, (호선, 역명 앞부분)으로 역을 찾는 규칙이 필요하다.
- 같은 역·같은 장소에 대체 경로만 다른 행이 있다(제기동 1번 출입구 2건). 기본키를 (역, 장소, 시작일)로 잡으면 충돌하므로 대체 경로까지 포함하거나 대리키를 쓴다.

## 5. 수집 운영

- 작업 스케줄러 작업명 `ENDB_SubwayCollect`: 11/17 01:00부터 매시, 23일간(12/9 00시까지) 반복. 실행 파일 `run_collect.cmd` → `C:\Users\dongh\.venvs\endb\Scripts\python.exe src\collect.py`
- 설정: 로그인 상태에서 실행, 배터리 사용 중에도 실행, 놓친 실행은 PC가 켜지면 바로 1회 실행, 10분 넘으면 중단
- **한계**: PC가 꺼져 있거나 절전 중인 시간은 수집되지 않는다. 빠진 시각은 `collect_log.csv`의 시각 간격으로 확인하고, 비가동 시간 산정 때 결측으로 처리한다.
- 용량: 1회 약 58KB(gzip), 3주 약 30MB. 원본 폴더는 `.gitignore`로 저장소에서 제외한다.
- 확인 방법: `data/snapshots/collect_stdout.log` 마지막 줄, 또는 PowerShell `Get-ScheduledTaskInfo ENDB_SubwayCollect`의 `LastTaskResult`(0이면 정상)
