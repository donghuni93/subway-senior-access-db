---
name: CREATE TABLE
english: CREATE TABLE
chapter: 07장
pages: p.9-10, 18-21
related: [NOT NULL과 DEFAULT, PRIMARY KEY와 UNIQUE, FOREIGN KEY와 참조 옵션, CHECK 제약조건, SQL 데이터 타입]
---
## 정의
테이블을 생성하는 DDL 문. 속성 정의, 기본키, 대체키, 외래키, 데이터 무결성 제약조건을 한 문장에 정의한다.

## 핵심 내용
- 형식: CREATE TABLE 테이블_이름 ( 속성_이름 데이터_타입 [NOT NULL] [DEFAULT 기본_값], [PRIMARY KEY(속성_리스트)], [UNIQUE(속성_리스트)], [FOREIGN KEY(속성_리스트) REFERENCES 테이블_이름(속성_리스트)] [ON DELETE 옵션] [ON UPDATE 옵션], [CONSTRAINT 이름] [CHECK(조건)] ); (p.9)
- [ ]의 내용은 생략 가능. 문장 끝은 세미콜론(;). SQL 문은 대소문자를 구분하지 않는다 (p.9)
- 번호 의미(p.10): 1 속성 이름·타입·기본 제약, 2 기본키, 3 대체키, 4 외래키, 5 데이터 무결성 제약조건

## 예시
예제 7-1 고객 테이블 (p.18)
```sql
CREATE TABLE 고객 (
  고객아이디 VARCHAR(20) NOT NULL,
  고객이름 VARCHAR(10) NOT NULL,
  나이 INT,
  등급 VARCHAR(10) NOT NULL,
  직업 VARCHAR(20),
  적립금 INT DEFAULT 0,
  PRIMARY KEY(고객아이디)
);
```
예제 7-2 제품(CHECK 포함, p.19), 7-3 주문(외래키 2개, p.20), 7-4 배송업체(p.21)는 sql_patterns 문서 참조.

## 흔한 실수/혼동
- 주문일자 DATE는 MS SQL에서는 DATETIME으로 지정한다고 강의가 주석한다 (p.20).
- 참조되는 테이블(고객, 제품)을 먼저 만들어야 주문 테이블의 외래키를 정의할 수 있다 [강의 범위 밖: 일반 지식, 강의 순서(7-1,7-2,7-3)와 일치].

## 출처
07장 p.9-10, p.18-21
