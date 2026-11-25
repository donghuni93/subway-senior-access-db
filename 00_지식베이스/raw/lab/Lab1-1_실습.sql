-- Lab1-1 MySQL 서버 실습
-- PDF "Lab1-1 MySQL 서버_2026.pdf" 8~15페이지 내용을 그대로 따라합니다.
-- VS Code Database Client 확장에서 이 파일을 열고,
-- 실행하고 싶은 줄(또는 블록)을 마우스로 드래그해서 선택한 뒤
-- Ctrl+Enter (또는 우클릭 > Run Query) 로 한 줄씩 실행해보세요.

-- 1. 데이터베이스 목록 확인
show databases;

-- 2. edb 데이터베이스 생성
create database edb;

-- 3. 다시 목록 확인 (edb가 추가된 것을 확인)
show databases;

-- 4. edb 데이터베이스를 사용하도록 전환
use edb;

-- 5. board 테이블 생성
create table board (
  no int not null auto_increment,
  name varchar(20) not null,
  subject varchar(100) not null,
  content text not null,
  password char(20) not null,
  primary key(no)
);

-- 6. 생성된 테이블 목록 확인
show tables;

-- 7. board 테이블 구조(속성) 확인
desc board;

-- 8. 레코드 삽입
insert into board (no, name, subject, content, password)
values (1, 'test', 'it is a test', 'just test', '1234');

-- 9. 레코드 검색
select * from board where no = 1;

-- 10. 레코드 삭제
delete from board where no = 1;

-- 11. 삭제 확인 (결과가 0행이면 정상)
select * from board where no = 1;
