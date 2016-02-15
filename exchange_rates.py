# -*- coding: utf-8 -*-

import json
from datetime import date, timedelta

import click
import falcon
from collections import defaultdict
from config.di import DiContainer
from database.db_handler import update_db
from database.db_model import ExchangeRate, Base
from sqlalchemy import and_


def update_rates(container, all_days=False):
    if all_days:
        for data_provider in container.data_providers:
            day_rates = data_provider.get_historical(ExchangeRate.currencies(), container["origin_date"])
            for day, rates in day_rates:
                update_db(container.db_session, day, str(data_provider), rates)
    else:
        update_data_from_providers(container.db_session, date.today(), ExchangeRate.currencies(), container.data_providers)


def get_rates(db_session, date_of_exchange, query, currencies, data_providers):
    p = [getattr(ExchangeRate, currency).isnot(None) for currency in currencies]
    rates = db_session.query(*query).filter(and_(ExchangeRate.date == date_of_exchange, *p)).all()
    if not rates:
        rates = update_data_from_providers(db_session, date_of_exchange, currencies, data_providers)
    return rates[0]


def get_range_rates(db_session, start_date, end_date, query, currencies, data_providers):
    date_range = [start_date]
    while date_range[-1] != end_date:
        date_range.append(date_range[-1] + timedelta(1))

    p = [getattr(ExchangeRate, currency).isnot(None) for currency in currencies]
    rates = db_session.query(ExchangeRate).filter(ExchangeRate.date.in_(date_range), *p).all()
    if len(rates) != len(date_range):
        print("warning: some days miss")

    rates_per_date = defaultdict(list)
    for rate in rates:
        rates_per_date[rate.date].append(rate)

    rates_per_date = [rate[0] for rate in rates_per_date.values()]
    average_rates = defaultdict(int)
    for rate in rates_per_date:
        for currency in currencies:
            average_rates[currency] += getattr(rate, currency)
    average_exchange_rate = ExchangeRate()
    number_of_days = len(rates_per_date)
    for currency, value in average_rates.items():
        setattr(average_exchange_rate, currency, value / number_of_days)
    return average_exchange_rate


def update_data_from_providers(db_session, date_of_exchange, currencies, data_providers):
    all_rates = []
    for data_provider in data_providers:
        rates = data_provider.get_by_date(date_of_exchange, currencies)
        if rates:
            update_db(db_session, date_of_exchange, str(data_provider), rates)
            all_rates.append(ExchangeRate(date=date_of_exchange, provider=str(data_provider), **rates))
        print(date_of_exchange, data_provider, rates)
    return all_rates


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
        date_rate_resource = DateRateResource(c.db_session, c.data_providers)
        range_rate_resource = RangeRateResource(c.db_session, c.data_providers)

        app.add_route("/rate", date_rate_resource)
        app.add_route("/range", range_rate_resource)

        from wsgiref import simple_server
        server = simple_server.make_server("localhost", 25800, app)
        server.serve_forever()


class DatabaseResource:
    def __init__(self, db_session, data_providers):
        self.db_session = db_session
        self.data_providers = data_providers


class DateRateResource(DatabaseResource):
    def on_get(self, req, resp):
        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to")
        date_of_exchange = req.get_param_as_date("date")

        from_currency_attr = getattr(ExchangeRate, from_currency, None)
        if from_currency_attr is None:
            raise falcon.HTTPInvalidParam("Invalid currency", from_currency)

        date_of_exchange = date_of_exchange if date_of_exchange else date.today()

        if to_currency:
            to_currency_attr = getattr(ExchangeRate, to_currency, None)
            if to_currency_attr is None:
                raise falcon.HTTPInvalidParam("Invalid currency", to_currency)
            query = ExchangeRate.USD, from_currency_attr, to_currency_attr
            to_currencies = {to_currency}
        else:
            query = ExchangeRate,
            to_currencies = set(ExchangeRate.currencies())

        for i in range(10):
            rate = get_rates(self.db_session, date_of_exchange - timedelta(i), query, to_currencies.union(("USD", from_currency)), self.data_providers)
            if rate:
                break
            print("trying yesterday")
        else:
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

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
        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to")
        start_date = req.get_param_as_date("start_date", required=True)
        end_date = req.get_param_as_date("end_date", required=True)

        from_currency_attr = getattr(ExchangeRate, from_currency, None)
        if from_currency_attr is None:
            raise falcon.HTTPInvalidParam("Invalid currency", from_currency)

        if to_currency:
            to_currency_attr = getattr(ExchangeRate, to_currency, None)
            if to_currency_attr is None:
                raise falcon.HTTPInvalidParam("Invalid currency", to_currency)
            query = ExchangeRate.USD, from_currency_attr, to_currency_attr
            to_currencies = {to_currency}
        else:
            query = ExchangeRate,
            to_currencies = set(ExchangeRate.currencies())

        rate = get_range_rates(self.db_session, start_date, end_date, query, to_currencies.union(("USD", from_currency)), self.data_providers)

        conversion = rate.USD / getattr(rate, from_currency)

        exchange_rates = {}
        for to in to_currencies:
            to_rate = getattr(rate, to)
            if to_rate:
                exchange_rates[to] = float(to_rate * conversion)

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "start_date": start_date.strftime(format="%Y-%m-%d"),
                "end_date": end_date.strftime(format="%Y-%m-%d"),
                "from_currency": from_currency,
                "exchange_rates": exchange_rates
            }
        )


if __name__ == "__main__":
    cli()
