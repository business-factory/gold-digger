# -*- coding: utf-8 -*-
import requests
from datetime import datetime, date
from collections import defaultdict
from decimal import Decimal, InvalidOperation


class GrandTrunk:
    """
    Service offers day exchange rates based on Federal Reserve and European Central Bank.
    It is currently free for use in low-volume and non-commercial settings.
    """
    BASE_URL = "http://currencies.apps.grandtrunk.net/"
    BASE_CURRENCY = "USD"
    name = "grandtrunk"

    def get_by_date(self, date_of_exchange, to_currency):
        response = requests.get("{url}/getrate/{date}/{from_currency}/{to}".format(
            url=self.BASE_URL, date=date_of_exchange, from_currency=self.BASE_CURRENCY, to=to_currency
        ))
        try:
            return Decimal(response.text.strip())
        except InvalidOperation:
            return

    def get_all_by_date(self, date_of_exchange, currencies):
        day_rates = {}
        for to_currency in currencies:
            response = requests.get("{url}/getrate/{date}/{from_currency}/{to}".format(
                url=self.BASE_URL, date=date_of_exchange, from_currency=self.BASE_CURRENCY, to=to_currency
            ))
            try:
                day_rates[to_currency] = Decimal(response.text.strip())
            except InvalidOperation:
                pass
        return day_rates

    def get_historical(self, currencies, origin_date):
        day_rates = defaultdict(dict)
        for to_currency in currencies:
            response = requests.get("{url}/getrange/{from_date}/{to_date}/{from_currency}/{to}".format(
                url=self.BASE_URL, from_date=origin_date, to_date=date.today(), from_currency=self.BASE_CURRENCY, to=to_currency
            ))
            for record in response.text.strip().split("\n"):
                record = record.rstrip()
                if record:
                    date_string, exchange_rate_string = record.split(" ")
                    day = datetime.strptime(date_string, "%Y-%m-%d")
                    day_rates[day][to_currency] = Decimal(exchange_rate_string)
        return day_rates

    def __str__(self):
        return self.name
