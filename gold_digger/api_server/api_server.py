# -*- coding: utf-8 -*-

import json
from datetime import date
from wsgiref import simple_server

import falcon
from sqlalchemy.exc import DatabaseError

from .helpers import http_api_logger
from .. import di_container
from ..settings import SUPPORTED_CURRENCIES


class DatabaseResource:
    def __init__(self, container):
        self.container = container


class DateRateResource(DatabaseResource):
    @http_api_logger
    def on_get_date_rate(self, req, resp, logger):
        """
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        :type logger: gold_digger.utils.ContextLogger
        """
        exchange_rate_manager = self.container.exchange_rate_manager

        logger.info("Data rate request: %s", req.params)

        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to", required=True)
        date_of_exchange = req.get_param_as_date("date")
        date_of_exchange = date_of_exchange if date_of_exchange else date.today()

        invalid_currencies = [currency for currency in (from_currency, to_currency) if currency not in SUPPORTED_CURRENCIES]
        if invalid_currencies:
            raise falcon.HTTPInvalidParam("Invalid currency", " and ".join(invalid_currencies))

        exchange_rate = None
        try:
            exchange_rate = exchange_rate_manager.get_exchange_rate_by_date(date_of_exchange, from_currency, to_currency, logger)
        except DatabaseError:
            self.container.db_session.rollback()
            logger.exception("Database error occurred. Rollback session to allow reconnect to the DB on next request.")
        except Exception:
            logger.exception("Unexpected exception while rate request %s->%s (%s)", from_currency, to_currency, date_of_exchange)

        if not exchange_rate:
            logger.error("Exchange rate not found: rate %s %s->%s", date_of_exchange, from_currency, to_currency)
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        logger.info("GET rate %s %s->%s %s", date_of_exchange, from_currency, to_currency, exchange_rate)

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "date": date_of_exchange.strftime("%Y-%m-%d"),
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": str(exchange_rate)
            }
        )


class DateRatesResource(DatabaseResource):
    @http_api_logger
    def on_get_date_rates(self, req, resp, logger):
        """
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        :type logger: gold_digger.utils.ContextLogger
        """
        logger.info("Rates request: %s", req.params)
        exchange_rate_manager = self.container.exchange_rate_manager

        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to", required=True)
        start_date = req.get_param_as_date("start_date", required=True)
        end_date = req.get_param_as_date("end_date", required=True)

        invalid_currencies = [currency for currency in (from_currency, to_currency) if currency not in SUPPORTED_CURRENCIES]
        if invalid_currencies:
            raise falcon.HTTPInvalidParam("Invalid currency", " and ".join(invalid_currencies))

        exchange_rates_by_dates = {}
        try:
            exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(start_date, end_date, from_currency, to_currency, logger)
        except DatabaseError:
            self.container.db_session.rollback()
            logger.exception("Database error occurred. Rollback session to allow reconnect to the DB on next request.")
        except Exception:
            logger.exception("Unexpected exception while rates request %s->%s (%s - %s)", from_currency, to_currency, start_date, end_date)

        logger.info("GET rates %s/%s %s->%s %s", start_date, end_date, from_currency, to_currency, exchange_rates_by_dates)

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(
            {
                "start_date": start_date.strftime(format="%Y-%m-%d"),
                "end_date": end_date.strftime(format="%Y-%m-%d"),
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rates": [
                    {
                        "date": date_from_range,
                        "exchange_rate": exchange_rate,
                    }
                    for date_from_range, exchange_rate in exchange_rates_by_dates.items()
                ],
            },
        )


class RangeRateResource(DatabaseResource):
    @http_api_logger
    def on_get_range_rate(self, req, resp, logger):
        """
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        :type logger: gold_digger.utils.ContextLogger
        """
        logger.info("Range rate request: %s", req.params)
        exchange_rate_manager = self.container.exchange_rate_manager

        from_currency = req.get_param("from", required=True)
        to_currency = req.get_param("to", required=True)
        start_date = req.get_param_as_date("start_date", required=True)
        end_date = req.get_param_as_date("end_date", required=True)

        invalid_currencies = [currency for currency in (from_currency, to_currency) if currency not in SUPPORTED_CURRENCIES]
        if invalid_currencies:
            raise falcon.HTTPInvalidParam("Invalid currency", " and ".join(invalid_currencies))

        exchange_rate = None
        try:
            if start_date == end_date:
                exchange_rate = exchange_rate_manager.get_exchange_rate_by_date(start_date, from_currency, to_currency, logger)
            else:
                exchange_rate = exchange_rate_manager.get_average_exchange_rate_by_dates(start_date, end_date, from_currency, to_currency, logger)
        except DatabaseError:
            self.container.db_session.rollback()
            logger.exception("Database error occurred. Rollback session to allow reconnect to the DB on next request.")
        except Exception:
            logger.exception("Unexpected exception while range request %s->%s (%s - %s)", from_currency, to_currency, start_date, end_date)

        if not exchange_rate:
            logger.error("Exchange rate not found: range %s/%s %s->%s", start_date, end_date, from_currency, to_currency)
            raise falcon.HTTPInternalServerError("Exchange rate not found", "Exchange rate not found")

        logger.info("GET range %s/%s %s->%s %s", start_date, end_date, from_currency, to_currency, exchange_rate)

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


class HealthCheckResource:
    def on_get_check_readiness(self, req, resp):
        """
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        """
        resp.body = '{"status": "UP"}'
        resp.status = falcon.HTTP_200


class HealthAliveResource(DatabaseResource):
    def on_get_check_liveness(self, req, resp):
        """
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        """
        logger = self.container.logger()
        try:
            self.container.db_session.execute("SELECT 1")
            resp.body = '{"status": "UP"}'
        except DatabaseError as e:
            self.container.db_session.rollback()
            info = "Database error. Service will reconnect to the DB automatically. Exception: %s" % e
            resp.body = '{"status": "DOWN", "info": "%s"}' % info
            logger.exception(info)
        except Exception as e:
            resp.body = '{"status": "DOWN", "info": "%s"}' % e
            logger.exception("Unexpected exception.")

        resp.status = falcon.HTTP_200


class API(falcon.API):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = di_container(__file__)
        self.add_route("/rate", DateRateResource(self.container), suffix="date_rate")
        self.add_route("/rates", DateRatesResource(self.container), suffix="date_rates")
        self.add_route("/range", RangeRateResource(self.container), suffix="range_rate")
        self.add_route("/health", HealthCheckResource(), suffix="check_readiness")
        self.add_route("/health/alive", HealthAliveResource(self.container), suffix="check_liveness")

    def simple_server(self, host, port):
        # Ignore PyPrintBear
        print("Starting HTTP server at {}:{}".format(host, port))
        server = simple_server.make_server(host, port, self)
        server.serve_forever()
