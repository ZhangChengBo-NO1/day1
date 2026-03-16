import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from models import Database, Transaction, Category


class DataValidator:
    @staticmethod
    def validate_amount(amount: float) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "金额必须大于0"
        if amount > 100000000:
            return False, "金额不能超过1亿"
        return True, ""

    @staticmethod
    def validate_type(type_: str) -> Tuple[bool, str]:
        if type_ not in ["收入", "支出"]:
            return False, "类型必须是'收入'或'支出'"
        return True, ""

    @staticmethod
    def validate_category(category: str, type_: str, categories: List[str]) -> Tuple[bool, str]:
        if not category or len(category) > 20:
            return False, "分类名称长度必须在1-20之间"
        if category not in categories:
            return False, f"分类'{category}'不存在，请先添加或选择现有分类"
        return True, ""

    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, str]:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except ValueError:
            try:
                datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return True, ""
            except ValueError:
                return False, "日期格式必须为'YYYY-MM-DD'或'YYYY-MM-DD HH:MM:SS'"


class DataProcessor:
    def __init__(self, db: Database):
        self.db = db
        self.transaction = Transaction(db)
        self.category = Category(db)
        self.validator = DataValidator()

    def add_transaction(self, user_id: int, amount: float, type_: str,
                        category: str, description: str = "",
                        transaction_date: Optional[str] = None) -> Tuple[bool, str, int]:
        valid, msg = self.validator.validate_amount(amount)
        if not valid:
            return False, msg, -1

        valid, msg = self.validator.validate_type(type_)
        if not valid:
            return False, msg, -1

        categories = [c["name"] for c in self.category.get_categories(type_)]
        valid, msg = self.validator.validate_category(category, type_, categories)
        if not valid:
            return False, msg, -1

        if transaction_date:
            valid, msg = self.validator.validate_date(transaction_date)
            if not valid:
                return False, msg, -1

        trans_id = self.transaction.add_transaction(
            user_id, amount, type_, category, description, transaction_date
        )
        return True, "交易添加成功", trans_id

    def get_monthly_summary(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        transactions = self.transaction.get_transactions(
            user_id, start_date=start_date, end_date=end_date
        )

        return self._calculate_summary(transactions)

    def get_yearly_summary(self, user_id: int, year: int) -> Dict[str, Any]:
        start_date = f"{year}-01-01"
        end_date = f"{year + 1}-01-01"

        transactions = self.transaction.get_transactions(
            user_id, start_date=start_date, end_date=end_date
        )

        return self._calculate_summary(transactions)

    def _calculate_summary(self, transactions: List[Dict]) -> Dict[str, Any]:
        if not transactions:
            return {
                "total_income": 0,
                "total_expense": 0,
                "balance": 0,
                "income_by_category": {},
                "expense_by_category": {},
                "transaction_count": 0
            }

        df = pd.DataFrame(transactions)

        income_df = df[df["type"] == "收入"]
        expense_df = df[df["type"] == "支出"]

        total_income = income_df["amount"].sum() if not income_df.empty else 0
        total_expense = expense_df["amount"].sum() if not expense_df.empty else 0

        income_by_category = {}
        if not income_df.empty:
            income_by_category = income_df.groupby("category")["amount"].sum().to_dict()

        expense_by_category = {}
        if not expense_df.empty:
            expense_by_category = expense_df.groupby("category")["amount"].sum().to_dict()

        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "balance": round(total_income - total_expense, 2),
            "income_by_category": {k: round(v, 2) for k, v in income_by_category.items()},
            "expense_by_category": {k: round(v, 2) for k, v in expense_by_category.items()},
            "transaction_count": len(transactions)
        }

    def get_category_statistics(self, user_id: int, start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict[str, Any]:
        transactions = self.transaction.get_transactions(
            user_id, start_date=start_date, end_date=end_date
        )

        if not transactions:
            return {"income": {}, "expense": {}}

        df = pd.DataFrame(transactions)

        result = {"income": {}, "expense": {}}

        for type_ in ["收入", "支出"]:
            type_df = df[df["type"] == type_]
            if not type_df.empty:
                stats = type_df.groupby("category").agg({
                    "amount": ["sum", "count", "mean", "max", "min"]
                }).round(2)
                stats.columns = ["total", "count", "average", "max", "min"]
                key = "income" if type_ == "收入" else "expense"
                result[key] = stats.to_dict("index")

        return result

    def generate_monthly_report(self, user_id: int, year: int, month: int) -> str:
        summary = self.get_monthly_summary(user_id, year, month)

        report = f"\n{'='*50}\n"
        report += f"{year}年{month}月财务报表\n"
        report += f"{'='*50}\n\n"

        report += f"总收入: ¥{summary['total_income']:,.2f}\n"
        report += f"总支出: ¥{summary['total_expense']:,.2f}\n"
        report += f"结余: ¥{summary['balance']:,.2f}\n"
        report += f"交易笔数: {summary['transaction_count']}\n\n"

        report += "收入分类统计:\n"
        if summary["income_by_category"]:
            for cat, amt in sorted(summary["income_by_category"].items(), key=lambda x: x[1], reverse=True):
                report += f"  {cat}: ¥{amt:,.2f}\n"
        else:
            report += "  无收入记录\n"

        report += "\n支出分类统计:\n"
        if summary["expense_by_category"]:
            for cat, amt in sorted(summary["expense_by_category"].items(), key=lambda x: x[1], reverse=True):
                report += f"  {cat}: ¥{amt:,.2f}\n"
        else:
            report += "  无支出记录\n"

        return report

    def generate_yearly_report(self, user_id: int, year: int) -> str:
        summary = self.get_yearly_summary(user_id, year)

        report = f"\n{'='*60}\n"
        report += f"{year}年度财务报表\n"
        report += f"{'='*60}\n\n"

        report += f"总收入: ¥{summary['total_income']:,.2f}\n"
        report += f"总支出: ¥{summary['total_expense']:,.2f}\n"
        report += f"年度结余: ¥{summary['balance']:,.2f}\n"
        report += f"总交易笔数: {summary['transaction_count']}\n\n"

        monthly_data = []
        for month in range(1, 13):
            monthly = self.get_monthly_summary(user_id, year, month)
            monthly_data.append({
                "month": month,
                "income": monthly["total_income"],
                "expense": monthly["total_expense"],
                "balance": monthly["balance"]
            })

        report += "月度收支情况:\n"
        report += f"{'月份':<8} {'收入':>12} {'支出':>12} {'结余':>12}\n"
        report += "-" * 48 + "\n"
        for data in monthly_data:
            report += f"{data['month']}月{':':<5} ¥{data['income']:>11,.2f} ¥{data['expense']:>11,.2f} ¥{data['balance']:>11,.2f}\n"

        report += "\n年度收入分类Top3:\n"
        if summary["income_by_category"]:
            sorted_income = sorted(summary["income_by_category"].items(), key=lambda x: x[1], reverse=True)[:3]
            for cat, amt in sorted_income:
                report += f"  {cat}: ¥{amt:,.2f}\n"

        report += "\n年度支出分类Top3:\n"
        if summary["expense_by_category"]:
            sorted_expense = sorted(summary["expense_by_category"].items(), key=lambda x: x[1], reverse=True)[:3]
            for cat, amt in sorted_expense:
                report += f"  {cat}: ¥{amt:,.2f}\n"

        return report

    def export_transactions_to_csv(self, user_id: int, output_path: str,
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> Tuple[bool, str]:
        try:
            transactions = self.transaction.get_transactions(
                user_id, start_date=start_date, end_date=end_date
            )

            if not transactions:
                return False, "没有可导出的交易记录"

            df = pd.DataFrame(transactions)
            df = df[["id", "amount", "type", "category", "description", "transaction_date"]]
            df.columns = ["交易ID", "金额", "类型", "分类", "描述", "交易时间"]
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            return True, f"导出成功，共{len(transactions)}条记录"
        except Exception as e:
            return False, f"导出失败: {str(e)}"
