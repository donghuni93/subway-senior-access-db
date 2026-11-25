---
name: WITH CHECK OPTION
english: WITH CHECK OPTION
chapter: 07장
pages: p.107-108
related: [CREATE VIEW, 변경 가능한 뷰와 불가능한 뷰]
---
## 정의
뷰에 삽입이나 수정 연산을 할 때 SELECT 문에서 제시한 뷰의 정의 조건을 위반하면 수행되지 않도록 하는 제약조건.

## 핵심 내용
- 7-55의 우수고객 뷰는 vip가 아닌 고객 삽입, 정의 조건을 위반하는 수정·삭제 시도를 거부한다.

## 예시
7-55: 등급 = 'vip' 조건이 있는 우수고객 뷰에 WITH CHECK OPTION 지정 (p.108).

## 흔한 실수/혼동
- Lab2에서는 MySQL이 GROUP BY 뷰(업체별제품수)의 WITH CHECK OPTION을 거부해 옵션 없이 생성했다(Lab2-2 SQL(Code).txt).

## 출처
07장 p.107-108 / Lab2-2
