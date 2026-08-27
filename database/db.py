import mysql.connector
import os
import socket
import time
from mysql.connector import pooling
from dotenv import load_dotenv

socket.setdefaulttimeout(10)
MAX_CONN_AGE = 240  # seconds — safely under AWS Global Accelerator's 340s cutoff

load_dotenv()

SCHEMA_MIGRATIONS = [
    ("campaigns", "status", "VARCHAR(50) DEFAULT 'Draft'"),
    ("campaigns", "template_name", "VARCHAR(150) DEFAULT 'corporate'"),
    ("users", "created_by", "INT NULL"),
]

# 1. Define the database configuration
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "4000")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connect_timeout": 10,  # Prevents hanging indefinitely if the DB is unreachable
}

# 2. Initialize the connection pool once at the module level
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10,             # Adjust this based on your traffic and Gunicorn workers
        pool_reset_session=True,  # Cleans up temporary tables/variables when reused
        **dbconfig
    )
    print("[DB] Connection pool initialized successfully.")
except mysql.connector.Error as err:
    print(f"[DB] Error initializing connection pool: {err}")
    raise

_conn_created_at = {}  # id(conn) -> timestamp, tracks age for proactive recycling


def get_connection():
    """Fetch a validated, non-stale connection from the pool."""
    conn = connection_pool.get_connection()
    created = _conn_created_at.get(id(conn), 0)

    if time.time() - created > MAX_CONN_AGE:
        try:
            conn.close()
        except mysql.connector.Error:
            pass
        conn = connection_pool.get_connection()

    try:
        conn.ping(reconnect=True, attempts=2, delay=1)
    except mysql.connector.Error as err:
        print(f"[DB] Connection unhealthy and could not be revived: {err}")
        raise

    _conn_created_at[id(conn)] = time.time()
    return conn

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
