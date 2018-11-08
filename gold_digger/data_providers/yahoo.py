# -*- coding: utf-8 -*-

from datetime import date
from functools import lru_cache

from ._provider import Provider
from ..settings import SUPPORTED_CURRENCIES


class Yahoo(Provider):
    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/spark?symbols={}&range=1d&interval=1d"
    name = "yahoo"

    def __init__(self, base_currency, logger):
        super().__init__(base_currency, logger)
        self._downloaded_rates = {}
        self._supported_currencies = SUPPORTED_CURRENCIES - {
            "GGP", "GRD", "LUF", "NLG", "BEF", "ATS", "VAL", "MTL", "MCF", "FIM", "IMP", "JEP", "VEB",
            "ESP", "EEK", "SML", "KGS", "CYP", "LTL", "BYR", "VEF", "FRF", "MGA", "DEM", "ITL", "ZWL",
            "ZMK", "IEP",  "LVL", "SIT", "CUC"
        }

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange=date.today()):
        """
        :type date_of_exchange: date
        :rtype: set
        """

        self.logger.debug("Yahoo supported currencies: %s", self._supported_currencies)
        return self._supported_currencies

    def get_by_date(self, date_of_exchange, currency):
        """
        :type date_of_exchange: date
        :type currency: str
        :rtype: decimal.Decimal | None
        """
        date_str = date_of_exchange.strftime("%Y-%m-%d")
        self.logger.debug("Requesting Yahoo for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        if date_of_exchange == date.today():
            return self._get_latest(currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        """
        :type date_of_exchange: date
        :type currencies: set[str]
        :rtype: dict[str,decimal.Decimal] | None
        """
        if date_of_exchange == date.today():
            rates = self._get_all_latest()
            return {currency: rate for currency, rate in rates.items() if currency in currencies}

    def _get_latest(self, currency):
        response = self._get(self.BASE_URL.format(currency + "%3DX"))
        currencies_rates = self._parse_response(response)
        return currencies_rates.get(currency)

    def _get_all_latest(self):
        """
        :rtype: dict[str,decimal.Decimal]
        """
        default_rates = {i: None for i in self.get_supported_currencies()}

        response = self._get(self.BASE_URL.format(",".join({i + "%3DX" for i in self.get_supported_currencies()})))
        currency_rates = self._parse_response(response)

        return {**default_rates, **currency_rates}

    def _parse_response(self, response):
        """
        :rtype: dict[str, Decimal] | None
        """
        rates = {}
        if response:
            data = response.json()
            for i in data["spark"]["result"]:
                currency = ""
                try:
                    currency = i["response"][0]["meta"]["currency"]
                    rate = i["response"][0]["indicators"]["quote"][0]["close"][0]
                    rate = self._to_decimal(str(rate), currency)

                    if currency in self._supported_currencies:
                        rates[currency] = rate
                except (KeyError, IndexError) as e:
                    self.logger.warning("Cannot get rate for {}.".format(currency))

        return rates

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
