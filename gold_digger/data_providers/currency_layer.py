# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date, timedelta
from ._provider import Provider


class CurrencyLayer(Provider):
    """
    Real-time service with free plan for 1000 requests per month.
    Implicit base currency is USD.
    """
    BASE_URL = "http://www.apilayer.net/api/live?access_key=8497c277171dfc3ad271f1ccb733a6a8"
    BASE_CURRENCY = "USD"
    name = "currency_layer"

    def get_by_date(self, date_of_exchange, currency):
        response = self._get("{url}&date={date}&currencies={currencies}".format(
            url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=currency))
        records = response.json().get("quotes", {}) if response else {}
        value = records.get("%s%s" % (self.BASE_CURRENCY, currency))
        return self._to_decimal(value, currency) if value is not None else None

    def get_all_by_date(self, date_of_exchange, currencies):
        response = self._get("{url}&date={date}&currencies={currencies}".format(
            url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)))
        records = response.json().get("quotes", {}) if response else {}
        day_rates = {}
        for currency_pair, value in records.items():
            currency = currency_pair[3:]
            decimal_value = self._to_decimal(value, currency) if value is not None else None
            if currency and decimal_value:
                day_rates[currency] = decimal_value
        return day_rates

    def get_historical(self, origin_date, currencies):
        day_rates = defaultdict(dict)
        date_of_exchange = origin_date
        date_of_today = date.today()
        while date_of_exchange != date_of_today:
            response = self._get("{url}&date={date}&currencies={currencies}".format(
                url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)))
            records = response.json().get("quotes", {}) if response else {}
            for currency_pair, value in records.items():
                currency = currency_pair[3:]
                decimal_value = self._to_decimal(value, currency) if value is not None else None
                if currency and decimal_value:
                    day_rates[date_of_exchange][currency] = decimal_value
            date_of_exchange = date_of_exchange + timedelta(1)
        return day_rates

    def __str__(self):
        return self.name
