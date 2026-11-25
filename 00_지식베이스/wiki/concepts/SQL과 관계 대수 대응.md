---
name: SQL과 관계 대수 대응
english: SQL vs. Relational Algebra
chapter: 06장
pages: p.50-54
related: [셀렉트, 프로젝트, 조인, 카티션 프로덕트, 재명명, 외부 조인_06장]
---
## 정의
SQL 질의를 관계 대수 식으로 대응시킨 슬라이드 모음. SQL의 기본 틀은 SELECT {ColumnName(s)} FROM {TableName(s)} WHERE {Conditions}; 이며 모든 SQL문은 세미콜론(;)으로 끝난다. (p.50)

## 핵심 내용
- DML을 SQL문으로 전달해 RDBMS에서 데이터를 추출하는 구조: 클라이언트가 SQL문을 서버에 보내고, 서버가 DB에서 추출해 결과를 돌려준다. RDB는 데이터를 테이블로 관리한다. (p.50)
- 집계함수(sum, count, avg, min, max)는 관계 대수에서 F로 표기한다. group by는 F 앞에 그룹 속성을 아래첨자로 쓴다. (p.54)

## 예시
table E(nr, name, salary): (1,John,100), (5,Sarah,300), (7,Tom,100) (p.51)

| SQL | 관계 대수 |
|---|---|
| select DISTINCT salary from E; | π_DISTINCT(salary)(E) |
| select nr, salary from E; | π_nr,salary(E) |
| select * from E where salary < 200; | σ_salary<200(E) |
| select * from E where salary < 200 and nr >= 7; | σ_salary<200 and nr>=7(E) |
| select name, salary from E where salary < 200; | π_name,salary(σ_salary<200(E)) 또는 Temp ← σ_salary<200(E), Result ← π_name,salary(Temp) |

조인·곱 (p.52, E(enr,ename,dept), D(dnr,dname)): `select * from E, D where dept = dnr;` ↔ σ_dept=dnr(E × D) … E ⋈_dept=dnr D. `select * from E, D` ↔ E × D (9행).

속성 이름이 같은 경우 (p.53): `E as E(enr, ename, dept), D as D(dnr, dname)` ↔ (ρ_(enr, ename, dept)(E)) ⋈_dept=dnr (ρ_(dnr, dname)(D)). `where dept = D.nr` ↔ E ⋈_dept=D.nr D.

집계 (p.54, table E: (1,John,100,A), (5,Sarah,300,C), (7,Tom,100,A), (12,Anne,null,C)):
- count(salary) → 3, F_count(salary)(E)
- count(DISTINCT salary) → 2, F_count(salary)(π_DISTINCT(salary)(E))
- sum(salary) → 500, F_sum(salary)(E)
- group by dept 합계 → (A,200), (C,300), _dept F_sum(salary)(E)
- sum, count(*) group by dept → (A,200,2), (C,300,1)

## 흔한 실수/혼동
- p.53 두 번째 예에서 SQL 결과의 열은 nr, name, dept, nr, name으로 중복 이름이 그대로 나온다(원문 표).
- 집계의 F 기호와 아래첨자 위치는 슬라이드 표기를 따른다. 원문은 `_dept F_sum(salary)(E)` 형태.

## 출처
06장 p.50-54
