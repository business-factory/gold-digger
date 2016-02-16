# -*- coding: utf-8 -*-
from decimal import Decimal, InvalidOperation

import requests
from datetime import date


class Yahoo:
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
            return self.get_latest(currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        if date_of_exchange == date.today():
            return self.get_all_latest(currencies)

    def get_latest(self, currency, base_currency="USD"):
        self.params["q"] = self.PREPARED_YQL.format(pairs="%s,%s" % (base_currency, currency))
        response = requests.post(self.BASE_URL, params=self.params)
        value = response.json()["query"]["results"]["rate"][0]["Rate"]
        try:
            return Decimal(value)
        except InvalidOperation:
            return

    def get_all_latest(self, currencies):
        day_rates = {}
        self.params["q"] = self.PREPARED_YQL.format(pairs=",".join(currencies))
        response = requests.post(self.BASE_URL, params=self.params)
        for record in response.json()["query"]["results"]["rate"]:
            try:
                day_rates[record["id"][:3]] = Decimal(record["Rate"])
            except InvalidOperation:
                pass
        return day_rates

    def get_historical(self, currencies, origin_date):
        return None

    def __str__(self):
        return self.name
