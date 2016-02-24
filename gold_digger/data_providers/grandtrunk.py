# -*- coding: utf-8 -*-
from datetime import datetime, date
from collections import defaultdict
from ._provider import Provider


class GrandTrunk(Provider):
    """
    Service offers day exchange rates based on Federal Reserve and European Central Bank.
    It is currently free for use in low-volume and non-commercial settings.
    """
    BASE_URL = "http://currencies.apps.grandtrunk.net"
    BASE_CURRENCY = "USD"
    name = "grandtrunk"

    def get_by_date(self, date_of_exchange, currency):
        response = self._get("{url}/getrate/{date}/{from_currency}/{to}".format(
            url=self.BASE_URL, date=date_of_exchange, from_currency=self.BASE_CURRENCY, to=currency))
        if response:
            return self._to_decimal(response.text.strip(), currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        day_rates = {}
        for currency in currencies:
            response = self._get("{url}/getrate/{date}/{from_currency}/{to}".format(
                url=self.BASE_URL, date=date_of_exchange, from_currency=self.BASE_CURRENCY, to=currency))
            if response:
                decimal_value = self._to_decimal(response.text.strip(), currency)
                if decimal_value:
                    day_rates[currency] = decimal_value
        return day_rates

    def get_historical(self, origin_date, currencies):
        day_rates = defaultdict(dict)
        origin_date_string = origin_date.strftime(format="%Y-%m-%d")
        for currency in currencies:
            response = self._get("{url}/getrange/{from_date}/{to_date}/{from_currency}/{to}".format(
                url=self.BASE_URL, from_date=origin_date_string, to_date=date.today(), from_currency=self.BASE_CURRENCY, to=currency
            ))
            records = response.text.strip().split("\n") if response else []
            for record in records:
                record = record.rstrip()
                if record:
                    try:
                        date_string, exchange_rate_string = record.split(" ")
                        day = datetime.strptime(date_string, "%Y-%m-%d")
                    except ValueError as e:
                        self.logger.error("%s - Parsing of rate&date on record '%s' failed: %s" % (self, record, e))
                        continue
                    decimal_value = self._to_decimal(exchange_rate_string, currency)
                    if decimal_value:
                        day_rates[day][currency] = decimal_value
        return day_rates

    def __str__(self):
        return self.name
