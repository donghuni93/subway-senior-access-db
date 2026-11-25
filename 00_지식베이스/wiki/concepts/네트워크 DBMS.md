---
name: 네트워크 DBMS
english: Network DBMS
chapter: 02장
pages: p.17, 19
related: [계층 DBMS, DBMS의 발전 과정]
---
## 정의
네트워크 DBMS는 데이터베이스를 그래프 형태로 구성하는 1세대 DBMS이다. 예: IDS(Integrated Data Store).

## 핵심 내용
- (Recent Update, p.19) 자식이 여러 부모를 가질 수 있어 N:M 관계 지원. CODASYL이 1970년대 초반 표준화. Owner/Member, Set 구조, 물리적 포인터
- 단점(p.19): 설계 복잡('데이터 스파게티'), 구조 변경 시 포인터 수정, 사용자가 물리적 경로를 알아야 함

## 예시
그림 2-8(a) 네트워크 DBMS: 부서, 직원, 상품, 고객이 주문·판매·담당·관리·소속 관계로 그래프 연결.

## 흔한 실수/혼동
- 계층은 트리(자식의 부모 1개), 네트워크는 그래프(부모 여러 개)로 구분한다.

## 출처
02장 p.17, 19
