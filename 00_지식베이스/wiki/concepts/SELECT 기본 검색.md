---
name: SELECT 기본 검색
english: SELECT ... FROM
chapter: 07장
pages: p.30-33
related: [DISTINCT와 ALL, 별칭 AS, WHERE 조건 검색, SQL 분류 DDL DML DCL]
---
## 정의
SELECT 키워드와 함께 검색할 속성을, FROM 키워드와 함께 속성이 있는 테이블을 나열한다. 검색 결과는 테이블 형태로 반환된다.

## 핵심 내용
- 형식: SELECT [ALL | DISTINCT] 속성_리스트 FROM 테이블_리스트; (p.30)
- 모든 속성을 검색할 때는 속성 이름을 전부 나열하지 않고 * 를 쓸 수 있다 (p.33)

## 예시
```sql
SELECT 고객아이디, 고객이름, 등급 FROM 고객;   -- 7-10 (p.31)
SELECT * FROM 고객;                            -- 7-12 (p.33)
```
7-10 결과 첫 행: apple, 정소화, gold (총 7행). 7-12 결과의 peach 나이는 (null).

## 흔한 실수/혼동
- 결과 테이블의 행 순서는 실습 환경에 따라 바뀔 수 있다(p.78 주석).

## 출처
07장 p.30-33
