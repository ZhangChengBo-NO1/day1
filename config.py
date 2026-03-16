"""
配置文件 - 智能财务管理系统

包含数据库配置、分类设置、权限配置等全局参数
"""

import os
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASE_CONFIG = {
    'name': 'finance.db',
    'path': os.path.join(BASE_DIR, 'finance.db')
}

# 收支分类配置
CATEGORIES = {
    'income': [
        '工资', '奖金', '投资', '兼职', '红包', '其他收入'
    ],
    'expense': [
        '餐饮', '交通', '购物', '娱乐', '医疗', '教育',
        '住房', '水电', '通讯', '旅游', '其他支出'
    ]
}

# 用户权限配置
ROLES = {
    'admin': {
        'permissions': ['read', 'write', 'delete', 'export', 'manage_users'],
        'description': '管理员'
    },
    'user': {
        'permissions': ['read', 'write', 'export'],
        'description': '普通用户'
    },
    'viewer': {
        'permissions': ['read'],
        'description': '只读用户'
    }
}

# 默认用户凭证（实际应用中应使用加密存储）
DEFAULT_USERS = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'created_at': datetime.now().isoformat()
    },
    'user': {
        'password': 'user123',
        'role': 'user',
        'created_at': datetime.now().isoformat()
    }
}

# 报表配置
REPORT_CONFIG = {
    'date_format': '%Y-%m-%d',
    'month_format': '%Y-%m',
    'currency_symbol': '¥',
    'default_chart_type': 'bar'
}

# 数据验证配置
VALIDATION = {
    'max_amount': 999999999.99,
    'min_amount': 0.01,
    'max_note_length': 200,
    'allowed_date_range_years': 10
}

# 可视化配置
VISUALIZATION = {
    'figure_size': (10, 6),
    'dpi': 100,
    'style': 'seaborn-v0_8-darkgrid',
    'color_palette': ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c']
}

# 导出配置
EXPORT_CONFIG = {
    'supported_formats': ['csv', 'json', 'excel'],
    'default_format': 'csv',
    'export_dir': os.path.join(BASE_DIR, 'exports')
}

# 确保导出目录存在
os.makedirs(EXPORT_CONFIG['export_dir'], exist_ok=True)
