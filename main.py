# -*- coding: utf-8 -*-
"""
智能财务管理系统 - 主程序入口
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import cli


def main():
    """主函数"""
    cli()


if __name__ == '__main__':
    main()
