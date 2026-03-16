"""
数据处理层 - 智能财务管理系统

负责数据的持久化、CRUD操作、报表生成、数据分析等核心功能
使用SQLite3作为数据库
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import pandas as pd

from config import DATABASE_CONFIG, CATEGORIES, ROLES, DEFAULT_USERS
from models import (
    Transaction, TransactionType, User, MonthlyReport, 
    AnnualReport, QueryFilter
)
from utils import (
    Validator, SecurityUtils, DateUtils, CalculationUtils,
    ValidationError, AuthenticationError, validate_transaction_data
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or DATABASE_CONFIG['path']
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'default'
                )
            ''')
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    permissions TEXT,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            ''')
            
            # 创建分类预算表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    year_month TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    UNIQUE(category, year_month, user_id)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_date 
                ON transactions(date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_type 
                ON transactions(type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_user 
                ON transactions(user_id)
            ''')
            
            # 初始化默认用户
            self._init_default_users(cursor)
    
    def _init_default_users(self, cursor: sqlite3.Cursor):
        """初始化默认用户"""
        for username, user_data in DEFAULT_USERS.items():
            cursor.execute(
                'SELECT username FROM users WHERE username = ?',
                (username,)
            )
            if not cursor.fetchone():
                password_hash, salt = SecurityUtils.hash_password(
                    user_data['password']
                )
                permissions = json.dumps(
                    ROLES[user_data['role']]['permissions']
                )
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, salt, role, permissions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    username, password_hash, salt, 
                    user_data['role'], permissions,
                    user_data['created_at']
                ))


class TransactionManager:
    """交易记录管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化交易记录管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def add_transaction(self, transaction: Transaction) -> int:
        """
        添加交易记录
        
        Args:
            transaction: 交易记录对象
            
        Returns:
            int: 新记录ID
            
        Raises:
            ValidationError: 数据验证失败
        """
        # 验证数据
        validate_transaction_data(
            transaction.amount,
            transaction.type.value,
            transaction.category,
            transaction.date,
            transaction.note
        )
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (amount, type, category, date, note, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.amount,
                transaction.type.value,
                transaction.category,
                transaction.date,
                transaction.note,
                transaction.created_at,
                transaction.updated_at,
                transaction.user_id
            ))
            return cursor.lastrowid
    
    def update_transaction(self, transaction_id: int, 
                          updates: Dict[str, Any]) -> bool:
        """
        更新交易记录
        
        Args:
            transaction_id: 记录ID
            updates: 更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        allowed_fields = ['amount', 'type', 'category', 'date', 'note']
        update_fields = []
        values = []
        
        validator = Validator()
        
        for field, value in updates.items():
            if field not in allowed_fields:
                continue
            
            # 验证字段
            if field == 'amount':
                value = validator.validate_amount(value)
            elif field == 'date':
                value = validator.validate_date(value)
            elif field == 'category':
                trans_type = updates.get('type', 'expense')
                value = validator.validate_category(value, trans_type)
            elif field == 'note':
                value = validator.validate_note(value)
            
            update_fields.append(f"{field} = ?")
            values.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(transaction_id)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE transactions 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        删除交易记录
        
        Args:
            transaction_id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM transactions WHERE id = ?',
                (transaction_id,)
            )
            return cursor.rowcount > 0
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        根据ID获取交易记录
        
        Args:
            transaction_id: 记录ID
            
        Returns:
            Optional[Transaction]: 交易记录对象或None
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM transactions WHERE id = ?',
                (transaction_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_transaction(row)
            return None
    
    def query_transactions(self, filter_obj: QueryFilter = None,
                          order_by: str = 'date DESC',
                          limit: int = None) -> List[Transaction]:
        """
        查询交易记录
        
        Args:
            filter_obj: 查询过滤器
            order_by: 排序方式
            limit: 限制数量
            
        Returns:
            List[Transaction]: 交易记录列表
        """
        conditions = []
        values = []
        
        if filter_obj:
            filters = filter_obj.build()
            
            if 'date_range' in filters:
                start, end = filters['date_range']
                conditions.append('date BETWEEN ? AND ?')
                values.extend([start, end])
            
            if 'type' in filters:
                conditions.append('type = ?')
                values.append(filters['type'].value)
            
            if 'category' in filters:
                conditions.append('category = ?')
                values.append(filters['category'])
            
            if 'amount_range' in filters:
                min_amt, max_amt = filters['amount_range']
                conditions.append('amount BETWEEN ? AND ?')
                values.extend([min_amt, max_amt])
            
            if 'user_id' in filters:
                conditions.append('user_id = ?')
                values.append(filters['user_id'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        query = f'''
            SELECT * FROM transactions 
            WHERE {where_clause}
            ORDER BY {order_by}
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            rows = cursor.fetchall()
            
            return [self._row_to_transaction(row) for row in rows]
    
    def get_transactions_by_month(self, year_month: str,
                                   user_id: str = None) -> List[Transaction]:
        """
        获取指定月份的交易记录
        
        Args:
            year_month: 年月（YYYY-MM）
            user_id: 用户ID
            
        Returns:
            List[Transaction]: 交易记录列表
        """
        start_date, end_date = DateUtils.get_month_range(year_month)
        
        filter_obj = QueryFilter().by_date_range(start_date, end_date)
        if user_id:
            filter_obj.by_user(user_id)
        
        return self.query_transactions(filter_obj)
    
    def get_all_categories_summary(self, start_date: str = None,
                                    end_date: str = None,
                                    user_id: str = None) -> Dict[str, Dict[str, float]]:
        """
        获取所有分类汇总
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            
        Returns:
            Dict: 分类汇总数据
        """
        conditions = ['1=1']
        values = []
        
        if start_date and end_date:
            conditions.append('date BETWEEN ? AND ?')
            values.extend([start_date, end_date])
        
        if user_id:
            conditions.append('user_id = ?')
            values.append(user_id)
        
        where_clause = ' AND '.join(conditions)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT type, category, SUM(amount) as total
                FROM transactions
                WHERE {where_clause}
                GROUP BY type, category
                ORDER BY total DESC
            ''', values)
            
            result = {'income': {}, 'expense': {}}
            for row in cursor.fetchall():
                result[row['type']][row['category']] = row['total']
            
            return result
    
    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """将数据库行转换为Transaction对象"""
        return Transaction(
            id=row['id'],
            amount=row['amount'],
            type=TransactionType(row['type']),
            category=row['category'],
            date=row['date'],
            note=row['note'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            user_id=row['user_id']
        )
    
    def export_to_dataframe(self, filter_obj: QueryFilter = None) -> pd.DataFrame:
        """
        导出为DataFrame
        
        Args:
            filter_obj: 查询过滤器
            
        Returns:
            pd.DataFrame: 数据框
        """
        transactions = self.query_transactions(filter_obj)
        data = [t.to_dict() for t in transactions]
        return pd.DataFrame(data)


class UserManager:
    """用户管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化用户管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Optional[User]: 认证成功返回用户对象，失败返回None
            
        Raises:
            AuthenticationError: 认证失败
        """
        validator = Validator()
        username = validator.validate_username(username)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE username = ? AND is_active = 1',
                (username,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise AuthenticationError('用户名或密码错误')
            
            # 验证密码
            if not SecurityUtils.verify_password(
                password, row['password_hash'], row['salt']
            ):
                raise AuthenticationError('用户名或密码错误')
            
            # 更新最后登录时间
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE username = ?
            ''', (datetime.now().isoformat(), username))
            
            return self._row_to_user(row)
    
    def create_user(self, username: str, password: str,
                    role: str = 'user') -> bool:
        """
        创建用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色
            
        Returns:
            bool: 是否创建成功
        """
        validator = Validator()
        username = validator.validate_username(username)
        password = validator.validate_password(password)
        
        password_hash, salt = SecurityUtils.hash_password(password)
        permissions = json.dumps(ROLES.get(role, ROLES['user'])['permissions'])
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, salt, role, permissions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    username, password_hash, salt, role,
                    permissions, datetime.now().isoformat()
                ))
                return True
        except sqlite3.IntegrityError:
            raise ValidationError(f'用户 "{username}" 已存在')
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """将数据库行转换为User对象"""
        return User(
            username=row['username'],
            password_hash=row['password_hash'],
            role=row['role'],
            permissions=json.loads(row['permissions']) if row['permissions'] else [],
            created_at=row['created_at'],
            last_login=row['last_login'],
            is_active=bool(row['is_active'])
        )


class ReportManager:
    """报表管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化报表管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def generate_monthly_report(self, year_month: str,
                                 user_id: str = None) -> MonthlyReport:
        """
        生成月度报表
        
        Args:
            year_month: 年月（YYYY-MM）
            user_id: 用户ID
            
        Returns:
            MonthlyReport: 月度报表
        """
        start_date, end_date = DateUtils.get_month_range(year_month)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = ['date BETWEEN ? AND ?']
            values = [start_date, end_date]
            
            if user_id:
                conditions.append('user_id = ?')
                values.append(user_id)
            
            where_clause = ' AND '.join(conditions)
            
            # 获取总收入和支出
            cursor.execute(f'''
                SELECT type, SUM(amount) as total, COUNT(*) as count
                FROM transactions
                WHERE {where_clause}
                GROUP BY type
            ''', values)
            
            total_income = 0.0
            total_expense = 0.0
            transaction_count = 0
            
            for row in cursor.fetchall():
                if row['type'] == 'income':
                    total_income = row['total'] or 0.0
                else:
                    total_expense = row['total'] or 0.0
                transaction_count += row['count']
            
            # 获取分类统计
            category_breakdown = {'income': {}, 'expense': {}}
            cursor.execute(f'''
                SELECT type, category, SUM(amount) as total
                FROM transactions
                WHERE {where_clause}
                GROUP BY type, category
            ''', values)
            
            for row in cursor.fetchall():
                category_breakdown[row['type']][row['category']] = row['total']
            
            return MonthlyReport(
                year_month=year_month,
                total_income=total_income,
                total_expense=total_expense,
                category_breakdown=category_breakdown,
                transaction_count=transaction_count
            )
    
    def generate_annual_report(self, year: int,
                                user_id: str = None) -> AnnualReport:
        """
        生成年度报表
        
        Args:
            year: 年份
            user_id: 用户ID
            
        Returns:
            AnnualReport: 年度报表
        """
        report = AnnualReport(year=year)
        
        # 生成12个月的报表
        for month in range(1, 13):
            year_month = f"{year}-{month:02d}"
            monthly_report = self.generate_monthly_report(year_month, user_id)
            report.monthly_data.append(monthly_report)
            report.total_income += monthly_report.total_income
            report.total_expense += monthly_report.total_expense
        
        # 计算结余
        report.balance = report.total_income - report.total_expense
        
        # 获取主要分类
        start_date, end_date = DateUtils.get_year_range(year)
        trans_manager = TransactionManager(self.db)
        summary = trans_manager.get_all_categories_summary(
            start_date, end_date, user_id
        )
        
        report.top_categories = {
            'income': sorted(
                summary['income'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'expense': sorted(
                summary['expense'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
        
        return report
    
    def get_trend_analysis(self, months: int = 12,
                          user_id: str = None) -> Dict[str, List]:
        """
        获取收支趋势分析
        
        Args:
            months: 分析月数
            user_id: 用户ID
            
        Returns:
            Dict: 趋势数据
        """
        month_list = DateUtils.parse_months(months)
        
        trend_data = {
            'months': month_list,
            'income': [],
            'expense': [],
            'balance': []
        }
        
        for year_month in month_list:
            report = self.generate_monthly_report(year_month, user_id)
            trend_data['income'].append(report.total_income)
            trend_data['expense'].append(report.total_expense)
            trend_data['balance'].append(report.balance)
        
        return trend_data


class FinanceManager:
    """
    财务管理器 - 整合所有管理器的主类
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化财务管理器
        
        Args:
            db_path: 数据库路径（可选）
        """
        self.db = DatabaseManager(db_path)
        self.transactions = TransactionManager(self.db)
        self.users = UserManager(self.db)
        self.reports = ReportManager(self.db)
        self.current_user: Optional[User] = None
    
    def login(self, username: str, password: str) -> bool:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 登录是否成功
        """
        try:
            self.current_user = self.users.authenticate(username, password)
            return True
        except AuthenticationError:
            return False
    
    def logout(self):
        """用户登出"""
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.current_user is not None
    
    def has_permission(self, permission: str) -> bool:
        """检查当前用户是否有指定权限"""
        if not self.current_user:
            return False
        return permission in self.current_user.permissions
