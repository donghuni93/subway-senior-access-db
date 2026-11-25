---
name: SQL 데이터 타입
english: SQL data types
chapter: 07장
pages: p.12
related: [CREATE TABLE]
---
## 정의
속성의 데이터 타입. 표 7-1에 제시된 타입은 아래와 같다.

## 핵심 내용
- INT 또는 INTEGER: 정수
- SMALLINT: INT보다 작은 정수
- CHAR(n) 또는 CHARACTER(n): 길이 n인 고정 길이 문자열
- VARCHAR(n) 또는 CHARACTER VARYING(n): 최대 길이 n인 가변 길이 문자열
- NUMERIC(p, s) 또는 DECIMAL(p, s): 고정 소수점 실수. p는 소수점을 제외한 전체 숫자 길이, s는 소수점 이하 숫자 길이
- FLOAT(n): 길이 n인 부동 소수점 실수 / REAL: 부동 소수점 실수
- DATE: 연·월·일 / TIME: 시·분·초 / DATETIME: 날짜와 시간

## 예시
예제 7-1~7-3에서 고객아이디 VARCHAR(20), 제품번호 CHAR(3), 나이 INT, 주문일자 DATE 사용.

## 흔한 실수/혼동
- CHAR(n)은 고정 길이, VARCHAR(n)은 최대 길이 n의 가변 길이다.
- 문자열·날짜 값은 작은따옴표로 묶고, 작은따옴표 문자열은 대소문자를 구분한다 (p.11).

## 출처
07장 p.12, p.11
