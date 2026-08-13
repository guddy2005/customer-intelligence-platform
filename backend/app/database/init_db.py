import sys
import logging
from backend.app.database.connection import get_db_connection

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
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `ingestion_batches` (
        `batch_id` VARCHAR(100) PRIMARY KEY,
        `filename` VARCHAR(255) NOT NULL,
        `source_domain` VARCHAR(50) NOT NULL,
        `total_records` INT DEFAULT 0,
        `valid_records` INT DEFAULT 0,
        `rejected_records` INT DEFAULT 0,
        `duplicate_records` INT DEFAULT 0,
        `inserted_records` INT DEFAULT 0,
        `status` ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
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
        `error_reason` VARCHAR(255) NOT NULL,
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
        `amount` DECIMAL(15, 2) NOT NULL,
        `currency` VARCHAR(10) DEFAULT 'INR',
        `payment_method` VARCHAR(50),
        `merchant_or_provider` VARCHAR(255),
        `location` VARCHAR(100),
        `status` VARCHAR(50) DEFAULT 'COMPLETED',
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
    """
]


def init_db():
    logger.info("Initializing database tables...")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for sql in CREATE_TABLES_SQL:
            cursor.execute(sql)
        conn.commit()
        logger.info("All database tables created successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_db()
