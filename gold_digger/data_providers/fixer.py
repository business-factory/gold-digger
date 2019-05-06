# -*- coding: utf-8 -*-

from datetime import date, timedelta
from operator import attrgetter

from cachetools import cachedmethod, keys

from ._provider import Provider


class Fixer(Provider):
    """
    Base currency is in EUR and cannot be changed in free subscription.
    We have to convert exchange rates to base currency (USD) before returning the rates from the provider.
    https://fixer.io/documentation
    """
    BASE_URL = "http://data.fixer.io/api/{path}?access_key=%s"
    name = "fixer.io"

    def __init__(self, access_key, logger, *args, **kwargs):
        """
        :type access_key: str
        :type logger: gold_digger.utils.ContextLogger
        """
        super().__init__(*args, **kwargs)
        if access_key:
            self._url = self.BASE_URL % access_key
        else:
            logger.critical("You need an access token to use Fixer provider!")
            self._url = self.BASE_URL % ""

    @cachedmethod(cache=attrgetter("_cache"), key=lambda date_of_exchange, _: keys.hashkey(date_of_exchange))
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        currencies = set()
        response = self._get(self._url.format(path="symbols"), logger=logger)
        if response:
            response = response.json()
            if response.get("success"):
                currencies = set((response.get("symbols") or {}).keys())
            else:
                logger.error("Fixer supported currencies not found. Error: %s. Date: %s", response, date_of_exchange.isoformat())
        else:
            logger.error("Fixer unexpected response. Response: %s", response)

        if currencies:
            logger.debug("Fixer supported currencies: %s", currencies)

        return currencies

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        return self._get_by_date(date_of_exchange_string, currency, logger)

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal]
        """
        logger.debug("Fixer.io - get all for date %s", date_of_exchange)
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        day_rates_in_eur = {}

        url = self._url.format(path=date_of_exchange_string)
        response = self._get(url, logger=logger)

        if response:
            try:
                response = response.json()
                if not response.get("success"):
                    logger.error("Fixer.io - Unsuccessful response. Response: %s", response)
                    return {}

                rates = response.get("rates", {})

                for currency in currencies:
                    if currency in rates:
                        decimal_value = self._to_decimal(rates[currency], currency, logger=logger)
                        if decimal_value is not None:
                            day_rates_in_eur[currency] = decimal_value
            except Exception:
                logger.exception("Fixer.io - Exception while parsing of the HTTP response.")
                return {}

        day_rates = {}
        base_currency_rate = day_rates_in_eur.get(self.base_currency)
        if base_currency_rate is not None:
            for currency, day_rate in day_rates_in_eur.items():
                day_rates[currency] = self._conversion_to_base_currency(base_currency_rate, day_rate, logger)

        return day_rates

    def _conversion_to_base_currency(self, base_currency_rate, currency_rate, logger):
        """
        :type base_currency_rate: decimal.Decimal
        :type currency_rate: decimal.Decimal
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal
        """
        return self._to_decimal(currency_rate / base_currency_rate, logger=logger)

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

    def _get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: str
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        logger.debug("Requesting Fixer for %s (%s)", currency, date_of_exchange, extra={"currency": currency, "date": date_of_exchange})

        url = self._url.format(path=date_of_exchange)
        response = self._get(url, params={"symbols": "%s,%s" % (self.base_currency, currency)}, logger=logger)
        if response:
            try:
                response = response.json()
                if not response.get("success"):
                    logger.error("Fixer.io - Unsuccessful response. Response: %s", response)
                    return None

                rates = response.get("rates", {})
                if currency in rates and self.base_currency in rates:
                    return self._conversion_to_base_currency(
                        self._to_decimal(rates[self.base_currency], self.base_currency, logger=logger),
                        self._to_decimal(rates[currency], currency, logger=logger),
                        logger=logger,
                     )

            except Exception:
                logger.exception("Fixer.io - Exception while parsing of the HTTP response.")

        return None
