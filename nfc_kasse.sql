/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admins` (
  `username` varchar(20) NOT NULL,
  `password` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `otps` varchar(32) DEFAULT NULL,
  `otp_validated` tinyint(1) NOT NULL DEFAULT 0,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

-- admin : changeme
INSERT INTO `admins` VALUES ('admin','$2b$12$GBF3.7raScFvBqQHC.bb6u0eIEBmmVr6aV619vnXU1AebvI28nndm', NULL, 0, 1);

--
-- Table structure for table `eventlog`
--

DROP TABLE IF EXISTS `eventlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `eventlog` (
  `eid` int(11) NOT NULL AUTO_INCREMENT,
  `edate` datetime NOT NULL DEFAULT current_timestamp(),
  `user` varchar(20) NOT NULL,
  `action` text DEFAULT NULL,
  PRIMARY KEY (`eid`),
  KEY `user` (`user`),
  CONSTRAINT `eventlog_ibfk_1` FOREIGN KEY (`user`) REFERENCES `admins` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cards`
--

DROP TABLE IF EXISTS `cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cards` (
  `uid` varchar(32) NOT NULL,
  `value` decimal(7,2) unsigned NOT NULL DEFAULT 0.00,
  `registered_on` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product_categories`
--

DROP TABLE IF EXISTS `product_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_categories` (
  `name` varchar(30) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `products` (
  `ean` varchar(20) unsigned NOT NULL,
  `name` varchar(30) NOT NULL,
  `price` decimal(4,2) NOT NULL,
  `stock` int(10) NOT NULL DEFAULT 0,
  `category` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`ean`),
  KEY `category` (`category`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`category`) REFERENCES `product_categories` (`name`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `product_alias`
--

DROP TABLE IF EXISTS `product_alias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_alias` (
  `ean` varchar(20) NOT NULL,
  `target` varchar(20) NOT NULL,
  PRIMARY KEY (`ean`),
  KEY `target` (`target`),
  CONSTRAINT `product_alias_ibfk_1` FOREIGN KEY (`target`) REFERENCES `products` (`ean`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `topups`
--

DROP TABLE IF EXISTS `topups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `topups` (
  `code` varchar(32) NOT NULL,
  `value` decimal(6,2) NOT NULL,
  `used` tinyint(1) NOT NULL DEFAULT 0,
  `created_on` datetime NOT NULL,
  `created_by` varchar(20) NOT NULL,
  `used_on` datetime DEFAULT NULL,
  `used_by` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`code`),
  KEY `used_by` (`used_by`),
  CONSTRAINT `topups_ibfk_1` FOREIGN KEY (`used_by`) REFERENCES `cards` (`uid`),
  CONSTRAINT `topups_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `admins` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transactions` (
  `tid` int(11) NOT NULL AUTO_INCREMENT,
  `uid` varchar(32) NOT NULL,
  `ean` varchar(20) unsigned DEFAULT NULL,
  `topupcode` varchar(32) DEFAULT NULL,
  `exchange_with_uid` varchar(32) DEFAULT NULL,
  `value` decimal(5,2) NOT NULL,
  `tdate` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`tid`),
  KEY `ean` (`ean`),
  KEY `uid` (`uid`),
  KEY `exchange_with_uid` (`exchange_with_uid`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`ean`) REFERENCES `products` (`ean`) ON UPDATE CASCADE,
  CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`uid`) REFERENCES `cards` (`uid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `transactions_ibfk_3` FOREIGN KEY (`exchange_with_uid`) REFERENCES `cards` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
