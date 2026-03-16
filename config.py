# -*- coding: utf-8 -*-
"""
配置文件 - 系统配置和常量定义
"""
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'finance.db')

DEFAULT_CATEGORIES = {
    'income': ['工资', '奖金', '投资收益', '其他收入'],
    'expense': ['餐饮', '交通', '购物', '娱乐', '医疗', '教育', '房租', '水电', '其他支出']
}

USER_ROLES = {
    'admin': ['read', 'write', 'delete', 'export'],
    'user': ['read', 'write'],
    'guest': ['read']
}

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

REPORT_TYPES = ['monthly', 'yearly', 'category']

CHART_COLORS = {
    'income': '#2ecc71',
    'expense': '#e74c3c',
    'balance': '#3498db'
}

DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'role': 'admin'
}

MIN_AMOUNT = 0.01
MAX_AMOUNT = 100000000.0
