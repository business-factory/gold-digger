# -*- coding: utf-8 -*-

import json
import falcon
from datetime import date
from wsgiref import simple_server
from ..config import DiContainer, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS


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

        try:
            exchange_rate = self.container.exchange_rate_manager.get_exchange_rate_by_date(date_of_exchange, from_currency, to_currency)
        except Exception as e:
            exchange_rate = None
            self.container.logger.exception(e)

        if not exchange_rate:
            self.container.logger.error("Exchange rate not found: rate %s %s->%s", date_of_exchange, from_currency, to_currency)
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        self.container.logger.debug("GET rate %s %s->%s %s", date_of_exchange, from_currency, to_currency, exchange_rate)

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

        try:
            if start_date == end_date:
                exchange_rate = self.container.exchange_rate_manager.get_exchange_rate_by_date(start_date, from_currency, to_currency)
            else:
                exchange_rate = self.container.exchange_rate_manager.get_average_exchange_rate_by_dates(start_date, end_date, from_currency, to_currency)
        except Exception as e:
            exchange_rate = None
            self.container.logger.exception(e)

        if not exchange_rate:
            self.container.logger.error("Exchange rate not found: range %s/%s %s->%s", start_date, end_date, from_currency, to_currency)
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        self.container.logger.debug("GET range %s/%s %s->%s %s", start_date, end_date, from_currency, to_currency, exchange_rate)

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


class HealthCheckResource(DatabaseResource):
    def on_get(self, req, resp):
        try:
            exchange_rate = self.container.exchange_rate_manager.get_exchange_rate_by_date(date.today(), "USD", "USD")
            if exchange_rate:
                resp.body = '{"status": "UP"}'
            else:
                resp.body = '{"status": "DOWN", "info": "No exchange rate available."}'

        except Exception as e:
            resp.body = '{"status": "DOWN", "info": "%s"}' % e

        resp.status = falcon.HTTP_200


class API(falcon.API):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = DiContainer(__file__, DEFAULT_CONFIG_PARAMS, LOCAL_CONFIG_PARAMS)
        self.add_route("/rate", DateRateResource(self.container))
        self.add_route("/range", RangeRateResource(self.container))
        self.add_route("/health", HealthCheckResource(self.container))

    def simple_server(self, host, port):
        server = simple_server.make_server(host, port, self)
        server.serve_forever()
