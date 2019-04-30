# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from datetime import date, timedelta
from operator import attrgetter

from cachetools import cachedmethod, keys

from ._provider import Provider


class CurrencyLayer(Provider):
    """
    Real-time service with free plan for 1000 requests per month.
    Implicit base currency is USD.
    """
    BASE_URL = "http://www.apilayer.net/api/live?access_key=%s"
    name = "currency_layer"

    def __init__(self, access_key, logger, *args, **kwargs):
        """
        :type access_key: str
        :type logger: gold_digger.utils.ContextLogger
        """
        super().__init__(*args, **kwargs)
        if access_key:
            self._url = self.BASE_URL % access_key
        else:
            logger.critical("You need an access token to use CurrencyLayer provider!")
            self._url = self.BASE_URL % ""
        self._requestLimitReached = False

    @cachedmethod(cache=attrgetter("_cache"), key=lambda date_of_exchange, _: keys.hashkey(date_of_exchange))
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        currencies = set()
        response = self._get("https://currencylayer.com/downloads/cl-currencies-table.txt", logger=logger)
        if response:
            currencies = set(re.findall("<td>([A-Z]{3})</td>", response.text))
        if currencies:
            logger.debug("CurrencyLayer supported currencies: %s", currencies)
        else:
            logger.error("CurrencyLayer supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        if not self.check_request_limit(logger):
            return None

        date_str = date_of_exchange.strftime("%Y-%m-%d")
        logger.debug("Requesting CurrencyLayer for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        response = self._get(f"{self._url}&date={date_str}&currencies={currency}", logger=logger)
        records = {}
        if response:
            response = response.json()
            if response["success"]:
                records = response.get("quotes", {})
            elif response["error"]["code"] == 104:
                self._requestLimitReached = True
                logger.warning(
                    "CurrencyLayer unsuccessful request. Error: %s", response.get("error", {}).get("info"), extra={"currency": currency, "date": date_str}
                )
                return None
        else:
            logger.warning("CurrencyLayer error. Status: %s", response.status_code, extra={"currency": currency, "date": date_str})
            return None

        value = records.get("%s%s" % (self.base_currency, currency))
        return self._to_decimal(value, currency, logger=logger) if value is not None else None

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        if not self.check_request_limit(logger):
            return {}

        response = self._get(f"{self._url}&date={date_of_exchange.strftime('%Y-%m-%d')}&currencies={','.join(currencies)}", logger=logger)
        records = {}
        if response:
            response = response.json()
            if response["success"]:
                records = response.get("quotes", {})
            elif response["error"]["code"] == 104:
                self._requestLimitReached = True
                return {}
        else:
            return {}
        day_rates = {}
        for currency_pair, value in records.items():
            currency = currency_pair[3:]
            decimal_value = self._to_decimal(value, currency, logger=logger) if value is not None else None
            if currency and decimal_value:
                day_rates[currency] = decimal_value
        return day_rates

    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
        if not self.check_request_limit(logger):
            return {}

        day_rates = defaultdict(dict)
        date_of_exchange = origin_date
        date_of_today = date.today()

        while date_of_exchange != date_of_today:
            response = self._get(f"{self._url}&date={date_of_exchange.strftime('%Y-%m-%d')}&currencies={','.join(currencies)}", logger=logger)
            records = {}
            if response:
                response = response.json()
                if response["success"]:
                    records = response.get("quotes", {})
                elif response["error"]["code"] == 104:
                    self._requestLimitReached = True
                    return {}
            else:
                return {}
            for currency_pair, value in records.items():
                currency = currency_pair[3:]
                decimal_value = self._to_decimal(value, currency, logger=logger) if value is not None else None
                if currency and decimal_value:
                    day_rates[date_of_exchange][currency] = decimal_value
            date_of_exchange = date_of_exchange + timedelta(1)

        return day_rates

    def check_request_limit(self, logger):
        if self._requestLimitReached:
            if self._get_today_day() == 1:
                self._requestLimitReached = False
                return True
            else:
                logger.debug("Currency Layer monthly requests limit was reached.")
                return False
        return True

    @staticmethod
    def _get_today_day():
        return date.today().day
