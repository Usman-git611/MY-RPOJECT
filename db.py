import os
import sys
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / ".vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

import mysql.connector
from mysql.connector import Error


def load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


class Database:
    def __init__(self):
        self.config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "hostelfix"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
        }

    def connect(self):
        return mysql.connector.connect(**self.config)

    def fetch_one(self, query, params=()):
        with self.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            return result

    def fetch_all(self, query, params=()):
        with self.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result

    def execute(self, query, params=()):
        try:
            with self.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(query, params)
                connection.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
        except Error:
            raise

    def dashboard_stats(self):
        totals = self.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(status = 'Pending') AS pending,
                SUM(status = 'In Progress') AS progress,
                SUM(status = 'Resolved') AS resolved
            FROM complaints
            """
        )
        return {
            "total": totals["total"] or 0,
            "pending": totals["pending"] or 0,
            "progress": totals["progress"] or 0,
            "resolved": totals["resolved"] or 0,
        }
