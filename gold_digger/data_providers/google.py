# -*- coding: utf-8 -*-

import re
from datetime import date
from functools import lru_cache

from ._provider import Provider


class Google(Provider):
    """
    Offers only latest exchange rates for only one currency pair at the moment.
    """
    BASE_URL = "https://finance.google.com/finance/converter?a=1&from={}&to={}"
    RESULT_REGEX = re.compile("class=bld>([\d.]+)")
    name = "google"

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange):
        """
        :type date_of_exchange: datetime.date
        :rtype: set
        """
        currencies = set()
        response = self._get("https://finance.google.com/finance/converter")
        if response:
            currencies = set(re.findall('<option +value="([A-Z]{3})">', response.text))
        if currencies:
            self.logger.debug("Google supported currencies: %s", currencies)
        else:
            self.logger.error("Google supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency):
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        self.logger.debug("Requesting Google for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        if date_of_exchange == date.today():
            return self._get_latest(currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        if date_of_exchange == date.today():
            return self._get_all_latest(date_of_exchange, currencies)

    def _get_latest(self, currency):
        response = self._get(self.BASE_URL.format(self.base_currency, currency))
        if response:
            result = self.RESULT_REGEX.search(response.text)
            if result:
                return self._to_decimal(result.group(1), currency)

            self.logger.warning("Google provider - no result for %s", currency)
        else:
            self.logger.warning("Google provider unexpected response: %s", response)

    def _get_all_latest(self, date_of_exchange, currencies):
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        rates = {}
        for currency in currencies:
            self.logger.debug("Requesting Google for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})
            rate = self._get_latest(currency)
            if rate:
                rates[currency] = rate
        return rates

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
