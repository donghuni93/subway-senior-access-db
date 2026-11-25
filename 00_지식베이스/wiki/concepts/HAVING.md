---
name: HAVING
english: HAVING
chapter: 07장
pages: p.63, 67-68
related: [GROUP BY, 집계 함수, WHERE 조건 검색]
---
## 정의
HAVING 키워드로 그룹에 대한 조건을 작성한다. 집계 함수를 이용한 조건은 WHERE가 아니라 HAVING에서 작성한다.

## 핵심 내용
- HAVING은 GROUP BY 절 뒤에 온다.

## 예시
```sql
SELECT 제조업체, COUNT(*) AS 제품수, MAX(단가) AS 최고가 FROM 제품 GROUP BY 제조업체 HAVING COUNT(*)>=3;   -- 7-34: 한빛제과 3 2600
SELECT 등급, COUNT(*) AS 고객수, AVG(적립금) AS 평균적립금 FROM 고객 GROUP BY 등급 HAVING AVG(적립금)>=1000;   -- 7-35: gold 3 3500, vip 1 2500
```

## 흔한 실수/혼동
- HAVING은 그룹에 대한 조건이다 (07장 p.63). [강의 범위 밖: 모델 일반 지식] WHERE는 그룹을 만들기 전에 행 단위로 평가되는 조건이라, 강의 원문에는 이 대비 표현이 없다.

## 출처
07장 p.63, 67-68
