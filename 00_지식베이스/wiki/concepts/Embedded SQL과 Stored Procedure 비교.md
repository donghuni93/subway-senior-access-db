---
name: Embedded SQL과 Stored Procedure 비교
english: Embedded SQL vs Stored Procedure
chapter: 07장
pages: p.127-129
related: [삽입 SQL]
---
## 정의
별첨 자료. Embedded SQL은 응용 프로그램 코드에 SQL을 포함시켜 실행하는 방식, Stored Procedure는 SQL 로직을 DB 내부에 저장하고 호출만 하는 방식이다.

## 핵심 내용
- 실행 위치: 클라이언트(애플리케이션) / DB 서버 내부
- 배포 위치: 응용 프로그램 코드 / DB에 저장
- 실행 속도: SQL마다 네트워크 요청 / 한 번 호출로 여러 SQL 실행(빠름)
- 수정 방법: 코드 수정 후 재배포 / DB 내 프로시저 수정만
- 동적 SQL: 쉽게 가능 / 제한적(PREPARE)
- 트랜잭션 관리: 애플리케이션 제어 / DB 내 제어 가능
- 주 사용 목적: 일반 응용 개발 / DB 내부 로직 자동화·성능 최적화 (p.127)

## 예시
```sql
DELIMITER $$
CREATE PROCEDURE AddUser(IN p_name VARCHAR(50), IN p_age INT)
BEGIN
  INSERT INTO users (name, age) VALUES (p_name, p_age);
END $$
DELIMITER ;
CALL AddUser('홍길동', 30);   -- p.129
```
p.128의 C 예시는 mysql_query(conn, "INSERT INTO users (name, age) VALUES ('홍길동', 30)") 로 SQL을 전달한다.

## 흔한 실수/혼동
- p.128 'Embedded SQL' C 예시는 EXEC SQL 방식이 아니라 MySQL C API 호출이다.

## 출처
07장 p.127-129
