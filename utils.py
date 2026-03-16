# -*- coding: utf-8 -*-
"""
工具/通用层 - 数据校验、权限控制、辅助函数
"""
import re
from datetime import datetime, date
from typing import Tuple, Optional, Dict, Any, List
from functools import wraps

import config


class ValidationError(Exception):
    """数据校验异常"""
    pass


class PermissionError(Exception):
    """权限异常"""
    pass


class DataValidator:
    """数据校验器"""
    
    @staticmethod
    def validate_amount(amount: Any) -> float:
        """
        校验金额
        Args:
            amount: 待校验的金额
        Returns:
            校验后的金额
        Raises:
            ValidationError: 校验失败
        """
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValidationError(f"金额格式错误: {amount}")
        
        if amount < config.MIN_AMOUNT:
            raise ValidationError(f"金额不能小于 {config.MIN_AMOUNT}")
        
        if amount > config.MAX_AMOUNT:
            raise ValidationError(f"金额不能超过 {config.MAX_AMOUNT}")
        
        return round(amount, 2)
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """
        校验日期格式
        Args:
            date_str: 日期字符串
        Returns:
            校验后的日期字符串
        Raises:
            ValidationError: 校验失败
        """
        try:
            parsed_date = datetime.strptime(date_str, config.DATE_FORMAT)
            if parsed_date.date() > date.today():
                raise ValidationError("日期不能是未来日期")
            return date_str
        except ValueError:
            raise ValidationError(f"日期格式错误，请使用 {config.DATE_FORMAT} 格式")
    
    @staticmethod
    def validate_category(category: str, trans_type: str, 
                         categories: List[str]) -> str:
        """
        校验分类
        Args:
            category: 分类名称
            trans_type: 交易类型
            categories: 有效分类列表
        Returns:
            校验后的分类名称
        Raises:
            ValidationError: 校验失败
        """
        if not category or not category.strip():
            raise ValidationError("分类不能为空")
        
        category = category.strip()
        
        if category not in categories:
            raise ValidationError(f"无效分类: {category}，有效分类: {', '.join(categories)}")
        
        return category
    
    @staticmethod
    def validate_transaction_type(trans_type: str) -> str:
        """
        校验交易类型
        Args:
            trans_type: 交易类型
        Returns:
            校验后的交易类型
        Raises:
            ValidationError: 校验失败
        """
        if trans_type not in ['income', 'expense']:
            raise ValidationError(f"交易类型错误: {trans_type}，必须是 income 或 expense")
        return trans_type
    
    @staticmethod
    def validate_username(username: str) -> str:
        """
        校验用户名
        Args:
            username: 用户名
        Returns:
            校验后的用户名
        Raises:
            ValidationError: 校验失败
        """
        if not username or not username.strip():
            raise ValidationError("用户名不能为空")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError("用户名长度不能少于3个字符")
        
        if len(username) > 20:
            raise ValidationError("用户名长度不能超过20个字符")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("用户名只能包含字母、数字和下划线")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """
        校验密码
        Args:
            password: 密码
        Returns:
            校验后的密码
        Raises:
            ValidationError: 校验失败
        """
        if not password:
            raise ValidationError("密码不能为空")
        
        if len(password) < 6:
            raise ValidationError("密码长度不能少于6个字符")
        
        if len(password) > 50:
            raise ValidationError("密码长度不能超过50个字符")
        
        return password
    
    @staticmethod
    def validate_description(description: str) -> str:
        """
        校验描述
        Args:
            description: 描述内容
        Returns:
            校验后的描述
        """
        if description is None:
            return ''
        
        description = str(description).strip()
        
        if len(description) > 200:
            raise ValidationError("描述长度不能超过200个字符")
        
        return description


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.user_permissions = config.USER_ROLES
    
    def has_permission(self, role: str, permission: str) -> bool:
        """
        检查角色是否具有指定权限
        Args:
            role: 用户角色
            permission: 权限名称
        Returns:
            是否具有权限
        """
        if role not in self.user_permissions:
            return False
        return permission in self.user_permissions[role]
    
    def check_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """
        检查用户是否具有指定权限
        Args:
            user: 用户信息字典
            permission: 权限名称
        Returns:
            是否具有权限
        """
        if not user:
            return False
        return self.has_permission(user.get('role', 'guest'), permission)
    
    def require_permission(self, permission: str):
        """
        权限装饰器
        Args:
            permission: 所需权限
        Returns:
            装饰器函数
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = kwargs.get('user') or (args[0] if args else None)
                if not self.check_permission(user, permission):
                    raise PermissionError(f"权限不足: 需要 {permission} 权限")
                return func(*args, **kwargs)
            return wrapper
        return decorator


def format_currency(amount: float) -> str:
    """
    格式化货币金额
    Args:
        amount: 金额
    Returns:
        格式化后的金额字符串
    """
    return f"¥{amount:,.2f}"


def format_date(date_str: str) -> str:
    """
    格式化日期显示
    Args:
        date_str: 日期字符串
    Returns:
        格式化后的日期字符串
    """
    try:
        dt = datetime.strptime(date_str, config.DATE_FORMAT)
        return dt.strftime('%Y年%m月%d日')
    except ValueError:
        return date_str


def parse_date_range(start: str, end: str) -> Tuple[str, str]:
    """
    解析日期范围
    Args:
        start: 开始日期
        end: 结束日期
    Returns:
        (开始日期, 结束日期) 元组
    Raises:
        ValidationError: 日期范围无效
    """
    try:
        start_date = datetime.strptime(start, config.DATE_FORMAT)
        end_date = datetime.strptime(end, config.DATE_FORMAT)
        
        if start_date > end_date:
            raise ValidationError("开始日期不能晚于结束日期")
        
        return start, end
    except ValueError:
        raise ValidationError(f"日期格式错误，请使用 {config.DATE_FORMAT} 格式")


def get_month_range(year: int, month: int) -> Tuple[str, str]:
    """
    获取月份的日期范围
    Args:
        year: 年份
        month: 月份
    Returns:
        (开始日期, 结束日期) 元组
    """
    if month == 12:
        next_month = f'{year + 1}-01-01'
    else:
        next_month = f'{year}-{month + 1:02d}-01'
    
    start_date = f'{year}-{month:02d}-01'
    return start_date, next_month


def get_year_range(year: int) -> Tuple[str, str]:
    """
    获取年份的日期范围
    Args:
        year: 年份
    Returns:
        (开始日期, 结束日期) 元组
    """
    return f'{year}-01-01', f'{year + 1}-01-01'


def calculate_percentage(value: float, total: float) -> float:
    """
    计算百分比
    Args:
        value: 数值
        total: 总数
    Returns:
        百分比
    """
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def print_table(data: List[Dict[str, Any]], columns: List[str], 
                headers: List[str] = None):
    """
    打印表格数据
    Args:
        data: 数据列表
        columns: 列名列表
        headers: 表头列表（可选）
    """
    if not data:
        print("暂无数据")
        return
    
    if headers is None:
        headers = columns
    
    col_widths = [len(h) for h in headers]
    
    for row in data:
        for i, col in enumerate(columns):
            value = str(row.get(col, ''))
            col_widths[i] = max(col_widths[i], len(value))
    
    header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, col_widths))
    separator = '-+-'.join('-' * w for w in col_widths)
    
    print(header_line)
    print(separator)
    
    for row in data:
        row_line = ' | '.join(
            str(row.get(col, '')).ljust(w) 
            for col, w in zip(columns, col_widths)
        )
        print(row_line)


def export_to_csv(data: List[Dict[str, Any]], filepath: str, 
                  encoding: str = 'utf-8-sig'):
    """
    导出数据到CSV文件
    Args:
        data: 数据列表
        filepath: 文件路径
        encoding: 文件编码
    """
    import csv
    
    if not data:
        raise ValueError("没有数据可导出")
    
    fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='', encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def import_from_csv(filepath: str, encoding: str = 'utf-8-sig') -> List[Dict[str, Any]]:
    """
    从CSV文件导入数据
    Args:
        filepath: 文件路径
        encoding: 文件编码
    Returns:
        数据列表
    """
    import csv
    
    data = []
    with open(filepath, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(dict(row))
    
    return data
