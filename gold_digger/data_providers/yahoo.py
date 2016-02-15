# -*- coding: utf-8 -*-
import requests
from datetime import date


class Yahoo:
    BASE_URL = "http://query.yahooapis.com/v1/public/yql"
    PREPARED_YQL = "SELECT * FROM yahoo.finance.xchange WHERE pair IN ('{pairs}')"
    params = {
        "env": "store://datatables.org/alltableswithkeys",
        "format": "json"
    }

    def get_by_date(self, date_of_exchange, currencies):
        if date_of_exchange == date.today():
            return self.get_latest(currencies)

    def get_latest(self, currencies, base_currency="USD"):
        rates = {}
        for currency in currencies:
            self.params["q"] = self.PREPARED_YQL.format(pairs="%s,%s" % (base_currency, currency))
            response = requests.post(self.BASE_URL, params=self.params)
            _rates = response.json()["query"]["results"]["rate"]
            _rates = [rate["Rate"] for rate in _rates if rate["Name"] == "%s/%s" % (base_currency, currency)]
            try:
                rates[currency] = _rates[0]
            except IndexError:
                continue    # no available rate for currency pair

        return rates

    def get_historical(self, currencies, origin_date):
        return None

    def __str__(self):
        return "yahoo"
