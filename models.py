"""
数据模型层 - 智能财务管理系统

定义财务数据的实体类和数据结构，包括交易记录、用户、分类等模型
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class TransactionType(Enum):
    """交易类型枚举"""
    INCOME = 'income'
    EXPENSE = 'expense'


class Permission(Enum):
    """权限枚举"""
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'
    EXPORT = 'export'
    MANAGE_USERS = 'manage_users'


@dataclass
class Transaction:
    """
    交易记录模型
    
    Attributes:
        id: 唯一标识符
        amount: 金额（正数）
        type: 交易类型（收入/支出）
        category: 分类
        date: 交易日期
        note: 备注
        created_at: 创建时间
        updated_at: 更新时间
        user_id: 所属用户ID
    """
    id: Optional[int] = None
    amount: float = 0.0
    type: TransactionType = TransactionType.EXPENSE
    category: str = ''
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    note: str = ''
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: str = 'default'
    
    def __post_init__(self):
        """初始化后处理，确保类型正确"""
        if isinstance(self.type, str):
            self.type = TransactionType(self.type)
        if isinstance(self.amount, str):
            self.amount = float(self.amount)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """从字典创建实例"""
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = TransactionType(data['type'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Transaction':
        """从JSON字符串创建实例"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class User:
    """
    用户模型
    
    Attributes:
        username: 用户名
        password_hash: 密码哈希
        role: 角色
        permissions: 权限列表
        created_at: 创建时间
        last_login: 最后登录时间
        is_active: 是否激活
    """
    username: str
    password_hash: str
    role: str = 'user'
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建实例"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        return permission.value in self.permissions or self.role == 'admin'


@dataclass
class Category:
    """
    分类模型
    
    Attributes:
        name: 分类名称
        type: 分类类型（收入/支出）
        description: 描述
        budget_limit: 预算限额（可选）
    """
    name: str
    type: TransactionType
    description: str = ''
    budget_limit: Optional[float] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.type, str):
            self.type = TransactionType(self.type)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        return data


@dataclass
class MonthlyReport:
    """
    月度报表模型
    
    Attributes:
        year_month: 年月（格式：YYYY-MM）
        total_income: 总收入
        total_expense: 总支出
        balance: 结余
        category_breakdown: 分类统计
        transaction_count: 交易笔数
    """
    year_month: str
    total_income: float = 0.0
    total_expense: float = 0.0
    balance: float = 0.0
    category_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    transaction_count: int = 0
    
    def __post_init__(self):
        """计算结余"""
        self.balance = self.total_income - self.total_expense
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AnnualReport:
    """
    年度报表模型
    
    Attributes:
        year: 年份
        total_income: 总收入
        total_expense: 总支出
        balance: 结余
        monthly_data: 月度数据列表
        top_categories: 主要分类
    """
    year: int
    total_income: float = 0.0
    total_expense: float = 0.0
    balance: float = 0.0
    monthly_data: List[MonthlyReport] = field(default_factory=list)
    top_categories: Dict[str, List[tuple]] = field(default_factory=dict)
    
    def __post_init__(self):
        """计算结余"""
        self.balance = self.total_income - self.total_expense
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'year': self.year,
            'total_income': self.total_income,
            'total_expense': self.total_expense,
            'balance': self.balance,
            'monthly_data': [m.to_dict() for m in self.monthly_data],
            'top_categories': self.top_categories
        }


class QueryFilter:
    """
    查询过滤器
    
    用于构建灵活的查询条件
    """
    
    def __init__(self):
        self.conditions: Dict[str, Any] = {}
    
    def by_date_range(self, start_date: str, end_date: str) -> 'QueryFilter':
        """按日期范围过滤"""
        self.conditions['date_range'] = (start_date, end_date)
        return self
    
    def by_type(self, trans_type: TransactionType) -> 'QueryFilter':
        """按交易类型过滤"""
        self.conditions['type'] = trans_type
        return self
    
    def by_category(self, category: str) -> 'QueryFilter':
        """按分类过滤"""
        self.conditions['category'] = category
        return self
    
    def by_amount_range(self, min_amount: float, max_amount: float) -> 'QueryFilter':
        """按金额范围过滤"""
        self.conditions['amount_range'] = (min_amount, max_amount)
        return self
    
    def by_user(self, user_id: str) -> 'QueryFilter':
        """按用户过滤"""
        self.conditions['user_id'] = user_id
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建查询条件"""
        return self.conditions.copy()
