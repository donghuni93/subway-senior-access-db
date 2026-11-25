---
name: DROP TABLE
english: DROP TABLE
chapter: 07장
pages: p.26, 103
related: [ALTER TABLE, DELETE, FOREIGN KEY와 참조 옵션]
---
## 정의
테이블을 삭제하는 DDL 문: DROP TABLE 테이블_이름;

## 핵심 내용
- 삭제할 테이블을 참조하는 테이블이 있으면 삭제가 수행되지 않으며, 관련된 외래키 제약조건을 먼저 삭제해야 한다 (p.26).

## 예시
```sql
DROP TABLE 배송업체;   -- 예제 7-9
```

## 흔한 실수/혼동
- DELETE FROM 테이블(모든 투플 삭제)은 빈 테이블이 남지만 DROP TABLE과는 다르다 (p.103).

## 출처
07장 p.26, p.103
