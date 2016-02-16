# -*- coding: utf-8 -*-
import requests
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


class CurrencyLayer:
    """
    Real-time service with free plan for 1000 requests per month.
    Implicit base currency is USD.
    """
    BASE_URL = "http://www.apilayer.net/api/live?access_key=8497c277171dfc3ad271f1ccb733a6a8"
    name = "currency_layer"

    def get_by_date(self, date_of_exchange, currency):
        response = requests.get("{url}&date={date}&currencies={currencies}".format(
            url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=currency
        ))
        for currency_pair, value in response.json()["quotes"].items():
            try:
                return Decimal(value)
            except InvalidOperation:
                return

    def get_all_by_date(self, date_of_exchange, currencies):
        response = requests.get("{url}&date={date}&currencies={currencies}".format(
            url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)
        ))
        day_rates = {}
        for currency_pair, value in response.json()["quotes"].items():
            try:
                day_rates[currency_pair[3:]] = Decimal(value)
            except InvalidOperation:
                pass
        return day_rates

    def get_historical(self, currencies, origin_date):
        day_rates = defaultdict(dict)
        date_of_exchange = origin_date
        date_of_today = date.today()
        while date_of_exchange != date_of_today:
            response = requests.get("{url}&date={date}&currencies={currencies}".format(
                url=self.BASE_URL, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)
            ))
            for currency_pair, value in response.json()["quotes"].items():
                day_rates[date_of_exchange][currency_pair[3:]] = Decimal(value)
            date_of_exchange = date_of_exchange + timedelta(1)
        return day_rates

    def __str__(self):
        return self.name
