# -*- coding: utf-8 -*-
"""
可视化层 - 图表生成和数据可视化
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

import config


plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.dirname(os.path.abspath(__file__))
        self.colors = config.CHART_COLORS
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _save_figure(self, fig, filename: str, dpi: int = 150) -> str:
        """
        保存图表
        Args:
            fig: 图表对象
            filename: 文件名
            dpi: 分辨率
        Returns:
            文件路径
        """
        self._ensure_output_dir()
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        return filepath
    
    def generate_trend_chart(self, trend_data: Dict[str, Any], 
                            title: str = "收支趋势图") -> str:
        """
        生成收支趋势图
        Args:
            trend_data: 趋势数据
            title: 图表标题
        Returns:
            图表文件路径
        """
        data = trend_data.get('trend_data', [])
        if not data:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        labels = [d['label'] for d in data]
        income = [d['income'] for d in data]
        expense = [d['expense'] for d in data]
        balance = [d['balance'] for d in data]
        
        x = np.arange(len(labels))
        width = 0.25
        
        bars1 = ax.bar(x - width, income, width, label='收入', 
                      color=self.colors['income'], alpha=0.8)
        bars2 = ax.bar(x, expense, width, label='支出', 
                      color=self.colors['expense'], alpha=0.8)
        bars3 = ax.bar(x + width, balance, width, label='结余', 
                      color=self.colors['balance'], alpha=0.8)
        
        ax.set_xlabel('月份')
        ax.set_ylabel('金额 (元)')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
        
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                if height != 0:
                    ax.annotate(f'¥{height:,.0f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=8)
        
        ax.grid(axis='y', alpha=0.3)
        
        filename = f"trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def generate_pie_chart(self, category_data: Dict[str, Any], 
                          trans_type: str = 'expense',
                          title: str = None) -> str:
        """
        生成分类饼图
        Args:
            category_data: 分类数据
            trans_type: 交易类型
            title: 图表标题
        Returns:
            图表文件路径
        """
        data = category_data.get('category_data', [])
        if not data:
            return None
        
        filtered_data = [d for d in data if d['type'] == trans_type]
        if not filtered_data:
            return None
        
        if title is None:
            title = f"{'支出' if trans_type == 'expense' else '收入'}分类占比"
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = [d['category'] for d in filtered_data]
        sizes = [d['total'] for d in filtered_data]
        percentages = [d['percentage'] for d in filtered_data]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        explode = [0.02] * len(labels)
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors, explode=explode,
            shadow=True, startangle=90
        )
        
        ax.set_title(title)
        
        legend_labels = [f'{l}: ¥{s:,.2f} ({p:.1f}%)' 
                        for l, s, p in zip(labels, sizes, percentages)]
        ax.legend(wedges, legend_labels, title="分类详情",
                 loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        
        filename = f"pie_{trans_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def generate_monthly_bar_chart(self, monthly_data: Dict[str, Any],
                                   title: str = "月度收支对比") -> str:
        """
        生成月度收支柱状图
        Args:
            monthly_data: 月度数据
            title: 图表标题
        Returns:
            图表文件路径
        """
        data = monthly_data.get('monthly_data', [])
        if not data:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        months = [f"{d['year']}-{d['month']:02d}" for d in data]
        income = [d['income'] for d in data]
        expense = [d['expense'] for d in data]
        
        x = np.arange(len(months))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, income, width, label='收入', 
                      color=self.colors['income'], alpha=0.8)
        bars2 = ax.bar(x + width/2, expense, width, label='支出', 
                      color=self.colors['expense'], alpha=0.8)
        
        ax.set_xlabel('月份')
        ax.set_ylabel('金额 (元)')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.legend()
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height != 0:
                    ax.annotate(f'¥{height:,.0f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=8)
        
        ax.grid(axis='y', alpha=0.3)
        
        filename = f"monthly_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def generate_balance_line_chart(self, trend_data: Dict[str, Any],
                                    title: str = "结余趋势图") -> str:
        """
        生成结余趋势折线图
        Args:
            trend_data: 趋势数据
            title: 图表标题
        Returns:
            图表文件路径
        """
        data = trend_data.get('trend_data', [])
        if not data:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        labels = [d['label'] for d in data]
        balance = [d['balance'] for d in data]
        
        x = range(len(labels))
        
        ax.plot(x, balance, marker='o', linewidth=2, markersize=8,
               color=self.colors['balance'], label='结余')
        
        ax.fill_between(x, balance, alpha=0.3, color=self.colors['balance'])
        
        for i, (xi, yi) in enumerate(zip(x, balance)):
            color = self.colors['income'] if yi >= 0 else self.colors['expense']
            ax.annotate(f'¥{yi:,.0f}',
                       xy=(xi, yi),
                       xytext=(0, 10 if yi >= 0 else -15),
                       textcoords="offset points",
                       ha='center', va='bottom' if yi >= 0 else 'top',
                       fontsize=9, color=color)
        
        ax.set_xlabel('月份')
        ax.set_ylabel('金额 (元)')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.grid(alpha=0.3)
        
        filename = f"balance_line_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def generate_comparison_chart(self, data1: Dict[str, Any], 
                                  data2: Dict[str, Any],
                                  label1: str = "本期",
                                  label2: str = "上期",
                                  title: str = "收支对比图") -> str:
        """
        生成对比图
        Args:
            data1: 数据1
            data2: 数据2
            label1: 数据1标签
            label2: 数据2标签
            title: 图表标题
        Returns:
            图表文件路径
        """
        summary1 = data1.get('summary', {})
        summary2 = data2.get('summary', {})
        
        if not summary1 or not summary2:
            return None
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        categories = ['收入', '支出', '结余']
        values1 = [summary1.get('income', 0), 
                  summary1.get('expense', 0), 
                  summary1.get('balance', 0)]
        values2 = [summary2.get('income', 0), 
                  summary2.get('expense', 0), 
                  summary2.get('balance', 0)]
        
        for i, (ax, cat) in enumerate(zip(axes, categories)):
            x = [0, 1]
            values = [values1[i], values2[i]]
            colors = [self.colors['income'] if i == 0 else 
                     self.colors['expense'] if i == 1 else 
                     self.colors['balance']]
            
            bars = ax.bar(x, values, color=colors, alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([label1, label2])
            ax.set_title(cat)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
            
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'¥{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=10)
            
            ax.grid(axis='y', alpha=0.3)
        
        fig.suptitle(title, fontsize=14)
        plt.tight_layout()
        
        filename = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def generate_dashboard(self, overview: Dict[str, Any],
                          trend_data: Dict[str, Any],
                          category_data: Dict[str, Any]) -> str:
        """
        生成仪表盘图表
        Args:
            overview: 概览数据
            trend_data: 趋势数据
            category_data: 分类数据
        Returns:
            图表文件路径
        """
        fig = plt.figure(figsize=(16, 12))
        
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_summary(ax1, overview)
        
        ax2 = fig.add_subplot(gs[1, :])
        self._plot_trend(ax2, trend_data)
        
        ax3 = fig.add_subplot(gs[2, 0])
        self._plot_category_pie(ax3, category_data, 'expense')
        
        ax4 = fig.add_subplot(gs[2, 1])
        self._plot_category_pie(ax4, category_data, 'income')
        
        ax5 = fig.add_subplot(gs[2, 2])
        self._plot_balance_trend(ax5, trend_data)
        
        fig.suptitle('财务仪表盘', fontsize=16, fontweight='bold')
        
        filename = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self._save_figure(fig, filename)
    
    def _plot_summary(self, ax, overview: Dict[str, Any]):
        """绘制概览摘要"""
        current_month = overview.get('current_month', {})
        current_year = overview.get('current_year', {})
        
        ax.axis('off')
        
        summary_text = f"""
        当月收支概览
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        收入: ¥{current_month.get('income', 0):,.2f}    支出: ¥{current_month.get('expense', 0):,.2f}    结余: ¥{current_month.get('balance', 0):,.2f}
        
        年度收支概览
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        收入: ¥{current_year.get('income', 0):,.2f}    支出: ¥{current_year.get('expense', 0):,.2f}    结余: ¥{current_year.get('balance', 0):,.2f}
        """
        
        ax.text(0.5, 0.5, summary_text, transform=ax.transAxes,
               fontsize=12, verticalalignment='center',
               horizontalalignment='center',
               family='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_trend(self, ax, trend_data: Dict[str, Any]):
        """绘制趋势图"""
        data = trend_data.get('trend_data', [])
        if not data:
            return
        
        labels = [d['label'] for d in data]
        income = [d['income'] for d in data]
        expense = [d['expense'] for d in data]
        
        x = np.arange(len(labels))
        width = 0.35
        
        ax.bar(x - width/2, income, width, label='收入', 
              color=self.colors['income'], alpha=0.8)
        ax.bar(x + width/2, expense, width, label='支出', 
              color=self.colors['expense'], alpha=0.8)
        
        ax.set_title('收支趋势')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
    
    def _plot_category_pie(self, ax, category_data: Dict[str, Any], 
                          trans_type: str):
        """绘制分类饼图"""
        data = category_data.get('category_data', [])
        filtered_data = [d for d in data if d['type'] == trans_type]
        
        if not filtered_data:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center')
            ax.set_title(f"{'支出' if trans_type == 'expense' else '收入'}分类")
            return
        
        labels = [d['category'] for d in filtered_data]
        sizes = [d['total'] for d in filtered_data]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%',
              colors=colors, startangle=90)
        ax.set_title(f"{'支出' if trans_type == 'expense' else '收入'}分类")
    
    def _plot_balance_trend(self, ax, trend_data: Dict[str, Any]):
        """绘制结余趋势"""
        data = trend_data.get('trend_data', [])
        if not data:
            return
        
        labels = [d['label'] for d in data]
        balance = [d['balance'] for d in data]
        
        ax.plot(range(len(labels)), balance, marker='o', 
               color=self.colors['balance'])
        ax.fill_between(range(len(labels)), balance, alpha=0.3, 
                       color=self.colors['balance'])
        ax.set_title('结余趋势')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.grid(alpha=0.3)
