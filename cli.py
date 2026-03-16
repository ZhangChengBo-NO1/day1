"""
用户交互层 - 智能财务管理系统

提供命令行交互界面(CLI)，处理用户输入和输出展示
"""

import os
import sys
from typing import Optional, List, Callable
from datetime import datetime
from getpass import getpass

from config import CATEGORIES, REPORT_CONFIG, EXPORT_CONFIG
from models import Transaction, TransactionType, QueryFilter
from data_manager import FinanceManager
from visualizer import FinanceVisualizer, Dashboard
from utils import (
    FormatUtils, DateUtils, ValidationError, 
    AuthenticationError, format_report_number
)


class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class CLI:
    """命令行交互界面"""
    
    def __init__(self):
        """初始化CLI"""
        self.manager = FinanceManager()
        self.visualizer = FinanceVisualizer()
        self.dashboard = Dashboard(self.visualizer)
        self.running = False
        
        # 检查是否支持颜色
        self.use_color = sys.platform != 'win32' or 'ANSICON' in os.environ
    
    def _color(self, text: str, color: str) -> str:
        """添加颜色"""
        if self.use_color:
            return f"{color}{text}{Colors.END}"
        return text
    
    def _print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 60)
        print(self._color(f"{title:^60}", Colors.HEADER + Colors.BOLD))
        print("=" * 60)
    
    def _print_success(self, message: str):
        """打印成功消息"""
        print(self._color(f"✓ {message}", Colors.GREEN))
    
    def _print_error(self, message: str):
        """打印错误消息"""
        print(self._color(f"✗ {message}", Colors.FAIL))
    
    def _print_warning(self, message: str):
        """打印警告消息"""
        print(self._color(f"! {message}", Colors.WARNING))
    
    def _print_info(self, message: str):
        """打印信息"""
        print(self._color(f"ℹ {message}", Colors.CYAN))
    
    def _input_required(self, prompt: str) -> str:
        """获取必填输入"""
        while True:
            value = input(prompt).strip()
            if value:
                return value
            self._print_error("此项为必填项，请重新输入")
    
    def _input_number(self, prompt: str, min_value: float = None,
                     max_value: float = None) -> float:
        """获取数字输入"""
        while True:
            try:
                value = float(input(prompt).strip())
                if min_value is not None and value < min_value:
                    self._print_error(f"数值不能小于 {min_value}")
                    continue
                if max_value is not None and value > max_value:
                    self._print_error(f"数值不能大于 {max_value}")
                    continue
                return value
            except ValueError:
                self._print_error("请输入有效的数字")
    
    def _input_choice(self, prompt: str, choices: List[str]) -> str:
        """获取选项输入"""
        while True:
            value = input(prompt).strip()
            if value in choices:
                return value
            self._print_error(f"无效选项，请从 {', '.join(choices)} 中选择")
    
    def _input_date(self, prompt: str, default: str = None) -> str:
        """获取日期输入"""
        while True:
            value = input(prompt).strip()
            if not value and default:
                return default
            if not value:
                value = datetime.now().strftime(REPORT_CONFIG['date_format'])
            
            try:
                datetime.strptime(value, REPORT_CONFIG['date_format'])
                return value
            except ValueError:
                self._print_error(
                    f"日期格式错误，请使用 {REPORT_CONFIG['date_format']} 格式"
                )
    
    def _display_menu(self, title: str, options: List[tuple]):
        """
        显示菜单
        
        Args:
            title: 菜单标题
            options: 选项列表 [(key, description), ...]
        """
        self._print_header(title)
        for key, desc in options:
            print(f"  {self._color(key, Colors.BOLD)}. {desc}")
        print("-" * 60)
    
    def run(self):
        """运行主程序"""
        self.running = True
        
        self._print_header("智能财务管理系统")
        print("欢迎使用智能财务管理系统！")
        
        # 登录
        if not self._login():
            return
        
        # 主循环
        while self.running:
            self._show_main_menu()
    
    def _login(self) -> bool:
        """
        用户登录
        
        Returns:
            bool: 登录是否成功
        """
        print("\n请先登录系统")
        print("默认账号: admin/admin123 或 user/user123")
        
        attempts = 3
        while attempts > 0:
            username = input("用户名: ").strip()
            password = getpass("密码: ")
            
            if self.manager.login(username, password):
                self._print_success(f"欢迎回来，{username}！")
                return True
            else:
                attempts -= 1
                self._print_error(f"登录失败，还剩 {attempts} 次尝试机会")
        
        self._print_error("登录失败次数过多，程序退出")
        return False
    
    def _show_main_menu(self):
        """显示主菜单"""
        options = [
            ("1", "记账管理 - 添加、修改、删除收支记录"),
            ("2", "数据查询 - 查看交易记录和明细"),
            ("3", "统计报表 - 生成月度/年度报表"),
            ("4", "数据分析 - 趋势分析和可视化"),
            ("5", "数据导出 - 导出数据到文件"),
            ("6", "系统管理 - 用户和设置"),
            ("0", "退出系统"),
        ]
        
        self._display_menu("主菜单", options)
        choice = input("请选择操作: ").strip()
        
        actions = {
            '1': self._transaction_management,
            '2': self._query_data,
            '3': self._generate_reports,
            '4': self._data_analysis,
            '5': self._export_data,
            '6': self._system_management,
            '0': self._exit,
        }
        
        action = actions.get(choice)
        if action:
            action()
        else:
            self._print_error("无效选项")
    
    def _transaction_management(self):
        """记账管理"""
        options = [
            ("1", "添加收入"),
            ("2", "添加支出"),
            ("3", "修改记录"),
            ("4", "删除记录"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("记账管理", options)
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            self._add_transaction(TransactionType.INCOME)
        elif choice == '2':
            self._add_transaction(TransactionType.EXPENSE)
        elif choice == '3':
            self._update_transaction()
        elif choice == '4':
            self._delete_transaction()
        elif choice == '0':
            return
        else:
            self._print_error("无效选项")
    
    def _add_transaction(self, trans_type: TransactionType):
        """
        添加交易记录
        
        Args:
            trans_type: 交易类型
        """
        self._print_header(f"添加{'收入' if trans_type == TransactionType.INCOME else '支出'}")
        
        try:
            # 选择分类
            categories = CATEGORIES[trans_type.value]
            print("分类选项:")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            
            cat_idx = int(self._input_choice(
                "请选择分类编号: ",
                [str(i) for i in range(1, len(categories) + 1)]
            )) - 1
            category = categories[cat_idx]
            
            # 输入金额
            amount = self._input_number("金额: ", min_value=0.01)
            
            # 输入日期
            date = self._input_date(
                f"日期 (默认今天 {datetime.now().strftime(REPORT_CONFIG['date_format'])}): ",
                datetime.now().strftime(REPORT_CONFIG['date_format'])
            )
            
            # 输入备注
            note = input("备注 (可选): ").strip()
            
            # 创建交易记录
            transaction = Transaction(
                amount=amount,
                type=trans_type,
                category=category,
                date=date,
                note=note,
                user_id=self.manager.current_user.username
            )
            
            # 保存
            trans_id = self.manager.transactions.add_transaction(transaction)
            self._print_success(f"记录添加成功，ID: {trans_id}")
            
        except ValidationError as e:
            self._print_error(f"数据验证失败: {e}")
        except Exception as e:
            self._print_error(f"添加失败: {e}")
    
    def _update_transaction(self):
        """修改交易记录"""
        self._print_header("修改记录")
        
        try:
            trans_id = int(self._input_required("请输入记录ID: "))
            
            # 获取原记录
            transaction = self.manager.transactions.get_transaction_by_id(trans_id)
            if not transaction:
                self._print_error("记录不存在")
                return
            
            print(f"\n当前记录: {transaction}")
            print("（直接回车保持不变）\n")
            
            updates = {}
            
            # 修改金额
            amount_str = input(f"金额 [{transaction.amount}]: ").strip()
            if amount_str:
                updates['amount'] = float(amount_str)
            
            # 修改分类
            print(f"当前分类: {transaction.category}")
            if input("是否修改分类? (y/n): ").lower() == 'y':
                categories = CATEGORIES[transaction.type.value]
                for i, cat in enumerate(categories, 1):
                    print(f"  {i}. {cat}")
                cat_idx = int(input("选择分类: ")) - 1
                updates['category'] = categories[cat_idx]
            
            # 修改日期
            date_str = input(f"日期 [{transaction.date}]: ").strip()
            if date_str:
                updates['date'] = date_str
            
            # 修改备注
            note_str = input(f"备注 [{transaction.note}]: ").strip()
            if note_str:
                updates['note'] = note_str
            
            if updates:
                if self.manager.transactions.update_transaction(trans_id, updates):
                    self._print_success("记录更新成功")
                else:
                    self._print_error("更新失败")
            else:
                self._print_info("没有修改任何内容")
                
        except ValidationError as e:
            self._print_error(f"数据验证失败: {e}")
        except Exception as e:
            self._print_error(f"更新失败: {e}")
    
    def _delete_transaction(self):
        """删除交易记录"""
        self._print_header("删除记录")
        
        try:
            trans_id = int(self._input_required("请输入记录ID: "))
            
            # 确认删除
            transaction = self.manager.transactions.get_transaction_by_id(trans_id)
            if not transaction:
                self._print_error("记录不存在")
                return
            
            print(f"\n要删除的记录: {transaction}")
            confirm = input("确认删除? (y/n): ").lower()
            
            if confirm == 'y':
                if self.manager.transactions.delete_transaction(trans_id):
                    self._print_success("记录删除成功")
                else:
                    self._print_error("删除失败")
            else:
                self._print_info("已取消删除")
                
        except Exception as e:
            self._print_error(f"删除失败: {e}")
    
    def _query_data(self):
        """数据查询"""
        options = [
            ("1", "查看最近记录"),
            ("2", "按日期查询"),
            ("3", "按分类查询"),
            ("4", "按类型查询"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("数据查询", options)
        choice = input("请选择操作: ").strip()
        
        try:
            if choice == '1':
                limit = int(input("显示多少条记录 (默认10): ") or "10")
                transactions = self.manager.transactions.query_transactions(
                    limit=limit
                )
                self._display_transactions(transactions)
                
            elif choice == '2':
                start_date = self._input_date("开始日期: ")
                end_date = self._input_date("结束日期: ")
                filter_obj = QueryFilter().by_date_range(start_date, end_date)
                transactions = self.manager.transactions.query_transactions(filter_obj)
                self._display_transactions(transactions)
                
            elif choice == '3':
                print("分类选项:")
                all_categories = (CATEGORIES['income'] + CATEGORIES['expense'])
                for i, cat in enumerate(all_categories, 1):
                    print(f"  {i}. {cat}")
                cat_idx = int(input("选择分类: ")) - 1
                category = all_categories[cat_idx]
                
                filter_obj = QueryFilter().by_category(category)
                transactions = self.manager.transactions.query_transactions(filter_obj)
                self._display_transactions(transactions)
                
            elif choice == '4':
                trans_type = self._input_choice(
                    "类型 (income/expense): ",
                    ['income', 'expense']
                )
                filter_obj = QueryFilter().by_type(TransactionType(trans_type))
                transactions = self.manager.transactions.query_transactions(filter_obj)
                self._display_transactions(transactions)
                
            elif choice == '0':
                return
            else:
                self._print_error("无效选项")
                
        except Exception as e:
            self._print_error(f"查询失败: {e}")
    
    def _display_transactions(self, transactions: List[Transaction]):
        """
        显示交易记录列表
        
        Args:
            transactions: 交易记录列表
        """
        if not transactions:
            self._print_info("没有找到记录")
            return
        
        print("\n" + "-" * 80)
        print(f"{'ID':<6}{'日期':<12}{'类型':<8}{'分类':<10}{'金额':<15}{'备注':<20}")
        print("-" * 80)
        
        for t in transactions:
            type_str = "收入" if t.type == TransactionType.INCOME else "支出"
            amount_str = FormatUtils.format_currency(t.amount)
            note_str = FormatUtils.truncate_string(t.note, 18)
            
            print(f"{t.id:<6}{t.date:<12}{type_str:<8}{t.category:<10}"
                  f"{amount_str:<15}{note_str:<20}")
        
        print("-" * 80)
        self._print_info(f"共 {len(transactions)} 条记录")
    
    def _generate_reports(self):
        """生成报表"""
        options = [
            ("1", "月度报表"),
            ("2", "年度报表"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("统计报表", options)
        choice = input("请选择操作: ").strip()
        
        try:
            if choice == '1':
                year_month = input(f"月份 (默认 {DateUtils.get_current_month()}): ").strip()
                if not year_month:
                    year_month = DateUtils.get_current_month()
                
                report = self.manager.reports.generate_monthly_report(year_month)
                
                # 显示文本报表
                text_report = self.visualizer.generate_text_report(report)
                print(text_report)
                
                # 询问是否生成图表
                if input("\n是否生成图表? (y/n): ").lower() == 'y':
                    self.visualizer.plot_category_pie(
                        report.category_breakdown.get('expense', {}),
                        title=f'{year_month} 支出分类'
                    )
                
            elif choice == '2':
                year = input(f"年份 (默认 {DateUtils.get_current_year()}): ").strip()
                year = int(year) if year else DateUtils.get_current_year()
                
                report = self.manager.reports.generate_annual_report(year)
                
                # 显示文本报表
                text_report = self.visualizer.generate_text_report(report)
                print(text_report)
                
                # 询问是否生成图表
                if input("\n是否生成图表? (y/n): ").lower() == 'y':
                    self.visualizer.plot_annual_summary(report)
                
            elif choice == '0':
                return
            else:
                self._print_error("无效选项")
                
        except Exception as e:
            self._print_error(f"生成报表失败: {e}")
    
    def _data_analysis(self):
        """数据分析"""
        options = [
            ("1", "收支趋势分析"),
            ("2", "分类统计分析"),
            ("3", "财务仪表盘"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("数据分析", options)
        choice = input("请选择操作: ").strip()
        
        try:
            if choice == '1':
                months = int(input("分析最近几个月 (默认12): ") or "12")
                trend_data = self.manager.reports.get_trend_analysis(months)
                
                self.visualizer.plot_monthly_trend(
                    trend_data,
                    title=f'近{months}个月收支趋势'
                )
                
            elif choice == '2':
                start_date = input("开始日期 (可选): ").strip() or None
                end_date = input("结束日期 (可选): ").strip() or None
                
                summary = self.manager.transactions.get_all_categories_summary(
                    start_date, end_date
                )
                
                self.visualizer.plot_category_comparison(
                    summary.get('income', {}),
                    summary.get('expense', {})
                )
                
            elif choice == '3':
                year_month = input(f"月份 (默认 {DateUtils.get_current_month()}): ").strip()
                if not year_month:
                    year_month = DateUtils.get_current_month()
                
                monthly_report = self.manager.reports.generate_monthly_report(year_month)
                trend_data = self.manager.reports.get_trend_analysis(12)
                
                self.dashboard.show_monthly_dashboard(monthly_report, trend_data)
                
            elif choice == '0':
                return
            else:
                self._print_error("无效选项")
                
        except Exception as e:
            self._print_error(f"分析失败: {e}")
    
    def _export_data(self):
        """数据导出"""
        options = [
            ("1", "导出为CSV"),
            ("2", "导出为JSON"),
            ("3", "导出报表为文本"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("数据导出", options)
        choice = input("请选择操作: ").strip()
        
        try:
            if choice == '1':
                df = self.manager.transactions.export_to_dataframe()
                filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(EXPORT_CONFIG['export_dir'], filename)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self._print_success(f"数据已导出: {filepath}")
                
            elif choice == '2':
                df = self.manager.transactions.export_to_dataframe()
                filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(EXPORT_CONFIG['export_dir'], filename)
                df.to_json(filepath, orient='records', force_ascii=False, indent=2)
                self._print_success(f"数据已导出: {filepath}")
                
            elif choice == '3':
                year_month = input(f"月份 (默认 {DateUtils.get_current_month()}): ").strip()
                if not year_month:
                    year_month = DateUtils.get_current_month()
                
                report = self.manager.reports.generate_monthly_report(year_month)
                text = self.visualizer.generate_text_report(report, save_to_file=True)
                print(text)
                
            elif choice == '0':
                return
            else:
                self._print_error("无效选项")
                
        except Exception as e:
            self._print_error(f"导出失败: {e}")
    
    def _system_management(self):
        """系统管理"""
        # 检查权限
        if not self.manager.has_permission('manage_users'):
            self._print_error("您没有权限访问系统管理")
            return
        
        options = [
            ("1", "创建新用户"),
            ("2", "查看系统信息"),
            ("3", "切换用户"),
            ("0", "返回主菜单"),
        ]
        
        self._display_menu("系统管理", options)
        choice = input("请选择操作: ").strip()
        
        try:
            if choice == '1':
                username = self._input_required("新用户名: ")
                password = getpass("密码: ")
                confirm_password = getpass("确认密码: ")
                
                if password != confirm_password:
                    self._print_error("两次输入的密码不一致")
                    return
                
                print("角色选项:")
                for role, info in ROLES.items():
                    print(f"  {role}: {info['description']}")
                
                role = self._input_choice(
                    "选择角色: ",
                    list(ROLES.keys())
                )
                
                if self.manager.users.create_user(username, password, role):
                    self._print_success(f"用户 {username} 创建成功")
                
            elif choice == '2':
                self._print_header("系统信息")
                print(f"当前用户: {self.manager.current_user.username}")
                print(f"用户角色: {self.manager.current_user.role}")
                print(f"权限列表: {', '.join(self.manager.current_user.permissions)}")
                print(f"数据库路径: {DATABASE_CONFIG['path']}")
                print(f"导出目录: {EXPORT_CONFIG['export_dir']}")
                
            elif choice == '3':
                self.manager.logout()
                if not self._login():
                    self.running = False
                
            elif choice == '0':
                return
            else:
                self._print_error("无效选项")
                
        except Exception as e:
            self._print_error(f"操作失败: {e}")
    
    def _exit(self):
        """退出系统"""
        self._print_info("感谢使用智能财务管理系统，再见！")
        self.running = False


def main():
    """主入口函数"""
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()
