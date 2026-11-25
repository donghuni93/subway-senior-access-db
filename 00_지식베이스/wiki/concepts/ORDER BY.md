---
name: ORDER BY
english: ORDER BY
chapter: 07장
pages: p.52-54
related: [SELECT 기본 검색, NULL 검색 IS NULL]
---
## 정의
ORDER BY 키워드로 결과 테이블 내용을 원하는 순서로 정렬해 출력한다. 정렬 기준 속성과 정렬 방식을 지정한다.

## 핵심 내용
- 오름차순(기본) ASC, 내림차순 DESC.
- 널 값은 오름차순에서는 맨 마지막, 내림차순에서는 맨 먼저 출력된다.
- 여러 기준은 속성을 차례로 나열한다.
- 형식: SELECT [ALL|DISTINCT] 속성_리스트 FROM 테이블_리스트 [WHERE 조건] [ORDER BY 속성_리스트 [ASC|DESC]];

## 예시
```sql
SELECT 고객이름, 등급, 나이 FROM 고객 ORDER BY 나이 DESC;   -- 7-26: 첫 행 오형준 (null), 이어 성원용 35 ...
SELECT 주문고객, 주문제품, 수량, 주문일자 FROM 주문 WHERE 수량 >= 10 ORDER BY 주문제품 ASC, 수량 DESC;   -- 7-27
```
7-27은 p01 먼저, p03 중에서는 수량 22가 먼저 출력된다.

## 흔한 실수/혼동
- 내림차순에서 NULL이 맨 앞에 나오는 점(7-26)을 놓치기 쉽다.

## 출처
07장 p.52-54
