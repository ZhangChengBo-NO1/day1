import click
import os
from datetime import datetime
from models import Database, Category, Transaction
from data_processor import DataProcessor
from visualizer import Visualizer
from utils import AuthManager, Config, DateUtils, FileUtils


class FinanceCLI:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.get("db_path", "finance.db"))
        self.auth = AuthManager(self.db)
        self.data_processor = DataProcessor(self.db)
        self.visualizer = Visualizer(self.db)
        self.category = Category(self.db)
        self.transaction = Transaction(self.db)

    def print_header(self, title: str):
        click.echo("\n" + "=" * 60)
        click.echo(f"  {title}")
        click.echo("=" * 60 + "\n")

    def print_success(self, message: str):
        click.secho(f"✓ {message}", fg="green")

    def print_error(self, message: str):
        click.secho(f"✗ {message}", fg="red")

    def print_info(self, message: str):
        click.secho(f"ℹ {message}", fg="blue")


pass_finance = click.make_pass_decorator(FinanceCLI)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = FinanceCLI()


@cli.command()
@pass_finance
def init(finance: FinanceCLI):
    finance.print_header("初始化系统")
    finance.print_success("数据库初始化完成")
    finance.print_info("默认分类已加载")


@cli.group()
def user():
    pass


@user.command("register")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="密码")
@click.option("--role", default="user", help="用户角色")
@pass_finance
def register(finance: FinanceCLI, username: str, password: str, role: str):
    finance.print_header("用户注册")
    success, message = finance.auth.register(username, password, role)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@user.command("login")
@click.option("--username", prompt="用户名", help="用户名")
@click.option("--password", prompt=True, hide_input=True, help="密码")
@pass_finance
def login(finance: FinanceCLI, username: str, password: str):
    finance.print_header("用户登录")
    success, message = finance.auth.login(username, password)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@user.command("logout")
@pass_finance
def logout(finance: FinanceCLI):
    finance.print_header("退出登录")
    success, message = finance.auth.logout()
    if success:
        finance.print_success(message)
    else:
        finance.print_info(message)


@user.command("status")
@pass_finance
def status(finance: FinanceCLI):
    finance.print_header("登录状态")
    user = finance.auth.get_current_user()
    if user:
        click.echo(f"当前用户: {user['username']}")
        click.echo(f"用户角色: {user['role']}")
        click.echo(f"用户ID: {user['id']}")
    else:
        finance.print_info("未登录")


@cli.group()
def transaction():
    pass


@transaction.command("add")
@click.option("--amount", type=float, prompt="金额", help="交易金额")
@click.option("--type", "type_", type=click.Choice(["收入", "支出"]), prompt="类型", help="交易类型")
@click.option("--category", prompt="分类", help="交易分类")
@click.option("--description", default="", help="交易描述")
@click.option("--date", default=None, help="交易日期 (YYYY-MM-DD)")
@pass_finance
def add_transaction(finance: FinanceCLI, amount: float, type_: str, category: str, description: str, date: str):
    finance.print_header("添加交易")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]

    success, message, trans_id = finance.data_processor.add_transaction(
        user_id, amount, type_, category, description, date
    )
    if success:
        finance.print_success(f"{message} (ID: {trans_id})")
    else:
        finance.print_error(message)


@transaction.command("list")
@click.option("--limit", default=10, help="显示记录数")
@click.option("--type", "type_", default=None, help="筛选类型")
@pass_finance
def list_transactions(finance: FinanceCLI, limit: int, type_: str):
    finance.print_header("交易记录")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]
    transactions = finance.transaction.get_transactions(user_id, type_=type_)

    if not transactions:
        finance.print_info("没有交易记录")
        return

    click.echo(f"{'ID':<5} {'日期':<20} {'类型':<6} {'分类':<10} {'金额':>12}")
    click.echo("-" * 60)

    for trans in transactions[:limit]:
        click.echo(
            f"{trans['id']:<5} {trans['transaction_date']:<20} "
            f"{trans['type']:<6} {trans['category']:<10} ¥{trans['amount']:>11,.2f}"
        )


@transaction.command("delete")
@click.option("--id", "trans_id", type=int, prompt="交易ID", help="要删除的交易ID")
@pass_finance
def delete_transaction(finance: FinanceCLI, trans_id: int):
    finance.print_header("删除交易")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]
    success = finance.transaction.delete_transaction(trans_id, user_id)

    if success:
        finance.print_success(f"交易 {trans_id} 已删除")
    else:
        finance.print_error("删除失败，交易不存在或无权操作")


@cli.group()
def report():
    pass


@report.command("monthly")
@click.option("--year", type=int, default=datetime.now().year, help="年份")
@click.option("--month", type=int, default=datetime.now().month, help="月份")
@pass_finance
def monthly_report(finance: FinanceCLI, year: int, month: int):
    finance.print_header(f"{year}年{month}月报表")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]
    report_text = finance.data_processor.generate_monthly_report(user_id, year, month)
    click.echo(report_text)


@report.command("yearly")
@click.option("--year", type=int, default=datetime.now().year, help="年份")
@pass_finance
def yearly_report(finance: FinanceCLI, year: int):
    finance.print_header(f"{year}年度报表")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]
    report_text = finance.data_processor.generate_yearly_report(user_id, year)
    click.echo(report_text)


@report.command("export")
@click.option("--output", default=None, help="输出文件路径")
@pass_finance
def export_report(finance: FinanceCLI, output: str):
    finance.print_header("导出交易记录")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]

    if not output:
        export_dir = finance.config.get("export_dir", "exports")
        FileUtils.ensure_dir(export_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join(export_dir, f"transactions_{timestamp}.csv")

    success, message = finance.data_processor.export_transactions_to_csv(user_id, output)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@cli.group()
def chart():
    pass


@chart.command("monthly-trend")
@click.option("--year", type=int, default=datetime.now().year, help="年份")
@click.option("--output", default=None, help="输出图片路径")
@pass_finance
def monthly_trend(finance: FinanceCLI, year: int, output: str):
    finance.print_header(f"{year}年度月度收支趋势")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]

    if not output:
        chart_dir = finance.config.get("chart_dir", "charts")
        FileUtils.ensure_dir(chart_dir)
        output = os.path.join(chart_dir, f"monthly_trend_{year}.png")

    success, message = finance.visualizer.plot_monthly_trend(user_id, year, output)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@chart.command("category-pie")
@click.option("--type", "type_", type=click.Choice(["收入", "支出"]), default="支出", help="类型")
@click.option("--output", default=None, help="输出图片路径")
@pass_finance
def category_pie(finance: FinanceCLI, type_: str, output: str):
    finance.print_header(f"{type_}分类占比")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]

    if not output:
        chart_dir = finance.config.get("chart_dir", "charts")
        FileUtils.ensure_dir(chart_dir)
        timestamp = datetime.now().strftime("%Y%m%d")
        output = os.path.join(chart_dir, f"category_{type_}_{timestamp}.png")

    success, message = finance.visualizer.plot_category_pie(user_id, type_, save_path=output)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@chart.command("daily-trend")
@click.option("--days", type=int, default=30, help="天数")
@click.option("--output", default=None, help="输出图片路径")
@pass_finance
def daily_trend(finance: FinanceCLI, days: int, output: str):
    finance.print_header(f"最近{days}天收支趋势")

    logged_in, msg = finance.auth.require_login()
    if not logged_in:
        finance.print_error(msg)
        return

    user_id = finance.auth.get_current_user()["id"]

    if not output:
        chart_dir = finance.config.get("chart_dir", "charts")
        FileUtils.ensure_dir(chart_dir)
        output = os.path.join(chart_dir, f"daily_trend_{days}days.png")

    success, message = finance.visualizer.plot_daily_trend(user_id, days, output)
    if success:
        finance.print_success(message)
    else:
        finance.print_error(message)


@cli.group()
def category():
    pass


@category.command("list")
@click.option("--type", "type_", default=None, help="筛选类型")
@pass_finance
def list_categories(finance: FinanceCLI, type_: str):
    finance.print_header("分类列表")

    categories = finance.category.get_categories(type_)

    if not categories:
        finance.print_info("没有分类")
        return

    click.echo(f"{'ID':<5} {'名称':<15} {'类型':<6}")
    click.echo("-" * 30)

    for cat in categories:
        click.echo(f"{cat['id']:<5} {cat['name']:<15} {cat['type']:<6}")


@category.command("add")
@click.option("--name", prompt="分类名称", help="分类名称")
@click.option("--type", "type_", type=click.Choice(["收入", "支出"]), prompt="类型", help="分类类型")
@pass_finance
def add_category(finance: FinanceCLI, name: str, type_: str):
    finance.print_header("添加分类")

    cat_id = finance.category.add_category(name, type_)
    if cat_id == -1:
        finance.print_error("分类已存在")
    else:
        finance.print_success(f"分类添加成功 (ID: {cat_id})")


@cli.command()
@pass_finance
def menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("智能财务管理系统")

        user = finance.auth.get_current_user()
        if user:
            click.secho(f"当前用户: {user['username']} ({user['role']})\n", fg="cyan")

        click.echo("1. 用户管理")
        click.echo("2. 交易管理")
        click.echo("3. 报表生成")
        click.echo("4. 可视化分析")
        click.echo("5. 分类管理")
        click.echo("0. 退出系统\n")

        choice = click.prompt("请选择功能", type=int)

        if choice == 0:
            finance.print_success("感谢使用，再见！")
            break
        elif choice == 1:
            _user_menu(finance)
        elif choice == 2:
            _transaction_menu(finance)
        elif choice == 3:
            _report_menu(finance)
        elif choice == 4:
            _chart_menu(finance)
        elif choice == 5:
            _category_menu(finance)
        else:
            finance.print_error("无效选择，请重试")
            click.pause()


def _user_menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("用户管理")
        click.echo("1. 用户注册")
        click.echo("2. 用户登录")
        click.echo("3. 退出登录")
        click.echo("4. 查看登录状态")
        click.echo("0. 返回主菜单\n")

        choice = click.prompt("请选择", type=int)

        if choice == 0:
            break
        elif choice == 1:
            username = click.prompt("用户名")
            password = click.prompt("密码", hide_input=True, confirmation_prompt=True)
            success, msg = finance.auth.register(username, password)
            click.echo(msg)
        elif choice == 2:
            username = click.prompt("用户名")
            password = click.prompt("密码", hide_input=True)
            success, msg = finance.auth.login(username, password)
            click.echo(msg)
        elif choice == 3:
            success, msg = finance.auth.logout()
            click.echo(msg)
        elif choice == 4:
            user = finance.auth.get_current_user()
            if user:
                click.echo(f"已登录: {user['username']}")
            else:
                click.echo("未登录")
        click.pause()


def _transaction_menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("交易管理")
        click.echo("1. 添加交易")
        click.echo("2. 查看交易记录")
        click.echo("3. 删除交易")
        click.echo("0. 返回主菜单\n")

        choice = click.prompt("请选择", type=int)

        if choice == 0:
            break
        elif choice == 1:
            amount = click.prompt("金额", type=float)
            type_ = click.prompt("类型 (收入/支出)", type=click.Choice(["收入", "支出"]))
            category = click.prompt("分类")
            description = click.prompt("描述 (可选)", default="")
            user_id = finance.auth.get_current_user()["id"] if finance.auth.is_logged_in() else None
            if user_id:
                success, msg, _ = finance.data_processor.add_transaction(
                    user_id, amount, type_, category, description
                )
                click.echo(msg)
            else:
                finance.print_error("请先登录")
        elif choice == 2:
            if finance.auth.is_logged_in():
                user_id = finance.auth.get_current_user()["id"]
                transactions = finance.transaction.get_transactions(user_id)
                for t in transactions[:10]:
                    click.echo(f"{t['transaction_date']} {t['type']} {t['category']} ¥{t['amount']}")
            else:
                finance.print_error("请先登录")
        elif choice == 3:
            trans_id = click.prompt("交易ID", type=int)
            if finance.auth.is_logged_in():
                user_id = finance.auth.get_current_user()["id"]
                success = finance.transaction.delete_transaction(trans_id, user_id)
                click.echo("删除成功" if success else "删除失败")
            else:
                finance.print_error("请先登录")
        click.pause()


def _report_menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("报表生成")
        click.echo("1. 月度报表")
        click.echo("2. 年度报表")
        click.echo("3. 导出数据")
        click.echo("0. 返回主菜单\n")

        choice = click.prompt("请选择", type=int)

        if choice == 0:
            break
        elif choice == 1:
            year = click.prompt("年份", type=int, default=datetime.now().year)
            month = click.prompt("月份", type=int, default=datetime.now().month)
            if finance.auth.is_logged_in():
                user_id = finance.auth.get_current_user()["id"]
                click.echo(finance.data_processor.generate_monthly_report(user_id, year, month))
            else:
                finance.print_error("请先登录")
        elif choice == 2:
            year = click.prompt("年份", type=int, default=datetime.now().year)
            if finance.auth.is_logged_in():
                user_id = finance.auth.get_current_user()["id"]
                click.echo(finance.data_processor.generate_yearly_report(user_id, year))
            else:
                finance.print_error("请先登录")
        elif choice == 3:
            click.echo("导出功能")
        click.pause()


def _category_menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("分类管理")
        click.echo("1. 查看分类")
        click.echo("2. 添加分类")
        click.echo("0. 返回主菜单\n")

        choice = click.prompt("请选择", type=int)

        if choice == 0:
            break
        elif choice == 1:
            categories = finance.category.get_categories()
            for cat in categories:
                click.echo(f"{cat['name']} ({cat['type']})")
        elif choice == 2:
            name = click.prompt("分类名称")
            type_ = click.prompt("类型", type=click.Choice(["收入", "支出"]))
            cat_id = finance.category.add_category(name, type_)
            click.echo(f"添加成功 ID: {cat_id}" if cat_id != -1 else "分类已存在")
        click.pause()


def _chart_menu(finance: FinanceCLI):
    while True:
        click.clear()
        finance.print_header("可视化分析")
        click.echo("1. 月度趋势图")
        click.echo("2. 分类占比图")
        click.echo("3. 每日收支图")
        click.echo("0. 返回主菜单\n")

        choice = click.prompt("请选择", type=int)

        if choice == 0:
            break
        click.echo("图表功能")
        click.pause()


if __name__ == "__main__":
    cli()
