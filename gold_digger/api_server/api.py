# -*- coding: utf-8 -*-

import json
import falcon
from datetime import date, timedelta
from wsgiref import simple_server
from ..database.db_model import ExchangeRate
from ..managers.exchange_rate_manager import get_rates, get_range_rates


def make_server(container):
    app = falcon.API()
    date_rate_resource = DateRateResource(container.db_session, container.data_providers)
    range_rate_resource = RangeRateResource(container.db_session, container.data_providers)

    app.add_route("/rate", date_rate_resource)
    app.add_route("/range", range_rate_resource)

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
