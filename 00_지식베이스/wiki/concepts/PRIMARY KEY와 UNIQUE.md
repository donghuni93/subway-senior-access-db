---
name: PRIMARY KEY와 UNIQUE
english: PRIMARY KEY / UNIQUE
chapter: 07장
pages: p.13
related: [CREATE TABLE, FOREIGN KEY와 참조 옵션]
---
## 정의
PRIMARY KEY는 기본키를 지정하는 키워드, UNIQUE는 대체키를 지정하는 키워드다.

## 핵심 내용
- UNIQUE로 지정된 속성 값은 유일성을 가지며, 기본키와 달리 널 값이 허용된다.
- 복합 속성으로 기본키를 지정할 수 있다: PRIMARY KEY(주문고객, 주문제품)

## 예시
- PRIMARY KEY(고객아이디)
- PRIMARY KEY(주문고객, 주문제품)
- UNIQUE(고객이름)

## 흔한 실수/혼동
- UNIQUE(대체키)는 NULL 허용, PRIMARY KEY는 NULL 불가(강의 비교: '기본키와 달리 널 값이 허용').

## 출처
07장 p.13
