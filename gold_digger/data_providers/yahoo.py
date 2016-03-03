# -*- coding: utf-8 -*-
from datetime import date
from ._provider import Provider


class Yahoo(Provider):
    """
    Real-time service with no known limits offers only latest exchange rates.
    Implicit base currency is USD.
    """
    BASE_URL = "http://query.yahooapis.com/v1/public/yql"
    PREPARED_YQL = "SELECT * FROM yahoo.finance.xchange WHERE pair IN ('{pairs}')"
    params = {
        "env": "store://datatables.org/alltableswithkeys",
        "format": "json"
    }
    name = "yahoo"

    def get_by_date(self, date_of_exchange, currency):
        if date_of_exchange == date.today():
            return self._get_latest(currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        if date_of_exchange == date.today():
            return self._get_all_latest(currencies)

    def _get_latest(self, currency, base_currency="USD"):
        self.params["q"] = self.PREPARED_YQL.format(pairs="%s,%s" % (base_currency, currency))
        response = self._post(self.BASE_URL, params=self.params)
        if response:
            rates = self._get_rates_from_response(response)
            if len(rates) > 0:
                return self._to_decimal(rates[0].get("Rate", ""), currency)

    def _get_all_latest(self, currencies):
        day_rates = {}
        self.params["q"] = self.PREPARED_YQL.format(pairs=",".join(currencies))
        response = self._post(self.BASE_URL, params=self.params)
        for record in self._get_rates_from_response(response):
            currency = record.get("id", "")[:3]
            decimal_value = self._to_decimal(record.get("Rate", ""), currency)
            if currency and decimal_value:
                day_rates[currency] = decimal_value
        return day_rates

    def _get_rates_from_response(self, response):
        if response:
            self.logger.debug("%s - Requested %s" % (self, response.url))
            try:
                results = response.json()["query"]["results"]
                return results["rate"] if results else []
            except KeyError as e:
                self.logger.error("%s - Accessing records failed: %s" % (self, e))
        return []

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
