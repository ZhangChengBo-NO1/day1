"""
工具/通用层 - 智能财务管理系统

提供通用工具函数、数据验证、加密、格式化等功能
"""

import hashlib
import re
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any, Union
from decimal import Decimal, ROUND_HALF_UP

from config import VALIDATION, CATEGORIES, REPORT_CONFIG


class ValidationError(Exception):
    """数据验证异常"""
    pass


class AuthenticationError(Exception):
    """认证异常"""
    pass


class DataFormatError(Exception):
    """数据格式异常"""
    pass


class Validator:
    """数据验证器"""
    
    @staticmethod
    def validate_amount(amount: Union[str, float, int]) -> float:
        """
        验证金额
        
        Args:
            amount: 金额值
            
        Returns:
            float: 验证后的金额
            
        Raises:
            ValidationError: 金额不合法
        """
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValidationError('金额必须是数字')
        
        if amount < VALIDATION['min_amount']:
            raise ValidationError(f'金额不能小于 {VALIDATION["min_amount"]}')
        
        if amount > VALIDATION['max_amount']:
            raise ValidationError(f'金额不能超过 {VALIDATION["max_amount"]}')
        
        # 保留两位小数
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """
        验证日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            str: 验证后的日期字符串
            
        Raises:
            ValidationError: 日期格式不合法
        """
        try:
            date_obj = datetime.strptime(date_str, REPORT_CONFIG['date_format'])
        except ValueError:
            raise ValidationError(f'日期格式错误，请使用 {REPORT_CONFIG["date_format"]} 格式')
        
        # 检查日期范围
        now = datetime.now()
        max_date = now + timedelta(days=1)  # 允许明天的数据
        min_date = now - timedelta(days=365 * VALIDATION['allowed_date_range_years'])
        
        # 只检查年份是否合理，不限制未来日期（允许录入未来的预算）
        if date_obj.year > now.year + 1:
            raise ValidationError('日期年份不能超过明年')
        
        if date_obj.year < now.year - VALIDATION['allowed_date_range_years']:
            raise ValidationError(f'日期年份不能早于 {now.year - VALIDATION["allowed_date_range_years"]} 年')
        
        return date_str
    
    @staticmethod
    def validate_category(category: str, trans_type: str) -> str:
        """
        验证分类
        
        Args:
            category: 分类名称
            trans_type: 交易类型
            
        Returns:
            str: 验证后的分类
            
        Raises:
            ValidationError: 分类不合法
        """
        if not category or not isinstance(category, str):
            raise ValidationError('分类不能为空')
        
        category = category.strip()
        
        valid_categories = CATEGORIES.get(trans_type, [])
        if category not in valid_categories:
            raise ValidationError(f'无效的分类 "{category}"，有效分类: {", ".join(valid_categories)}')
        
        return category
    
    @staticmethod
    def validate_note(note: str) -> str:
        """
        验证备注
        
        Args:
            note: 备注内容
            
        Returns:
            str: 验证后的备注
            
        Raises:
            ValidationError: 备注不合法
        """
        if note is None:
            return ''
        
        note = str(note).strip()
        
        if len(note) > VALIDATION['max_note_length']:
            raise ValidationError(f'备注长度不能超过 {VALIDATION["max_note_length"]} 字符')
        
        return note
    
    @staticmethod
    def validate_username(username: str) -> str:
        """
        验证用户名
        
        Args:
            username: 用户名
            
        Returns:
            str: 验证后的用户名
            
        Raises:
            ValidationError: 用户名不合法
        """
        if not username:
            raise ValidationError('用户名不能为空')
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError('用户名长度至少3个字符')
        
        if len(username) > 20:
            raise ValidationError('用户名长度不能超过20个字符')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('用户名只能包含字母、数字和下划线')
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            str: 验证后的密码
            
        Raises:
            ValidationError: 密码不合法
        """
        if not password:
            raise ValidationError('密码不能为空')
        
        if len(password) < 6:
            raise ValidationError('密码长度至少6个字符')
        
        return password


class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        对密码进行哈希处理
        
        Args:
            password: 原始密码
            salt: 盐值（可选）
            
        Returns:
            Tuple[str, str]: (哈希后的密码, 盐值)
        """
        if salt is None:
            salt = os.urandom(32).hex()
        
        salted_password = f"{password}{salt}"
        hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
        
        return hash_obj.hexdigest(), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed_password: 哈希后的密码
            salt: 盐值
            
        Returns:
            bool: 密码是否正确
        """
        computed_hash, _ = SecurityUtils.hash_password(password, salt)
        return computed_hash == hashed_password
    
    @staticmethod
    def generate_token(username: str) -> str:
        """
        生成简单的认证令牌
        
        Args:
            username: 用户名
            
        Returns:
            str: 令牌字符串
        """
        timestamp = datetime.now().isoformat()
        data = f"{username}:{timestamp}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


class FormatUtils:
    """格式化工具类"""
    
    @staticmethod
    def format_currency(amount: float, symbol: str = None) -> str:
        """
        格式化货币金额
        
        Args:
            amount: 金额
            symbol: 货币符号
            
        Returns:
            str: 格式化后的金额字符串
        """
        if symbol is None:
            symbol = REPORT_CONFIG['currency_symbol']
        
        return f"{symbol}{amount:,.2f}"
    
    @staticmethod
    def format_date(date_str: str, output_format: str = None) -> str:
        """
        格式化日期
        
        Args:
            date_str: 日期字符串
            output_format: 输出格式
            
        Returns:
            str: 格式化后的日期字符串
        """
        if output_format is None:
            output_format = REPORT_CONFIG['date_format']
        
        try:
            date_obj = datetime.strptime(date_str, REPORT_CONFIG['date_format'])
            return date_obj.strftime(output_format)
        except ValueError:
            return date_str
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """
        格式化百分比
        
        Args:
            value: 小数值（如0.25表示25%）
            decimals: 小数位数
            
        Returns:
            str: 格式化后的百分比字符串
        """
        return f"{value * 100:.{decimals}f}%"
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
        """
        截断字符串
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            str: 截断后的字符串
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix


class DateUtils:
    """日期工具类"""
    
    @staticmethod
    def get_current_month() -> str:
        """获取当前月份"""
        return datetime.now().strftime(REPORT_CONFIG['month_format'])
    
    @staticmethod
    def get_current_year() -> int:
        """获取当前年份"""
        return datetime.now().year
    
    @staticmethod
    def get_month_range(year_month: str) -> Tuple[str, str]:
        """
        获取月份的起止日期
        
        Args:
            year_month: 年月（YYYY-MM）
            
        Returns:
            Tuple[str, str]: (开始日期, 结束日期)
        """
        year, month = map(int, year_month.split('-'))
        start_date = f"{year_month}-01"
        
        # 计算下月第一天，再减一天
        if month == 12:
            next_month = f"{year + 1}-01-01"
        else:
            next_month = f"{year}-{month + 1:02d}-01"
        
        end_date = (datetime.strptime(next_month, REPORT_CONFIG['date_format']) - 
                   timedelta(days=1)).strftime(REPORT_CONFIG['date_format'])
        
        return start_date, end_date
    
    @staticmethod
    def get_year_range(year: int) -> Tuple[str, str]:
        """
        获取年份的起止日期
        
        Args:
            year: 年份
            
        Returns:
            Tuple[str, str]: (开始日期, 结束日期)
        """
        return f"{year}-01-01", f"{year}-12-31"
    
    @staticmethod
    def parse_months(months: int = 12) -> List[str]:
        """
        获取最近N个月的月份列表
        
        Args:
            months: 月数
            
        Returns:
            List[str]: 月份列表（YYYY-MM）
        """
        result = []
        now = datetime.now()
        
        for i in range(months):
            date = now - timedelta(days=30 * i)
            result.append(date.strftime(REPORT_CONFIG['month_format']))
        
        return sorted(result)


class CalculationUtils:
    """计算工具类"""
    
    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        """
        计算百分比
        
        Args:
            part: 部分值
            total: 总值
            
        Returns:
            float: 百分比（0-1之间）
        """
        if total == 0:
            return 0.0
        return round(part / total, 4)
    
    @staticmethod
    def calculate_growth_rate(current: float, previous: float) -> float:
        """
        计算增长率
        
        Args:
            current: 当前值
            previous: 前值
            
        Returns:
            float: 增长率
        """
        if previous == 0:
            return 0.0 if current == 0 else float('inf')
        return round((current - previous) / previous, 4)
    
    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """
        计算平均值
        
        Args:
            values: 数值列表
            
        Returns:
            float: 平均值
        """
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)
    
    @staticmethod
    def calculate_median(values: List[float]) -> float:
        """
        计算中位数
        
        Args:
            values: 数值列表
            
        Returns:
            float: 中位数
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]


# 便捷函数
def validate_transaction_data(amount, trans_type, category, date, note=''):
    """验证交易数据"""
    validator = Validator()
    
    validated = {
        'amount': validator.validate_amount(amount),
        'type': trans_type,
        'category': validator.validate_category(category, trans_type),
        'date': validator.validate_date(date),
        'note': validator.validate_note(note)
    }
    
    return validated


def format_report_number(number: float, is_currency: bool = True) -> str:
    """格式化报表数字"""
    if is_currency:
        return FormatUtils.format_currency(number)
    return f"{number:,.2f}"
