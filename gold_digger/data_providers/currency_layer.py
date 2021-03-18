import re
from collections import defaultdict
from datetime import date, timedelta
from operator import attrgetter

from cachetools import cachedmethod, keys

from ._provider import Provider


class CurrencyLayer(Provider):
    """
    Real-time service with free plan for 250 requests per month.
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
            logger.critical("%s - You need an access token!", self)
            self._url = self.BASE_URL % ""

        self.has_request_limit = True

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
            logger.debug("%s - Supported currencies: %s", self, currencies)
        else:
            logger.error("%s - Supported currencies not found.", self)
        return currencies

    @Provider.check_request_limit(return_value=None)
    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        date_str = date_of_exchange.strftime("%Y-%m-%d")
        logger.debug("%s - Requesting for %s (%s)", self, currency, date_str, extra={"currency": currency, "date": date_str})

        response = self._get(f"{self._url}&date={date_str}&currencies={currency}", logger=logger)
        if not response:
            logger.warning("%s - Error. Status: %s", self, response.status_code, extra={"currency": currency, "date": date_str})
            return None

        response = response.json()
        if response["success"]:
            records = response.get("quotes", {})
        elif response["error"]["code"] == 104:
            self.set_request_limit_reached(logger)
            return None
        else:
            logger.warning(
                "%s - Unsuccessful request. Error: %s", self, response.get("error", {}).get("info"), extra={"currency": currency, "date": date_str}
            )
            return None

        value = records.get("%s%s" % (self.base_currency, currency))
        return self._to_decimal(value, currency, logger=logger) if value is not None else None

    @Provider.check_request_limit(return_value={})
    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        logger.debug("%s - Requesting for all rates for date %s", self, date_of_exchange)

        response = self._get(f"{self._url}&date={date_of_exchange.strftime('%Y-%m-%d')}&currencies={','.join(currencies)}", logger=logger)
        if not response:
            return {}

        response = response.json()
        records = {}
        if response["success"]:
            records = response.get("quotes", {})
        elif response["error"]["code"] == 104:
            self.set_request_limit_reached(logger)
            return {}

        day_rates = {}
        for currency_pair, value in records.items():
            currency = currency_pair[3:]
            decimal_value = self._to_decimal(value, currency, logger=logger) if value is not None else None
            if currency and decimal_value:
                day_rates[currency] = decimal_value
        return day_rates

    @Provider.check_request_limit(return_value={})
    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
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
                    self.set_request_limit_reached(logger)
                    break

            for currency_pair, value in records.items():
                currency = currency_pair[3:]
                decimal_value = self._to_decimal(value, currency, logger=logger) if value is not None else None
                if currency and decimal_value:
                    day_rates[date_of_exchange][currency] = decimal_value
            date_of_exchange = date_of_exchange + timedelta(1)

        return day_rates
