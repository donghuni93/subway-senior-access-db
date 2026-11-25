---
name: DELETE
english: DELETE
chapter: 07장
pages: p.100-103
related: [INSERT, UPDATE, DROP TABLE, 부속 질의문]
---
## 정의
테이블에 저장된 데이터를 삭제하는 DML 문.

## 핵심 내용
- 형식: DELETE FROM 테이블_이름 [WHERE 조건];
- WHERE 조건을 만족하는 투플만 삭제하며, WHERE를 생략하면 모든 투플이 삭제되어 빈 테이블이 된다.

## 예시
```sql
DELETE FROM 주문 WHERE 주문일자 = '2022-05-22';   -- 7-52: o10 삭제
DELETE FROM 주문 WHERE 주문고객 IN (SELECT 고객아이디 FROM 고객 WHERE 고객이름 = '정소화');   -- 7-53
DELETE FROM 주문;   -- 7-54: 빈 테이블
```

## 흔한 실수/혼동
- DELETE FROM 주문은 빈 테이블을 남기며 DROP TABLE과 다르다(p.103).

## 출처
07장 p.100-103
