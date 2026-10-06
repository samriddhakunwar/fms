-- ===========================================================================
-- Factory Management System (fms_db) — schema
-- Generated from the live local MySQL database via SHOW CREATE TABLE.
-- Matches manage.py migrate exactly — verified column-for-column,
-- index-for-index, constraint-for-constraint against a fresh migrate run.
--
-- Table names are the readable ones set via Meta.db_table / db_table on the
-- M2M fields (activity_log, admin, customer_order, customer_order_item,
-- manager, product, sale, sale_item, sales_report, staff, stock_movement,
-- user, user_group, user_permission).
-- Django's own auth_*/django_* tables keep their framework names.
--
-- Orders and sales are separate tables on purpose: an order records what the
-- customer asked for and moves no stock, and `sale`.`order_id` points back at
-- the order an invoice was raised from (NULL for a direct sale).
--
-- ROLES. `user` is the single login table. Each Admin / Manager account has
-- one row in `admin` / `manager`; `staff` is the employee (HR) table, linked
-- one-to-one to a STAFF login through `staff`.`user_id` (UNIQUE).
-- Who-did-what columns point at the ROLE table, not at `user`. Where an Admin
-- or a Manager may do the same thing there is one FK to each, and a CHECK
-- (`*_one_role`) allows at most one to be set. All of them are nullable and
-- SET NULL on delete in Django, so removing an account never blocks on its
-- history; NULL also means "recorded before this was tracked".
--
-- FUNCTIONAL REQUIREMENTS -> TABLES / FOREIGN KEYS
--
--   All roles: log in and log out (securely)
--     `user` (login), `activity_log`.`user_id` -> `user`
--     (action LOGIN / LOGOUT / LOGIN_FAILED, role, ip_address)
--
--   Admin: create and manage Manager and Staff accounts
--     `manager`.`created_by_admin_id` -> `admin`
--     `staff`.`created_by_admin_id`   -> `admin`
--
--   Admin, Manager: add / view / update / delete stock items and quantities
--     `product`.`created_by_admin_id` -> `admin`,
--     `product`.`created_by_manager_id` -> `manager`   (product_created_by_one_role)
--     `product`.`updated_by_admin_id` -> `admin`,
--     `product`.`updated_by_manager_id` -> `manager`   (product_updated_by_one_role)
--     `stock_movement`.`admin_id` -> `admin`,
--     `stock_movement`.`manager_id` -> `manager`       (stock_movement_one_role)
--     `stock_movement`.`product_id` -> `product` (CASCADE), `sale_id` -> `sale`
--
--   Admin: add / view / update / delete orders;
--   Manager: add / view / delete orders
--     `customer_order`.`created_by_admin_id` -> `admin`,
--     `customer_order`.`created_by_manager_id` -> `manager`
--                                     (customer_order_created_by_one_role)
--     (replaces the old created_by_id -> `user`; orders/0004 copied it by role)
--
--   Admin: add / view / update / delete sales   (Manager: view only, so no
--   manager FK on sale)
--     `sale`.`created_by_admin_id` -> `admin`
--     `sale`.`updated_by_admin_id` -> `admin`
--
--   Admin, Manager: generate sales reports
--     `sales_report`.`admin_id` -> `admin`,
--     `sales_report`.`manager_id` -> `manager`         (sales_report_one_role)
--     CHECK sales_report_start_before_end (start_date <= end_date)
--
--   Manager: view Staff records
--     `staff`.`manager_id` -> `manager` (who each staff member reports to)
--     `activity_log` VIEW rows, target 'staff'
--
--   Manager: view sales records only
--     `activity_log` VIEW rows, target 'sale'
--
--   Staff: view their own employee profile
--     `staff`.`user_id` -> `user` (UNIQUE, one-to-one)
--     `activity_log` VIEW rows, target 'staff'
--
--   Staff: view inventory stock levels
--     `product`.`quantity_in_stock`, `activity_log` VIEW rows, target 'product'
--
-- Run with:
--   mysql -u root -p < database_schema.sql
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS `fms_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `fms_db`;

SET FOREIGN_KEY_CHECKS = 0;


-- -------------------------------------------------------------------------
-- Django built-in tables
-- -------------------------------------------------------------------------

CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- accounts app (custom user model)
-- -------------------------------------------------------------------------

CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `phone_number` varchar(20) NOT NULL,
  `role` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_group` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_permission` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Logins, logouts, failed logins and read-only views for all three roles.
-- `role` is copied at the time so the entry keeps its meaning if the
-- account's role changes later; user_id is NULL for an unknown username.
CREATE TABLE `activity_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `action` varchar(20) NOT NULL,
  `target` varchar(50) NOT NULL,
  `object_id` bigint unsigned DEFAULT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `activity_log_user_created_idx` (`user_id`,`created_at`),
  CONSTRAINT `activity_log_user_id_f1e09264_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `activity_log_chk_1` CHECK ((`object_id` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- Role tables. `user` above is the single login table (one password, one
-- session login for everyone); each account also has exactly one record in
-- the table for its role. Admin and Manager rows are created automatically
-- with the account. `staff` is the employee/HR table (formerly `employee`,
-- renamed in place by employees/0005 so ids were kept); its user_id is
-- optional because some staff have no login, and only STAFF accounts may be
-- linked. The FK keeps its original `employee_` name from before the rename,
-- which is also what a fresh migrate produces.
-- -------------------------------------------------------------------------

CREATE TABLE `admin` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `admin_user_id_8a7d8779_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `manager` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  `created_by_admin_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `manager_created_by_admin_id_591e6234_fk_admin_id` (`created_by_admin_id`),
  CONSTRAINT `manager_created_by_admin_id_591e6234_fk_admin_id` FOREIGN KEY (`created_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `manager_user_id_03d26107_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `staff` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `full_name` varchar(255) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `address` longtext NOT NULL,
  `designation` varchar(100) NOT NULL,
  `joining_date` date NOT NULL,
  `salary` decimal(12,2) NOT NULL,
  `status` varchar(10) NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `created_by_admin_id` bigint DEFAULT NULL,
  `manager_id` bigint DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `staff_created_by_admin_id_52387d7c_fk_admin_id` (`created_by_admin_id`),
  KEY `staff_manager_id_180ce6db_fk_manager_id` (`manager_id`),
  CONSTRAINT `employee_user_id_cc4f5a1c_fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `staff_created_by_admin_id_52387d7c_fk_admin_id` FOREIGN KEY (`created_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `staff_manager_id_180ce6db_fk_manager_id` FOREIGN KEY (`manager_id`) REFERENCES `manager` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- inventory app
-- -------------------------------------------------------------------------

CREATE TABLE `product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `product_name` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `sku` varchar(100) NOT NULL,
  `selling_price` decimal(12,2) NOT NULL,
  `quantity_in_stock` int unsigned NOT NULL,
  `minimum_stock_level` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_by_admin_id` bigint DEFAULT NULL,
  `created_by_manager_id` bigint DEFAULT NULL,
  `updated_by_admin_id` bigint DEFAULT NULL,
  `updated_by_manager_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `product_created_by_admin_id_28bae7e1_fk_admin_id` (`created_by_admin_id`),
  KEY `product_created_by_manager_id_dcce9cc3_fk_manager_id` (`created_by_manager_id`),
  KEY `product_updated_by_admin_id_f217b439_fk_admin_id` (`updated_by_admin_id`),
  KEY `product_updated_by_manager_id_3181fb75_fk_manager_id` (`updated_by_manager_id`),
  CONSTRAINT `product_created_by_admin_id_28bae7e1_fk_admin_id` FOREIGN KEY (`created_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `product_created_by_manager_id_dcce9cc3_fk_manager_id` FOREIGN KEY (`created_by_manager_id`) REFERENCES `manager` (`id`),
  CONSTRAINT `product_updated_by_admin_id_f217b439_fk_admin_id` FOREIGN KEY (`updated_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `product_updated_by_manager_id_3181fb75_fk_manager_id` FOREIGN KEY (`updated_by_manager_id`) REFERENCES `manager` (`id`),
  CONSTRAINT `product_chk_1` CHECK ((`quantity_in_stock` >= 0)),
  CONSTRAINT `product_chk_2` CHECK ((`minimum_stock_level` >= 0)),
  CONSTRAINT `product_created_by_one_role` CHECK (((`created_by_admin_id` is null) or (`created_by_manager_id` is null))),
  CONSTRAINT `product_updated_by_one_role` CHECK (((`updated_by_admin_id` is null) or (`updated_by_manager_id` is null)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Ledger of every change to product.quantity_in_stock, credited to the
-- admin or manager who made it (at most one). sale_id links a SALE row to its
-- invoice and is set to NULL if the invoice is deleted; the SALE_RETURN rows
-- written on delete name the invoice in `reason` instead.
CREATE TABLE `stock_movement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `movement_type` varchar(20) NOT NULL,
  `quantity_change` int NOT NULL,
  `quantity_after` int unsigned NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `admin_id` bigint DEFAULT NULL,
  `manager_id` bigint DEFAULT NULL,
  `product_id` bigint NOT NULL,
  `sale_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `stock_movement_admin_id_0c4ef19d_fk_admin_id` (`admin_id`),
  KEY `stock_movement_manager_id_f74d04b6_fk_manager_id` (`manager_id`),
  KEY `stock_movement_product_id_126b1c0d_fk_product_id` (`product_id`),
  KEY `stock_movement_sale_id_702cc30e_fk_sale_id` (`sale_id`),
  CONSTRAINT `stock_movement_admin_id_0c4ef19d_fk_admin_id` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `stock_movement_manager_id_f74d04b6_fk_manager_id` FOREIGN KEY (`manager_id`) REFERENCES `manager` (`id`),
  CONSTRAINT `stock_movement_product_id_126b1c0d_fk_product_id` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `stock_movement_sale_id_702cc30e_fk_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `sale` (`id`),
  CONSTRAINT `stock_movement_chk_1` CHECK ((`quantity_after` >= 0)),
  CONSTRAINT `stock_movement_one_role` CHECK (((`admin_id` is null) or (`manager_id` is null)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- orders app
-- -------------------------------------------------------------------------

CREATE TABLE `customer_order` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_number` varchar(50) NOT NULL,
  `customer_name` varchar(255) NOT NULL,
  `status` varchar(20) NOT NULL,
  `total_amount` decimal(14,2) NOT NULL,
  `order_date` datetime(6) NOT NULL,
  `expected_delivery_date` date DEFAULT NULL,
  `notes` longtext NOT NULL,
  `created_by_admin_id` bigint DEFAULT NULL,
  `created_by_manager_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_number` (`order_number`),
  KEY `customer_order_created_by_admin_id_4d1301c0_fk_admin_id` (`created_by_admin_id`),
  KEY `customer_order_created_by_manager_id_a41dacf3_fk_manager_id` (`created_by_manager_id`),
  CONSTRAINT `customer_order_created_by_admin_id_4d1301c0_fk_admin_id` FOREIGN KEY (`created_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `customer_order_created_by_manager_id_a41dacf3_fk_manager_id` FOREIGN KEY (`created_by_manager_id`) REFERENCES `manager` (`id`),
  CONSTRAINT `customer_order_created_by_one_role` CHECK (((`created_by_admin_id` is null) or (`created_by_manager_id` is null)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `customer_order_item` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `subtotal` decimal(14,2) NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `customer_order_item_order_id_0d213d76_fk_customer_order_id` (`order_id`),
  KEY `customer_order_item_product_id_a8dfa297_fk_product_id` (`product_id`),
  CONSTRAINT `customer_order_item_order_id_0d213d76_fk_customer_order_id` FOREIGN KEY (`order_id`) REFERENCES `customer_order` (`id`),
  CONSTRAINT `customer_order_item_product_id_a8dfa297_fk_product_id` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `customer_order_item_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- sales app
-- -------------------------------------------------------------------------

CREATE TABLE `sale` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invoice_number` varchar(50) NOT NULL,
  `total_amount` decimal(14,2) NOT NULL,
  `sale_date` datetime(6) NOT NULL,
  `sold_to` varchar(255) NOT NULL,
  `order_id` bigint DEFAULT NULL,
  `created_by_admin_id` bigint DEFAULT NULL,
  `updated_by_admin_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `invoice_number` (`invoice_number`),
  UNIQUE KEY `order_id` (`order_id`),
  KEY `sale_created_by_admin_id_a1dd1e31_fk_admin_id` (`created_by_admin_id`),
  KEY `sale_updated_by_admin_id_3f1fe7e0_fk_admin_id` (`updated_by_admin_id`),
  CONSTRAINT `sale_created_by_admin_id_a1dd1e31_fk_admin_id` FOREIGN KEY (`created_by_admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `sale_order_id_269295d8_fk_customer_order_id` FOREIGN KEY (`order_id`) REFERENCES `customer_order` (`id`),
  CONSTRAINT `sale_updated_by_admin_id_3f1fe7e0_fk_admin_id` FOREIGN KEY (`updated_by_admin_id`) REFERENCES `admin` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `sale_item` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `subtotal` decimal(14,2) NOT NULL,
  `product_id` bigint NOT NULL,
  `sale_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sales_saleitem_product_id_aeb6c9cd_fk_product_id` (`product_id`),
  KEY `sales_saleitem_sale_id_56e67045_fk_sales_sale_id` (`sale_id`),
  CONSTRAINT `sales_saleitem_product_id_aeb6c9cd_fk_product_id` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `sales_saleitem_sale_id_56e67045_fk_sales_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `sale` (`id`),
  CONSTRAINT `sale_item_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -------------------------------------------------------------------------
-- reports app
-- -------------------------------------------------------------------------

-- One row per sales report generated: the admin or manager who ran it (at
-- most one), the date range and its totals.
CREATE TABLE `sales_report` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `sales_count` int unsigned NOT NULL,
  `items_sold` int unsigned NOT NULL,3
  `total_revenue` decimal(14,2) NOT NULL,
  `generated_at` datetime(6) NOT NULL,
  `admin_id` bigint DEFAULT NULL,
  `manager_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sales_report_admin_id_692cc982_fk_admin_id` (`admin_id`),
  KEY `sales_report_manager_id_53fee0ac_fk_manager_id` (`manager_id`),
  CONSTRAINT `sales_report_admin_id_692cc982_fk_admin_id` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`),
  CONSTRAINT `sales_report_manager_id_53fee0ac_fk_manager_id` FOREIGN KEY (`manager_id`) REFERENCES `manager` (`id`),
  CONSTRAINT `sales_report_chk_1` CHECK ((`sales_count` >= 0)),
  CONSTRAINT `sales_report_chk_2` CHECK ((`items_sold` >= 0)),
  CONSTRAINT `sales_report_one_role` CHECK (((`admin_id` is null) or (`manager_id` is null))),
  CONSTRAINT `sales_report_start_before_end` CHECK ((`start_date` <= `end_date`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
