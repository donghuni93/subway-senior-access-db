# 07장 데이터베이스 언어 SQL

## 학습 목표
- SQL의 역할을 이해하고, 이를 기능별로 분류해본다. (p.2)
- SQL의 데이터 정의/조작 기능을 예제를 통해 익힌다. (p.2)
- 뷰의 개념과 장점을 이해한다. (p.2)
- 삽입 SQL의 역할을 이해한다. (p.2)

## 핵심 요약
- SQL은 관계 DB를 위한 표준 비절차적 질의어로 SEQUEL에서 유래했고, 대화식 SQL과 삽입 SQL 방식으로 쓴다. (p.4)
- SQL은 DDL(정의), DML(조작), DCL(제어)로 분류한다. DDL은 CREATE/ALTER/DROP TABLE, DML은 SELECT/INSERT/UPDATE/DELETE. (p.5, 8, 28)
- CREATE TABLE은 속성(타입, NOT NULL, DEFAULT), PRIMARY KEY, UNIQUE, FOREIGN KEY(ON DELETE/UPDATE 옵션), CHECK를 정의한다. (p.9-17)
- ALTER TABLE로 속성 추가(ADD)·삭제(DROP COLUMN), 제약조건 추가·삭제를 하고 DROP TABLE로 테이블을 삭제한다. (p.22-26)
- SELECT는 ALL/DISTINCT, *, AS 별칭, 산술식을 지원하고 WHERE에서 비교·논리 연산자, LIKE(%, _), IS NULL을 쓴다. (p.30-51)
- ORDER BY는 ASC(기본)/DESC이며 NULL은 오름차순에서 맨 뒤, 내림차순에서 맨 앞에 나온다. (p.52)
- 집계 함수 COUNT/MAX/MIN/SUM/AVG는 NULL을 제외하며 WHERE에는 쓸 수 없고 SELECT·HAVING에서만 쓴다. (p.55)
- GROUP BY로 그룹을 만들고 HAVING으로 그룹 조건을 건다. 그룹 기준·집계 함수 외의 속성은 SELECT에 쓸 수 없다. (p.63-69)
- 조인은 FROM에 테이블을 나열하고 WHERE에 조인 조건을 두거나 INNER JOIN ... ON을 쓰며, 외부 조인(LEFT/RIGHT/FULL OUTER JOIN)은 조건을 만족하지 않는 투플도 검색한다. (p.70-79)
- 부속 질의문은 단일 행(비교 연산자)과 다중 행(IN, NOT IN, EXISTS, NOT EXISTS, ALL, ANY)으로 나뉜다. (p.80-89)
- INSERT(직접/부속 질의문), UPDATE, DELETE는 WHERE를 생략하면 전체 투플이 대상이 된다. (p.90-103)
- 뷰는 데이터를 저장하지 않는 가상 테이블이며 CREATE VIEW ... AS SELECT [WITH CHECK OPTION]으로 만든다. 기본키 미포함·집계·DISTINCT·GROUP BY 뷰는 변경 불가. (p.105-117)
- 뷰의 장점: 질의 단순화, 보안, 관리 편의. DROP VIEW는 기본 테이블에 영향이 없다. (p.118-119)
- 삽입 SQL은 EXEC SQL로 시작하고 변수에 콜론(:)을 붙이며, 여러 행은 커서(DECLARE/OPEN/FETCH/CLOSE)로 처리한다. (p.120-126)
- 별첨으로 Embedded SQL과 Stored Procedure를 비교한다. (p.127-129)

## 개념 목록
- SQL 소개: [[SQL 개요]], [[SQL 분류 DDL DML DCL]], [[판매 데이터베이스 예제]]
- 데이터 정의(DDL): [[CREATE TABLE]], [[SQL 데이터 타입]], [[NOT NULL과 DEFAULT]], [[PRIMARY KEY와 UNIQUE]], [[FOREIGN KEY와 참조 옵션]], [[CHECK 제약조건]], [[ALTER TABLE]], [[DROP TABLE]]
- 데이터 조작(DML) - 검색: [[SELECT 기본 검색]], [[DISTINCT와 ALL]], [[별칭 AS]], [[산술식 검색]], [[WHERE 조건 검색]], [[LIKE 검색]], [[NULL 검색 IS NULL]], [[ORDER BY]], [[집계 함수]], [[GROUP BY]], [[HAVING]], [[조인 검색]], [[외부 조인]], [[부속 질의문]], [[IN과 NOT IN]], [[ALL과 ANY]], [[EXISTS와 NOT EXISTS]]
- 데이터 조작(DML) - 삽입·수정·삭제: [[INSERT]], [[UPDATE]], [[DELETE]]
- 뷰: [[뷰]], [[CREATE VIEW]], [[WITH CHECK OPTION]], [[변경 가능한 뷰와 불가능한 뷰]], [[뷰의 장점]], [[DROP VIEW]]
- 삽입 SQL: [[삽입 SQL]], [[커서]], [[Embedded SQL과 Stored Procedure 비교]]
- 인덱스: 07장 원문에 인덱스(CREATE INDEX) 내용이 없어 카드를 만들지 않았다.
- DCL 권한 구문(GRANT/REVOKE 등): 원문에 구문이 없고 개념 설명(p.5)만 있다.

## 시험·과제 포인트
- 예제 7-1~7-4(테이블 생성), 7-5~7-9(ALTER/DROP), 7-10~7-54(검색·삽입·수정·삭제), 7-55~7-59(뷰)가 강의 예제의 전부이며 Lab2 실습이 같은 번호로 그대로 실행한다. (sql_patterns/07장_SQL_구문_패턴.md)
- 헷갈리기 쉬운 쌍: WHERE(행 조건) vs HAVING(그룹 조건, 집계 함수), COUNT(속성) vs COUNT(*)(NULL 제외 여부), DELETE FROM 테이블 vs DROP TABLE, 단일 행(=) vs 다중 행(IN) 부속 질의문. (p.49, 59, 67, 80, 103)
- NULL 비교는 IS NULL로 하고, ORDER BY에서 NULL 위치(오름차순 맨 뒤/내림차순 맨 앞)를 묻는 문제가 가능하다. (p.49, 52)
- 변경 불가능한 뷰의 조건(기본키 미포함, 집계, DISTINCT, GROUP BY, 조인)과 제품1/제품2 예(p.113-117). (p.112)
- Lab 실습에서 MySQL은 CHECK 추가/삭제, GROUP BY 뷰의 WITH CHECK OPTION이 강의 표기대로 동작하지 않았다. (sql_patterns/Lab1_Lab2_실습_구문_요약.md)
