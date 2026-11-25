# 03_본프로젝트 — Claude 작업 규칙

서울 지하철 고령 이용·승강기 접근성 DB (MySQL 8.0.46 `subway_access_db`, Python + Streamlit). 할 일·담당은 `README.md`, 현재 상태는 `01_문서/현재_상태.md`.

## 이 프로젝트의 기준
성능 좋은 DB가 목표가 아니다. **강의(00~09장)로 설명할 수 있는 DB**가 목표다. 스키마·SQL을 바꾸면:
1. 강의 근거를 `kb-answer` 스킬 절차로 찾는다.
2. `02_설계/07_설계근거_추적표.md`를 `design-trace` 스킬로 갱신한다.
3. 바꾼 이유를 `01_문서/진행기록.md`에 날짜와 함께 남긴다.
4. 승인 전에 `kb-design-reviewer` 에이전트로 검토한다.
강의 밖 기법(인덱스, 집계 테이블, 군집)을 더할 때는 설명할 이유가 있을 때만 하고, 추적표의 "강의 범위 밖" 절에 적는다.

## 폴더
| 위치 | 내용 |
|---|---|
| `02_설계/` | 01 요구사항 → 02 ER → 03 릴레이션 → 04 정규화 → 05 물리 → 06 테스트 → 07 설계 근거 추적표, `ERD.png` |
| `03_sql/` | 01 DDL(실행하면 DB를 지우고 새로 만든다) · 02 무결성 점검 · 03 질의 Q1~Q3 · 04 뷰 · 05 제약 위반 테스트 |
| `05_코드/` | collect → preprocess → load_db → db(질의 함수) → analysis(군집) → visualize → app(대시보드). guide_*·build_guide_html은 읽기 가이드 |
| `06_테스트/` | pytest |
| `07_데이터/` | snapshots·raw(원본, 수정 금지) → clean(정제 결과) |
| `04_결과/` | 그림·군집 CSV |
| `01_문서/` | 현재 상태, 구현 정리, 진행기록(설계 변경 이유) |

## 명령 (저장소 루트에서)
```
uv run pytest 03_본프로젝트/06_테스트          # 67건 통과가 기준선
uv run ruff check 03_본프로젝트
uv run streamlit run 03_본프로젝트/05_코드/app.py          # 대시보드 8501 (MySQL 필요)
uv run python 03_본프로젝트/05_코드/analysis.py            # 재분석 후 visualize.py
uv run python 03_본프로젝트/05_코드/build_guide_html.py   # 문서를 고치면 읽기 가이드 다시 생성
```
py 파일을 고치면 훅이 ruff를 자동 실행한다.

## 지킬 것
- 인증키는 루트 `.env`에만 있다. 읽거나 출력하지 않는다. DB 접속은 MySQL login-path `endb`.
- `subway_db`는 HW2용 DB다. 건드리지 않는다.
- `07_데이터/snapshots/`, `07_데이터/raw/`는 수정하지 않는다. 가공은 다시 읽어서 한다.
- `03_sql/01_schema.sql` 실행(DB를 지우고 새로 만듦)과 운영 DB의 구조 변경(ALTER·DROP)은 사용자 확인 후에만 한다. 조회는 자유롭게 한다. 실행 뒤에는 `load_db.py`와 `03_sql/04_views.sql`을 다시 실행해야 한다.
- `05_코드/collect.py`, `06_테스트/test_collect.py`는 서버 수집 담당 세션의 파일이다. 고치기 전에 알린다.
- 문서 파일을 옮기거나 이름을 바꾸면 `05_코드/guide_catalog.py`의 경로도 고치고 `uv run pytest 03_본프로젝트/06_테스트/test_app.py`로 확인한다.
