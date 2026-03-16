# -*- coding: utf-8 -*-
"""
数据模型层 - 数据库模型和表结构定义
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    user_id INTEGER,
                    is_default INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            self._init_default_data(cursor)
    
    def _init_default_data(self, cursor):
        """初始化默认数据"""
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', 
                      (config.DEFAULT_ADMIN['username'],))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (username, password, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                config.DEFAULT_ADMIN['username'],
                config.DEFAULT_ADMIN['password'],
                config.DEFAULT_ADMIN['role'],
                datetime.now().strftime(config.DATETIME_FORMAT)
            ))
        
        cursor.execute('SELECT COUNT(*) FROM categories WHERE is_default = 1')
        if cursor.fetchone()[0] == 0:
            for cat_type, categories in config.DEFAULT_CATEGORIES.items():
                for cat_name in categories:
                    cursor.execute('''
                        INSERT INTO categories (name, type, is_default)
                        VALUES (?, ?, 1)
                    ''', (cat_name, cat_type))


class User:
    """用户模型类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, username: str, password: str, role: str = 'user') -> int:
        """创建新用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, password, role, 
                  datetime.now().strftime(config.DATETIME_FORMAT)))
            return cursor.lastrowid
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().strftime(config.DATETIME_FORMAT), user_id))
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        user = self.get_by_username(username)
        if user and user['password'] == password:
            self.update_last_login(user['id'])
            return user
        return None


class Transaction:
    """交易记录模型类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, user_id: int, trans_type: str, amount: float,
               category: str, description: str = '', date: str = None) -> int:
        """创建交易记录"""
        if date is None:
            date = datetime.now().strftime(config.DATE_FORMAT)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, type, amount, category, description, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, trans_type, amount, category, description, date,
                  datetime.now().strftime(config.DATETIME_FORMAT)))
            return cursor.lastrowid
    
    def get_by_id(self, trans_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取交易记录"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (trans_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_user(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户的所有交易记录"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC, created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_date_range(self, user_id: int, start_date: str, 
                          end_date: str) -> List[Dict[str, Any]]:
        """获取日期范围内的交易记录"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC, created_at DESC
            ''', (user_id, start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
    
    def update(self, trans_id: int, **kwargs) -> bool:
        """更新交易记录"""
        allowed_fields = ['type', 'amount', 'category', 'description', 'date']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.now().strftime(config.DATETIME_FORMAT)
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE transactions SET {set_clause} WHERE id = ?
            ''', (*updates.values(), trans_id))
            return cursor.rowcount > 0
    
    def delete(self, trans_id: int) -> bool:
        """删除交易记录"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
            return cursor.rowcount > 0
    
    def get_monthly_summary(self, user_id: int, year: int, 
                           month: int) -> Dict[str, Any]:
        """获取月度汇总"""
        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year + 1}-01-01'
        else:
            end_date = f'{year}-{month + 1:02d}-01'
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT type, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND date >= ? AND date < ?
                GROUP BY type
            ''', (user_id, start_date, end_date))
            
            result = {'income': 0, 'expense': 0}
            for row in cursor.fetchall():
                result[row['type']] = row['total'] or 0
            
            result['balance'] = result['income'] - result['expense']
            return result
    
    def get_yearly_summary(self, user_id: int, year: int) -> Dict[str, Any]:
        """获取年度汇总"""
        start_date = f'{year}-01-01'
        end_date = f'{year + 1}-01-01'
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT type, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND date >= ? AND date < ?
                GROUP BY type
            ''', (user_id, start_date, end_date))
            
            result = {'income': 0, 'expense': 0}
            for row in cursor.fetchall():
                result[row['type']] = row['total'] or 0
            
            result['balance'] = result['income'] - result['expense']
            return result
    
    def get_category_summary(self, user_id: int, trans_type: str = None,
                            start_date: str = None, 
                            end_date: str = None) -> List[Dict[str, Any]]:
        """获取分类汇总"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT category, type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if trans_type:
                query += ' AND type = ?'
                params.append(trans_type)
            
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            query += ' GROUP BY category, type ORDER BY total DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


class Category:
    """分类模型类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_all(self, trans_type: str = None) -> List[Dict[str, Any]]:
        """获取所有分类"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if trans_type:
                cursor.execute('''
                    SELECT * FROM categories 
                    WHERE type = ? 
                    ORDER BY name
                ''', (trans_type,))
            else:
                cursor.execute('SELECT * FROM categories ORDER BY type, name')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create(self, name: str, trans_type: str, 
               user_id: int = None) -> int:
        """创建自定义分类"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, type, user_id, is_default)
                VALUES (?, ?, ?, 0)
            ''', (name, trans_type, user_id))
            return cursor.lastrowid
