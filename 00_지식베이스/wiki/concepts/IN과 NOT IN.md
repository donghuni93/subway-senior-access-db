---
name: IN과 NOT IN
english: IN / NOT IN
chapter: 07장
pages: p.83-85
related: [부속 질의문, EXISTS와 NOT EXISTS]
---
## 정의
IN: 부속 질의문 결과 값 중 일치하는 것이 있으면 조건이 참. NOT IN: 일치하는 것이 없으면 참 (표 7-7).

## 핵심 내용
- 다중 행 부속 질의문에 사용한다.

## 예시
```sql
SELECT 제품명, 제조업체 FROM 제품
WHERE 제품번호 IN (SELECT 주문제품 FROM 주문 WHERE 주문고객 = 'banana');   -- 7-42: 그냥만두 대한식품, 맛난초콜릿 한빛제과, 통통우동 민국푸드
SELECT 제품명, 제조업체 FROM 제품
WHERE 제품번호 NOT IN (SELECT 주문제품 FROM 주문 WHERE 주문고객 = 'banana');   -- 7-43: 쿵떡파이, 매운쫄면, 얼큰라면, 달콤비스킷
```

## 흔한 실수/혼동
- (강의에 별도 언급 없음)

## 출처
07장 p.83-85
