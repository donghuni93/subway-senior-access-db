---
name: DROP VIEW
english: DROP VIEW
chapter: 07장
pages: p.119
related: [뷰, CREATE VIEW, DROP TABLE]
---
## 정의
뷰를 삭제하는 문: DROP VIEW 뷰_이름;

## 핵심 내용
- 뷰를 삭제해도 기본 테이블은 영향을 받지 않는다.
- 삭제할 뷰를 참조하는 제약조건(예: 그 뷰로 만든 다른 뷰)이 있으면 삭제가 수행되지 않으며 먼저 삭제해야 한다.

## 예시
```sql
DROP VIEW 우수고객;   -- 7-59
```

## 흔한 실수/혼동
- (강의에 별도 언급 없음)

## 출처
07장 p.119
