# -*- coding: utf-8 -*-

from datetime import date
from functools import lru_cache

from ._provider import Provider


class Yahoo(Provider):
    """
    Real-time service with no known limits offers only latest exchange rates.
    Implicit base currency is USD.
    """
    BASE_URL = "http://query.yahooapis.com/v1/public/yql"
    PREPARED_YQL = "SELECT * FROM yahoo.finance.xchange WHERE pair IN ('{currencies}')"
    params = {
        "env": "store://datatables.org/alltableswithkeys",
        "format": "json"
    }
    name = "yahoo"

    def __init__(self, currencies, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._currencies = currencies

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange):
        """
        :type date_of_exchange: date
        :rtype: set
        """
        rates = self._get_all_latest(self._currencies)
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
            return self._get_all_latest(currencies)

    def _get_latest(self, currency):
        self.params["q"] = self.PREPARED_YQL.format(currencies=currency)
        response = self._get(self.BASE_URL, params=self.params)
        if response:
            rate = self._get_rates_from_response(response)
            return self._to_decimal(rate.get("Rate"), currency)

    def _get_all_latest(self, currencies):
        day_rates = {}
        self.params["q"] = self.PREPARED_YQL.format(currencies=",".join(currencies))
        response = self._get(self.BASE_URL, params=self.params)
        for rates in self._get_rates_from_response(response):
            currency = rates.get("id")
            currency = currency[:3] if currency else currency
            decimal_value = self._to_decimal(rates.get("Rate"), currency)
            if currency and decimal_value:
                day_rates[currency] = decimal_value
        return day_rates

    def _get_rates_from_response(self, response):
        """
        :rtype: dict | list[dict]
        :returns:
            if one currency has been requested, the method returns dict
            if more currencies have been requested, the method returns list of dicts
            {
                'Ask': '0.7579',
                'Bid': '0.7579',
                'Date': '9/14/2016',
                'Name': 'USD/GBP',
                'Rate': '0.7579',
                'Time': '8:59am',
                'id': 'GBP=X'
            }
        """
        if response:
            try:
                rates = response.json()["query"]["results"]["rate"]
                return rates
            except KeyError as e:
                self.logger.error("%s - Accessing records failed: %s. Response: %s.", self, e, response.json())
        return []

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
