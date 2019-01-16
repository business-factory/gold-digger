# -*- coding: utf-8 -*-
import click
from crontab import CronTab
from datetime import datetime, date
from . import di_container
from .api_server.api_server import API
from .database.db_model import Base
from .settings import DATABASE_NAME


def _parse_date(ctx, param, value):
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise click.BadParameter('Date should be in format yyyy-mm-dd')


@click.group()
def cli():
    pass


@cli.command("cron", help="Run cron jobs")
def cron(**kwargs):
    with di_container(__file__) as c:
        cron_tab = CronTab(
            tab="""
                # m h dom mon dow command
                5 0 * * * cd /app && python -m gold_digger update --exclude-providers fixer.io {redirect}
                5 2 * * * cd /app && python -m gold_digger update --providers fixer.io {redirect}
                * * * * * echo "cron health check (hourly)" {redirect}
            """.format(redirect="> /proc/1/fd/1 2>/proc/1/fd/2")  # redirect to stdout/stderr
        )

        c.logger.info("Cron started. Commands:\n{}\n---".format("\n".join(list(map(str, cron_tab.crons)))))

        for result in cron_tab.run_scheduler():
            print(result)


@cli.command("initialize-db", help="Create empty table (drop if exists)")
def command(**kwargs):
    with di_container(__file__) as c:
        print("This will drop & create all tables in '%s'. To continue press 'c'" % DATABASE_NAME)
        if input() != "c":
            return
        Base.metadata.drop_all(c.db_connection)
        Base.metadata.create_all(c.db_connection)


@cli.command("update-all", help="Update rates since origin date (default 2015-01-01)")
@click.option("--origin-date", default=date(2015, 1, 1), callback=_parse_date, help="Specify date in format 'yyyy-mm-dd'")
def command(**kwargs):
    with di_container(__file__) as c:
        c.exchange_rate_manager.update_all_historical_rates(kwargs["origin_date"])


@cli.command("update", help="Update rates of specified day (default today)")
@click.option("--date", default=date.today(), callback=_parse_date, help="Specify date in format 'yyyy-mm-dd'")
@click.option("--providers", type=str, help="Specify data providers names separated by comma.")
@click.option("--exclude-providers", type=str, help="Specify data providers names separated by comma.")
def command(**kwargs):
    with di_container(__file__) as c:
        if kwargs["providers"]:
            providers = kwargs["providers"].split(",")
        else:
            providers = list(c.data_providers)

        if kwargs["exclude_providers"]:
            excluded_providers = kwargs["exclude_providers"].split(",")
            providers = [p for p in providers if p not in excluded_providers]

        data_providers = [c.data_providers[provider_name] for provider_name in providers]
        c.exchange_rate_manager.update_all_rates_by_date(kwargs["date"], data_providers)


@cli.command("api", help="Run API server (simple)")
@click.option("--host", "-h", default="localhost")
@click.option("--port", "-p", default=8080)
def command(**kwargs):
    app = API()
    app.simple_server(kwargs["host"], kwargs["port"])


if __name__ == "__main__":
    cli()
