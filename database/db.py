import sqlite3
import os

# Get the main project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database and schema file paths
DB_PATH = os.path.join(BASE_DIR, "smartpark.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create all database tables using schema.sql."""

    connection = get_connection()

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)
        connection.commit()

        print("SmartPark AI database initialized successfully!")

    except Exception as error:
        print("Database initialization failed:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
