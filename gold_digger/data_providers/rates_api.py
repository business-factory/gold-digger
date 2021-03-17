from datetime import date, timedelta
from operator import attrgetter

import requests
from cachetools import cachedmethod, keys

from ._provider import Provider


class RatesAPI(Provider):
    """
    Free service for current and historical foreign exchange rates built on top of data published by European Central Bank.
    Rates are updated only on working days around 16:00 CET
    """
    BASE_URL = "http://api.ratesapi.io/api/{date}"
    name = "rates_api"

    @cachedmethod(cache=attrgetter("_cache"), key=lambda date_of_exchange, _: keys.hashkey(date_of_exchange))
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        currencies = set()
        url = self.BASE_URL.format(date=date_of_exchange.isoformat())
        response = self._get(url, logger=logger)
        if response is not None:
            response = response.json()
            if not response.get("error"):
                currencies = set((response.get("rates") or {}).keys())
                currencies.add(response["base"])
            else:
                logger.error("%s - Supported currencies not found. Error: %s. Date: %s", self, response["error"], date_of_exchange.isoformat())

        if currencies:
            logger.debug("%s - Supported currencies: %s", self, currencies)

        return currencies

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal]
        """
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        logger.debug("%s - Requesting rates for all currencies (%s)", self, date_of_exchange_string, extra={"date": date_of_exchange_string})
        day_rates = {}

        url = self.BASE_URL.format(date=date_of_exchange_string)
        response = self._get(url, params={"base": self.base_currency}, logger=logger)

        if response is not None:
            try:
                response = response.json()
                if response.get("error"):
                    logger.error("%s - Unsuccessful response. Error message: %s", self, response["error"])
                    return {}

                rates = response.get("rates", {})
                if self.base_currency == "EUR":  # Rates API doesn't return EUR in response if it is base currency
                    rates["EUR"] = 1

                for currency in currencies:
                    if currency in rates:
                        decimal_value = self._to_decimal(rates[currency], currency, logger=logger)
                        if decimal_value is not None:
                            day_rates[currency] = decimal_value
            except ValueError:
                logger.exception("%s - Exception while parsing of the HTTP response.", self)
                return {}

        return day_rates

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        logger.debug("%s - Requesting for %s (%s)", self, currency, date_of_exchange_string, extra={"currency": currency, "date": date_of_exchange_string})

        if currency == "EUR" and self.base_currency == "EUR":  # Rates API in this combination returns error
            return self._to_decimal(1, "EUR", logger=logger)

        url = self.BASE_URL.format(date=date_of_exchange_string)
        response = self._get(url, params={"symbols": currency, "base": self.base_currency}, logger=logger)
        if response is not None:
            try:
                response = response.json()
                if response.get("error"):
                    logger.error("%s - Unsuccessful response. Error message: %s", self, response["error"])
                    return None

                rates = response.get("rates", {})
                if currency in rates:
                    return self._to_decimal(rates[currency], currency, logger=logger)

            except ValueError:
                logger.exception("%s - Exception while parsing of the HTTP response.", self)

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
                logger.error("%s - Status code: %s, URL: %s, Params: %s", self, response.status_code, url, params)
            return response
        except requests.exceptions.RequestException as e:
            logger.error("%s - Exception: %s, URL: %s, Params: %s", self, e, url, params)
