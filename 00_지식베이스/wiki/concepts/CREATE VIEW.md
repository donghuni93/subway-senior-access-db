---
name: CREATE VIEW
english: CREATE VIEW
chapter: 07장
pages: p.107-110
related: [뷰, WITH CHECK OPTION, DROP VIEW]
---
## 정의
뷰를 생성하는 DDL 문: CREATE VIEW 뷰_이름[(속성_리스트)] AS SELECT 문 [WITH CHECK OPTION];

## 핵심 내용
- 속성 리스트를 생략하면 SELECT 절의 속성 이름을 그대로 사용한다.
- AS 다음 SELECT 문이 뷰의 정의이며 ORDER BY는 사용할 수 없다(오라클 등 일부 DBMS는 허용).
- 집계 함수로 계산된 속성은 기본 테이블에 없던 속성이므로 속성 이름을 명확히 제시해야 한다 (p.110).

## 예시
```sql
CREATE VIEW 우수고객(고객아이디, 고객이름, 나이, 등급)
AS SELECT 고객아이디, 고객이름, 나이, 등급 FROM 고객 WHERE 등급 = 'vip' WITH CHECK OPTION;   -- 7-55
CREATE VIEW 업체별제품수(제조업체, 제품수)
AS SELECT 제조업체, COUNT(*) FROM 제품 GROUP BY 제조업체 WITH CHECK OPTION;   -- 7-56
```

## 흔한 실수/혼동
- 속성 리스트를 생략한 형식(p.109)도 같은 뷰를 만든다.

## 출처
07장 p.107-110
