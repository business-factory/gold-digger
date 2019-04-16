# -*- coding: utf-8 -*-

from datetime import date, timedelta

import requests

from ._provider import Provider


class RatesAPI(Provider):
    """
    Free service for current and historical foreign exchange rates built on top of data published by European Central Bank.
    Rates are updated only on working days around 16:00 CET
    """
    BASE_URL = "http://api.ratesapi.io/api/{date}"
    name = "rates_api"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = self.BASE_URL
        self._supported_currencies = {}

    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        currencies = self._supported_currencies.get(date_of_exchange)
        if currencies:
            return currencies

        currencies = set()
        response = self._get(self._url.format(date=date_of_exchange.isoformat()), logger=logger)
        if response:
            response = response.json()
            if not response.get("error"):
                currencies = set((response.get("rates") or {}).keys())
            else:
                logger.error("Rates API supported currencies not found. Error: %s. Date: %s", response, date_of_exchange.isoformat())
        else:
            logger.error("Rates API unexpected response. Response: %s", response)

        if currencies:
            logger.debug("Rates API supported currencies: %s", currencies)

        self._supported_currencies = {date_of_exchange: currencies}

        return currencies

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal]
        """
        logger.debug("Rates API - Requesting rates for all currencies (%s)", date_of_exchange, extra={"date": date_of_exchange})
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        day_rates = {}

        url = self._url.format(date=date_of_exchange_string)
        response = self._get(url, params={"base": self.base_currency}, logger=logger)

        if response is not None:
            try:
                response = response.json()
                if response.get("error"):
                    logger.error("Rates API - Unsuccessful response. Error message: %s", response["error"])
                    return {}

                rates = response.get("rates", {})

                for currency in currencies:
                    if currency in rates:
                        decimal_value = self._to_decimal(rates[currency], currency, logger=logger)
                        if decimal_value is not None:
                            day_rates[currency] = decimal_value
            except ValueError:
                logger.exception("Rates API - Exception while parsing of the HTTP response.")
                return {}

        return day_rates

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        """
                :type date_of_exchange: str
                :type currency: str
                :type logger: gold_digger.utils.ContextLogger
                :rtype: decimal.Decimal | None
                """
        logger.debug("Rates API - Requesting rates for %s (%s)", currency, date_of_exchange, extra={"currency": currency, "date": date_of_exchange})

        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")

        url = self._url.format(date=date_of_exchange_string)
        response = self._get(url, params={"symbols": currency, "base": self.base_currency}, logger=logger)
        if response:
            try:
                response = response.json()
                if response.get("error"):
                    logger.error("Rates API - Unsuccessful response. Error message: %s", response["error"])
                    return None

                rates = response.get("rates", {})
                if currency in rates:
                    print(self._to_decimal(rates[currency], currency, logger=logger))
                    return self._to_decimal(rates[currency], currency, logger=logger)

            except ValueError:
                logger.exception("Rates API - Exception while parsing of the HTTP response.")

        return None

    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
        date_of_exchange = origin_date
        date_of_today = date.today()
        if date_of_exchange > date_of_today:
            date_of_exchange, date_of_today = date_of_today, date_of_exchange

        step_by_day = timedelta(days=1)
        historical_rates = {}

        while date_of_exchange != date_of_today:
            day_rates = self.get_all_by_date(date_of_exchange, currencies, logger)
            if day_rates:
                historical_rates[date_of_exchange] = day_rates
            date_of_exchange += step_by_day

        return historical_rates

    def _get(self, url, params=None, *, logger):
        """
        :type url: str
        :type params: dict[str, str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: requests.Response | None
        """
        try:
            response = requests.get(url, params=params, timeout=self.DEFAULT_REQUEST_TIMEOUT)
            if response.status_code != 200:
                logger.error("%s - status code: %s, URL: %s, Params: %s", self, response.status_code, url, params)
            return response
        except requests.exceptions.RequestException as e:
            logger.error("%s - exception: %s, URL: %s, Params: %s", self, e, url, params)

    def __str__(self):
        return self.name
