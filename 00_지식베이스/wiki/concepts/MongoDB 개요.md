---
name: MongoDB 개요
english: MongoDB overview
chapter: 09장
pages: p.64-67
related: [NoSQL DBMS, 커서]
---
## 정의
C++로 작성된 오픈소스 문서 지향(Document-Oriented) Cross-platform 데이터베이스이며 뛰어난 확장성과 성능을 가진다 (별첨2, p.65).

## 핵심 내용
- 구조(p.65): mongos, mongod, Config Servers 3가지. Client ↔ mongos ↔ Config Server(메타데이터: Shard data 정보, Mongos 상태, 이벤트 변경 로그), mongos ↔ mongod(Shard Server, 각 Primary 1·Secondary 2). Master 노드 문제 시 Arbiter를 통해 Secondary → Master 전환.
- 용어 대응(p.66):

| MongoDB | RDBMS |
|---|---|
| 데이터베이스(Database) | 데이터베이스(Database) |
| 컬렉션(Collection) | 테이블(Table) |
| 도큐먼트(Document) | 레코드(Record OR Row) |
| 필드(Field) | 컬럼(Column) |
| 인덱스(Index) | 인덱스(Index) |
| 쿼리 결과로 "커서(Cursor)" 반환 | 쿼리 결과로 "레코드(Record)" 반환 |

- 도큐먼트 예(Posts): _id, title("Welcome to MongoDB"), body, published(true), created, updated, tags(["databases","MongoDB","awesome"]), comments(comment_id, author "Bob", email, body, created) 중첩 배열. [판독 불확실] p.66 JSON 예시 일부 글자는 해상도가 낮아 원문 표기를 그대로 확정할 수 없다.
- 검색(p.67): `db.patient.find({name: "Chloe"})`. 결과 4개 도큐먼트가 모두 name 'Chloe', age 24이고 email, diseases(['Covid-19', 'Colorectal Cancer']), cure(false) 필드가 있는 문서와 없는 문서가 섞여 있다(필드 구성이 도큐먼트마다 다름).

## 예시
위 find 결과가 예시이다. 스키마 없이 문서별 필드가 다를 수 있다는 해석은 [강의 범위 밖] 일반 설명이며 원문은 출력만 제시한다.

## 흔한 실수/혼동
컬렉션=테이블, 도큐먼트=레코드 대응이며 쿼리 결과는 커서다.

## 출처
09장 p.64-67
