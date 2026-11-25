---
name: 계층 DBMS
english: Hierarchical DBMS
chapter: 02장
pages: p.17-18
related: [네트워크 DBMS, DBMS의 발전 과정]
---
## 정의
계층 DBMS는 데이터베이스를 트리 형태로 구성하는 1세대 DBMS이다. 예: IMS(Information Management System).

## 핵심 내용
- (Recent Update, p.18) 부모 하나가 여러 자식을 가질 수 있으나 자식은 반드시 하나의 부모만 가지는 1:N 관계
- 장점(p.18): 고속 처리, 일관성. 단점: 구조 변경 어려움, N:M 표현 불가, 루트부터 경로를 따라 탐색
- 1960년대 IBM IMS가 대표(p.18)

## 예시
그림 2-8(b) 계층 DBMS: 부서 - 직원, 상품 - 고객 등을 트리 형태로 연결(주문고객, 판매상품).

## 흔한 실수/혼동
- p.18은 Recent Update 슬라이드이며 p.17의 정의와 예(IMS)가 본문이다.

## 출처
02장 p.17-18
