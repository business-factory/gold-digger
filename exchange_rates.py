# -*- coding: utf-8 -*-

import json
from datetime import date, datetime
from decimal import Decimal

import click
import falcon
import requests
from collections import defaultdict
from db_model import ExchangeRate, Base
from di import DiContainer


def get_historical_rates_grandtrunk(provider_grandtrunk, origin_date, base_currency):
    day_rates = defaultdict(dict)
    for to_currency in ExchangeRate.currencies():
        response = requests.get("{url}/getrange/{from_date}/{to_date}/{from_currency}/{to}".format(
            url=provider_grandtrunk, from_date=origin_date, to_date="2016-02-01", from_currency=base_currency, to=to_currency
        ))
        for record in response.text.strip().split("\n"):
            record = record.rstrip()
            if record:
                date_string, exchange_rate_string = record.split(" ")
                day = datetime.strptime(date_string, "%Y-%m-%d")
                day_rates[day][to_currency] = Decimal(exchange_rate_string)
    return day_rates


def get_today_cl(provider_cl):
    date_string = date.today()
    response = requests.get("{url}&date={date}".format(url=provider_cl, date=date_string))
    day_rate = {}
    for currency_pair, value in response.json()["quotes"].items():
        day_rate[currency_pair[3:]] = Decimal(value)
    return {date.today(): day_rate}


def _update_db(session, day, provider, currencies):
    db_day = session.query(ExchangeRate).filter(ExchangeRate.date == day).first()
    if db_day:
        session.query(ExchangeRate).filter(ExchangeRate.date == db_day.date).update(currencies)
    else:
        session.add(ExchangeRate(date=day, provider=provider, **currencies))
    session.commit()


def update_rates(container, all_days=False):
    if all_days:
        day_rates_grandtrunk = get_historical_rates_grandtrunk(
            container["data_providers"]["grandtrunk"], container["origin_date"], container["base_currency"])
        day_rates_cl = {}
    else:
        day_rates_grandtrunk = {}
        day_rates_cl = get_today_cl(container["data_providers"]["currency_layer"])

    for day, currencies in day_rates_grandtrunk.items():
        _update_db(container.db_session, day, "grandtrunk", currencies)
    for day, currencies in day_rates_cl.items():
        _update_db(container.db_session, day, "cl", currencies)


@click.group()
def cli():
    pass


@cli.command("recreate-db")
def command(**kwargs):
    with DiContainer() as c:
        Base.metadata.drop_all(c.db_connection)
        Base.metadata.create_all(c.db_connection)


@cli.command("update-all")
def command(**kwargs):
    with DiContainer() as c:
        update_rates(c, all_days=True)


@cli.command("update")
def command(**kwargs):
    with DiContainer() as c:
        update_rates(c)


@cli.command("serve")
def command(**kwargs):
    with DiContainer() as c:
        app = falcon.API()
        date_rate_resource = DateRateResource(c.db_session)
        range_rate_resource = RangeRateResource(c.db_session)

        app.add_route("/rate", date_rate_resource)
        app.add_route("/range", range_rate_resource)

        from wsgiref import simple_server
        server = simple_server.make_server("localhost", 25800, app)
        server.serve_forever()


class DatabaseResource:
    def __init__(self, db_session):
        self.db_session = db_session


class DateRateResource(DatabaseResource):
    def on_get(self, req, resp):
        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to")
        date_of_exchange = req.get_param_as_date("date")

        from_currency_attr = getattr(ExchangeRate, from_currency, None)
        if from_currency_attr is None:
            raise falcon.HTTPInvalidParam("Invalid currency", from_currency)
        to_currency_attr = getattr(ExchangeRate, to_currency, None)
        if to_currency is not None and to_currency_attr is None:
            raise falcon.HTTPInvalidParam("Invalid currency", to_currency)

        date_of_exchange = date_of_exchange if date_of_exchange else date.today()

        if to_currency:
            query = ExchangeRate.USD, from_currency_attr, to_currency_attr
            to_currencies = to_currency,
        else:
            query = ExchangeRate,
            to_currencies = ExchangeRate.currencies()

        rate = self.db_session.query(*query).filter(ExchangeRate.date == date_of_exchange).first()
        conversion = rate.USD / getattr(rate, from_currency)

        exchange_rates = {}
        for to in to_currencies:
            to_rate = getattr(rate, to)
            if to_rate:
                exchange_rates[to] = float(to_rate * conversion)

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "date": date_of_exchange.strftime(format="%Y-%m-%d"),
                "from_currency": from_currency,
                "exchange_rates": exchange_rates
            }
        )


class RangeRateResource(DatabaseResource):
    def on_get(self, req, resp):
        _from = req.get_param("from", required=True)
        _to = req.get_param("to")
        _start_date = req.get_param_as_date("start_date", required=True)
        _end_date = req.get_param_as_date("end_date", required=True)

        resp.status = falcon.HTTP_200
        resp.body = "TODO"


if __name__ == "__main__":
    cli()
