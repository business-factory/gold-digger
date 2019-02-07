# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime, date
from functools import lru_cache

from ._provider import Provider


class GrandTrunk(Provider):
    """
    Service offers day exchange rates based on Federal Reserve and European Central Bank.
    It is currently free for use in low-volume and non-commercial settings.
    """
    BASE_URL = "http://currencies.apps.grandtrunk.net"
    name = "grandtrunk"

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: date
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: set
        """
        currencies = set()
        response = self._get(f"{self.BASE_URL}/currencies/{date_of_exchange.strftime('%Y-%m-%d')}", logger=logger)
        if response:
            currencies = set(response.text.split("\n"))
        if currencies:
            logger.debug("Grandtrunk supported currencies: %s", currencies)
        else:
            logger.error("Grandtrunk supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.datetime
        :type currency: str
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: decimal.Decimal | None
        """
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        logger.debug("Requesting GrandTrunk for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        response = self._get(f"{self.BASE_URL}/getrate/{date_str}/{self.base_currency}/{currency}", logger=logger)
        if response:
            return self._to_decimal(response.text.strip())

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.datetime
        :type currencies: [str]
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: {str: decimal.Decimal | None}
        """
        day_rates = {}
        supported_currencies = self.get_supported_currencies(date_of_exchange, logger)
        for currency in currencies:
            if currency in supported_currencies:
                response = self._get(f"{self.BASE_URL}/getrate/{date_of_exchange}/{self.base_currency}/{currency}", logger=logger)
                if response:
                    decimal_value = self._to_decimal(response.text.strip())
                    if decimal_value:
                        day_rates[currency] = decimal_value
        return day_rates

    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime
        :type currencies: [str]
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: {datetime.Datetime: {str: decimal.Decimal | None}}
        """
        day_rates = defaultdict(dict)
        origin_date_string = origin_date.strftime("%Y-%m-%d")
        for currency in currencies:
            response = self._get(f"{self.BASE_URL}/getrange/{origin_date_string}/{date.today()}/{self.base_currency}/{currency}", logger=logger)
            records = response.text.strip().split("\n") if response else []
            for record in records:
                record = record.rstrip()
                if record:
                    try:
                        date_string, exchange_rate_string = record.split(" ")
                        day = datetime.strptime(date_string, "%Y-%m-%d")
                    except ValueError as e:
                        logger.error("%s - Parsing of rate & date on record '%s' failed: %s" % (self, record, e))
                        continue
                    decimal_value = self._to_decimal(exchange_rate_string)
                    if decimal_value:
                        day_rates[day][currency] = decimal_value
        return day_rates

    def __str__(self):
        return self.name
