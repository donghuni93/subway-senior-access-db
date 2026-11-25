---
name: EXISTS와 NOT EXISTS
english: EXISTS / NOT EXISTS
chapter: 07장
pages: p.83, 87-89
related: [부속 질의문, IN과 NOT IN, 조인 검색]
---
## 정의
EXISTS: 부속 질의문 결과 값이 하나라도 존재하면 조건이 참. NOT EXISTS: 하나도 존재하지 않으면 참.

## 핵심 내용
- 부속 질의문이 상위 질의문의 속성(고객.고객아이디)을 참조한다.
- 같은 질의를 조인, EXISTS, IN으로 다양하게 표현할 수 있어 사용자가 자유롭게 선택한다 (p.89).

## 예시
```sql
SELECT 고객이름 FROM 고객
WHERE EXISTS (SELECT * FROM 주문 WHERE 주문일자 = '2022-03-15' AND 주문.주문고객 = 고객.고객아이디);   -- 7-45: 정소화
```
7-46 NOT EXISTS 결과: 채광주, 성원용, 고명석, 오형준, 김선우, 김용욱.

## 흔한 실수/혼동
- (강의에 별도 언급 없음)

## 출처
07장 p.83, 87-89
