---
name: ALTER TABLE
english: ALTER TABLE
chapter: 07장
pages: p.22-25
related: [CHECK 제약조건, CREATE TABLE, DROP TABLE]
---
## 정의
테이블의 구조(속성·제약조건)를 변경하는 DDL 문.

## 핵심 내용
- 속성 추가: ALTER TABLE 테이블_이름 ADD 속성_이름 데이터_타입 [NOT NULL] [DEFAULT 기본_값]; (p.22)
- 속성 삭제: ALTER TABLE 테이블_이름 DROP COLUMN 속성_이름; 삭제할 속성과 관련된 제약조건이나 참조하는 다른 속성이 있으면 삭제가 수행되지 않으므로 먼저 삭제해야 한다 (p.23)
- 제약조건 추가: ALTER TABLE 테이블_이름 ADD CONSTRAINT 제약조건_이름 제약조건_내용; (p.24)
- 제약조건 삭제: ALTER TABLE 테이블_이름 DROP CONSTRAINT 제약조건_이름; (p.25)

## 예시
```sql
ALTER TABLE 고객 ADD 가입날짜 DATE;            -- 7-5
ALTER TABLE 고객 DROP COLUMN 가입날짜;         -- 7-6
ALTER TABLE 고객 ADD CONSTRAINT CHK_AGE CHECK(나이 >= 20);  -- 7-7
ALTER TABLE 고객 DROP CONSTRAINT CHK_AGE;      -- 7-8
```

## 흔한 실수/혼동
- 속성 삭제에는 COLUMN 키워드(DROP COLUMN), 제약조건 삭제에는 CONSTRAINT 키워드(DROP CONSTRAINT)를 쓴다.

## 출처
07장 p.22-25
