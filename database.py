import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def init_db():
    try:
        # Create database if it doesn't exist yet
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        conn.close()

        # Connect directly to our schema
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL,
                user_group VARCHAR(50) NOT NULL,
                points INT DEFAULT 0,
                email VARCHAR(100) DEFAULT 'Not Linked 🛑',
                email_verified TINYINT DEFAULT 0
            )
        """)

        # Default admin account setup
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, password, user_group, points, email, email_verified)
                VALUES ('admin', 'password123', 'All', 10000, 'admin@taskgreen.org', 1)
            """)
        conn.commit()
    except Error as e:
        print(f"Database Initialization Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()