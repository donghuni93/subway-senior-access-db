# Lab1-1 MySQL 서버_2026

---

## p.1

Lab.1
MySQL DBMS(서버)
◦ MySQL 설치
◦ MySQL 사용
◦ MySQL Workbench 사용

---

## p.2

MySQL 설치

---

## p.3

MySQL 설치

■ MySQL 이란?
▪ 전세계적으로 600만 사용자를 확보하고 있는 관계형 데이터베이스 관리시스템(Relational DBMS)이며, 응용 프로그램에서 MySQL 데이터베이스에 접근하기 위해 C/C++/C#, Java, PHP 등의 프로그래밍 언어로 된 API(Application Programming Interface) 제공함.

■ MySQL 장점
▪ 무료로 사용 가능하며, 소스 코드가 공개되어 있어 자유롭게 수정이 가능함.
▪ 뛰어난 안정성과 확장성을 갖추고 있음.
▪ 대용량 데이터 처리와 병렬 처리를 지원함.
▪ 다양한 운영 체제에서 사용할 수 있고, 다양한 프로그래밍 언어와 연동하여 사용할 수 있음. (예: PHP를 이용한 웹 개발에서 사용)
▪ 인기가 높아, 커뮤니티가 활발하게 운영되고 있어 다양한 정보와 지원을 받을 수 있음.

■ MySQL 단점
▪ 사용자 정의 함수 사용이 어렵고 유연하지 않음
▪ 데이터를 처리할 때에는 단일 쓰레드로 처리하기 때문에 병렬 처리에 대한 제한이 있음
▪ 수평적 스케일링(Scale-out)이 어렵다.

3

---

## p.4

MySQL 설치

■ APM(Apache Php Mysql) 개발 환경
▪ web server(apache)는 php파일을 처리하지 못하므로 php에게 보낸다.
▪ php파일에는 데이터베이스에 요청을 보내는 코드가 적혀있다.
▪ php는 mysql에게 query를 보낸다.
▪ php는 결과를 받아서 html 형태로 바꾸고 web server(apache)에게 보낸다.
▪ web server(apache)는 web browser에게 받은 데이터를 html보낸다.

[다이어그램: 모니터 아이콘 <-> Apache <-> PHP <-> MySql, 양방향 화살표]
Apache
php
PHP
MySQL
MySql

4

---

## p.5

별첨.

Windows 환경에서 MySQL을 설치하는 가장 안정적인 방법은 MySQL Installer를 사용하는 것입니다.
초보자부터 전문가까지 설정 과정을 시각적으로 확인하며 진행할 수 있습니다.

1. MySQL Installer 다운로드
1. MySQL 공식 다운로드 페이지에 접속합니다.
2. 두 가지 버전 중 용량이 큰 **(mysql-installer-community-x.x.x.msi)**를 선택하여 다운로드합니다. (웹 설치 버전보다 전체 설치 버전이 중간에 끊김 없이 안정적입니다.)
3. 로그인 창이 뜨면 하단의 **"No thanks, just start my download."**를 클릭합니다.

2. 설치 단계별 가이드

① 설치 타입 선택 (Choosing a Setup Type)
설치 프로그램을 실행하면 타입을 선택하는 화면이 나옵니다.
• Developer Default: 개발에 필요한 모든 도구 설치 (권장)
• Server only: MySQL 서버만 설치
• Custom: 원하는 구성 요소만 직접 선택

② 요구사항 확인 및 설치 (Check Requirements & Installation)
필요한 시각적 라이브러리(C++ Redistributable 등)가 없다면 자동으로 리스트가 뜹니다. **[Execute]**를 눌러 필요한 프로그램을 먼저 설치한 뒤, MySQL 구성 요소들을 설치합니다.

③ 서버 설정 (Type and Networking)
• Config Type: 'Development Computer'로 둡니다.
• Connectivity: TCP/IP가 체크되어 있는지 확인하고, 포트 번호가 3306인지 확인합니다.

[스크린샷: 브라우저 dev.mysql.com/downloads/installer/]
dev.mysql.com/downloads/installer/
MySQL Community Downloads
MySQL Installer
General Availability (GA) Releases | Archives
MySQL Installer 8.0.45
Note: MySQL 8.0 is the final series with MySQL Installer. As of MySQL 8.1, use a MySQL product's MSI or Zip archive for installation. MySQL Server 8.1 and higher also bundle MySQL Configurator, a tool that helps configure MySQL Server.
Select Version:
8.0.45
Select Operating System:
Microsoft Windows
Windows (x86, 32-bit), MSI Installer | 8.0.45 | 2.1M | Download
(mysql-installer-web-community-8.0.45.0.msi) | MD5: c221d45c90c003b585b9570edc46a8ad | Signature
Windows (x86, 32-bit), MSI Installer | 8.0.45 | 556.0M | Download
(mysql-installer-community-8.0.45.0.msi) | MD5: 2e6a5e6e9425700a3d066f185992e2ad | Signature
We suggest that you use the MD5 checksums and GnuPG signatures to verify the integrity of the packages you download.
[붉은 점선 화살표가 두 번째 Download 버튼을 가리킴]

5

---

## p.6

별첨.

④ 계정 및 비밀번호 설정 (Authentication Method)
• Root Password: 데이터베이스의 최고 관리자 비밀번호를 설정합니다. (절대 잊어버리면 안 됩니다!)
• MySQL User: 일반 사용자 계정을 추가할 수 있으나, 처음에는 Root 계정만 설정하고 넘어가도 무방합니다.

⑤ 윈도우 서비스 설정 (Windows Service)
MySQL이 윈도우 시작 시 자동으로 실행되도록 설정하는 단계입니다. 기본값 그대로 **[Next]**를 누릅니다.

3. 환경 변수 설정 (터미널 사용을 위한 필수 단계)
검색창이나 명령 프롬프트(CMD)에서 mysql 명령어를 바로 사용하려면 경로를 등록해야 합니다.
1. MySQL 설치 경로 복사: 보통 C:\Program Files\MySQL\MySQL Server 8.x\bin 입니다.
2. 시스템 환경 변수 편집: 윈도우 검색창에 '계정의 환경 변수 편집'을 검색해 실행합니다.
3. Path 수정: '시스템 변수' 항목에서 Path 를 찾아 선택하고 [편집] -> [새로 만들기]를 눌러 복사한 경로를 붙여넣습니다.

4. 설치 확인
1. 명령 프롬프트(CMD)를 엽니다.
2. mysql -u root -p 를 입력합니다.
3. 설정한 비밀번호를 입력했을 때 **"Welcome to the MySQL monitor"**라는 문구가 나오면 성공입니다!
[붉은 타원이 "mysql -u root -p" 항목을 강조]

[스크린샷: MySQL Installer 창]
MySQL Installer
MySQL. Installer
Adding Community
Choosing a Setup Type
Installation
Product Configuration
Installation Complete
Installation
The following products will be installed.
Product | Arch | Status | Progress | Notes
MySQL Server 8.0.45 | X64 | Complete
MySQL Workbench 8.0.46 | X64 | Complete
MySQL Shell 8.0.45 | X64 | Installing | 43%
MySQL Router 8.0.45 | X64 | Ready to Install
MySQL Documentation 8.0.45 | X86 | Ready to Install
Samples and Examples 8.0.45 | X86 | Ready to Install
Show Details >
< Back | Execute | Cancel

6

---

## p.7

MySQL 사용

---

## p.8

MySQL 사용(Terminal)
MySQL 사용

■ 데이터베이스 생성
▪ mysql >  show databases;
▪ mysql >  create database edb;

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
| @@datadir                          |
+------------------------------------+
| C:\AutoSet9\Server\MySQL5\Data\    |
+------------------------------------+
1 row in set (0.00 sec)

mysql> drop database edb;
Query OK, 0 rows affected (0.00 sec)

mysql>
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| test               |
+--------------------+
4 rows in set (0.00 sec)

mysql> create database edb;
Query OK, 1 row affected (0.00 sec)

mysql>
[붉은 사각형이 "show databases;"와 "create database edb;"를 강조]

8

---

## p.9

MySQL 사용(Terminal)
MySQL 사용

■ 데이터베이스 사용
▪ mysql >  show databases;
▪ mysql >  use edb;

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
mysql>
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| test               |
+--------------------+
4 rows in set (0.00 sec)

mysql> create database edb;
Query OK, 1 row affected (0.00 sec)

mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| edb                |
| mysql              |
| performance_schema |
| test               |
+--------------------+
5 rows in set (0.00 sec)

mysql> use edb;
Database changed
mysql>
[붉은 사각형이 "show databases;"와 "use edb;"를 강조]

9

---

## p.10

MySQL 사용(Terminal)
MySQL 사용

■ 테이블 생성
▪ mysql> create table board (no int not null auto_increment, name varchar(20) not null, subject varchar(100) not null, content text not null, password char(20) not null, primary key(no));

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
| performance_schema |
| test               |
+--------------------+
5 rows in set (0.00 sec)

mysql> use edb;
Database changed
mysql> create table board (
    ->  no int not null auto_increment,
    -> name varchar(20) not null,
    -> subject varchar(100) not null,
    -> content text not null,
    -> password char(20) not null,
    -> primary key(no));
Query OK, 0 rows affected (0.03 sec)
[붉은 사각형이 create table 문 전체를 강조]

10

---

## p.11

MySQL 사용(Terminal)
MySQL 사용

■ 생성된 테이블 보기
▪ mysql >  show tables;

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
mysql> use edb;
Database changed
mysql> create table board (
    ->  no int not null auto_increment,
    -> name varchar(20) not null,
    -> subject varchar(100) not null,
    -> content text not null,
    -> password char(20) not null,
    -> primary key(no));
Query OK, 0 rows affected (0.03 sec)

mysql> show tables;
+----------------+
| Tables_in_edb  |
+----------------+
| board          |
+----------------+
1 row in set (0.00 sec)

mysql>
[붉은 사각형이 "show tables;"를 강조]

11

---

## p.12

MySQL 사용(Terminal)
MySQL 사용

■ 테이블 속성 보기
▪ mysql >  desc board;

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
mysql>
mysql>
mysql> show tables;
+---------------+
| Tables_in_edb |
+---------------+
| board         |
+---------------+
1 row in set (0.00 sec)

mysql> desc board;
Field | Type | Null | Key | Default | Extra
no | int(11) | NO | PRI | NULL | auto_increment
name | varchar(20) | NO |  | NULL |
subject | varchar(100) | NO |  | NULL |
content | text | NO |  | NULL |
password | char(20) | NO |  | NULL |
5 rows in set (0.01 sec)
[붉은 사각형이 "desc board;"를 강조]

12

---

## p.13

MySQL 사용(Terminal)
MySQL 사용

■ 레코드 삽입
▪ mysql >  insert into board (no, name, subject, content, password) values (1, 'test', 'it is a test', 'just test', '1234');

[스크린샷: 터미널 창]
C:\AutoSet9\Server\MySQL5\bin\mysql.exe
mysql> desc board;
Field | Type | Null | Key | Default | Extra
no | int(11) | NO | PRI | NULL | auto_increment
name | varchar(20) | NO |  | NULL |
subject | varchar(100) | NO |  | NULL |
content | text | NO |  | NULL |
password | char(20) | NO |  | NULL |
5 rows in set (0.01 sec)

mysql> insert into board (no, name, subject, content, password) values (1, 'test', 'it is a test', 'just test', '1234');
Query OK, 1 row affected (0.01 sec)
[붉은 사각형이 insert 문을 강조]

13

---

## p.14

MySQL 사용(Terminal)
MySQL 사용

레코드 검색
mysql > select * from board where no=1;

[터미널 창 스크린샷: C:\AutoSet9\Server\MySQL5\bin\mysql.exe]
mysql> insert into board (no, name, subject, content, password) valu
es (1, 'test', 'it is a test', 'just test', '1234');
Query OK, 1 row affected (0.01 sec)

mysql> select * from board where no=1;   [빨간 박스 강조]
+----+------+--------------+-----------+----------+
| no | name | subject      | content   | password |
+----+------+--------------+-----------+----------+
|  1 | test | it is a test | just test | 1234     |
+----+------+--------------+-----------+----------+
1 row in set (0.00 sec)

14

---

## p.15

MySQL 사용(Terminal)
MySQL 사용

레코드 삭제
mysql > delete from board where no=1;

[터미널 창 스크린샷: C:\AutoSet9\Server\MySQL5\bin\mysql.exe]
mysql> select * from board where no=1;
+----+------+--------------+-----------+----------+
| no | name | subject      | content   | password |
+----+------+--------------+-----------+----------+
|  1 | test | it is a test | just test | 1234     |
+----+------+--------------+-----------+----------+
1 row in set (0.00 sec)

mysql>
mysql> delete from board where no=1;   [빨간 박스 강조]
Query OK, 1 row affected (0.00 sec)

mysql>

[MySQL 콘솔창] 종료
mysql > exit

15

---

## p.16

MySQL Workbench 사용

---

## p.17

Workbench 사용
MySQL Workbench 사용

MySQL Workbench는 SQL 개발과 관리, 데이터베이스 설계, 생성 그리고 유지를 위한 단일 개발 통합 환경을 제공하는 비주얼 데이터베이스 설계 도구임.

Windows 실행창 화면을 통해 “MySQL Workbench” 프로그램을 실행하면, 다음과 같은 홈 화면이 뜨며, Local instance 3306을 클릭하여 MySQL DBMS와 연결한 후, “root”  User의 Password 를 입력한다.
MySQL Workbench는 SQL 개발과 관리, 데이터베이스 설계, 생성 그리고 유지를 위한 단일 개발 통합 환경을 제공하는 비주얼 데이터베이스 설계 도구임.

[스크린샷 1: MySQL Workbench 홈 화면]
MySQL Workbench
File Edit View Database Tools Scripting Help
Welcome to MySQL Workbench
MySQL Workbench is the official graphical user interface (GUI) tool for MySQL. It allows you to design, create and browse your database schemas, work with database objects and insert data as well as design and run SQL queries to work with stored data. You can also migrate schemas and data from other database vendors to your MySQL database.
Browse Documentation > | Read the Blog > | Discuss on the Forums >
MySQL Connections ⊕⊗   [빨간 박스 강조]
Local instance 3306
root
localhost:3306
Ready.

[스크린샷 2: 대화상자]
Connect to MySQL Server
Please enter password for the following service:
Service: Mysql@localhost:3306
User: root
Password:
Save password in keychain
OK | Cancel

17

---

## p.18

MySQL Workbench 사용

DB에 접속이 된 화면

[스크린샷: MySQL Workbench 관리 화면 - Administration - Server Status]
MySQL Workbench
unconnected
File Edit View Query Database Server Tools Scripting Help
Navigator
MANAGEMENT
Server Status
Client Connections
Users and Privileges
Status and System Variables
Data Export
Data Import/Restore
INSTANCE
Startup / Shutdown
Server Logs
Options File
PERFORMANCE
SCHEMAS
Filter objects
test
Information
Connection:
Name:
Host: localhost
Port: 3306
Server: MySQL Community Server (GPL)
Version: 5.6.20
Login User: root
Object Info | Session
Query 1 | Administration - Server Status
Connection Name
Host: baek-labtop
Socket: C:/AutoSet9/Server/temp/mysql.sock
Port: 3306
Version: 5.6.20 MySQL Community Server (GPL)
Compiled For: Win64 (x86_64)
Configuration File: C:₩Program Files₩MySQL₩MySQL Server 5.0₩my.ini
Running Since: Thu Mar 19 12:52:20 2015 (0:23)
Refresh
Available Server Features
Performance Schema: On | SSL Availability: Off
Thread Pool: n/a | Windows Authentication: Off
Memcached Plugin: n/a | Password Validation: n/a
Semisync Replication Plugin: n/a | Audit Log: n/a
Server Directories
Base Directory: C:/AutoSet9/Server/MySQL5/
Data Directory: C:₩AutoSet9₩Server₩MySQL5₩Data₩
Disk Space in Data Dir: 37.00 GB of 118.00 GB available
InnoDB Data Directory: C:₩AutoSet9₩Server₩MySQL5₩Data₩
Plugins Directory: C:₩AutoSet9₩Server₩MySQL5₩lib₩plugin₩
Tmp Directory: C:₩Windows₩TEMP
Error Log: On C:₩AutoSet9₩Server₩MySQL5₩Data₩baek-labtop.err
General Log: Off
Slow Query Log: Off
Replication Slave
this server is not a slave in a replication setup
Authentication
SHA256 password private key: n/a
SHA256 password public key: n/a
Server Status Running | CPU 12% | Connections 3
Traffic 0.0 B/s | Key Efficiency 0.0%
Selects per Second 0 | InnoDB Buffer Usage 28.9%
InnoDB Reads per Second 0 | InnoDB Writes per Second 0

18

---

## p.19

MySQL Workbench 사용

메뉴상단의 “Open SQL Script” 버튼을 눌러서 “Lab1-2 SQL(Workbench)”을 로드한다(Open).

[스크린샷 1: Workbench 상단 메뉴/툴바, 두 번째 아이콘 빨간 박스 강조]
unconnected
File Edit View Query Database Server Tools Scripting Help
Navigator | Query 1
MANAGEMENT

[스크린샷 2: Open SQL Script 파일 대화상자]
MySQL Workbench
Local instance AutoSet9_MyS..
File Edit View Query Database Server Tools Scripting Help
Navigator
MANAGEMENT
Server Status
Client Connections
Users and Privileges
Status and System Variables
Data Export
Data Import/Restore
INSTANCE
Startup / Shutdown
Server Logs
Options File
PERFORMANCE
Dashboard
Performance Reports
Administration | Schemas
Information
No object selected
Object Info | Session
Open SQL Script
« 1. 강의 > EDB-07장-Lab
EDB-07장-Lab 검색
구성 ▾ | 새 폴더
바로 가기
바탕 화면
다운로드
Google 드라이브
문서
사진
1. 강의
Chap. 2
EDB-07장-Lab
Project
이름 | 수정한 날짜 | 유형
Lab-SQL | 2018-04-03 오전... | SQL Text File
파일 이름(N): Lab-SQL | SQL Files (*.sql)
열기(O) | 취소
SQL Additions
Jump to
Snippets

19

---

## p.20

MySQL Workbench 사용

옵션설정 창이 뜨면 OK를 누른다.

[스크린샷: Open SQL File 대화상자]
Open SQL File
Unknown File Encoding
The file 'C:₩Users₩Baek₩Documents₩sample.sql' is not UTF-8 encoded.
Please select the encoding of the file and press OK for Workbench to convert and open it.
Note that as Workbench works with UTF-8 text, if you save back to the original file,
its contents will be replaced with the converted data.
WARNING: If your file contains binary data, it may become corrupted.
Click "Run SQL Script..." to execute the file without opening for editing.
Character Set Encoding Name: latin1
Run SQL Script... | OK | Cancel

20

---

## p.21

MySQL Workbench 사용

“Lab1- 2  SQL(Workbench)” 스크립트가 로드되면 좌측 상단의 Query 실행 버튼(번개모양) 을 누른다.
실행 결과로 “movedb” 가 생성됨.

[MySQL 콘솔창]에서 실습했던 SQL 명령을 응용하여, MySQL Workbench에서 “movedb”를 대상으로 SQL 명령을 반복 실습한다.

[스크린샷: MySQL Workbench 쿼리 편집기, 번개 아이콘 빨간 박스 강조]
MySQL Workbench
Scripting Help
Query 1 | sample | Administration - Server Status | sample
Limit to 1000 rows
33
34 #
35 # Table structure for table 'ORDER_ITEM'
36 #
37
38 DROP TABLE IF EXISTS `ORDER_ITEM`;
39
40 CREATE TABLE `ORDER_ITEM` (
41   `ID` INTEGER NOT NULL AUTO_INCREMENT,
42   `OrderNumber` INTEGER,
43   `SKU` INTEGER,
44   `Quantity` INTEGER,
45   `Price` DECIMAL(19,4),
46   `ExtendedPrice` DECIMAL(19,4),
47   PRIMARY KEY (`ID`)
48 ) ENGINE=myisam DEFAULT CHARSET=utf8;
49
50 SET autocommit=1;
51
52 #
53 # Dumping data for table 'ORDER_ITEM'
54 #
55
56 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
57 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
58 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
59 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
60 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
61 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
62 INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPric
63 # 7 records
64
65 #
66 # Table structure for table 'RETAIL_ORDER'
Output
SQL Ad..
Auto.. toolb.. positi..
Context

21

---

## p.22

Thank You

---

## p.23

별첨.

1. 별첨자료
https://drive.google.com

2. 별첨자료
https://drive.google.com

3. 별첨자료
https://drive.google.com

23

---

## p.24

Recent Update

24

---

## p.25

별첨.

[다이어그램: Scale Up — 작은 서버에서 중간 서버, 큰 서버로 화살표 순서로 커짐]
Scale Up

스케일 업 (Scale-up)
물리적인 성능 향상 (cpu나 memory 등)
고비용, 고효율
수직 스케일링 (vertical scaling)
단순하거나 빠른 작업(DB 갱신 자주 일어나야 하는 경우)에 적합
- 이런 경우 스케일 아웃에서는 데이터 정합성을 유지하기 어렵기 때문이다

<장점>
상대적으로 쉽다 (사양만 올리면 되기 때문에)
낮은 관리 비용
적은 관리 이슈
데이터 정합성 이슈 발생 가능성이 적다

<단점>
성능 향상에 한계가 있다
서버 1대가 분담하는 양이 많아져서 문제가 생기면 큰 타격
서버 교체나 업그레이드 시에 서비스 이용이 어려울 수 있다 (다운타임)

25

---

## p.26

별첨.

[다이어그램: Scale Out — 동일한 서버 4대가 + 기호로 연결됨]
Scale Out

스케일 아웃 (Scale-out)
비슷한 사양의 서버를 추가로 연결
데이터 분석처럼 복잡한 작업에 더 적합
수평 스케일링 (horizontal scaling)

<장점>
확장에 용이 (확장의 유연성, 단계적인 확장 가능)
확장 비용이 상대적으로 적다

<단점>
관리하기 어렵고 관리 비용이 많이 든다 (데이터 정합성을 유지하기 위한 설계, 구축 비용 크다)
노드를 병렬 구조로 연결하기에 아키텍처에 대한 높은 이해도를 필요로 하고 이를 위해 로드 밸런싱이 필수다
데이터 정합성 이슈 발생 가능성이 커진다 (모든 서버에서 데이터 일관성 유지해야 하므로)

26
