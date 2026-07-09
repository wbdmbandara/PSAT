import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

SCHEMA_MIGRATIONS = [
    ("campaigns", "status", "VARCHAR(50) DEFAULT 'Draft'"),
    ("campaigns", "template_name", "VARCHAR(150) DEFAULT 'corporate'"),
    ("users", "created_by", "INT NULL"),
]


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def ensure_schema():
    """Apply missing column migrations for databases created from an older schema."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for table, column, definition in SCHEMA_MIGRATIONS:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = %s
                """,
                (table, column),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                conn.commit()
                print(f"[DB] Added missing column: {table}.{column}")
    finally:
        cursor.close()
        conn.close()
