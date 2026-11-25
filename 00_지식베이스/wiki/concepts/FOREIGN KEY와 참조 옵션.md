---
name: FOREIGN KEY와 참조 옵션
english: FOREIGN KEY, ON DELETE / ON UPDATE
chapter: 07장
pages: p.14-16, 20
related: [CREATE TABLE, PRIMARY KEY와 UNIQUE, CHECK 제약조건]
---
## 정의
FOREIGN KEY는 외래키를 지정하는 키워드이며 REFERENCES 다음에 참조하는 테이블·속성을 제시한다. 참조 무결성 유지를 위해 참조되는 테이블의 투플 삭제·변경 시 처리 방법을 ON DELETE / ON UPDATE 옵션으로 지정한다.

## 핵심 내용
- ON DELETE NO ACTION: 투플을 삭제하지 못하게 함 / CASCADE: 관련 투플을 함께 삭제 / SET NULL: 관련 투플의 외래키 값을 NULL로 변경 / SET DEFAULT: 외래키 값을 미리 지정한 기본 값으로 변경 (p.14)
- ON UPDATE NO ACTION: 변경하지 못하게 함 / CASCADE: 관련 투플의 외래키 값도 함께 변경 / SET NULL / SET DEFAULT (p.15)

## 예시
```sql
FOREIGN KEY(소속부서) REFERENCES 부서(부서번호)
FOREIGN KEY(소속부서) REFERENCES 부서(부서번호) ON DELETE CASCADE ON UPDATE CASCADE
```
그림 7-4 (p.16): 부서(1 인사부, 2 연구부, 3 홍보부), 사원(1001 정소화 3, 1002 김용욱 1, 1003 고명석 2). 홍보부 삭제 시 CASCADE면 정소화 사원 투플도 삭제, SET NULL이면 정소화의 소속부서가 NULL, SET DEFAULT면 기본값으로 변경, NO ACTION이면 부서 투플 삭제 불가.

## 흔한 실수/혼동
- 옵션을 생략했을 때 어떻게 동작하는지는 강의에 명시되어 있지 않다.

## 출처
07장 p.14-16
