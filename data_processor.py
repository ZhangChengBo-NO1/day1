# -*- coding: utf-8 -*-
"""
数据处理层 - 业务逻辑处理、CRUD操作封装、统计分析
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

import config
from models import Database, User, Transaction, Category
from utils import (DataValidator, PermissionManager, ValidationError, 
                   PermissionError, format_currency, get_month_range, 
                   get_year_range, calculate_percentage)


class FinanceService:
    """财务服务类 - 核心业务逻辑"""
    
    def __init__(self, db_path: str = None):
        self.db = Database(db_path)
        self.user_model = User(self.db)
        self.transaction_model = Transaction(self.db)
        self.category_model = Category(self.db)
        self.validator = DataValidator()
        self.permission_manager = PermissionManager()
    
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户登录
        Args:
            username: 用户名
            password: 密码
        Returns:
            用户信息字典，登录失败返回None
        """
        try:
            username = self.validator.validate_username(username)
            password = self.validator.validate_password(password)
            
            user = self.user_model.authenticate(username, password)
            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'last_login': user['last_login']
                }
            return None
        except ValidationError:
            return None
    
    def register(self, username: str, password: str, 
                 role: str = 'user') -> Tuple[bool, str]:
        """
        用户注册
        Args:
            username: 用户名
            password: 密码
            role: 角色
        Returns:
            (是否成功, 消息)
        """
        try:
            username = self.validator.validate_username(username)
            password = self.validator.validate_password(password)
            
            if self.user_model.get_by_username(username):
                return False, "用户名已存在"
            
            self.user_model.create(username, password, role)
            return True, "注册成功"
        except ValidationError as e:
            return False, str(e)
    
    def add_transaction(self, user: Dict[str, Any], trans_type: str,
                       amount: float, category: str, 
                       description: str = '', date: str = None) -> Tuple[bool, str]:
        """
        添加交易记录
        Args:
            user: 用户信息
            trans_type: 交易类型
            amount: 金额
            category: 分类
            description: 描述
            date: 日期
        Returns:
            (是否成功, 消息)
        """
        try:
            if not self.permission_manager.check_permission(user, 'write'):
                raise PermissionError("没有添加记录的权限")
            
            trans_type = self.validator.validate_transaction_type(trans_type)
            amount = self.validator.validate_amount(amount)
            
            categories = [c['name'] for c in self.category_model.get_all(trans_type)]
            category = self.validator.validate_category(category, trans_type, categories)
            
            description = self.validator.validate_description(description)
            
            if date:
                date = self.validator.validate_date(date)
            else:
                date = datetime.now().strftime(config.DATE_FORMAT)
            
            trans_id = self.transaction_model.create(
                user['id'], trans_type, amount, category, description, date
            )
            
            return True, f"交易记录添加成功，ID: {trans_id}"
        except (ValidationError, PermissionError) as e:
            return False, str(e)
    
    def update_transaction(self, user: Dict[str, Any], trans_id: int,
                          **kwargs) -> Tuple[bool, str]:
        """
        更新交易记录
        Args:
            user: 用户信息
            trans_id: 交易记录ID
            **kwargs: 更新字段
        Returns:
            (是否成功, 消息)
        """
        try:
            if not self.permission_manager.check_permission(user, 'write'):
                raise PermissionError("没有更新记录的权限")
            
            trans = self.transaction_model.get_by_id(trans_id)
            if not trans:
                return False, "交易记录不存在"
            
            if trans['user_id'] != user['id']:
                return False, "无权修改他人的记录"
            
            update_data = {}
            
            if 'amount' in kwargs:
                update_data['amount'] = self.validator.validate_amount(kwargs['amount'])
            
            if 'category' in kwargs:
                trans_type = kwargs.get('type', trans['type'])
                categories = [c['name'] for c in self.category_model.get_all(trans_type)]
                update_data['category'] = self.validator.validate_category(
                    kwargs['category'], trans_type, categories
                )
            
            if 'type' in kwargs:
                update_data['type'] = self.validator.validate_transaction_type(kwargs['type'])
            
            if 'description' in kwargs:
                update_data['description'] = self.validator.validate_description(
                    kwargs['description']
                )
            
            if 'date' in kwargs:
                update_data['date'] = self.validator.validate_date(kwargs['date'])
            
            if update_data:
                self.transaction_model.update(trans_id, **update_data)
                return True, "交易记录更新成功"
            
            return False, "没有需要更新的字段"
        except (ValidationError, PermissionError) as e:
            return False, str(e)
    
    def delete_transaction(self, user: Dict[str, Any], 
                          trans_id: int) -> Tuple[bool, str]:
        """
        删除交易记录
        Args:
            user: 用户信息
            trans_id: 交易记录ID
        Returns:
            (是否成功, 消息)
        """
        try:
            if not self.permission_manager.check_permission(user, 'delete'):
                raise PermissionError("没有删除记录的权限")
            
            trans = self.transaction_model.get_by_id(trans_id)
            if not trans:
                return False, "交易记录不存在"
            
            if trans['user_id'] != user['id']:
                return False, "无权删除他人的记录"
            
            self.transaction_model.delete(trans_id)
            return True, "交易记录删除成功"
        except PermissionError as e:
            return False, str(e)
    
    def get_transactions(self, user: Dict[str, Any], 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的交易记录
        Args:
            user: 用户信息
            limit: 返回数量限制
        Returns:
            交易记录列表
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return []
        
        return self.transaction_model.get_by_user(user['id'], limit)
    
    def get_transactions_by_date(self, user: Dict[str, Any], 
                                start_date: str, 
                                end_date: str) -> List[Dict[str, Any]]:
        """
        获取日期范围内的交易记录
        Args:
            user: 用户信息
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            交易记录列表
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return []
        
        return self.transaction_model.get_by_date_range(
            user['id'], start_date, end_date
        )
    
    def get_monthly_report(self, user: Dict[str, Any], 
                          year: int, month: int) -> Dict[str, Any]:
        """
        获取月度财务报告
        Args:
            user: 用户信息
            year: 年份
            month: 月份
        Returns:
            月度报告数据
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return {}
        
        summary = self.transaction_model.get_monthly_summary(user['id'], year, month)
        
        start_date, end_date = get_month_range(year, month)
        transactions = self.transaction_model.get_by_date_range(
            user['id'], start_date, end_date
        )
        
        category_summary = self.transaction_model.get_category_summary(
            user['id'], start_date=start_date, end_date=end_date
        )
        
        return {
            'year': year,
            'month': month,
            'summary': summary,
            'transactions': transactions,
            'category_summary': category_summary
        }
    
    def get_yearly_report(self, user: Dict[str, Any], 
                         year: int) -> Dict[str, Any]:
        """
        获取年度财务报告
        Args:
            user: 用户信息
            year: 年份
        Returns:
            年度报告数据
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return {}
        
        summary = self.transaction_model.get_yearly_summary(user['id'], year)
        
        start_date, end_date = get_year_range(year)
        
        monthly_data = []
        for month in range(1, 13):
            month_summary = self.transaction_model.get_monthly_summary(
                user['id'], year, month
            )
            monthly_data.append({
                'month': month,
                'income': month_summary['income'],
                'expense': month_summary['expense'],
                'balance': month_summary['balance']
            })
        
        category_summary = self.transaction_model.get_category_summary(
            user['id'], start_date=start_date, end_date=end_date
        )
        
        return {
            'year': year,
            'summary': summary,
            'monthly_data': monthly_data,
            'category_summary': category_summary
        }
    
    def get_category_report(self, user: Dict[str, Any], 
                           trans_type: str = None,
                           start_date: str = None, 
                           end_date: str = None) -> Dict[str, Any]:
        """
        获取分类统计报告
        Args:
            user: 用户信息
            trans_type: 交易类型
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            分类报告数据
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return {}
        
        category_data = self.transaction_model.get_category_summary(
            user['id'], trans_type, start_date, end_date
        )
        
        total_income = sum(c['total'] for c in category_data if c['type'] == 'income')
        total_expense = sum(c['total'] for c in category_data if c['type'] == 'expense')
        
        for item in category_data:
            if item['type'] == 'income':
                item['percentage'] = calculate_percentage(item['total'], total_income)
            else:
                item['percentage'] = calculate_percentage(item['total'], total_expense)
        
        return {
            'type': trans_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'total_expense': total_expense,
            'category_data': category_data
        }
    
    def get_trend_data(self, user: Dict[str, Any], 
                      months: int = 6) -> Dict[str, Any]:
        """
        获取收支趋势数据
        Args:
            user: 用户信息
            months: 月份数量
        Returns:
            趋势数据
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return {}
        
        today = datetime.now()
        trend_data = []
        
        for i in range(months - 1, -1, -1):
            date = today - timedelta(days=i * 30)
            year, month = date.year, date.month
            
            summary = self.transaction_model.get_monthly_summary(
                user['id'], year, month
            )
            
            trend_data.append({
                'year': year,
                'month': month,
                'label': f'{year}-{month:02d}',
                'income': summary['income'],
                'expense': summary['expense'],
                'balance': summary['balance']
            })
        
        return {
            'months': months,
            'trend_data': trend_data
        }
    
    def get_categories(self, trans_type: str = None) -> List[Dict[str, Any]]:
        """
        获取分类列表
        Args:
            trans_type: 交易类型
        Returns:
            分类列表
        """
        return self.category_model.get_all(trans_type)
    
    def add_category(self, name: str, trans_type: str, 
                    user_id: int = None) -> Tuple[bool, str]:
        """
        添加自定义分类
        Args:
            name: 分类名称
            trans_type: 交易类型
            user_id: 用户ID
        Returns:
            (是否成功, 消息)
        """
        try:
            trans_type = self.validator.validate_transaction_type(trans_type)
            
            if not name or not name.strip():
                return False, "分类名称不能为空"
            
            name = name.strip()
            
            existing = self.category_model.get_all(trans_type)
            if any(c['name'] == name for c in existing):
                return False, "分类已存在"
            
            self.category_model.create(name, trans_type, user_id)
            return True, "分类添加成功"
        except ValidationError as e:
            return False, str(e)
    
    def export_data(self, user: Dict[str, Any], 
                   filepath: str, start_date: str = None, 
                   end_date: str = None) -> Tuple[bool, str]:
        """
        导出数据到CSV
        Args:
            user: 用户信息
            filepath: 文件路径
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            (是否成功, 消息)
        """
        try:
            if not self.permission_manager.check_permission(user, 'export'):
                raise PermissionError("没有导出数据的权限")
            
            if start_date and end_date:
                transactions = self.get_transactions_by_date(
                    user, start_date, end_date
                )
            else:
                transactions = self.get_transactions(user, limit=10000)
            
            if not transactions:
                return False, "没有数据可导出"
            
            from utils import export_to_csv
            export_to_csv(transactions, filepath)
            
            return True, f"成功导出 {len(transactions)} 条记录到 {filepath}"
        except PermissionError as e:
            return False, str(e)
    
    def get_overview(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取财务概览
        Args:
            user: 用户信息
        Returns:
            概览数据
        """
        if not self.permission_manager.check_permission(user, 'read'):
            return {}
        
        today = datetime.now()
        year, month = today.year, today.month
        
        current_month = self.transaction_model.get_monthly_summary(
            user['id'], year, month
        )
        
        current_year = self.transaction_model.get_yearly_summary(
            user['id'], year
        )
        
        recent_transactions = self.transaction_model.get_by_user(user['id'], 10)
        
        return {
            'current_month': current_month,
            'current_year': current_year,
            'recent_transactions': recent_transactions
        }
