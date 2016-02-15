# -*- coding: utf-8 -*-

import click
from gold_digger.database.db_model import Base
from .api_server.api import make_server
from .config.di import DiContainer
from .managers.exchange_rate_manager import update_rates


@click.group()
def cli():
    pass


@cli.command("recreate-db", help="Create empty table (drop if exists)")
def command(**kwargs):
    with DiContainer() as c:
        Base.metadata.drop_all(c.db_connection)
        Base.metadata.create_all(c.db_connection)


@cli.command("update-all", help="Update historical rates")
def command(**kwargs):
    with DiContainer() as c:
        update_rates(c, all_days=True)


@cli.command("update", help="Update actual rates")
def command(**kwargs):
    with DiContainer() as c:
        update_rates(c)


@cli.command("serve", help="Run API server")
def command(**kwargs):
    with DiContainer() as c:
        make_server(c)


if __name__ == "__main__":
    cli()
