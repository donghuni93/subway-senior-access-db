---
name: DISTINCT와 ALL
english: DISTINCT / ALL
chapter: 07장
pages: p.30, 34-36
related: [SELECT 기본 검색, 집계 함수]
---
## 정의
ALL은 결과 테이블에 투플 중복을 허용하도록 지정(생략 가능), DISTINCT는 중복을 허용하지 않도록 지정한다.

## 핵심 내용
- COUNT(DISTINCT 속성)으로 서로 다른 값의 개수만 셀 수 있다 (p.62).

## 예시
```sql
SELECT 제조업체 FROM 제품;            -- 7-13: 7행, 제조업체 중복
SELECT ALL 제조업체 FROM 제품;        -- 7-14: 위와 같음
SELECT DISTINCT 제조업체 FROM 제품;   -- 7-15: 대한식품, 민국푸드, 한빛제과 (3행)
```

## 흔한 실수/혼동
- ALL은 기본 동작이므로 쓰든 생략하든 결과가 같다 (7-13과 7-14).

## 출처
07장 p.34-36
