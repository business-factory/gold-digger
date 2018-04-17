# -*- coding: utf-8 -*-

from datetime import date
from functools import lru_cache

from ._provider import Provider


class Yahoo(Provider):
    """
    Yahoo provides exchange rates pairs also here:
      https://query1.finance.yahoo.com/v8/finance/chart/USDEUR=X?range=1d&interval=1d
    """
    BASE_URL = "https://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json"
    name = "yahoo"

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange):
        """
        :type date_of_exchange: date
        :rtype: set
        """
        rates = self._get_all_latest()
        currencies = set(rates.keys())
        if currencies:
            self.logger.debug("Yahoo supported currencies: %s", currencies)
        else:
            self.logger.error("Yahoo supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency):
        """
        :type date_of_exchange: date
        :type currency: str
        :rtype: decimal.Decimal | None
        """
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        self.logger.debug("Requesting Yahoo for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        if date_of_exchange == date.today():
            return self._get_latest(currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        """
        :type date_of_exchange: date
        :type currencies: set[str]
        :rtype: dict[str,decimal.Decimal] | None
        """
        if date_of_exchange == date.today():
            rates = self._get_all_latest()
            return {currency: rate for currency, rate in rates.items() if currency in currencies}

    def _get_latest(self, currency):
        response = self._get(self.BASE_URL)
        rates = self._parse_response(response)
        return rates.get(currency)

    def _get_all_latest(self):
        response = self._get(self.BASE_URL)
        return self._parse_response(response)

    def _parse_response(self, response):
        """
        :rtype: dict
        :return:
        {
            "EUR": 0.864,
            ...
        }
        """
        rates = {}
        if response:
            data = response.json()
            for resource in data["list"]["resources"]:
                fields = resource["resource"]["fields"]
                if fields:
                    currency = fields["symbol"][:3]
                    rate = fields["price"]
                    rates[currency] = self._to_decimal(rate, currency)
        return rates

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
