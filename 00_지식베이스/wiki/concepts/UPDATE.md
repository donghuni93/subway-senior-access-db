---
name: UPDATE
english: UPDATE
chapter: 07장
pages: p.96-99
related: [INSERT, DELETE, 산술식 검색, 부속 질의문]
---
## 정의
테이블에 저장된 투플에서 특정 속성의 값을 수정하는 DML 문.

## 핵심 내용
- 형식: UPDATE 테이블_이름 SET 속성_이름1 = 값1, 속성_이름2 = 값2, ... [WHERE 조건];
- WHERE 조건을 만족하는 투플만 수정하며, WHERE를 생략하면 테이블의 모든 투플이 수정 대상이다.
- WHERE에 부속 질의문을 쓸 수 있다(7-51).

## 예시
```sql
UPDATE 제품 SET 제품명 = '통큰파이' WHERE 제품번호 = 'p03';   -- 7-49
UPDATE 제품 SET 단가 = 단가 * 1.1;   -- 7-50: 모든 제품 단가 10% 인상 (4500 -> 4950 ...)
UPDATE 주문 SET 수량 = 5 WHERE 주문고객 IN (SELECT 고객아이디 FROM 고객 WHERE 고객이름 = '정소화');   -- 7-51
```

## 흔한 실수/혼동
- WHERE 생략 시 전체 투플이 수정된다(7-50).

## 출처
07장 p.96-99
