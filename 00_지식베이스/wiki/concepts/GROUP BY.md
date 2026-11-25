---
name: GROUP BY
english: GROUP BY
chapter: 07장
pages: p.63-69
related: [HAVING, 집계 함수, ORDER BY]
---
## 정의
GROUP BY 키워드로 특정 속성의 값이 같은 투플을 모아 그룹을 만들고 그룹별로 검색한다.

## 핵심 내용
- 형식: SELECT ... FROM ... [WHERE 조건] [GROUP BY 속성_리스트 [HAVING 조건]] [ORDER BY ...]; (p.63)
- 그룹 기준 속성을 SELECT 절에도 쓰는 것이 좋다.
- 집계 함수나 GROUP BY 절에 명시된 속성 외의 속성은 SELECT 절에 쓸 수 없다 (p.69).

## 예시
```sql
SELECT 주문제품, SUM(수량) AS 총주문수량 FROM 주문 GROUP BY 주문제품;   -- 7-32: p03 52, p02 58, p06 81, p04 15, p01 24
SELECT 제조업체, COUNT(*) AS 제품수, MAX(단가) AS 최고가 FROM 제품 GROUP BY 제조업체;   -- 7-33: 대한식품 2 4500, 민국푸드 2 5500, 한빛제과 3 2600
SELECT 주문제품, 주문고객, SUM(수량) AS 총주문수량 FROM 주문 GROUP BY 주문제품, 주문고객;   -- 7-36: 9행
```

## 흔한 실수/혼동
- SELECT에 그룹 기준·집계 함수가 아닌 속성을 쓰면 안 된다.

## 출처
07장 p.63-69
