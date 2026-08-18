import sys
import logging
from backend.app.database.connection import get_db_connection
from backend.app.modules.audience.service import ensure_audience_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")


CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS `customers` (
        `customer_id` VARCHAR(100) PRIMARY KEY,
        `full_name` VARCHAR(255) NOT NULL,
        `email` VARCHAR(255),
        `phone` VARCHAR(50),
        `city` VARCHAR(100),
        `state` VARCHAR(100),
        `location` VARCHAR(255),
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `ingestion_batches` (
        `batch_id` VARCHAR(100) PRIMARY KEY,
        `filename` VARCHAR(255) NOT NULL,
        `input_type` VARCHAR(50) DEFAULT 'UNKNOWN',
        `source_domain` VARCHAR(50) DEFAULT 'UNKNOWN',
        `total_records` INT DEFAULT 0,
        `valid_records` INT DEFAULT 0,
        `rejected_records` INT DEFAULT 0,
        `duplicate_records` INT DEFAULT 0,
        `inserted_records` INT DEFAULT 0,
        `status` ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL') DEFAULT 'PENDING',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `completed_at` DATETIME DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `raw_ingestion_records` (
        `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
        `batch_id` VARCHAR(100) NOT NULL,
        `row_number` INT NOT NULL,
        `raw_data` LONGTEXT NOT NULL,
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `fk_raw_batch` FOREIGN KEY (`batch_id`) REFERENCES `ingestion_batches`(`batch_id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `ingestion_errors` (
        `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
        `batch_id` VARCHAR(100) NOT NULL,
        `row_number` INT NOT NULL,
        `field_name` VARCHAR(100),
        `error_reason` VARCHAR(500) NOT NULL,
        `raw_value` TEXT,
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `fk_error_batch` FOREIGN KEY (`batch_id`) REFERENCES `ingestion_batches`(`batch_id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `unified_transactions` (
        `transaction_id` VARCHAR(100) PRIMARY KEY,
        `raw_record_id` BIGINT,
        `batch_id` VARCHAR(100) NOT NULL,
        `customer_id` VARCHAR(100) NOT NULL,
        `source_domain` VARCHAR(50) NOT NULL,
        `source_name` VARCHAR(100) NOT NULL,
        `transaction_type` VARCHAR(50) NOT NULL,
        `category` VARCHAR(100) NOT NULL,
        `subcategory` VARCHAR(100),
        `transaction_date` DATETIME NOT NULL,
        `amount` DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
        `currency` VARCHAR(10) DEFAULT 'INR',
        `payment_method` VARCHAR(50),
        `merchant_or_provider` VARCHAR(255),
        `location` VARCHAR(100),
        `status` VARCHAR(50) DEFAULT 'COMPLETED',
        `raw_message` LONGTEXT DEFAULT NULL,
        `classification_confidence` DECIMAL(4, 2) DEFAULT NULL,
        `classified_at` DATETIME DEFAULT NULL,
        `record_hash` VARCHAR(64) UNIQUE NOT NULL,
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT `fk_txn_batch` FOREIGN KEY (`batch_id`) REFERENCES `ingestion_batches`(`batch_id`) ON DELETE CASCADE,
        CONSTRAINT `fk_txn_raw` FOREIGN KEY (`raw_record_id`) REFERENCES `raw_ingestion_records`(`id`) ON DELETE SET NULL,
        CONSTRAINT `fk_txn_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers`(`customer_id`) ON DELETE CASCADE,
        INDEX `idx_customer` (`customer_id`),
        INDEX `idx_domain` (`source_domain`),
        INDEX `idx_date` (`transaction_date`),
        INDEX `idx_category` (`category`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `feature_definitions` (
        `feature_id` VARCHAR(100) PRIMARY KEY,
        `display_name` VARCHAR(255) NOT NULL,
        `description` TEXT NULL,
        `category` VARCHAR(50) NOT NULL DEFAULT 'FINANCIAL',
        `data_type` VARCHAR(50) NOT NULL DEFAULT 'NUMBER',
        `aggregation_type` VARCHAR(50) NOT NULL DEFAULT 'SUM',
        `time_window` VARCHAR(50) NOT NULL DEFAULT 'ALL_TIME',
        `unit` VARCHAR(50) DEFAULT 'INR',
        `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        `version` VARCHAR(20) NOT NULL DEFAULT 'v1',
        `parameters_json` LONGTEXT NULL,
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX `idx_feature_category` (`category`),
        INDEX `idx_feature_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `customer_feature_values` (
        `customer_id` VARCHAR(100) NOT NULL,
        `feature_id` VARCHAR(100) NOT NULL,
        `value_numeric` DECIMAL(18, 2) NULL,
        `value_string` VARCHAR(255) NULL,
        `value_json` LONGTEXT NULL,
        `version` VARCHAR(20) NOT NULL DEFAULT 'v1',
        `confidence` DECIMAL(5, 2) NOT NULL DEFAULT 1.00,
        `calculated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`customer_id`, `feature_id`),
        CONSTRAINT `fk_cfv_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers`(`customer_id`) ON DELETE CASCADE,
        CONSTRAINT `fk_cfv_feature` FOREIGN KEY (`feature_id`) REFERENCES `feature_definitions`(`feature_id`) ON DELETE CASCADE,
        INDEX `idx_cfv_feature` (`feature_id`),
        INDEX `idx_cfv_calculated` (`calculated_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
]


def migrate_schema(cursor):
    """
    Safely migrates existing tables to add new columns if they are missing.
    Safe to run multiple times — uses ALTER TABLE with IF NOT EXISTS pattern.
    """
    migrations = [
        # ingestion_batches: add input_type column
        "ALTER TABLE `ingestion_batches` ADD COLUMN `input_type` VARCHAR(50) DEFAULT 'UNKNOWN'",
        # ingestion_batches: add completed_at column
        "ALTER TABLE `ingestion_batches` ADD COLUMN `completed_at` DATETIME DEFAULT NULL",
        # ingestion_batches: ensure source_domain is nullable
        "ALTER TABLE `ingestion_batches` MODIFY COLUMN `source_domain` VARCHAR(50) DEFAULT 'UNKNOWN'",
        # unified_transactions: add classification columns
        "ALTER TABLE `unified_transactions` ADD COLUMN `classification_confidence` DECIMAL(4, 2) DEFAULT NULL",
        "ALTER TABLE `unified_transactions` ADD COLUMN `classified_at` DATETIME DEFAULT NULL",
        # unified_transactions: add raw_message for SMS/communication preservation
        "ALTER TABLE `unified_transactions` ADD COLUMN `raw_message` LONGTEXT DEFAULT NULL",
        # unified_transactions: allow amount to be 0 (informational SMS)
        "ALTER TABLE `unified_transactions` MODIFY COLUMN `amount` DECIMAL(15, 2) NOT NULL DEFAULT 0.00",
        # ingestion_batches: extend status ENUM to include PARTIAL
        "ALTER TABLE `ingestion_batches` MODIFY COLUMN `status` ENUM('PENDING','PROCESSING','COMPLETED','FAILED','PARTIAL') DEFAULT 'PENDING'",
    ]

    for stmt in migrations:
        try:
            cursor.execute(stmt)
            logger.info(f"Migration applied: {stmt[:60]}...")
        except Exception as e:
            # Column/change already exists — safe to ignore
            err_str = str(e).lower()
            if "duplicate column" in err_str or "already exists" in err_str or "1060" in str(e):
                pass
            else:
                logger.debug(f"Migration skipped ({stmt[:50]}...): {e}")


def init_db():
    logger.info("Initializing database tables...")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for sql in CREATE_TABLES_SQL:
            cursor.execute(sql)
        conn.commit()

        # Apply schema migrations for existing databases
        migrate_schema(cursor)
        conn.commit()

        ensure_audience_tables()
        logger.info("All database tables initialized and migrations applied.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_db()
