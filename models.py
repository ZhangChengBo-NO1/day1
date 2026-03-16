import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                is_default INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        self._init_default_categories(cursor)
        conn.commit()
        conn.close()

    def _init_default_categories(self, cursor):
        default_categories = [
            ("工资", "收入"), ("奖金", "收入"), ("投资收益", "收入"), ("其他收入", "收入"),
            ("餐饮", "支出"), ("交通", "支出"), ("购物", "支出"), ("娱乐", "支出"),
            ("医疗", "支出"), ("教育", "支出"), ("住房", "支出"), ("其他支出", "支出")
        ]
        for name, type_ in default_categories:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name, type, is_default) VALUES (?, ?, 1)",
                (name, type_)
            )


class User:
    def __init__(self, db: Database):
        self.db = db

    def create_user(self, username: str, password: str, role: str = "user") -> int:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


class Transaction:
    def __init__(self, db: Database):
        self.db = db

    def add_transaction(self, user_id: int, amount: float, type_: str,
                        category: str, description: str = "",
                        transaction_date: Optional[str] = None) -> int:
        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, category, description, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, type_, category, description, transaction_date))
        conn.commit()
        trans_id = cursor.lastrowid
        conn.close()
        return trans_id

    def get_transactions(self, user_id: int, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, type_: Optional[str] = None,
                         category: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date)
        if type_:
            query += " AND type = ?"
            params.append(type_)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY transaction_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_transaction(self, trans_id: int, user_id: int) -> bool:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (trans_id, user_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0


class Category:
    def __init__(self, db: Database):
        self.db = db

    def get_categories(self, type_: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.db._get_connection()
        cursor = conn.cursor()

        if type_:
            cursor.execute("SELECT * FROM categories WHERE type = ?", (type_,))
        else:
            cursor.execute("SELECT * FROM categories")

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_category(self, name: str, type_: str) -> int:
        conn = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (name, type) VALUES (?, ?)",
                (name, type_)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()
