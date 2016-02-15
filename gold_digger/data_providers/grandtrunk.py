# -*- coding: utf-8 -*-
import requests
from datetime import datetime, date
from collections import defaultdict
from decimal import Decimal, InvalidOperation


class GrandTrunk:
    BASE_URL = "http://currencies.apps.grandtrunk.net/"

    def get_by_date(self, date_of_exchange, currencies, base_currency="USD"):
        """
        :rtype date_of_exchange: datetime.date
        :rtype currencies: set
        :rtype base_currency: str
        :return: dict
        """
        day_rate = {}
        for to_currency in currencies:
            response = requests.get("{url}/getrate/{date}/{from_currency}/{to}".format(
                url=self.BASE_URL, date=date_of_exchange, from_currency=base_currency, to=to_currency
            ))
            try:
                day_rate[to_currency] = Decimal(response.text.strip())
            except InvalidOperation:
                continue
        return day_rate

    def get_historical(self, currencies, origin_date, base_currency="USD"):
        day_rates = defaultdict(dict)
        for to_currency in currencies:
            response = requests.get("{url}/getrange/{from_date}/{to_date}/{from_currency}/{to}".format(
                url=self.BASE_URL, from_date=origin_date, to_date=date.today(), from_currency=base_currency, to=to_currency
            ))
            for record in response.text.strip().split("\n"):
                record = record.rstrip()
                if record:
                    date_string, exchange_rate_string = record.split(" ")
                    day = datetime.strptime(date_string, "%Y-%m-%d")
                    day_rates[day][to_currency] = Decimal(exchange_rate_string)
        return day_rates

    def __str__(self):
        return "gt"
