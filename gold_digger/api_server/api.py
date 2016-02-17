# -*- coding: utf-8 -*-

import json
import falcon
from datetime import date
from wsgiref import simple_server


def make_server(container):
    app = falcon.API()
    date_rate_resource = DateRateResource(container)
    range_rate_resource = RangeRateResource(container)

    app.add_route("/rate", date_rate_resource)
    app.add_route("/range", range_rate_resource)

    server = simple_server.make_server("localhost", 25800, app)
    server.serve_forever()


class DatabaseResource:
    def __init__(self, container):
        self.container = container


class DateRateResource(DatabaseResource):
    def on_get(self, req, resp):
        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to", required=True)
        date_of_exchange = req.get_param_as_date("date")
        date_of_exchange = date_of_exchange if date_of_exchange else date.today()

        invalid_currencies = [currency for currency in (from_currency, to_currency) if currency not in self.container["supported_currencies"]]
        if invalid_currencies:
            raise falcon.HTTPInvalidParam("Invalid currency", " and ".join(invalid_currencies))

        exchange_rate = self.container.exchange_rate_manager.get_exchange_rate_by_date(date_of_exchange, from_currency, to_currency)

        if not exchange_rate:
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "date": date_of_exchange.strftime(format="%Y-%m-%d"),
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": str(exchange_rate)
            }
        )


class RangeRateResource(DatabaseResource):
    def on_get(self, req, resp):
        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to", required=True)
        start_date = req.get_param_as_date("start_date", required=True)
        end_date = req.get_param_as_date("end_date", required=True)

        invalid_currencies = [currency for currency in (from_currency, to_currency) if currency not in self.container["supported_currencies"]]
        if invalid_currencies:
            raise falcon.HTTPInvalidParam("Invalid currency", " and ".join(invalid_currencies))

        exchange_rate = self.container.exchange_rate_manager.get_average_exchange_rate_by_dates(start_date, end_date, from_currency, to_currency)

        if not exchange_rate:
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "start_date": start_date.strftime(format="%Y-%m-%d"),
                "end_date": end_date.strftime(format="%Y-%m-%d"),
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": str(exchange_rate)
            }
        )
