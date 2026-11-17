# 04_본프로젝트 — 확정 주제로 구현 (11/17 갱신, ~12/10)

> 기준 문서: 최종 제출 제안서 `02_제안서/제출/프로젝트-제안서-이동훈-박재연.docx` (11/3)
> 주제: 고령 이용 수요와 승강기 운영 정보를 통합한 서울 지하철 이용 지원 시스템
> 세 질문: Q1 고령 수요가 몰리는 역·시간대 / Q2 승강기 비가동 빈도·시간과 영향받는 고령 이용객 / Q3 역 유형 군집과 우선 관리 역
> 릴레이션 9개: LINE, STATION, ELEVATOR, OUTAGE, RIDERSHIP, EXIT_CLOSURE, TRANSFER, CLUSTER_RESULT, LOAD_LOG

담당: 훈 = 이동훈(조장), 연 = 박재연, 공 = 공동. ●는 주담당, ○는 검토·지원 (제안서 표 8 기준)
완료: [x] 완료, [~] 일부 완료(남은 일은 `진행기록.md` 최신 항목), [ ] 시작 전

## 일정 요약

| 기간 | 단계 |
|---|---|
| 11/17~11/18 | 0. 수집 시작 (최우선) |
| 11/18~12/8 | API 수집 3주 (승강기 매시, 출입구 매일) |
| 11/18~11/21 | 1. 파일 데이터 확보, 설계 확정 |
| 11/20~11/25 | 2. DB 구축, 적재 |
| 11/24~11/28 | 3. 질의, 분석, 시각화 |
| 11/26~12/3 | 4. 대시보드, 발표 (**12/3 발표**) |
| 12/4~12/10 | 5. 3주분 반영, 최종보고서·증빙 (**12/10 제출**) |

수집 기간은 제안서의 11/10~12/1에서 11/18~12/8로 바꾸었다. 이유는 `진행기록.md` 11/17 항목에 있다.

## 인수인계 받은 사람을 위한 읽기 가이드

처음 받았다면 아래 순서로 읽는다. 문서·SQL·코드·그림을 한곳에서 훑어보는 화면도 있다(DB·인증키 불필요).

1. `인수인계_구현.md`: 현재 상태, 일정별 할 일, 명령, 지킬 것
2. `구현정리_파이프라인단계별.md` 0장 그림: 데이터 흐름 ①~⑩
3. `design/01` → `03` → `05`: 질문, 릴레이션, 물리 스키마 (`design/ERD.png`를 옆에 둔다)
4. `src/preprocess.py` → `load_db.py` → `db.py` → `analysis.py` → `app.py`
5. `sql/04_views.sql`, `sql/03_queries.sql`: 화면·분석이 DB에서 꺼내는 것
6. `진행기록.md`: 설계를 바꾼 이유

**읽기 화면 열기** (저장소 루트에서)

| 방법 | 명령 | 열리는 곳 |
|---|---|---|
| Streamlit 읽기 가이드 | `uv run streamlit run 04_본프로젝트/src/guide_app.py --server.port 8502` | http://localhost:8502 |
| 단일 HTML (서버 없이, 더블클릭) | 저장소 맨 위 `읽기가이드.html`을 더블클릭. 다시 만들 때: `uv run python 04_본프로젝트/src/build_guide_html.py --open` | `읽기가이드.html` (같은 내용: `output/guide.html`) |
| 한 번에 열기 (더블클릭) | 저장소 맨 위 `대시보드_열기.cmd`. 대시보드·읽기 가이드 서버를 켜고 응답하면 브라우저를 연다. 로그는 `%TEMP%\streamlit-8501.log`, `streamlit-8502.log` | 8501, 8502 |
| 대시보드 (MySQL 필요) | `uv run streamlit run 04_본프로젝트/src/app.py` | http://localhost:8501 |

`guide.html`은 문서를 고친 뒤 위 명령으로 다시 만들어야 반영된다. 파일 목록과 링크는 `src/guide_catalog.py`에 있다.

### 자료 링크

| 구분 | 자료 | 용도 |
|---|---|---|
| 팀 | [공유 노션](https://app.notion.com/p/4081341ea0178159b937ee1954358343) | 할 일, 회의록, 의사결정, 데이터 출처 |
| 수집 API | [OA-15994 승강기 가동현황](https://data.seoul.go.kr/dataList/OA-15994/S/1/datasetView.do) | 매시 수집 |
| 수집 API | [OA-22740 엘리베이터 현황](https://data.seoul.go.kr/dataList/OA-22740/S/1/datasetView.do) | 매시 수집 |
| 수집 API | [OA-22122 출입구 임시폐쇄](https://data.seoul.go.kr/dataList/OA-22122/S/1/datasetView.do) | 매시 수집 |
| 파일 | [OA-22483 노인 승하차 2025](https://data.seoul.go.kr/dataList/OA-22483/S/1/datasetView.do) | Q1 |
| 파일 | [OA-12921 전체 승하차](https://data.seoul.go.kr/dataList/OA-12921/S/1/datasetView.do) | Q1 |
| 파일 | [OA-13305 역사 심도](https://data.seoul.go.kr/dataList/OA-13305/S/1/datasetView.do) | Q3 |
| 파일 | [OA-13290 환승 거리](https://data.seoul.go.kr/dataList/OA-13290/S/1/datasetView.do) | Q3 |
| 파일 | [OA-12514 승강기 길이·높이](https://data.seoul.go.kr/dataList/OA-12514/S/1/datasetView.do) | 승강기 속성 |
| 포털 | [승하차 파일 15048032](https://www.data.go.kr/data/15048032/fileData.do), [역사심도 파일 15071319](https://www.data.go.kr/data/15071319/fileData.do) | 원본 파일 |
| 도구 | [Streamlit](https://docs.streamlit.io/), [uv](https://docs.astral.sh/uv/), [MySQL 8.4](https://dev.mysql.com/doc/refman/8.4/en/), [scikit-learn 군집](https://scikit-learn.org/stable/modules/clustering.html) | 문서 |

데이터셋 주소는 ID로 만든 것이라 페이지가 열리지 않으면 열린데이터광장에서 ID로 검색한다. OA-15442, OA-22534도 같은 방식이다.

## 0단계. 수집 시작 — 11/17~11/18 (최우선)

지난 시간의 승강기 상태는 나중에 받을 수 없다. 스키마 확정을 기다리지 않고, API 원본 응답을 시각별 JSON 파일로 그대로 저장하는 수집기부터 띄운다. OUTAGE·EXIT_CLOSURE 변환은 2단계에서 이 파일을 다시 읽어 수행한다.

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 0-1 | 서울 열린데이터광장 인증키를 `.env`(`SEOUL_API_KEY`)에 저장, `.gitignore`에 `.env`·스냅샷 폴더 추가 | 훈 | `.env` | [x] |
| 0-2 | OA-15994(`SeoulMetroFaciInfo`)와 OA-22740(`getWksnElvtr`) 실제 호출. 응답 필드, 역 식별 키, 승강기 ID 유일성, 상태 값 종류, 전체 건수 확인 후 주 수집 대상 결정 | 연● 훈○ | design/00_API확인.md | [x] |
| 0-3 | OA-22122 출입구 임시폐쇄 API 호출 확인 | 연● | design/00_API확인.md | [x] |
| 0-4 | 수집기 작성: 전체 페이지를 받아 `data/snapshots/{source}/YYYYMMDD_HH.json`로 저장, 건수·실패는 `data/snapshots/collect_log.csv`에 기록 (DB 없이 동작) | 연● 훈○ | src/collect.py | [x] |
| 0-5 | Windows 작업 스케줄러 등록: 승강기 매시, 출입구 매일 1회. PC가 꺼진 시간은 결측으로 남음 | 연● | 등록 화면 캡처(증빙) | [x] |
| 0-6 | 다음 날 아침 스냅샷 개수 확인 (승강기 24개) | 연 | — | [ ] |

## 1단계. 파일 데이터 확보와 설계 확정 — 11/18~11/21

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 1-1 | 파일 다운로드: OA-22483(노인 승하차 2025), OA-12921(전체 승하차 2025), OA-15442, OA-22534, OA-13305(심도), 역사건축정보, OA-12514(승강기 길이·높이), OA-13290(환승). 출처 URL 기록 | 연● | data/raw/, data/raw/출처.txt | [x] |
| 1-2 | 데이터 검사: 행 수, 컬럼, 결측, 키 형식, 역명 표기 차이 | 연● 훈○ | design/00_데이터검사.md | [x] |
| 1-3 | 역 코드 대응표 (역코드·외부코드·역번호·역명 표기 → station_no) | 연● 훈○ | data/clean/station_map.csv | [x] |
| 1-4 | 요구사항 명세서 확정 (제안서 ①~⑨를 실제 데이터 기준으로 수정) | 훈● | design/01_요구사항명세서.md | [x] |
| 1-5 | E-R 다이어그램 확정 (그림 포함) | 훈● | design/02_ER다이어그램.md + png | [x] |
| 1-6 | 릴레이션 스키마 확정 (PK/FK, 변환 규칙) | 훈● | design/03_릴레이션스키마.md | [x] |
| 1-7 | 정규화 검증: 실제 원본 행으로 이상현상 예시, 1NF→BCNF | 훈● | design/04_정규화.md | [x] |
| 1-8 | 물리 설계: 타입, CHECK, 인덱스, 테이블 명세서 | 훈● | design/05_물리스키마.md | [x] |

## 2단계. DB 구축과 적재 — 11/20~11/25

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 2-1 | DDL 작성·실행 (DB명 예: `subway_db`). 비밀번호는 login-path 또는 `.env` | 훈● | sql/01_schema.sql | [x] |
| 2-2 | 기준 정보 적재 (LINE, STATION, ELEVATOR, TRANSFER). 다시 실행해도 중복 없음 | 연● 훈○ | src/load_base.py | [x] |
| 2-3 | 승하차 적재: 시간대 열 → 행 변환, 노인·전체 병합 → RIDERSHIP | 연● | src/load_ridership.py | [x] |
| 2-4 | 스냅샷 → OUTAGE: 직전 상태와 비교해 비가동 시작·종료 기록, 수집 결측 시각 처리 규칙 | 훈● 연○ | src/build_outage.py | [x] |
| 2-5 | 출입구 스냅샷 → EXIT_CLOSURE: 새 건 추가, 종료일 변경 갱신 | 연● | src/load_closure.py | [x] |
| 2-6 | 모든 적재를 LOAD_LOG에 기록, 적재 오류와 처리 방법 정리 | 공 | design/적재기록.md | [x] |
| 2-7 | 무결성 점검 질의 (FK 고아 행, 음수 인원, 수집 빠진 시각) | 훈● | sql/02_checks.sql | [x] |
| 2-8 | 수집기를 DB 적재까지 연결 (매시 실행 때 OUTAGE 갱신) | 연● 훈○ | src/collect.py | [x] |

## 3단계. 질의·분석·시각화 — 11/24~11/28

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 3-1 | Q1 질의: 역·시간대별 고령 이용 규모와 비중 | 훈● | sql/03_queries.sql | [x] |
| 3-2 | Q2 질의: 현재 비가동 승강기와 그 시간대 평균 고령 이용객, 역별 비가동 횟수·누적 시간 | 훈● | sql/03_queries.sql | [x] |
| 3-3 | 출입구 폐쇄·대체 경로 조회, 대시보드용 뷰 | 훈● | sql/04_views.sql | [x] |
| 3-4 | 역 단위 지표(고령 수요, 깊이, 환승 시간, 비가동 시간) → 군집 분석(k 선정 근거 포함) → CLUSTER_RESULT 저장 | 연● 훈○ | src/analysis.py | [x] |
| 3-5 | 시각화: 시간대별 고령 이용, 역별 비가동 시간, 역 유형 지도 | 연● | src/visualize.py, output/*.png | [x] |

## 4단계. 대시보드와 발표 — 11/26~12/3

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 4-1 | Streamlit: 교통약자 화면(역 선택 → 승강기 상태, 폐쇄 출입구, 시간대별 이용 규모), 관리자 화면(비가동 승강기 영향 순위, 역 유형) | 공 | src/app.py | [x] |
| 4-2 | 테스트: 질의 결과 손계산 대조, 제약조건 위반 삽입, OUTAGE 변환 로직 단위 테스트 | 공 | design/06_테스트.md, tests/ | [x] |
| 4-3 | 발표 자료 (약 2주 수집분 기준), 시연 순서 | 공 | 발표 파일 | [ ] |
| 4-4 | **12/3 발표** | 공 | — | [ ] |

## 5단계. 마무리 — 12/4~12/10

| # | 할 일 | 담당 | 산출물 | 완료 |
|---|---|---|---|---|
| 5-1 | 12/8 수집 종료, 3주분으로 OUTAGE·군집·그래프 다시 생성 | 연● | output/ | [ ] |
| 5-2 | 발표 피드백 반영 | 공 | — | [ ] |
| 5-3 | 최종보고서 (서론 / 본론 설계·구현·테스트 / 결론 / 참고자료 + 맨 뒤 1쪽 요약문) | 공 | 05_최종제출/보고서/ | [ ] |
| 5-4 | 증빙 zip (소스, 실행 방법 README, 입력·결과 데이터, 수집 로그) | 훈● | 05_최종제출/증빙문서/ | [ ] |
| 5-5 | **12/10 제출** (조장 업로드), 파일명 조 번호 확인 | 훈 | — | [ ] |

## 단계별 완료 기준

- 0단계: 스케줄러 실행 기록에서 매시 성공, `data/snapshots/elevator/`에 하루 24개 파일, `collect_log.csv`에 실패 0건 또는 실패 사유 기록
- 2단계: `sql/02_checks.sql`의 점검 질의가 모두 0행, LOAD_LOG에 적재마다 1건 이상, 같은 적재를 두 번 실행해도 행 수 동일
- 코드: `uv run ruff check`, `uv run pytest` 통과 (OUTAGE 상태 전이 테스트 포함)

## 폴더 구성 (예정)

```
04_본프로젝트/
├─ data/raw/         내려받은 원본 파일과 출처.txt
├─ data/snapshots/   API 원본 응답 (시각별 JSON), collect_log.csv
├─ data/clean/       역 코드 대응표 등 정제 결과
├─ design/           설계 문서 00~06
├─ sql/              DDL, 점검 질의, 핵심 질의, 뷰
├─ src/              수집·적재·분석·시각화·대시보드
├─ tests/            단위 테스트
└─ output/           그래프, 결과 표
```

## 진행 기록
설계를 바꾸거나 오류를 해결할 때마다 `진행기록.md`에 날짜·내용·이유를 남긴다. 최종보고서의 "설계 과정"과 "결론(느낀 점)"을 쓸 때 재료가 된다.

날짜별 변경 이력(무엇이 바뀌었나, 상태, 남은 일)은 [기록/](기록/README.md) 폴더에 하루 한 파일로 쌓는다.

## 실행 방법 (11/17 갱신)

**대시보드만 볼 때**: 저장소 루트에서 `uv run streamlit run 04_본프로젝트/src/app.py` → 브라우저 http://localhost:8501

```powershell
# 처음부터 다시 만들 때 (저장소 루트에서)
uv run python 04_본프로젝트/src/fetch_reference.py     # 기준 정보·승하차 API 원본 내려받기 (1회)
#   2025 전체 승하차·역사심도 파일은 data/raw/file/에 있음 (공공데이터포털 15048032, 15071319)
uv run python 04_본프로젝트/src/preprocess.py          # 원본 → data/clean/*.csv (약 25초)
Get-Content -Raw -Encoding UTF8 04_본프로젝트/sql/01_schema.sql | mysql --login-path=endb   # DB 다시 만들기 (기존 데이터 삭제)
uv run python 04_본프로젝트/src/load_db.py             # CSV → MySQL + 시간대 프로필 계산 (약 1분, 다시 실행해도 결과 동일)
mysql --login-path=endb subway_access_db < 04_본프로젝트/sql/04_views.sql    # 뷰 만들기
mysql --login-path=endb subway_access_db < 04_본프로젝트/sql/02_checks.sql   # 무결성 점검 (모두 0이면 정상)
mysql --login-path=endb subway_access_db < 04_본프로젝트/sql/03_queries.sql  # 질문 1·2·3 질의
mysql --login-path=endb --force subway_access_db < 04_본프로젝트/sql/05_constraint_tests.sql  # 제약조건 위반 테스트 (모두 ERROR여야 정상)
uv run python 04_본프로젝트/src/analysis.py            # 역사 유형 군집 → CLUSTER_RUN·CLUSTER_RESULT, output/*.csv
uv run python 04_본프로젝트/src/visualize.py           # 그림 5개 → output/*.png
uv run python 04_본프로젝트/src/draw_erd.py            # DB 스키마 → design/ERD.png
uv run pytest 04_본프로젝트/tests                      # 테스트 20건
```

- 수집: 작업 스케줄러 `ENDB_SubwayCollect`가 매시 `run_collect.cmd`를 실행한다. 수집(`collect.py`) 뒤 `preprocess.py --live` → `load_db.py --live`로 승강기·비가동·출입구 테이블을 DB에 바로 반영한다(약 2초, 로그 `data/snapshots/db_refresh.log`).
- 군집 분석은 승강기 수집이 3일(72시간) 이상 쌓이면 비가동 지표를 포함해 다시 실행한다. 발표 전(12/2)과 수집 종료 후(12/8)에 `analysis.py` → `visualize.py`를 다시 돌린다.

## 산출물 위치 (11/17)

| 구분 | 파일 |
|---|---|
| 설계 | design/00_API확인.md, 00_데이터검사.md, 01_요구사항명세서.md, 02_ER다이어그램.md + ERD.png, 03_릴레이션스키마.md, 04_정규화.md, 05_물리스키마.md, 06_테스트.md |
| SQL | sql/01_schema.sql(DDL), 02_checks.sql(무결성), 03_queries.sql(질문별 질의), 04_views.sql(뷰), 05_constraint_tests.sql(제약 위반) |
| 프로그램 | src/collect.py(수집), fetch_reference.py(기준·이력 API), preprocess.py(정제·역사 묶음), load_db.py(적재, 삽입 SQL), db.py(질의 모듈), analysis.py(군집), visualize.py(그림), app.py(대시보드), draw_erd.py(ERD) |
| 결과 | output/q1_*.png, q2_*.png, q3_*.png, cluster_summary.csv, cluster_k_selection.csv, priority_ranking.csv |
