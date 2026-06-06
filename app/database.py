import mysql.connector
from mysql.connector import pooling
import os
import time

DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", 3306)),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "secret"),
    "database": os.getenv("MYSQL_DB", "urlshortener"),
}

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="urlpool",
            pool_size=32,          # max allowed by mysql-connector
            pool_reset_session=True,
            **DB_CONFIG
        )
    return _pool


def get_connection():
    try:
        return get_pool().get_connection()
    except Exception:
        # Pool exhausted — fall back to direct connection
        return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create urls table with retry loop."""
    retries = 15
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id          BIGINT AUTO_INCREMENT PRIMARY KEY,
        original    VARCHAR(2048) NOT NULL,
        short_code  VARCHAR(10)   UNIQUE NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hit_count   BIGINT DEFAULT 0
    )
""")

            cursor.execute("""
                SELECT COUNT(1) FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name   = 'urls'
                  AND index_name   = 'idx_short_code'
            """)
            if not cursor.fetchone()[0]:
                cursor.execute(
                    "CREATE INDEX idx_short_code ON urls(short_code)"
                )

            conn.commit()
            cursor.close()
            conn.close()

            get_pool()
            print("✅ Database initialised and pool ready.")
            return

        except Exception as e:
            print(f"⏳ MySQL not ready (attempt {attempt+1}/15): {e}")
            time.sleep(3)

    raise RuntimeError("❌ Could not connect to MySQL after all retries.")