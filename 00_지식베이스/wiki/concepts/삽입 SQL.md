---
name: 삽입 SQL
english: Embedded SQL (ESQL)
chapter: 07장
pages: p.120-123
related: [커서, Embedded SQL과 Stored Procedure 비교, SQL 개요]
---
## 정의
프로그래밍 언어로 작성된 응용 프로그램 안에 삽입하여 사용하는 SQL 문.

## 핵심 내용
- 프로그램에서 일반 명령문이 올 수 있는 곳이면 어디든 삽입 가능하다.
- 일반 명령문과 구별하기 위해 앞에 EXEC SQL을 붙인다.
- 프로그램 변수를 SQL 문에서 쓸 때는 이름 앞에 콜론(:)을 붙인다.
- 변수는 BEGIN DECLARE SECTION과 END DECLARE SECTION 사이에 선언한다.
- 커서가 필요 없는 경우: CREATE TABLE, INSERT, DELETE, UPDATE, 결과로 행 하나만 반환하는 SELECT (p.121).

## 예시
그림 7-14 (p.122): 제품번호를 입력받아 제품명·단가 출력
```c
EXEC SQL BEGIN DECLARE SECTION;
  char p_no[4], p_name[21];
  int price;
EXEC SQL END DECLARE SECTION;
printf("제품번호를 입력하세요 : ");
scanf("%s", p_no);
EXEC SQL SELECT 제품명, 단가 INTO :p_name, :price
      FROM 제품 WHERE 제품번호 = :p_no;
```

## 흔한 실수/혼동
- C에서는 널 문자('\0') 때문에 변수를 속성 문자열 길이보다 1 더 길게 선언한다(p.123).

## 출처
07장 p.120-123
