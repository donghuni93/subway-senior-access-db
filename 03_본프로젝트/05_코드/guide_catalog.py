"""인수인계 읽기 가이드: 문서 목록(읽는 순서)과 외부 자료 링크.

guide_app.py(Streamlit)와 build_guide_html.py(정적 HTML)가 함께 쓴다. DB·인증키가 필요 없다.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 03_본프로젝트/


@dataclass(frozen=True)
class Doc:
    group: str
    title: str
    path: str  # ROOT 기준 상대경로
    kind: str  # md | code | sql | image | csv
    desc: str

    @property
    def file(self) -> Path:
        return ROOT / self.path

    @property
    def slug(self) -> str:
        # 한글 경로를 그대로 쓰면 브라우저가 location.hash를 퍼센트 인코딩해 id 비교가 실패한다. ASCII로 고정한다.
        return "d_" + hashlib.md5(self.path.encode("utf-8")).hexdigest()[:10]


DOCS: list[Doc] = [
    # 1. 먼저 읽기
    Doc("1. 먼저 읽기", "현재 상태", "01_문서/현재_상태.md", "md", "지금 상태, 설계 규칙, 팀에서 정할 것. 가장 먼저 읽는다."),
    Doc("1. 먼저 읽기", "본 프로젝트 README", "README.md", "md", "0~5단계 할 일·담당·완료 여부, 실행 방법, 산출물 위치."),
    Doc("1. 먼저 읽기", "구현 정리: 파이프라인 단계별", "01_문서/구현정리_파이프라인단계별.md", "md", "수집→정제→적재→분석→화면 ①~⑩ 단계의 구현 내용과 한계."),
    Doc("1. 먼저 읽기", "진행 기록", "01_문서/진행기록.md", "md", "날짜별 결정과 오류 해결. 설계를 바꾼 이유가 여기 있다."),
    # 2. 설계
    Doc("2. 설계 문서", "00 API 확인", "02_설계/00_API확인.md", "md", "수집 대상 API 3종의 필드·건수·키 확인 결과."),
    Doc("2. 설계 문서", "00 데이터 검사", "02_설계/00_데이터검사.md", "md", "파일 데이터의 행 수·결측·역명 표기 차이."),
    Doc("2. 설계 문서", "01 요구사항 명세서", "02_설계/01_요구사항명세서.md", "md", "세 질문(Q1~Q3)과 기능·데이터 요구."),
    Doc("2. 설계 문서", "02 E-R 다이어그램", "02_설계/02_ER다이어그램.md", "md", "개체·관계 설계."),
    Doc("2. 설계 문서", "03 릴레이션 스키마", "02_설계/03_릴레이션스키마.md", "md", "PK/FK와 E-R 변환 규칙."),
    Doc("2. 설계 문서", "04 정규화", "02_설계/04_정규화.md", "md", "이상현상 예시와 1NF→BCNF 검증."),
    Doc("2. 설계 문서", "05 물리 스키마", "02_설계/05_물리스키마.md", "md", "타입·CHECK·인덱스·테이블 명세서."),
    Doc("2. 설계 문서", "06 테스트", "02_설계/06_테스트.md", "md", "질의 손계산 대조, 제약 위반, 단위 테스트."),
    Doc("2. 설계 문서", "07 설계 근거 추적표", "02_설계/07_설계근거_추적표.md", "md", "설계 결정마다 강의 개념·쪽수와 우리 데이터 예. 발표 예상 질문 포함."),
    Doc("2. 설계 문서", "ERD 그림 (14개 테이블)", "02_설계/ERD.png", "image", "draw_erd.py가 DB 스키마에서 생성."),
    # 3. SQL
    Doc("3. SQL", "01 스키마(DDL)", "03_sql/01_schema.sql", "sql", "실행하면 DB를 지우고 새로 만든다. 주의."),
    Doc("3. SQL", "02 무결성 점검", "03_sql/02_checks.sql", "sql", "모두 0이면 정상."),
    Doc("3. SQL", "03 질문별 질의", "03_sql/03_queries.sql", "sql", "Q1·Q2·Q3 핵심 질의."),
    Doc("3. SQL", "04 뷰", "03_sql/04_views.sql", "sql", "대시보드용 뷰 9개."),
    Doc("3. SQL", "05 제약조건 위반 테스트", "03_sql/05_constraint_tests.sql", "sql", "모두 ERROR여야 정상."),
    # 4. 코드 (데이터 흐름 순서)
    Doc("4. 프로그램", "collect.py: 수집", "05_코드/collect.py", "code", "API 원본을 매시 스냅샷으로 저장 (서버 수집 담당 세션 관리)."),
    Doc("4. 프로그램", "fetch_reference.py: 기준 정보", "05_코드/fetch_reference.py", "code", "기준·이력 API 1회 내려받기."),
    Doc("4. 프로그램", "preprocess.py: 정제", "05_코드/preprocess.py", "code", "원본 → 07_데이터/clean/*.csv, 역사 묶음, 비가동 구간 계산."),
    Doc("4. 프로그램", "load_db.py: 적재", "05_코드/load_db.py", "code", "CSV → MySQL, 시간대 프로필 계산."),
    Doc("4. 프로그램", "db.py: 질의 모듈", "05_코드/db.py", "code", "화면이 쓰는 매개변수 질의."),
    Doc("4. 프로그램", "analysis.py: 군집 분석", "05_코드/analysis.py", "code", "역사 유형 군집(Q3)."),
    Doc("4. 프로그램", "visualize.py: 그림", "05_코드/visualize.py", "code", "04_결과/그림/*.png 생성."),
    Doc("4. 프로그램", "app.py: 대시보드", "05_코드/app.py", "code", "Streamlit 3개 화면 (MySQL 필요)."),
    Doc("4. 프로그램", "draw_erd.py: ERD", "05_코드/draw_erd.py", "code", "스키마 → ERD.png."),
    Doc("4. 프로그램", "run_collect.cmd", "run_collect.cmd", "code", "스케줄러가 매시 실행하는 배치 파일."),
    # 5. 결과
    Doc("5. 결과", "Q1 시간대별 고령 이용 비중", "04_결과/그림/q1_hourly_senior_pct.png", "image", "질문 1."),
    Doc("5. 결과", "Q1 고령 이용 상위 역사", "04_결과/그림/q1_top_complexes.png", "image", "질문 1."),
    Doc("5. 결과", "Q2 비가동 상위 역", "04_결과/그림/q2_outage_top.png", "image", "질문 2."),
    Doc("5. 결과", "Q3 군집 지도", "04_결과/그림/q3_cluster_map.png", "image", "질문 3."),
    Doc("5. 결과", "Q3 군집 프로필", "04_결과/그림/q3_cluster_profile.png", "image", "질문 3."),
    Doc("5. 결과", "군집 요약", "04_결과/csv/군집/cluster_summary.csv", "csv", "군집별 평균 지표."),
    Doc("5. 결과", "k 선정 근거", "04_결과/csv/군집/cluster_k_selection.csv", "csv", "k별 실루엣."),
    Doc("5. 결과", "우선 관리 역 순위", "04_결과/csv/우선순위/priority_ranking.csv", "csv", "관리 우선순위."),
    Doc("5. 결과", "군집 진단 (안정성·비교)", "04_결과/csv/군집/cluster_diagnostics.csv", "csv", "k별 실루엣, 시드·부분표본 ARI, Ward 비교."),
    Doc("5. 결과", "군집 지표 상관", "04_결과/csv/군집/cluster_feature_corr.csv", "csv", "입력 지표 사이 상관 행렬."),
    Doc("5. 결과", "우선 순위 민감도", "04_결과/csv/우선순위/priority_sensitivity.csv", "csv", "가중치를 바꿨을 때 상위 20위 겹침."),
]

# (분류, 이름, URL, 설명). 서울 열린데이터광장·공공데이터포털은 데이터셋 ID 기준 주소다.
SEOUL = "https://data.seoul.go.kr/dataList/{}/S/1/datasetView.do"
LINKS: list[tuple[str, str, str, str]] = [
    ("팀", "팀 공유 노션", "https://app.notion.com/p/4081341ea0178159b937ee1954358343", "할 일·회의록·의사결정·데이터 출처"),
    ("실행", "대시보드 (로컬)", "http://localhost:8501", "uv run streamlit run 03_본프로젝트/05_코드/app.py"),
    ("실행", "읽기 가이드 (로컬)", "http://localhost:8502", "uv run streamlit run 03_본프로젝트/05_코드/guide_app.py --server.port 8502"),
    ("수집 API", "OA-15994 승강기 가동현황", SEOUL.format("OA-15994"), "SeoulMetroFaciInfo, 매시 수집"),
    ("수집 API", "OA-22740 엘리베이터 현황", SEOUL.format("OA-22740"), "getWksnElvtr, 매시 수집"),
    ("수집 API", "OA-22122 출입구 임시폐쇄", SEOUL.format("OA-22122"), "TbSubwayLineDetail, 매시 수집"),
    ("파일·기준", "OA-22483 노인 승하차 2025", SEOUL.format("OA-22483"), "Q1 고령 수요"),
    ("파일·기준", "OA-12921 전체 승하차", SEOUL.format("OA-12921"), "Q1 전체 이용"),
    ("파일·기준", "OA-13305 역사 심도", SEOUL.format("OA-13305"), "Q3 군집 지표"),
    ("파일·기준", "OA-15442", SEOUL.format("OA-15442"), "기준 정보"),
    ("파일·기준", "OA-22534", SEOUL.format("OA-22534"), "기준 정보"),
    ("파일·기준", "OA-12514 승강기 길이·높이", SEOUL.format("OA-12514"), "승강기 속성"),
    ("파일·기준", "OA-13290 환승 거리", SEOUL.format("OA-13290"), "Q3 군집 지표"),
    ("공공데이터포털", "승하차 파일 (15048032)", "https://www.data.go.kr/data/15048032/fileData.do", "OA-12921 원본 파일"),
    ("공공데이터포털", "역사심도 파일 (15071319)", "https://www.data.go.kr/data/15071319/fileData.do", "OA-13305 원본 파일"),
    ("도구 문서", "Streamlit", "https://docs.streamlit.io/", "대시보드 프레임워크"),
    ("도구 문서", "uv", "https://docs.astral.sh/uv/", "패키지·가상환경 관리"),
    ("도구 문서", "MySQL 8.4 레퍼런스", "https://dev.mysql.com/doc/refman/8.4/en/", "DB"),
    ("도구 문서", "scikit-learn KMeans", "https://scikit-learn.org/stable/modules/clustering.html#k-means", "군집 분석"),
]

READING_ORDER = [
    "01_문서/현재_상태.md로 현재 상태와 설계 규칙을 파악한다.",
    "01_문서/구현정리_파이프라인단계별.md의 0장 그림으로 데이터 흐름(①~⑩)을 잡는다.",
    "02_설계/01 → 03 → 05 순서로 질문, 릴레이션, 물리 스키마를 본다. ERD.png를 옆에 둔다. 왜 그렇게 설계했는지는 02_설계/07 추적표에서 강의 쪽수로 확인한다.",
    "05_코드/preprocess.py → load_db.py → db.py → analysis.py → app.py 순서로 코드를 읽는다.",
    "03_sql/04_views.sql과 03_queries.sql로 화면·분석이 DB에서 무엇을 꺼내는지 본다.",
    "01_문서/진행기록.md에서 설계를 바꾼 이유를 확인한다.",
]
