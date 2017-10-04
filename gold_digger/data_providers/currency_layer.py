# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

from ._provider import Provider


class CurrencyLayer(Provider):
    """
    Real-time service with free plan for 1000 requests per month.
    Implicit base currency is USD.
    """
    BASE_URL = "http://www.apilayer.net/api/live?access_key=%s"
    BASE_CURRENCY = "USD"
    name = "currency_layer"

    def __init__(self, access_keys, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._access_keys = access_keys
        self._url = self.BASE_URL % self._access_keys[1]

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange):
        """
        :type date_of_exchange: datetime.date
        :rtype: set
        """
        currencies = set()
        response = self._get("https://currencylayer.com/downloads/cl-currencies-table.txt")
        if response:
            currencies = set(re.findall("<td>([A-Z]{3})</td>", response.text))
        if currencies:
            self.logger.debug("CurrencyLayer supported currencies: %s", currencies)
        else:
            self.logger.error("CurrencyLayer supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency):
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        self.logger.debug("Requesting CurrencyLayer for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        response = self._get("{url}&date={date}&currencies={currencies}".format(url=self._url, date=date_str, currencies=currency))
        if not response:
            self.logger.warning("CurrencyLayer error. Status: %s", response.status_code, extra={"currency": currency, "date": date_str})
            return None

        response = response.json()
        if response and response.get("success") is False:
            self.logger.warning("CurrencyLayer unsuccessful request. Error: %s",
                                response.get("error", {}).get("info"), extra={"currency": currency, "date": date_str})
            return None

        records = response.get("quotes", {}) if response else {}
        value = records.get("%s%s" % (self.BASE_CURRENCY, currency))
        return self._to_decimal(value, currency) if value is not None else None

    def get_all_by_date(self, date_of_exchange, currencies):
        response = self._get("{url}&date={date}&currencies={currencies}".format(
            url=self._url, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)))
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
                url=self._url, date=date_of_exchange.strftime(format="%Y-%m-%d"), currencies=",".join(currencies)))
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
