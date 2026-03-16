"""
智能财务管理系统 - 主程序入口

Finance Management System - Main Entry Point

Usage:
    python main.py              # 启动交互式CLI
    python main.py --help       # 显示帮助信息
    python main.py --demo       # 运行演示模式

Author: Finance Management System
Version: 1.0.0
"""

import sys
import argparse
from datetime import datetime, timedelta
import random

from cli import CLI, main as cli_main
from data_manager import FinanceManager
from models import Transaction, TransactionType
from config import CATEGORIES


def print_banner():
    """打印系统横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           💰 智能财务管理系统 💰                               ║
    ║           Finance Management System                            ║
    ║                                                               ║
    ║           版本: 1.0.0                                         ║
    ║           支持: 收支管理 | 报表生成 | 数据分析 | 可视化        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_demo():
    """运行演示模式 - 生成示例数据并展示功能"""
    print_banner()
    print("\n正在启动演示模式...")
    print("=" * 60)
    
    # 初始化管理器
    manager = FinanceManager()
    
    # 登录
    print("\n1. 用户登录")
    if manager.login('admin', 'admin123'):
        print("✓ 登录成功！")
    else:
        print("✗ 登录失败")
        return
    
    # 生成示例数据
    print("\n2. 生成示例交易数据...")
    generate_sample_data(manager)
    
    # 展示功能
    print("\n3. 数据查询演示")
    from visualizer import FinanceVisualizer, Dashboard
    
    visualizer = FinanceVisualizer()
    dashboard = Dashboard(visualizer)
    
    # 生成本月报表
    current_month = datetime.now().strftime('%Y-%m')
    print(f"\n4. 生成 {current_month} 月度报表")
    monthly_report = manager.reports.generate_monthly_report(current_month)
    
    # 显示文本报表
    text_report = visualizer.generate_text_report(monthly_report)
    print(text_report)
    
    # 生成趋势分析
    print("\n5. 生成收支趋势分析（近6个月）")
    trend_data = manager.reports.get_trend_analysis(6)
    
    print("\n月度收支数据:")
    print("-" * 50)
    for i, month in enumerate(trend_data['months']):
        print(f"{month}: 收入 ¥{trend_data['income'][i]:,.2f} | "
              f"支出 ¥{trend_data['expense'][i]:,.2f} | "
              f"结余 ¥{trend_data['balance'][i]:,.2f}")
    
    # 生成分类统计
    print("\n6. 分类统计分析")
    summary = manager.transactions.get_all_categories_summary()
    
    print("\n收入分类:")
    for category, amount in sorted(summary['income'].items(), 
                                    key=lambda x: x[1], reverse=True):
        print(f"  {category}: ¥{amount:,.2f}")
    
    print("\n支出分类:")
    for category, amount in sorted(summary['expense'].items(),
                                    key=lambda x: x[1], reverse=True):
        print(f"  {category}: ¥{amount:,.2f}")
    
    # 生成图表（保存但不显示）
    print("\n7. 生成可视化图表...")
    
    # 趋势图
    trend_file = visualizer.plot_monthly_trend(
        trend_data,
        title='收支趋势分析（演示）',
        filename='demo_trend.png',
        show=False
    )
    if trend_file:
        print(f"  ✓ 趋势图已保存: {trend_file}")
    
    # 支出分类饼图
    if monthly_report.category_breakdown.get('expense'):
        pie_file = visualizer.plot_category_pie(
            monthly_report.category_breakdown['expense'],
            title='支出分类占比（演示）',
            filename='demo_expense_pie.png',
            show=False
        )
        if pie_file:
            print(f"  ✓ 支出饼图已保存: {pie_file}")
    
    # 收支对比图
    comparison_file = visualizer.plot_category_comparison(
        summary.get('income', {}),
        summary.get('expense', {}),
        title='收支分类对比（演示）',
        filename='demo_comparison.png',
        show=False
    )
    if comparison_file:
        print(f"  ✓ 对比图已保存: {comparison_file}")
    
    # 生成年报
    print("\n8. 生成年度报表")
    current_year = datetime.now().year
    annual_report = manager.reports.generate_annual_report(current_year)
    
    print(f"\n{current_year}年汇总:")
    print(f"  总收入: ¥{annual_report.total_income:,.2f}")
    print(f"  总支出: ¥{annual_report.total_expense:,.2f}")
    print(f"  年度结余: ¥{annual_report.balance:,.2f}")
    
    print("\n" + "=" * 60)
    print("演示模式完成！")
    print("\n生成的文件保存在 exports/ 目录中")
    print("\n提示: 使用 'python main.py' 启动交互式CLI进行完整操作")


def generate_sample_data(manager: FinanceManager):
    """生成示例数据"""
    # 生成最近3个月的数据
    today = datetime.now()
    
    income_categories = CATEGORIES['income']
    expense_categories = CATEGORIES['expense']
    
    transaction_count = 0
    
    # 为最近3个月生成数据
    for month_offset in range(3):
        month_date = today - timedelta(days=30*month_offset)
        year_month = month_date.strftime('%Y-%m')
        
        # 生成收入记录（每月5-8条）
        for _ in range(random.randint(5, 8)):
            day = random.randint(1, 28)
            date = f"{year_month}-{day:02d}"
            
            transaction = Transaction(
                amount=random.choice([5000, 8000, 12000, 3000, 2000]),
                type=TransactionType.INCOME,
                category=random.choice(income_categories),
                date=date,
                note="示例收入数据",
                user_id=manager.current_user.username
            )
            manager.transactions.add_transaction(transaction)
            transaction_count += 1
        
        # 生成支出记录（每月10-15条）
        for _ in range(random.randint(10, 15)):
            day = random.randint(1, 28)
            date = f"{year_month}-{day:02d}"
            
            transaction = Transaction(
                amount=random.choice([50, 100, 200, 500, 1000, 30, 80]),
                type=TransactionType.EXPENSE,
                category=random.choice(expense_categories),
                date=date,
                note="示例支出数据",
                user_id=manager.current_user.username
            )
            manager.transactions.add_transaction(transaction)
            transaction_count += 1
    
    print(f"  ✓ 已生成 {transaction_count} 条示例交易记录")


def run_tests():
    """运行基础测试"""
    print("\n运行基础测试...")
    print("=" * 60)
    
    try:
        # 测试1: 数据验证
        print("\n测试1: 数据验证")
        from utils import Validator, ValidationError
        
        validator = Validator()
        
        # 测试金额验证
        assert validator.validate_amount(100.50) == 100.50
        assert validator.validate_amount("200.75") == 200.75
        print("  ✓ 金额验证通过")
        
        # 测试日期验证
        assert validator.validate_date("2024-01-15") == "2024-01-15"
        print("  ✓ 日期验证通过")
        
        # 测试2: 数据库连接
        print("\n测试2: 数据库连接")
        manager = FinanceManager()
        print("  ✓ 数据库连接成功")
        
        # 测试3: 用户认证
        print("\n测试3: 用户认证")
        assert manager.login('admin', 'admin123') == True
        print("  ✓ 用户认证通过")
        
        # 测试4: 交易记录CRUD
        print("\n测试4: 交易记录操作")
        
        # 添加
        transaction = Transaction(
            amount=1000.00,
            type=TransactionType.INCOME,
            category='工资',
            date='2024-03-15',
            note='测试数据',
            user_id='admin'
        )
        trans_id = manager.transactions.add_transaction(transaction)
        assert trans_id is not None
        print(f"  ✓ 添加记录成功，ID: {trans_id}")
        
        # 查询
        retrieved = manager.transactions.get_transaction_by_id(trans_id)
        assert retrieved is not None
        assert retrieved.amount == 1000.00
        print("  ✓ 查询记录成功")
        
        # 更新
        updated = manager.transactions.update_transaction(
            trans_id, {'amount': 1500.00}
        )
        assert updated == True
        print("  ✓ 更新记录成功")
        
        # 删除
        deleted = manager.transactions.delete_transaction(trans_id)
        assert deleted == True
        print("  ✓ 删除记录成功")
        
        # 测试5: 报表生成
        print("\n测试5: 报表生成")
        report = manager.reports.generate_monthly_report('2024-03')
        assert report is not None
        print("  ✓ 月度报表生成成功")
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='智能财务管理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              # 启动交互式CLI
  python main.py --demo       # 运行演示模式
  python main.py --test       # 运行基础测试
        """
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示模式，生成示例数据并展示功能'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行基础测试'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='智能财务管理系统 1.0.0'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    elif args.demo:
        run_demo()
    else:
        # 默认启动CLI
        print_banner()
        cli_main()


if __name__ == '__main__':
    main()
