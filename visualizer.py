"""
可视化层 - 智能财务管理系统

负责数据可视化、图表生成、报表展示等功能
使用matplotlib进行图表绘制
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.font_manager as fm
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import os
import sys
import warnings

from config import VISUALIZATION, EXPORT_CONFIG, REPORT_CONFIG, CATEGORIES
from models import MonthlyReport, AnnualReport, Transaction
from utils import FormatUtils, DateUtils


def setup_chinese_font():
    """设置中文字体支持"""
    # 忽略字体警告
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # 根据操作系统设置中文字体
    if sys.platform == 'win32':
        # Windows 系统字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'NSimSun']
    elif sys.platform == 'darwin':
        # macOS 系统字体
        chinese_fonts = ['Arial Unicode MS', 'Heiti TC', 'PingFang TC']
    else:
        # Linux 系统字体
        chinese_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Source Han Sans CN']
    
    # 尝试设置中文字体
    font_set = False
    for font_name in chinese_fonts:
        try:
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
            font_set = True
            break
        except:
            continue
    
    if not font_set:
        # 如果找不到中文字体，使用默认字体并关闭警告
        plt.rcParams['font.family'] = 'sans-serif'


# 初始化时设置字体
setup_chinese_font()


class FinanceVisualizer:
    """财务可视化器"""
    
    def __init__(self):
        """初始化可视化器"""
        self.style = VISUALIZATION['style']
        self.figure_size = VISUALIZATION['figure_size']
        self.dpi = VISUALIZATION['dpi']
        self.colors = VISUALIZATION['color_palette']
        
        # 设置matplotlib样式
        try:
            plt.style.use(self.style)
        except:
            plt.style.use('default')
    
    def _create_figure(self, figsize: Tuple[int, int] = None) -> Tuple[Figure, Any]:
        """
        创建图表对象
        
        Args:
            figsize: 图表尺寸
            
        Returns:
            Tuple[Figure, Axes]: 图表和坐标轴对象
        """
        if figsize is None:
            figsize = self.figure_size
        
        fig, ax = plt.subplots(figsize=figsize, dpi=self.dpi)
        return fig, ax
    
    def _save_or_show(self, fig: Figure, filename: str = None,
                      show: bool = True) -> Optional[str]:
        """
        保存或显示图表
        
        Args:
            fig: 图表对象
            filename: 保存文件名（可选）
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        filepath = None
        
        if filename:
            filepath = os.path.join(EXPORT_CONFIG['export_dir'], filename)
            fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print(f"图表已保存: {filepath}")
        
        if show:
            plt.show()
        
        plt.close(fig)
        return filepath
    
    def plot_monthly_trend(self, trend_data: Dict[str, List],
                          title: str = '收支趋势图',
                          filename: str = None,
                          show: bool = True) -> Optional[str]:
        """
        绘制月度收支趋势图
        
        Args:
            trend_data: 趋势数据，包含months, income, expense, balance
            title: 图表标题
            filename: 保存文件名
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        fig, ax = self._create_figure((12, 6))
        
        months = trend_data['months']
        x = np.arange(len(months))
        width = 0.35
        
        # 绘制柱状图
        bars1 = ax.bar(x - width/2, trend_data['income'], width,
                       label='收入', color=self.colors[0], alpha=0.8)
        bars2 = ax.bar(x + width/2, trend_data['expense'], width,
                       label='支出', color=self.colors[1], alpha=0.8)
        
        # 绘制结余折线
        ax.plot(x, trend_data['balance'], 'o-', color=self.colors[2],
                linewidth=2, markersize=6, label='结余')
        
        # 设置标签
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('金额 (元)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}',
                       ha='center', va='bottom', fontsize=8)
        
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}',
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        return self._save_or_show(fig, filename, show)
    
    def plot_category_pie(self, category_data: Dict[str, float],
                         title: str = '分类占比',
                         filename: str = None,
                         show: bool = True) -> Optional[str]:
        """
        绘制分类饼图
        
        Args:
            category_data: 分类数据字典
            title: 图表标题
            filename: 保存文件名
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        if not category_data:
            print("没有数据可显示")
            return None
        
        fig, ax = self._create_figure((10, 8))
        
        # 准备数据
        labels = list(category_data.keys())
        sizes = list(category_data.values())
        
        # 选择颜色
        colors = self.colors[:len(labels)]
        
        # 突出显示最大的部分
        explode = [0.05 if i == sizes.index(max(sizes)) else 0 
                  for i in range(len(sizes))]
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90
        )
        
        # 设置字体大小
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._save_or_show(fig, filename, show)
    
    def plot_category_comparison(self, income_data: Dict[str, float],
                                 expense_data: Dict[str, float],
                                 title: str = '收支分类对比',
                                 filename: str = None,
                                 show: bool = True) -> Optional[str]:
        """
        绘制收支分类对比图
        
        Args:
            income_data: 收入分类数据
            expense_data: 支出分类数据
            title: 图表标题
            filename: 保存文件名
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 收入饼图
        if income_data:
            labels1 = list(income_data.keys())
            sizes1 = list(income_data.values())
            colors1 = self.colors[:len(labels1)]
            
            ax1.pie(sizes1, labels=labels1, colors=colors1,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            ax1.set_title('收入分类', fontsize=12, fontweight='bold')
        else:
            ax1.text(0.5, 0.5, '暂无收入数据', ha='center', va='center',
                    transform=ax1.transAxes, fontsize=12)
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)
            ax1.axis('off')
        
        # 支出饼图
        if expense_data:
            labels2 = list(expense_data.keys())
            sizes2 = list(expense_data.values())
            colors2 = self.colors[2:2+len(labels2)]
            
            ax2.pie(sizes2, labels=labels2, colors=colors2,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            ax2.set_title('支出分类', fontsize=12, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, '暂无支出数据', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12)
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
        
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        return self._save_or_show(fig, filename, show)
    
    def plot_annual_summary(self, annual_report: AnnualReport,
                           filename: str = None,
                           show: bool = True) -> Optional[str]:
        """
        绘制年度汇总图
        
        Args:
            annual_report: 年度报表对象
            filename: 保存文件名
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. 月度收支趋势
        ax1 = fig.add_subplot(gs[0, :])
        months = [m.year_month for m in annual_report.monthly_data]
        incomes = [m.total_income for m in annual_report.monthly_data]
        expenses = [m.total_expense for m in annual_report.monthly_data]
        
        x = np.arange(len(months))
        ax1.bar(x - 0.2, incomes, 0.4, label='收入', color=self.colors[0], alpha=0.8)
        ax1.bar(x + 0.2, expenses, 0.4, label='支出', color=self.colors[1], alpha=0.8)
        ax1.set_xlabel('月份')
        ax1.set_ylabel('金额 (元)')
        ax1.set_title(f'{annual_report.year}年 月度收支趋势', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(months, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. 收入分类占比
        ax2 = fig.add_subplot(gs[1, 0])
        if annual_report.top_categories.get('income'):
            income_dict = dict(annual_report.top_categories['income'])
            labels = list(income_dict.keys())
            sizes = list(income_dict.values())
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%',
                   colors=self.colors[:len(labels)], startangle=90)
            ax2.set_title('收入分类TOP5', fontweight='bold')
        else:
            ax2.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    transform=ax2.transAxes)
            ax2.axis('off')
        
        # 3. 支出分类占比
        ax3 = fig.add_subplot(gs[1, 1])
        if annual_report.top_categories.get('expense'):
            expense_dict = dict(annual_report.top_categories['expense'])
            labels = list(expense_dict.keys())
            sizes = list(expense_dict.values())
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%',
                   colors=self.colors[2:2+len(labels)], startangle=90)
            ax3.set_title('支出分类TOP5', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                    transform=ax3.transAxes)
            ax3.axis('off')
        
        # 4. 年度汇总信息
        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')
        
        summary_text = f"""
        年度财务汇总 ({annual_report.year}年)
        
        总收入: {FormatUtils.format_currency(annual_report.total_income):>15}
        总支出: {FormatUtils.format_currency(annual_report.total_expense):>15}
        年度结余: {FormatUtils.format_currency(annual_report.balance):>13}
        
        月均收入: {FormatUtils.format_currency(annual_report.total_income / 12):>14}
        月均支出: {FormatUtils.format_currency(annual_report.total_expense / 12):>14}
        """
        
        ax4.text(0.5, 0.5, summary_text, transform=ax4.transAxes,
                fontsize=12, verticalalignment='center',
                horizontalalignment='center', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        fig.suptitle(f'{annual_report.year}年 年度财务报告',
                    fontsize=16, fontweight='bold')
        
        return self._save_or_show(fig, filename, show)
    
    def plot_budget_vs_actual(self, budget_data: Dict[str, float],
                             actual_data: Dict[str, float],
                             title: str = '预算vs实际支出',
                             filename: str = None,
                             show: bool = True) -> Optional[str]:
        """
        绘制预算与实际支出对比图
        
        Args:
            budget_data: 预算数据
            actual_data: 实际支出数据
            title: 图表标题
            filename: 保存文件名
            show: 是否显示
            
        Returns:
            Optional[str]: 保存的文件路径
        """
        fig, ax = self._create_figure((12, 6))
        
        # 获取所有分类
        categories = list(set(list(budget_data.keys()) + list(actual_data.keys())))
        categories.sort()
        
        x = np.arange(len(categories))
        width = 0.35
        
        budget_values = [budget_data.get(cat, 0) for cat in categories]
        actual_values = [actual_data.get(cat, 0) for cat in categories]
        
        bars1 = ax.bar(x - width/2, budget_values, width,
                       label='预算', color=self.colors[0], alpha=0.8)
        bars2 = ax.bar(x + width/2, actual_values, width,
                       label='实际支出', color=self.colors[1], alpha=0.8)
        
        # 标记超预算的项目
        for i, (budget, actual) in enumerate(zip(budget_values, actual_values)):
            if budget > 0 and actual > budget:
                ax.text(i, max(budget, actual) * 1.05, '超支!',
                       ha='center', color='red', fontweight='bold')
        
        ax.set_xlabel('分类', fontsize=12)
        ax.set_ylabel('金额 (元)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return self._save_or_show(fig, filename, show)
    
    def generate_text_report(self, report: Union[MonthlyReport, AnnualReport],
                            save_to_file: bool = False) -> str:
        """
        生成文本格式报表
        
        Args:
            report: 报表对象
            save_to_file: 是否保存到文件
            
        Returns:
            str: 报表文本
        """
        if isinstance(report, MonthlyReport):
            text = self._format_monthly_report(report)
        elif isinstance(report, AnnualReport):
            text = self._format_annual_report(report)
        else:
            return "不支持的报表类型"
        
        if save_to_file:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(EXPORT_CONFIG['export_dir'], filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"报表已保存: {filepath}")
        
        return text
    
    def _format_monthly_report(self, report: MonthlyReport) -> str:
        """格式化月度报表"""
        lines = [
            "=" * 50,
            f"{'月度财务报告':^50}",
            "=" * 50,
            f"月份: {report.year_month}",
            "-" * 50,
            f"总收入: {FormatUtils.format_currency(report.total_income):>30}",
            f"总支出: {FormatUtils.format_currency(report.total_expense):>30}",
            f"结余: {FormatUtils.format_currency(report.balance):>32}",
            f"交易笔数: {report.transaction_count:>28}",
            "-" * 50,
            "收入分类:",
        ]
        
        for category, amount in report.category_breakdown.get('income', {}).items():
            lines.append(f"  {category}: {FormatUtils.format_currency(amount):>26}")
        
        lines.append("-" * 50)
        lines.append("支出分类:")
        
        for category, amount in report.category_breakdown.get('expense', {}).items():
            lines.append(f"  {category}: {FormatUtils.format_currency(amount):>26}")
        
        lines.append("=" * 50)
        
        return '\n'.join(lines)
    
    def _format_annual_report(self, report: AnnualReport) -> str:
        """格式化年度报表"""
        lines = [
            "=" * 60,
            f"{'年度财务报告':^60}",
            "=" * 60,
            f"年份: {report.year}",
            "-" * 60,
            f"年度总收入: {FormatUtils.format_currency(report.total_income):>35}",
            f"年度总支出: {FormatUtils.format_currency(report.total_expense):>35}",
            f"年度结余: {FormatUtils.format_currency(report.balance):>37}",
            f"月均收入: {FormatUtils.format_currency(report.total_income / 12):>37}",
            f"月均支出: {FormatUtils.format_currency(report.total_expense / 12):>37}",
            "-" * 60,
            "月度明细:",
        ]
        
        for monthly in report.monthly_data:
            lines.append(
                f"  {monthly.year_month}: 收{FormatUtils.format_currency(monthly.total_income):>12} "
                f"支{FormatUtils.format_currency(monthly.total_expense):>12} "
                f"余{FormatUtils.format_currency(monthly.balance):>12}"
            )
        
        lines.append("-" * 60)
        lines.append("收入分类TOP5:")
        for category, amount in report.top_categories.get('income', []):
            lines.append(f"  {category}: {FormatUtils.format_currency(amount):>34}")
        
        lines.append("-" * 60)
        lines.append("支出分类TOP5:")
        for category, amount in report.top_categories.get('expense', []):
            lines.append(f"  {category}: {FormatUtils.format_currency(amount):>34}")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)


class Dashboard:
    """仪表盘 - 综合数据展示"""
    
    def __init__(self, visualizer: FinanceVisualizer = None):
        """
        初始化仪表盘
        
        Args:
            visualizer: 可视化器实例
        """
        self.visualizer = visualizer or FinanceVisualizer()
    
    def show_monthly_dashboard(self, monthly_report: MonthlyReport,
                               trend_data: Dict[str, List] = None):
        """
        显示月度仪表盘
        
        Args:
            monthly_report: 月度报表
            trend_data: 趋势数据（可选）
        """
        print("\n" + "=" * 60)
        print(f"{'月度财务仪表盘':^60}")
        print("=" * 60)
        
        # 显示文本报表
        text_report = self.visualizer.generate_text_report(monthly_report)
        print(text_report)
        
        # 显示分类饼图
        if monthly_report.category_breakdown.get('expense'):
            print("\n正在生成支出分类图...")
            self.visualizer.plot_category_pie(
                monthly_report.category_breakdown['expense'],
                title=f'{monthly_report.year_month} 支出分类占比',
                filename=f'expense_pie_{monthly_report.year_month}.png'
            )
        
        # 显示趋势图
        if trend_data:
            print("\n正在生成趋势图...")
            self.visualizer.plot_monthly_trend(
                trend_data,
                title='近12个月收支趋势',
                filename='trend_12months.png'
            )
    
    def show_annual_dashboard(self, annual_report: AnnualReport):
        """
        显示年度仪表盘
        
        Args:
            annual_report: 年度报表
        """
        print("\n" + "=" * 60)
        print(f"{'年度财务仪表盘':^60}")
        print("=" * 60)
        
        # 显示文本报表
        text_report = self.visualizer.generate_text_report(annual_report)
        print(text_report)
        
        # 显示年度汇总图
        print("\n正在生成年报图表...")
        self.visualizer.plot_annual_summary(
            annual_report,
            filename=f'annual_report_{annual_report.year}.png'
        )
