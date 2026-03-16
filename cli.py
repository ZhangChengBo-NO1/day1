# -*- coding: utf-8 -*-
"""
用户交互层 - CLI命令行接口
"""
import click
from datetime import datetime
from typing import Optional

import config
from data_processor import FinanceService
from visualization import ChartGenerator
from utils import format_currency, format_date, print_table


pass_service = click.make_pass_decorator(FinanceService)


class Session:
    """用户会话管理"""
    def __init__(self):
        self.user = None
        self.service = FinanceService()
    
    def login(self, username: str, password: str) -> bool:
        self.user = self.service.login(username, password)
        return self.user is not None
    
    def logout(self):
        self.user = None
    
    def is_authenticated(self) -> bool:
        return self.user is not None


session = Session()


@click.group()
@click.pass_context
def cli(ctx):
    """智能财务管理系统 - 命令行界面"""
    ctx.obj = session.service


@cli.command()
@click.option('--username', '-u', prompt='用户名', help='用户名')
@click.option('--password', '-p', prompt='密码', hide_input=True, help='密码')
def login(username, password):
    """用户登录"""
    if session.login(username, password):
        click.echo(click.style(f"登录成功！欢迎 {session.user['username']}", fg='green'))
        click.echo(f"角色: {session.user['role']}")
    else:
        click.echo(click.style("登录失败！用户名或密码错误", fg='red'))


@cli.command()
@click.option('--username', '-u', prompt='用户名', help='用户名')
@click.option('--password', '-p', prompt='密码', hide_input=True, help='密码')
@click.option('--role', '-r', default='user', help='用户角色 (admin/user)')
def register(username, password, role):
    """用户注册"""
    success, message = session.service.register(username, password, role)
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"注册失败: {message}", fg='red'))


@cli.command()
def logout():
    """用户登出"""
    session.logout()
    click.echo("已登出")


@cli.command()
@click.option('--type', '-t', 'trans_type', type=click.Choice(['income', 'expense']), 
              required=True, help='交易类型 (income/expense)')
@click.option('--amount', '-a', type=float, required=True, help='金额')
@click.option('--category', '-c', required=True, help='分类')
@click.option('--description', '-d', default='', help='描述')
@click.option('--date', '-D', default=None, help='日期 (YYYY-MM-DD)')
@pass_service
def add(service, trans_type, amount, category, description, date):
    """添加交易记录"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    success, message = service.add_transaction(
        session.user, trans_type, amount, category, description, date
    )
    
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"添加失败: {message}", fg='red'))


@cli.command()
@click.option('--id', '-i', 'trans_id', required=True, type=int, help='交易记录ID')
@click.option('--amount', '-a', type=float, default=None, help='金额')
@click.option('--category', '-c', default=None, help='分类')
@click.option('--description', '-d', default=None, help='描述')
@click.option('--date', '-D', default=None, help='日期 (YYYY-MM-DD)')
@pass_service
def update(service, trans_id, amount, category, description, date):
    """更新交易记录"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    kwargs = {}
    if amount is not None:
        kwargs['amount'] = amount
    if category is not None:
        kwargs['category'] = category
    if description is not None:
        kwargs['description'] = description
    if date is not None:
        kwargs['date'] = date
    
    success, message = service.update_transaction(session.user, trans_id, **kwargs)
    
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"更新失败: {message}", fg='red'))


@cli.command()
@click.option('--id', '-i', 'trans_id', required=True, type=int, help='交易记录ID')
@click.confirmation_option(prompt='确定要删除这条记录吗？')
@pass_service
def delete(service, trans_id):
    """删除交易记录"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    success, message = service.delete_transaction(session.user, trans_id)
    
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"删除失败: {message}", fg='red'))


@cli.command()
@click.option('--limit', '-l', default=20, help='显示数量')
@click.option('--type', '-t', 'trans_type', type=click.Choice(['income', 'expense']), 
              default=None, help='交易类型筛选')
@pass_service
def list(service, limit, trans_type):
    """查看交易记录列表"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    transactions = service.get_transactions(session.user, limit)
    
    if trans_type:
        transactions = [t for t in transactions if t['type'] == trans_type]
    
    if not transactions:
        click.echo("暂无交易记录")
        return
    
    for t in transactions:
        t['amount'] = format_currency(t['amount'])
        t['date'] = format_date(t['date'])
        t['type'] = '收入' if t['type'] == 'income' else '支出'
    
    print_table(
        transactions,
        ['id', 'type', 'amount', 'category', 'date', 'description'],
        ['ID', '类型', '金额', '分类', '日期', '描述']
    )


@cli.command()
@click.option('--start', '-s', required=True, help='开始日期 (YYYY-MM-DD)')
@click.option('--end', '-e', required=True, help='结束日期 (YYYY-MM-DD)')
@pass_service
def range(service, start, end):
    """查看日期范围内的交易记录"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    transactions = service.get_transactions_by_date(session.user, start, end)
    
    if not transactions:
        click.echo("该日期范围内暂无交易记录")
        return
    
    for t in transactions:
        t['amount'] = format_currency(t['amount'])
        t['date'] = format_date(t['date'])
        t['type'] = '收入' if t['type'] == 'income' else '支出'
    
    print_table(
        transactions,
        ['id', 'type', 'amount', 'category', 'date', 'description'],
        ['ID', '类型', '金额', '分类', '日期', '描述']
    )


@cli.command()
@click.option('--year', '-y', default=None, type=int, help='年份')
@click.option('--month', '-m', default=None, type=int, help='月份')
@pass_service
def report(service, year, month):
    """生成财务报告"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    today = datetime.now()
    year = year or today.year
    month = month or today.month
    
    if month:
        report_data = service.get_monthly_report(session.user, year, month)
        _print_monthly_report(report_data)
    else:
        report_data = service.get_yearly_report(session.user, year)
        _print_yearly_report(report_data)


def _print_monthly_report(report_data):
    """打印月度报告"""
    click.echo(click.style(f"\n{'='*50}", fg='cyan'))
    click.echo(click.style(f"月度财务报告 ({report_data['year']}年{report_data['month']}月)", 
                          fg='cyan', bold=True))
    click.echo(click.style(f"{'='*50}", fg='cyan'))
    
    summary = report_data['summary']
    click.echo(f"\n收支汇总:")
    click.echo(f"  收入: {format_currency(summary['income'])}")
    click.echo(f"  支出: {format_currency(summary['expense'])}")
    click.echo(f"  结余: {format_currency(summary['balance'])}")
    
    category_summary = report_data['category_summary']
    if category_summary:
        click.echo(f"\n分类统计:")
        
        income_categories = [c for c in category_summary if c['type'] == 'income']
        expense_categories = [c for c in category_summary if c['type'] == 'expense']
        
        if income_categories:
            click.echo(click.style("\n  收入分类:", fg='green'))
            for c in income_categories:
                click.echo(f"    {c['category']}: {format_currency(c['total'])} ({c['count']}笔)")
        
        if expense_categories:
            click.echo(click.style("\n  支出分类:", fg='red'))
            for c in expense_categories:
                click.echo(f"    {c['category']}: {format_currency(c['total'])} ({c['count']}笔)")


def _print_yearly_report(report_data):
    """打印年度报告"""
    click.echo(click.style(f"\n{'='*50}", fg='cyan'))
    click.echo(click.style(f"年度财务报告 ({report_data['year']}年)", 
                          fg='cyan', bold=True))
    click.echo(click.style(f"{'='*50}", fg='cyan'))
    
    summary = report_data['summary']
    click.echo(f"\n年度收支汇总:")
    click.echo(f"  收入: {format_currency(summary['income'])}")
    click.echo(f"  支出: {format_currency(summary['expense'])}")
    click.echo(f"  结余: {format_currency(summary['balance'])}")
    
    monthly_data = report_data['monthly_data']
    if monthly_data:
        click.echo(f"\n月度明细:")
        for m in monthly_data:
            click.echo(f"  {m['year']}-{m['month']:02d}: "
                      f"收入 {format_currency(m['income'])} | "
                      f"支出 {format_currency(m['expense'])} | "
                      f"结余 {format_currency(m['balance'])}")


@cli.command()
@click.option('--type', '-t', 'trans_type', type=click.Choice(['income', 'expense']), 
              default=None, help='交易类型筛选')
@click.option('--start', '-s', default=None, help='开始日期 (YYYY-MM-DD)')
@click.option('--end', '-e', default=None, help='结束日期 (YYYY-MM-DD)')
@pass_service
def category(service, trans_type, start, end):
    """查看分类统计"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    category_data = service.get_category_report(
        session.user, trans_type, start, end
    )
    
    data = category_data.get('category_data', [])
    if not data:
        click.echo("暂无分类统计数据")
        return
    
    for d in data:
        d['total'] = format_currency(d['total'])
        d['percentage'] = f"{d['percentage']:.1f}%"
        d['type'] = '收入' if d['type'] == 'income' else '支出'
    
    print_table(
        data,
        ['category', 'type', 'total', 'count', 'percentage'],
        ['分类', '类型', '金额', '笔数', '占比']
    )


@cli.command()
@click.option('--months', '-m', default=6, help='显示月份数')
@pass_service
def trend(service, months):
    """查看收支趋势"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    trend_data = service.get_trend_data(session.user, months)
    data = trend_data.get('trend_data', [])
    
    if not data:
        click.echo("暂无趋势数据")
        return
    
    for d in data:
        d['income'] = format_currency(d['income'])
        d['expense'] = format_currency(d['expense'])
        d['balance'] = format_currency(d['balance'])
    
    print_table(
        data,
        ['label', 'income', 'expense', 'balance'],
        ['月份', '收入', '支出', '结余']
    )


@cli.command()
@pass_service
def overview(service):
    """查看财务概览"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    overview_data = service.get_overview(session.user)
    
    click.echo(click.style(f"\n{'='*50}", fg='cyan'))
    click.echo(click.style("财务概览", fg='cyan', bold=True))
    click.echo(click.style(f"{'='*50}", fg='cyan'))
    
    current_month = overview_data['current_month']
    current_year = overview_data['current_year']
    
    click.echo(f"\n本月收支:")
    click.echo(f"  收入: {format_currency(current_month['income'])}")
    click.echo(f"  支出: {format_currency(current_month['expense'])}")
    click.echo(f"  结余: {format_currency(current_month['balance'])}")
    
    click.echo(f"\n本年收支:")
    click.echo(f"  收入: {format_currency(current_year['income'])}")
    click.echo(f"  支出: {format_currency(current_year['expense'])}")
    click.echo(f"  结余: {format_currency(current_year['balance'])}")
    
    recent = overview_data['recent_transactions']
    if recent:
        click.echo(f"\n最近交易记录:")
        for t in recent[:5]:
            trans_type = '收入' if t['type'] == 'income' else '支出'
            click.echo(f"  [{t['date']}] {trans_type}: "
                      f"{format_currency(t['amount'])} - {t['category']}")


@cli.command()
@click.option('--type', '-t', 'chart_type', 
              type=click.Choice(['trend', 'pie', 'bar', 'balance', 'dashboard']),
              default='trend', help='图表类型')
@click.option('--months', '-m', default=6, help='趋势图月份数')
@click.option('--trans-type', '-T', default='expense', 
              type=click.Choice(['income', 'expense']),
              help='饼图交易类型')
@pass_service
def chart(service, chart_type, months, trans_type):
    """生成可视化图表"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    generator = ChartGenerator()
    
    if chart_type == 'trend':
        trend_data = service.get_trend_data(session.user, months)
        filepath = generator.generate_trend_chart(trend_data)
    elif chart_type == 'pie':
        category_data = service.get_category_report(session.user, trans_type)
        filepath = generator.generate_pie_chart(category_data, trans_type)
    elif chart_type == 'bar':
        today = datetime.now()
        monthly_data = service.get_yearly_report(session.user, today.year)
        filepath = generator.generate_monthly_bar_chart(monthly_data)
    elif chart_type == 'balance':
        trend_data = service.get_trend_data(session.user, months)
        filepath = generator.generate_balance_line_chart(trend_data)
    elif chart_type == 'dashboard':
        overview = service.get_overview(session.user)
        trend_data = service.get_trend_data(session.user, months)
        category_data = service.get_category_report(session.user)
        filepath = generator.generate_dashboard(overview, trend_data, category_data)
    
    if filepath:
        click.echo(click.style(f"图表已生成: {filepath}", fg='green'))
    else:
        click.echo(click.style("图表生成失败", fg='red'))


@cli.command()
@click.option('--type', '-t', 'trans_type', type=click.Choice(['income', 'expense']), 
              default=None, help='交易类型筛选')
@pass_service
def categories(service, trans_type):
    """查看分类列表"""
    categories_list = service.get_categories(trans_type)
    
    if not categories_list:
        click.echo("暂无分类")
        return
    
    income_cats = [c for c in categories_list if c['type'] == 'income']
    expense_cats = [c for c in categories_list if c['type'] == 'expense']
    
    if not trans_type or trans_type == 'income':
        click.echo(click.style("\n收入分类:", fg='green'))
        for c in income_cats:
            default = " (默认)" if c['is_default'] else ""
            click.echo(f"  - {c['name']}{default}")
    
    if not trans_type or trans_type == 'expense':
        click.echo(click.style("\n支出分类:", fg='red'))
        for c in expense_cats:
            default = " (默认)" if c['is_default'] else ""
            click.echo(f"  - {c['name']}{default}")


@cli.command()
@click.option('--name', '-n', required=True, help='分类名称')
@click.option('--type', '-t', 'trans_type', 
              type=click.Choice(['income', 'expense']),
              required=True, help='交易类型')
@pass_service
def add_category(service, name, trans_type):
    """添加自定义分类"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    success, message = service.add_category(name, trans_type, session.user['id'])
    
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"添加失败: {message}", fg='red'))


@cli.command()
@click.option('--output', '-o', 'filepath', required=True, help='输出文件路径')
@click.option('--start', '-s', default=None, help='开始日期 (YYYY-MM-DD)')
@click.option('--end', '-e', default=None, help='结束日期 (YYYY-MM-DD)')
@pass_service
def export(service, filepath, start, end):
    """导出数据到CSV"""
    if not session.is_authenticated():
        click.echo(click.style("请先登录", fg='red'))
        return
    
    success, message = service.export_data(session.user, filepath, start, end)
    
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(f"导出失败: {message}", fg='red'))


@cli.command()
def help():
    """显示帮助信息"""
    click.echo(click.style("\n智能财务管理系统 - 命令帮助", fg='cyan', bold=True))
    click.echo(click.style("="*50, fg='cyan'))
    
    commands = [
        ('login', '用户登录'),
        ('register', '用户注册'),
        ('logout', '用户登出'),
        ('add', '添加交易记录'),
        ('update', '更新交易记录'),
        ('delete', '删除交易记录'),
        ('list', '查看交易记录列表'),
        ('range', '查看日期范围内的交易记录'),
        ('report', '生成财务报告'),
        ('category', '查看分类统计'),
        ('trend', '查看收支趋势'),
        ('overview', '查看财务概览'),
        ('chart', '生成可视化图表'),
        ('categories', '查看分类列表'),
        ('add-category', '添加自定义分类'),
        ('export', '导出数据到CSV'),
    ]
    
    for cmd, desc in commands:
        click.echo(f"  {cmd:<15} - {desc}")
    
    click.echo(f"\n使用 'python main.py <command> --help' 查看详细帮助")


if __name__ == '__main__':
    cli()
