---
name: NOT NULL과 DEFAULT
english: NOT NULL / DEFAULT
chapter: 07장
pages: p.11
related: [CREATE TABLE, NULL 검색 IS NULL]
---
## 정의
NOT NULL은 속성이 널 값을 허용하지 않음을 의미하는 키워드, DEFAULT는 속성의 기본 값을 지정하는 키워드다.

## 핵심 내용
- 속성을 정의할 때 데이터 타입을 고른 뒤 널 값 허용 여부와 기본 값 필요 여부를 결정한다.
- 문자열이나 날짜 데이터는 작은따옴표로 묶어 표현한다.

## 예시
- 고객아이디 VARCHAR(20) NOT NULL
- 적립금 INT DEFAULT 0
- 담당자 VARCHAR(10) DEFAULT '방경아'

## 흔한 실수/혼동
- INSERT에서 DEFAULT 속성을 생략하면 기본값이 들어가고, 기본값이 없으면 NULL이 된다는 설명은 강의에 직접 없다(예제 7-48의 직업은 NULL로 삽입).

## 출처
07장 p.11
