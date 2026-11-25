# Lab1·Lab2 실습에서 쓴 SQL 구문 요약

출처 파일 (모두 `02. 엔지니어링DB/` 아래, 강의 raw가 아닌 실습 자료):
- `Lab1 MySQL 서버_2026/Lab1-1_실습.sql`, `Lab1-2 SQL(Workbench).sql`, `movedb_ER다이어그램.md`, `Lab1-1 MySQL 서버_2026.md`
- `Lab2 SQL(DDL DML)_2026/raw/lab/Lab2-2 SQL(Code).txt`

강의 쪽수 기준 설명은 [[07장_SQL_구문_패턴]] 참조. 이 문서의 내용은 실습 파일에 있는 것만 적었다.

## Lab1-1: MySQL 서버 기본 사용 (edb 데이터베이스)
Lab1-1_실습.sql은 PDF 8~15쪽을 따라 하는 순서로 구성되어 있다.
```sql
show databases;            -- 데이터베이스 목록
create database edb;       -- 데이터베이스 생성
use edb;                   -- 사용할 데이터베이스 전환
create table board (
  no int not null auto_increment,
  name varchar(20) not null,
  subject varchar(100) not null,
  content text not null,
  password char(20) not null,
  primary key(no)
);
show tables;               -- 테이블 목록
desc board;                -- 테이블 구조 확인
insert into board (no, name, subject, content, password) values (1, 'test', 'it is a test', 'just test', '1234');
select * from board where no = 1;
delete from board where no = 1;
```
- 강의 07장에 없는 MySQL 구문: `show databases/tables`, `create database`, `use`, `desc`, `AUTO_INCREMENT`, `TEXT` 타입.
- Lab1-1 MySQL 서버_2026.md는 MySQL 설치(MySQL Installer), `mysql -u root -p` 접속, Terminal 사용(`show databases;`), Workbench 사용을 다룬다.

## Lab1-2: movedb (Workbench 스크립트)
`Lab1-2 SQL(Workbench).sql`은 MS Access에서 변환한 덤프 파일이다.
- `CREATE DATABASE IF NOT EXISTS movedb; USE movedb;`
- 테이블 3개: ORDER_ITEM(ID, OrderNumber, SKU, Quantity, Price DECIMAL(19,4), ExtendedPrice DECIMAL(19,4)), RETAIL_ORDER(ID, OrderNumber, StoreNumber, StoreZip, OrderMonth, OrderYear, OrderTotal), SKU_DATA(ID, SKU, SKU_Desciption, Department, Buyer). 각각 `ID INTEGER NOT NULL AUTO_INCREMENT`, `PRIMARY KEY (ID)`, `ENGINE=myisam DEFAULT CHARSET=utf8`.
- `DROP TABLE IF EXISTS`, 건별 `INSERT INTO ... VALUES` (ORDER_ITEM 7건, RETAIL_ORDER 3건, SKU_DATA 8건).
- 확인: `use movedb; show tables; select * from ORDER_ITEM; select * from SKU_DATA;`
- movedb_ER다이어그램.md: 실제 FOREIGN KEY 제약은 없고(MyISAM, PK만 정의), OrderNumber·SKU 컬럼명 일치를 근거로 추론한 논리적 관계(RETAIL_ORDER 1:N ORDER_ITEM, SKU_DATA 1:N ORDER_ITEM)를 그렸다.

## Lab2: 판매 DB로 07장 예제 실행
raw/lab/Lab2-2 SQL(Code).txt는 예제 7-1~7-59를 강의 번호 그대로 실행한다. 강의 SQL과 다른 점만 정리한다.

| 예제 | 실습 파일의 처리 |
|---|---|
| 7-2 CHECK | 같은 CREATE TABLE을 3가지 형태(CHECK 없음, `CHECK ('재고량' >= 0 AND '재고량' <=10000)`, `CONSTRAINT chk_stock CHECK(...)`)로 시도. 속성명을 작은따옴표로 감싼 형태가 들어 있다 |
| 7-7 | 주석: MySQL은 CHECK 제약을 지원하지 않음(실행은 되지만 제약이 추가되지 않음) |
| 7-8 | 주석: MySQL에서 실행 안 됨 |
| 7-10 준비 | 고객 7행, 제품 7행, 주문 10행을 `INSERT INTO 테이블 VALUES (...)` 로 삽입. 주문일자는 '19/01/01' ~ '19/05/22' (강의는 2022년) |
| 7-17, 7-29, 7-31 | 별칭을 큰따옴표와 작은따옴표 모두 MySQL에서 실행 가능 |
| 7-32 | 두 번째 질의로 `SELECT SUM(수량) AS 총주문수량 FROM 주문 GROUP BY 주문제품;` (그룹 기준 속성을 SELECT에서 뺀 형태)를 함께 실행 |
| 7-38 | WHERE 조인, `고객 AS c, 주문 AS o` 별칭, `고객 INNER JOIN 주문 ON 고객아이디 = 주문고객 WHERE 나이 >= 30` 3가지. 별칭에 AS 키워드 사용 |
| [추가] | `고객 LEFT JOIN 주문 ON 고객아이디 = 주문고객`, `LEFT OUTER JOIN`, `RIGHT JOIN`, `RIGHT OUTER JOIN`. RIGHT JOIN 실습 전에 `INSERT INTO 고객 VALUES ('avocado', '박찬호', 31, 'silver', '회사원', 500);` 를 삽입 |
| 7-45, 7-46 | 날짜 조건이 '2019-03-15' (강의는 '2022-03-15') |
| 7-48 | `INSERT INTO 한빛제품(제품명, 재고량, 단가) SELECT ... FROM 제품 WHERE 제조업체 = '한빛제과'` 를 함께 실행. 한빛제품 테이블의 생성 문은 실습 파일에 없다 |
| 7-52 | 삭제 조건 '2019-05-22' |
| 7-55 | 뷰를 `우수고객(고객아이디, 고객이름, 나이)` 3개 속성(등급 제외)으로 생성, 속성 리스트 생략 형태도 함께 제시. 이 뷰의 정의에 등급이 없으므로 WITH CHECK OPTION 동작은 강의 7-55와 속성 구성이 다르다 |
| 7-56 | 주석: GROUP BY 뷰는 MySQL에서 WITH CHECK OPTION이 실행 안 됨. 옵션 없이 `CREATE VIEW 업체별제품수(제조업체, 제품수) AS SELECT 제조업체, COUNT(*) FROM 제품 GROUP BY 제조업체;` 로 변경 |
| 7-57 | `SELECT * FROM 우수고객 WHERE 나이 >= 25;` (강의는 20), 이어서 제품1·제품2 뷰 생성 |
| 7-58 | `INSERT INTO 제품1 VALUES ('p08', 1000, '신선식품');` 후 제품1, 제품 조회 |
| 7-59 | `DROP VIEW 우수고객;` |

## 정리
- 실습에서 MySQL로 강의 SQL을 그대로 실행하되, CHECK 추가/삭제와 GROUP BY 뷰의 WITH CHECK OPTION만 강의와 다르게 처리했다 (Lab2-2 주석).
- 과제·시험에서는 강의 표기(07장)를 따르고, MySQL 실행 결과가 필요할 때만 이 문서의 차이를 참조한다.
