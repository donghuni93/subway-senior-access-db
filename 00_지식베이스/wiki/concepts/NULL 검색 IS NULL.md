---
name: NULL 검색 IS NULL
english: IS NULL / IS NOT NULL
chapter: 07장
pages: p.49-51
related: [NOT NULL과 DEFAULT, 집계 함수, ORDER BY]
---
## 정의
IS NULL로 속성 값이 널인지, IS NOT NULL로 널이 아닌지를 비교한다. 검색 조건에서 널 값을 다른 값과 크기 비교하면 결과가 모두 거짓이 된다.

## 핵심 내용
- 재고량이 NULL이면 재고량 > 10, < 10, >= 10, <= 10, = 10, <> 10 이 모두 거짓 (p.49).

## 예시
```sql
SELECT 고객이름 FROM 고객 WHERE 나이 IS NULL;       -- 7-24: 오형준
SELECT 고객이름 FROM 고객 WHERE 나이 IS NOT NULL;   -- 7-25: 정소화, 김선우, 고명석, 김용욱, 성원용, 채광주 (6명)
```

## 흔한 실수/혼동
- '나이 = NULL' 로는 찾을 수 없고 IS NULL을 써야 한다(비교 결과가 모두 거짓).

## 출처
07장 p.49-51
