# 07장 SQL 구문 패턴 (강의 예제 그대로)

출처: raw/md/07장 데이터베이스 언어 SQL_2026.md. 쪽수는 `## p.N` 기준. 판매 데이터베이스(고객·제품·주문, p.6) 기준이다. 개념 설명은 [[ch07_데이터베이스_언어_SQL]] 참조.

## 1. 테이블 생성·변경·삭제 (DDL)

### CREATE TABLE 일반형 (p.9)
```sql
CREATE TABLE 테이블_이름 (
    속성_이름  데이터_타입 [NOT NULL] [DEFAULT 기본_값]
    [PRIMARY KEY (속성_리스트)]
    [UNIQUE (속성_리스트)]
    [FOREIGN KEY (속성_리스트) REFERENCES 테이블_이름(속성_리스트)]
       [ON DELETE 옵션] [ON UPDATE 옵션]
    [CONSTRAINT 이름] [CHECK(조건)]
);
```

### 예제 7-1 고객 (p.18)
```sql
CREATE TABLE 고객 (
고객아이디 VARCHAR(20) NOT NULL,
고객이름 VARCHAR(10) NOT NULL,
나이 INT,
등급 VARCHAR(10) NOT NULL,
직업 VARCHAR(20),
적립금 INT DEFAULT 0,
PRIMARY KEY(고객아이디)
);
```

### 예제 7-2 제품, CHECK 포함 (p.19)
```sql
CREATE TABLE 제품 (
제품번호 CHAR(3) NOT NULL,
제품명 VARCHAR(20),
재고량 INT,
단가 INT,
제조업체 VARCHAR(20),
PRIMARY KEY(제품번호),
CHECK (재고량 >= 0 AND 재고량 <=10000)
);
```

### 예제 7-3 주문, 외래키 (p.20)
```sql
CREATE TABLE 주문 (
주문번호 CHAR(3) NOT NULL,
주문고객 VARCHAR(20),
주문제품 CHAR(3),
수량 INT,
배송지 VARCHAR(30),
주문일자 DATE,
PRIMARY KEY(주문번호),
FOREIGN KEY(주문고객) REFERENCES 고객(고객아이디),
FOREIGN KEY(주문제품) REFERENCES 제품(제품번호)
);
```
(MS SQL에서는 주문일자를 DATETIME으로 지정, p.20)

### 예제 7-4 배송업체 (p.21)
```sql
CREATE TABLE 배송업체 (
업체번호 CHAR(3) NOT NULL,
업체명 VARCHAR(20),
주소 VARCHAR(100),
전화번호 VARCHAR(20),
PRIMARY KEY(업체번호)
);
```

### 외래키 / CHECK 조각 (p.15, p.17)
```sql
FOREIGN KEY(소속부서) REFERENCES 부서(부서번호)
FOREIGN KEY(소속부서) REFERENCES 부서(부서번호) ON DELETE CASCADE ON UPDATE CASCADE
CHECK(재고량 >= 0 AND 재고량 <= 10000)
CONSTRAINT CHK_CPY CHECK(제조업체 = '한빛제과')
```

### ALTER TABLE / DROP TABLE (p.22-26)
```sql
ALTER TABLE 테이블_이름 ADD 속성_이름 데이터_타입 [NOT NULL] [DEFAULT 기본_값];       -- p.22
ALTER TABLE 고객 ADD 가입날짜 DATE;                                                   -- 7-5
ALTER TABLE 테이블_이름 DROP COLUMN 속성_이름;                                        -- p.23
ALTER TABLE 고객 DROP COLUMN 가입날짜;                                                -- 7-6
ALTER TABLE 테이블_이름 ADD CONSTRAINT 제약조건_이름 제약조건_내용;                    -- p.24
ALTER TABLE 고객 ADD CONSTRAINT CHK_AGE CHECK(나이 >= 20);                            -- 7-7
ALTER TABLE 테이블_이름 DROP CONSTRAINT 제약조건_이름;                                -- p.25
ALTER TABLE 고객 DROP CONSTRAINT CHK_AGE;                                             -- 7-8
DROP TABLE 테이블_이름;                                                               -- p.26
DROP TABLE 배송업체;                                                                  -- 7-9
```

## 2. 기본 검색 (p.30-38)
```sql
SELECT [ ALL | DISTINCT ] 속성_리스트 FROM 테이블_리스트;                -- p.30

SELECT 고객아이디, 고객이름, 등급 FROM 고객;                             -- 7-10 (p.31)
SELECT 고객아이디, 고객이름, 나이, 등급, 직업, 적립금 FROM 고객;         -- 7-11 (p.32)
SELECT * FROM 고객;                                                      -- 7-12 (p.33)
SELECT 제조업체 FROM 제품;                                               -- 7-13 (p.34)
SELECT ALL 제조업체 FROM 제품;                                           -- 7-14 (p.35)
SELECT DISTINCT 제조업체 FROM 제품;                                      -- 7-15 (p.36)
SELECT 제품명, 단가 AS 가격 FROM 제품;                                   -- 7-16 (p.37)
SELECT 제품명, 단가 + 500 AS "조정 단가" FROM 제품;                      -- 7-17 (p.38)
```

## 3. 조건 검색 WHERE (p.39-51)
```sql
SELECT [ ALL | DISTINCT ] 속성_리스트 FROM 테이블_리스트 [ WHERE 조건 ];   -- p.39

SELECT 제품명, 재고량, 단가 FROM 제품 WHERE 제조업체 = '한빛제과';          -- 7-18 (p.41)
SELECT 주문제품, 수량, 주문일자 FROM 주문 WHERE 주문고객 = 'apple' AND 수량 >= 15;   -- 7-19 (p.42)
SELECT 주문제품, 수량, 주문일자, 주문고객 FROM 주문 WHERE 주문고객 = 'apple' OR 수량 >= 15;   -- 7-20 (p.43)
SELECT 제품명, 단가, 제조업체 FROM 제품 WHERE 단가 >= 2000 AND 단가 <= 3000;   -- 7-21 (p.44)
SELECT 고객이름, 나이, 등급, 적립금 FROM 고객 WHERE 고객이름 LIKE '김%';        -- 7-22 (p.47)
SELECT 고객아이디, 고객이름, 등급 FROM 고객 WHERE 고객아이디 LIKE '_____';      -- 7-23 (p.48)
SELECT 고객이름 FROM 고객 WHERE 나이 IS NULL;                                    -- 7-24 (p.50)
SELECT 고객이름 FROM 고객 WHERE 나이 IS NOT NULL;                                -- 7-25 (p.51)
```
LIKE 패턴 (p.46): `LIKE '데이터%'` 시작, `LIKE '%데이터'` 끝, `LIKE '%데이터%'` 포함, `LIKE '데이터___'` 시작+6자, `LIKE '__한%'` 세 번째 글자가 한.

## 4. 정렬 ORDER BY (p.52-54)
```sql
SELECT [ ALL | DISTINCT ] 속성_리스트 FROM 테이블_리스트
[ WHERE 조건 ] [ ORDER BY 속성_리스트 [ ASC | DESC ] ];                    -- p.52

SELECT 고객이름, 등급, 나이 FROM 고객 ORDER BY 나이 DESC;                  -- 7-26 (p.53)

SELECT 주문고객, 주문제품, 수량, 주문일자
FROM 주문
WHERE 수량 >= 10
ORDER BY 주문제품 ASC, 수량 DESC;                                          -- 7-27 (p.54)
```

## 5. 집계 함수 (p.55-62)
```sql
SELECT AVG(단가) FROM 제품;                                                       -- 7-28 (p.56)
SELECT SUM(재고량) AS "재고량 합계" FROM 제품 WHERE 제조업체 = '한빛제과';       -- 7-29 (p.58)
SELECT COUNT(고객아이디) AS 고객수 FROM 고객;                                     -- 7-30 (p.59) 결과 7
SELECT COUNT(나이) AS 고객수 FROM 고객;                                           -- 결과 6
SELECT COUNT(*) AS 고객수 FROM 고객;                                              -- 결과 7
SELECT COUNT(DISTINCT 제조업체) AS "제조업체 수" FROM 제품;                       -- 7-31 (p.62)
```

## 6. 그룹별 검색 GROUP BY / HAVING (p.63-69)
```sql
SELECT [ ALL | DISTINCT ] 속성_리스트
FROM 테이블_리스트
[ WHERE 조건 ]
[ GROUP BY 속성_리스트 [ HAVING 조건 ] ]
[ ORDER BY 속성_리스트 [ ASC | DESC ] ];                                    -- p.63

SELECT 주문제품, SUM(수량) AS 총주문수량 FROM 주문 GROUP BY 주문제품;       -- 7-32 (p.64)
SELECT 제조업체, COUNT(*) AS 제품수, MAX(단가) AS 최고가 FROM 제품 GROUP BY 제조업체;   -- 7-33 (p.66)
SELECT 제조업체, COUNT(*) AS 제품수, MAX(단가) AS 최고가
FROM 제품 GROUP BY 제조업체 HAVING COUNT(*)>=3;                             -- 7-34 (p.67)
SELECT 등급, COUNT(*) AS 고객수, AVG(적립금) AS 평균적립금
FROM 고객 GROUP BY 등급 HAVING AVG(적립금)>=1000;                           -- 7-35 (p.68)
SELECT 주문제품, 주문고객, SUM(수량) AS 총주문수량
FROM 주문 GROUP BY 주문제품, 주문고객;                                       -- 7-36 (p.69)
```

## 7. 조인 (p.70-79)
```sql
SELECT 제품.제품명 FROM 제품, 주문
WHERE 주문.주문고객 = 'banana' AND 제품.제품번호 = 주문.주문제품;            -- 7-37 (p.72)

SELECT 주문.주문제품, 주문.주문일자 FROM 고객, 주문
WHERE 고객.나이 >= 30 AND 고객.고객아이디 = 주문.주문고객;                   -- 7-38 (p.73)

SELECT o.주문제품, o.주문일자 FROM 고객 c, 주문 o
WHERE c.나이 >= 30 AND c.고객아이디 = o.주문고객                             -- 별명 사용 (p.74)

SELECT 제품.제품명 FROM 고객, 제품, 주문
WHERE 고객.고객이름 = '고명석' AND 고객.고객아이디 = 주문.주문고객
 AND 제품.제품번호 = 주문.주문제품;                                          -- 7-39 (p.75)

SELECT 속성_리스트 FROM 테이블1 INNER JOIN 테이블2 ON 조인조건 [ WHERE 검색조건 ]   -- p.76
SELECT 주문.주문제품, 주문.주문일자
FROM 고객 INNER JOIN 주문 ON 고객.고객아이디 = 주문.주문고객
WHERE 고객.나이 >= 30;                                                       -- (7-38 INNER JOIN 표현, p.76)

SELECT 속성_리스트 FROM 테이블1 LEFT | RIGHT | FULL OUTER JOIN 테이블2 ON 조인조건 [ WHERE 검색조건 ]   -- p.77
SELECT 고객.고객이름, 주문.주문제품, 주문.주문일자
FROM 고객 LEFT OUTER JOIN 주문 ON 고객.고객아이디 = 주문.주문고객;           -- p.78
SELECT 고객.고객이름, 주문.주문제품, 주문.주문일자
FROM 주문 RIGHT OUTER JOIN 고객 ON 주문.주문고객 = 고객.고객아이디;          -- 위와 결과 같음 (p.79)
```

## 8. 부속 질의문 (p.80-89)
```sql
SELECT 제품명, 단가 FROM 제품
WHERE 제조업체 = (SELECT 제조업체 FROM 제품 WHERE 제품명 = '달콤비스킷');   -- 7-40 (p.81)

SELECT 고객이름, 적립금 FROM 고객
WHERE 적립금 = (SELECT MAX(적립금) FROM 고객);                              -- 7-41 (p.82)

SELECT 제품명, 제조업체 FROM 제품
WHERE 제품번호 IN (SELECT 주문제품 FROM 주문 WHERE 주문고객 = 'banana');     -- 7-42 (p.84)

SELECT 제품명, 제조업체 FROM 제품
WHERE 제품번호 NOT IN (SELECT 주문제품 FROM 주문 WHERE 주문고객 = 'banana'); -- 7-43 (p.85)

SELECT 제품명, 단가, 제조업체 FROM 제품
WHERE 단가 > ALL (SELECT 단가 FROM 제품 WHERE 제조업체 = '대한식품');        -- 7-44 (p.86)

SELECT 고객이름 FROM 고객
WHERE EXISTS (SELECT * FROM 주문
              WHERE 주문일자 = '2022-03-15' AND 주문.주문고객 = 고객.고객아이디);   -- 7-45 (p.87)

SELECT 고객이름 FROM 고객
WHERE NOT EXISTS (SELECT * FROM 주문
                  WHERE 주문일자 = '2022-03-15' AND 주문.주문고객 = 고객.고객아이디); -- 7-46 (p.88)
```
같은 질의의 세 가지 표현 (p.89): 조인(`FROM 제품, 주문 WHERE 제품.제품번호 = 주문.주문제품 AND 주문.주문고객 = 'banana'`), EXISTS, IN (7-42).

## 9. 삽입·수정·삭제 (p.90-103)
```sql
INSERT INTO 테이블_이름[(속성_리스트)] VALUES (속성값_리스트);                    -- p.90

INSERT INTO 고객(고객아이디, 고객이름, 나이, 등급, 직업, 적립금)
VALUES ('strawberry', '최유경', 30, 'vip', '공무원', 100);                       -- 7-47 (p.91)
INSERT INTO 고객 VALUES ('strawberry', '최유경', 30, 'vip', '공무원', 100);      -- 위와 같음 (p.92)

INSERT INTO 고객(고객아이디, 고객이름, 나이, 등급, 적립금)
VALUES ('tomato', '정은심', 36, 'gold', 4000);                                   -- 7-48 (p.93)
INSERT INTO 고객 VALUES ('tomato', '정은심', 36, 'gold', NULL, 4000);            -- 위와 같음 (p.94)

INSERT INTO 한빛제품(제품명, 재고량, 단가)
SELECT 제품명, 재고량, 단가 FROM 제품 WHERE 제조업체 = '한빛제과';               -- p.95

UPDATE 테이블_이름 SET 속성_이름1 = 값1, 속성_이름2 = 값2, ... [WHERE 조건];     -- p.96
UPDATE 제품 SET 제품명 = '통큰파이' WHERE 제품번호 = 'p03';                      -- 7-49 (p.97)
UPDATE 제품 SET 단가 = 단가 * 1.1;                                               -- 7-50 (p.98)
UPDATE 주문 SET 수량 = 5
WHERE 주문고객 IN (SELECT 고객아이디 FROM 고객 WHERE 고객이름 = '정소화');       -- 7-51 (p.99)

DELETE FROM 테이블_이름 [WHERE 조건];                                            -- p.100
DELETE FROM 주문 WHERE 주문일자 = '2022-05-22';                                  -- 7-52 (p.101)
DELETE FROM 주문 WHERE 주문고객 IN (SELECT 고객아이디 FROM 고객 WHERE 고객이름 = '정소화');   -- 7-53 (p.102)
DELETE FROM 주문;                                                                -- 7-54 (p.103)
```

## 10. 뷰 (p.107-119)
```sql
CREATE VIEW 뷰_이름[(속성_리스트)] AS SELECT 문 [WITH CHECK OPTION];             -- p.107

CREATE VIEW 우수고객(고객아이디, 고객이름, 나이, 등급)
AS SELECT 고객아이디, 고객이름, 나이, 등급
FROM 고객
WHERE 등급 = 'vip'
WITH CHECK OPTION;                                                               -- 7-55 (p.108)

CREATE VIEW 우수고객
AS SELECT 고객아이디, 고객이름, 나이, 등급
FROM 고객
WHERE 등급 = 'vip'
WITH CHECK OPTION;                                                               -- 속성 리스트 생략 (p.109)

CREATE VIEW 업체별제품수(제조업체, 제품수)
AS SELECT 제조업체, COUNT(*)
FROM 제품
GROUP BY 제조업체
WITH CHECK OPTION;                                                               -- 7-56 (p.110)

SELECT * FROM 우수고객 WHERE 나이 >= 20;                                          -- 7-57 (p.111)

CREATE VIEW 제품1 AS SELECT 제품번호, 재고량, 제조업체 FROM 제품 WITH CHECK OPTION;   -- p.113
INSERT INTO 제품1 VALUES ('p08', 1000, '신선식품');                              -- 7-58 (p.114) 성공
CREATE VIEW 제품2 AS SELECT 제품명, 재고량, 제조업체 FROM 제품 WITH CHECK OPTION;     -- p.116
INSERT INTO 제품2 VALUES ('시원냉면', 1000, '신선식품');                         -- 실패 (p.117)

DROP VIEW 뷰_이름;                                                               -- p.119
DROP VIEW 우수고객;                                                              -- 7-59
```

## 11. 삽입 SQL (p.120-126)
```c
EXEC SQL BEGIN DECLARE SECTION;
      char p_no[4], p_name[21];
      int price;
EXEC SQL END DECLARE SECTION;
printf("제품번호를 입력하세요 : ");
scanf("%s", p_no);
EXEC SQL SELECT 제품명, 단가 INTO :p_name, :price
      FROM 제품
      WHERE 제품번호 = :p_no;                    // 그림 7-14 (p.122)

EXEC SQL DECLARE product_cursor CURSOR FOR SELECT 제품명, 단가 FROM 제품;   // p.124
EXEC SQL OPEN product_cursor;                                               // p.124
EXEC SQL FETCH product_cursor INTO :p_name, :price;                          // p.125
EXEC SQL CLOSE procuct_cursor;                                               // p.126 (원문 표기 그대로)
```

## 12. Stored Procedure (별첨, p.129)
```sql
DELIMITER $$

CREATE PROCEDURE AddUser(IN p_name VARCHAR(50), IN p_age INT)
BEGIN
    INSERT INTO users (name, age) VALUES (p_name, p_age);
END $$

DELIMITER ;

CALL AddUser('홍길동', 30);
```
