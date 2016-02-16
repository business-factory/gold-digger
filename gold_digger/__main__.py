# -*- coding: utf-8 -*-

import click
from gold_digger.database.db_model import Base
from .api_server.api import make_server
from .config import DiContainer, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS
from .managers.exchange_rate_manager import update_all_rates_by_date, update_all_historical_rates


@click.group()
def cli():
    pass


@cli.command("initialize-db", help="Create empty table (drop if exists)")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        Base.metadata.drop_all(c.db_connection)
        Base.metadata.create_all(c.db_connection)


@cli.command("update-all", help="Update rates since origin date (default 2015-01-01)")
@click.option("--origin-date", default="2015-01-01", help="Specify date in format 'yyyy-mm-dd'")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        update_all_historical_rates(c, kwargs["origin_date"])


@cli.command("update", help="Update rates of specified day (default today)")
@click.option("--date", default=None, help="Specify date in format 'yyyy-mm-dd'")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        update_all_rates_by_date(c, kwargs["date"])


@cli.command("serve", help="Run API server")
def command(**kwargs):
    with DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS) as c:
        make_server(c)


if __name__ == "__main__":
    cli()
