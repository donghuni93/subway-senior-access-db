#
# DUMP FILE
#
# Database is ported from MS Access 
#------------------------------------------------------------------
# Created using "MS Access to MySQL" form http://www.bullzip.com
# Program Version 5.3.259
#
# OPTIONS:
#   sourcefilename=F:\DaumCloud\??ì\EDB\edbLab1.accdb
#   sourceusername=
#   sourcepassword=
#   sourcesystemdatabase=
#   destinationdatabase=movedb
#   storageengine=MyISAM
#   dropdatabase=0
#   createtables=1
#   unicode=1
#   autocommit=1
#   transferdefaultvalues=1
#   transferindexes=1
#   transferautonumbers=1
#   transferrecords=1
#   columnlist=1
#   tableprefix=
#   negativeboolean=0
#   ignorelargeblobs=0
#   memotype=LONGTEXT
#

CREATE DATABASE IF NOT EXISTS `movedb`;
USE `movedb`;

#
# Table structure for table 'ORDER_ITEM'
#

DROP TABLE IF EXISTS `ORDER_ITEM`;

CREATE TABLE `ORDER_ITEM` (
  `ID` INTEGER NOT NULL AUTO_INCREMENT, 
  `OrderNumber` INTEGER, 
  `SKU` INTEGER, 
  `Quantity` INTEGER, 
  `Price` DECIMAL(19,4), 
  `ExtendedPrice` DECIMAL(19,4), 
  PRIMARY KEY (`ID`)
) ENGINE=myisam DEFAULT CHARSET=utf8;

SET autocommit=1;

#
# Dumping data for table 'ORDER_ITEM'
#

INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (1, 3000, 100200, 1, 300, 300);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (2, 2000, 101100, 4, 50, 200);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (3, 3000, 101100, 2, 50, 100);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (4, 2000, 101200, 2, 50, 100);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (5, 3000, 101200, 1, 50, 50);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (6, 1000, 201000, 1, 300, 300);
INSERT INTO `ORDER_ITEM` (`ID`, `OrderNumber`, `SKU`, `Quantity`, `Price`, `ExtendedPrice`) VALUES (7, 1000, 202000, 1, 130, 130);
# 7 records

#
# Table structure for table 'RETAIL_ORDER'
#

DROP TABLE IF EXISTS `RETAIL_ORDER`;

CREATE TABLE `RETAIL_ORDER` (
  `ID` INTEGER NOT NULL AUTO_INCREMENT, 
  `OrderNumber` INTEGER, 
  `StoreNumber` INTEGER, 
  `StoreZip` VARCHAR(255), 
  `OrderMonth` VARCHAR(255), 
  `OrderYear` VARCHAR(255), 
  `OrderTotal` DECIMAL(19,4), 
  PRIMARY KEY (`ID`)
) ENGINE=myisam DEFAULT CHARSET=utf8;

SET autocommit=1;

#
# Dumping data for table 'RETAIL_ORDER'
#

INSERT INTO `RETAIL_ORDER` (`ID`, `OrderNumber`, `StoreNumber`, `StoreZip`, `OrderMonth`, `OrderYear`, `OrderTotal`) VALUES (1, 1000, 10, '98110', 'December', '2003', 445);
INSERT INTO `RETAIL_ORDER` (`ID`, `OrderNumber`, `StoreNumber`, `StoreZip`, `OrderMonth`, `OrderYear`, `OrderTotal`) VALUES (2, 2000, 20, '02335', 'December', '2003', 310);
INSERT INTO `RETAIL_ORDER` (`ID`, `OrderNumber`, `StoreNumber`, `StoreZip`, `OrderMonth`, `OrderYear`, `OrderTotal`) VALUES (3, 3000, 10, '98110', 'January', '2004', 480);
# 3 records

#
# Table structure for table 'SKU_DATA'
#

DROP TABLE IF EXISTS `SKU_DATA`;

CREATE TABLE `SKU_DATA` (
  `ID` INTEGER NOT NULL AUTO_INCREMENT, 
  `SKU` INTEGER, 
  `SKU_Desciption` VARCHAR(255), 
  `Department` VARCHAR(255), 
  `Buyer` VARCHAR(255), 
  PRIMARY KEY (`ID`)
) ENGINE=myisam DEFAULT CHARSET=utf8;

SET autocommit=1;

#
# Dumping data for table 'SKU_DATA'
#

INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (1, 100100, 'Std, Scuba Tank, Yellow', 'Water Sports', 'Pete Hansen');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (2, 100200, 'Std, Scuba Tank, Magenta', 'Water Sports', 'Pete Hansen');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (3, 101100, 'Dive Mask, Small Clear', 'Water Sports', 'Nancy Meyers');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (4, 101200, 'Dive Mask, Med Clear', 'Water Sports', 'Nancy Meyers');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (5, 201000, 'Half-dome Tent', 'Camping', 'Cindy Lo');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (6, 202000, 'Half_dome Tent Footprint', 'Camping', 'Cindy Lo');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (7, 301000, 'Light Fly Climbing Harness', 'Climbing', 'Jerry Martin');
INSERT INTO `SKU_DATA` (`ID`, `SKU`, `SKU_Desciption`, `Department`, `Buyer`) VALUES (8, 302000, 'Locking carabiner, Oval', 'Climbing', 'Jerry Martin');
# 8 records

use movedb;
show tables;
select * from ORDER_ITEM;
select * from SKU_DATA;
