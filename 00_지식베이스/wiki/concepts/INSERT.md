---
name: INSERT
english: INSERT
chapter: 07장
pages: p.90-95
related: [UPDATE, DELETE, NOT NULL과 DEFAULT, 부속 질의문]
---
## 정의
테이블에 투플을 삽입하는 DML 문.

## 핵심 내용
- 형식: INSERT INTO 테이블_이름[(속성_리스트)] VALUES (속성값_리스트); (p.90)
- 속성 리스트를 생략하면 테이블 정의 시 지정한 속성 순서대로 값이 삽입된다. 속성 이름과 값은 순서대로 일대일 대응해야 한다.
- 값을 주지 않은 속성은 NULL이 삽입된다(7-48, 직업). INSERT INTO ... VALUES (..., NULL, ...)로 명시할 수도 있다 (p.94).
- 부속 질의문 이용: INSERT INTO 테이블_이름[(속성_리스트)] SELECT 문; (p.95)

## 예시
```sql
INSERT INTO 고객(고객아이디, 고객이름, 나이, 등급, 직업, 적립금) VALUES ('strawberry', '최유경', 30, 'vip', '공무원', 100);   -- 7-47
INSERT INTO 고객(고객아이디, 고객이름, 나이, 등급, 적립금) VALUES ('tomato', '정은심', 36, 'gold', 4000);   -- 7-48 직업 NULL
INSERT INTO 한빛제품(제품명, 재고량, 단가) SELECT 제품명, 재고량, 단가 FROM 제품 WHERE 제조업체 = '한빛제과';   -- p.95
```

## 흔한 실수/혼동
- 속성 리스트를 생략한 INSERT는 NULL 자리에도 NULL을 써야 한다(p.94).

## 출처
07장 p.90-95
