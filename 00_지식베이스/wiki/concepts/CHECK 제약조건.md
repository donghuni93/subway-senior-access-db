---
name: CHECK 제약조건
english: CHECK constraint
chapter: 07장
pages: p.17, 19, 24-25
related: [CREATE TABLE, ALTER TABLE]
---
## 정의
테이블에 정확하고 유효한 데이터를 유지하기 위해 특정 속성에 대한 제약조건을 지정하는 데이터 무결성 제약조건이다. CONSTRAINT 키워드로 고유의 이름을 부여할 수도 있다.

## 핵심 내용
- CREATE TABLE 안에 CHECK(조건)을 쓰거나 ALTER TABLE ... ADD CONSTRAINT 이름 CHECK(조건)으로 추가한다.
- 제약조건 삭제: ALTER TABLE 테이블 DROP CONSTRAINT 이름;

## 예시
```sql
CHECK(재고량 >= 0 AND 재고량 <= 10000)          -- p.17, 7-2(p.19)
CONSTRAINT CHK_CPY CHECK(제조업체 = '한빛제과')   -- p.17
ALTER TABLE 고객 ADD CONSTRAINT CHK_AGE CHECK(나이 >= 20);   -- 7-7 (p.24)
ALTER TABLE 고객 DROP CONSTRAINT CHK_AGE;                    -- 7-8 (p.25)
```

## 흔한 실수/혼동
- Lab2 실습 파일은 MySQL에서 CHECK 제약이 지원되지 않아 7-7은 실행되어도 추가되지 않고 7-8은 실행 안 된다고 주석한다 (raw/lab/Lab2-2 SQL(Code).txt). 강의 표기는 위와 같다.

## 출처
07장 p.17, 19, 24-25 / Lab2-2
