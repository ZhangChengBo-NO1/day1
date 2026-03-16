import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Database, Transaction


class Visualizer:
    def __init__(self, db: Database):
        self.db = db
        self.transaction = Transaction(db)
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

    def _prepare_trend_data(self, transactions: List[Dict]) -> pd.DataFrame:
        if not transactions:
            return pd.DataFrame()

        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['date'] = df['transaction_date'].dt.date
        return df

    def plot_monthly_trend(self, user_id: int, year: int, save_path: Optional[str] = None) -> Tuple[bool, str]:
        try:
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-01-01"

            transactions = self.transaction.get_transactions(
                user_id, start_date=start_date, end_date=end_date
            )

            if not transactions:
                return False, "该年度没有交易记录"

            df = self._prepare_trend_data(transactions)
            df['month'] = df['transaction_date'].dt.month

            monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)

            for col in ['收入', '支出']:
                if col not in monthly_data.columns:
                    monthly_data[col] = 0

            all_months = pd.DataFrame(index=range(1, 13))
            monthly_data = all_months.join(monthly_data).fillna(0)

            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(monthly_data.index, monthly_data.get('收入', 0),
                    marker='o', label='收入', color='#2ecc71', linewidth=2)
            ax.plot(monthly_data.index, monthly_data.get('支出', 0),
                    marker='s', label='支出', color='#e74c3c', linewidth=2)

            balance = monthly_data.get('收入', 0) - monthly_data.get('支出', 0)
            ax.bar(monthly_data.index, balance, alpha=0.3,
                   label='结余', color='#3498db')

            ax.set_xlabel('月份', fontsize=12)
            ax.set_ylabel('金额 (元)', fontsize=12)
            ax.set_title(f'{year}年度月度收支趋势', fontsize=14, pad=20)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels([f'{m}月' for m in range(1, 13)])

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close()
                return True, f"图表已保存至: {save_path}"
            else:
                plt.show()
                return True, "图表已显示"

        except Exception as e:
            plt.close()
            return False, f"生成图表失败: {str(e)}"

    def plot_category_pie(self, user_id: int, type_: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          save_path: Optional[str] = None) -> Tuple[bool, str]:
        try:
            transactions = self.transaction.get_transactions(
                user_id, start_date=start_date, end_date=end_date, type_=type_
            )

            if not transactions:
                return False, f"没有找到{type_}记录"

            df = pd.DataFrame(transactions)
            category_data = df.groupby('category')['amount'].sum()

            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12',
                      '#9b59b6', '#1abc9c', '#e67e22', '#34495e']

            fig, ax = plt.subplots(figsize=(8, 8))

            wedges, texts, autotexts = ax.pie(
                category_data.values,
                labels=category_data.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )

            ax.axis('equal')

            period_text = ""
            if start_date and end_date:
                period_text = f"\n({start_date} 至 {end_date})"

            plt.setp(autotexts, size=9, weight='bold')
            ax.set_title(f'{type_}分类占比{period_text}', fontsize=14, pad=20)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close()
                return True, f"图表已保存至: {save_path}"
            else:
                plt.show()
                return True, "图表已显示"

        except Exception as e:
            plt.close()
            return False, f"生成图表失败: {str(e)}"

    def plot_daily_trend(self, user_id: int, days: int = 30,
                         save_path: Optional[str] = None) -> Tuple[bool, str]:
        try:
            end_date = datetime.now()
            start_date = (end_date - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            transactions = self.transaction.get_transactions(
                user_id, start_date=start_date, end_date=end_date_str
            )

            if not transactions:
                return False, f"最近{days}天没有交易记录"

            df = self._prepare_trend_data(transactions)

            date_range = pd.date_range(start=start_date, end=end_date_str)
            daily_df = pd.DataFrame(index=date_range)
            daily_df['date'] = daily_df.index.date

            daily_income = df[df['type'] == '收入'].groupby('date')['amount'].sum()
            daily_expense = df[df['type'] == '支出'].groupby('date')['amount'].sum()

            daily_df['income'] = daily_df.index.map(lambda x: daily_income.get(x, 0))
            daily_df['expense'] = daily_df.index.map(lambda x: daily_expense.get(x, 0))

            fig, ax = plt.subplots(figsize=(14, 6))

            ax.bar(daily_df.index, daily_df['income'], alpha=0.7,
                   label='收入', color='#2ecc71', width=0.4)
            ax.bar(daily_df.index + pd.Timedelta(hours=12), daily_df['expense'],
                   alpha=0.7, label='支出', color='#e74c3c', width=0.4)

            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('金额 (元)', fontsize=12)
            ax.set_title(f'最近{days}天每日收支情况', fontsize=14, pad=20)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

            plt.gcf().autofmt_xdate()
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close()
                return True, f"图表已保存至: {save_path}"
            else:
                plt.show()
                return True, "图表已显示"

        except Exception as e:
            plt.close()
            return False, f"生成图表失败: {str(e)}"

    def plot_cumulative_balance(self, user_id: int, year: int,
                                save_path: Optional[str] = None) -> Tuple[bool, str]:
        try:
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-01-01"

            transactions = self.transaction.get_transactions(
                user_id, start_date=start_date, end_date=end_date
            )

            if not transactions:
                return False, "该年度没有交易记录"

            df = self._prepare_trend_data(transactions)
            df = df.sort_values('transaction_date')

            df['signed_amount'] = df.apply(
                lambda x: x['amount'] if x['type'] == '收入' else -x['amount'],
                axis=1
            )
            df['cumulative'] = df['signed_amount'].cumsum()

            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(df['transaction_date'], df['cumulative'],
                    color='#3498db', linewidth=2, label='累计结余')
            ax.fill_between(df['transaction_date'], df['cumulative'],
                            alpha=0.3, color='#3498db')

            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('累计结余 (元)', fontsize=12)
            ax.set_title(f'{year}年度累计结余趋势', fontsize=14, pad=20)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

            plt.gcf().autofmt_xdate()
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close()
                return True, f"图表已保存至: {save_path}"
            else:
                plt.show()
                return True, "图表已显示"

        except Exception as e:
            plt.close()
            return False, f"生成图表失败: {str(e)}"
