# -*- coding: utf-8 -*-
import click
from datetime import datetime, date
from .api_server.api_server import API
from .database.db_model import Base
from .config import DiContainer, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS


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


@cli.command("initialize-db", help="Create empty table (drop if exists)")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        Base.metadata.drop_all(c.db_connection)
        Base.metadata.create_all(c.db_connection)


@cli.command("update-all", help="Update rates since origin date (default 2015-01-01)")
@click.option("--origin-date", default=date(2015, 1, 1), callback=_parse_date, help="Specify date in format 'yyyy-mm-dd'")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        c.exchange_rate_manager.update_all_historical_rates(kwargs["origin_date"])


@cli.command("update", help="Update rates of specified day (default today)")
@click.option("--date", default=date.today(), callback=_parse_date, help="Specify date in format 'yyyy-mm-dd'")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        c.exchange_rate_manager.update_all_rates_by_date(kwargs["date"])


@cli.command("serve", help="Run API server (simple)")
@click.option("--host", default="localhost")
@click.option("--port", default=8000)
def command(**kwargs):
    app = API()
    app.simple_server(kwargs["host"], kwargs["port"])


if __name__ == "__main__":
    cli()
