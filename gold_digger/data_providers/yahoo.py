# -*- coding: utf-8 -*-

from datetime import date

from ._provider import Provider


class Yahoo(Provider):
    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/spark?symbols={}&range=1d&interval=1d"
    SYMBOLS_PATTERN = "{}{}%3DX"
    name = "yahoo"

    def __init__(self, base_currency, supported_currencies, logger):
        super().__init__(base_currency, logger)
        self._downloaded_rates = {}
        self._supported_currencies = supported_currencies - {
            "ATS", "BEF", "BYR", "CUC", "CYP", "DEM", "EEK", "ESP", "FIM", "FRF", "GGP", "GRD", "IEP",
            "IMP", "ITL", "JEP", "KGS", "LTL", "LUF", "LVL", "MCF", "MGA", "MTL", "NLG", "PTE", "SIT",
            "SML", "VAL", "VEB", "VEF", "ZMK", "ZWL"
        }

    def get_supported_currencies(self, date_of_exchange=date.today()):
        """
        :type date_of_exchange: date
        :rtype: set
        """
        return self._supported_currencies

    def get_by_date(self, date_of_exchange, currency):
        """
        :type date_of_exchange: datetime.date
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
        response = self._get(self.BASE_URL.format(self.SYMBOLS_PATTERN.format(self.base_currency, currency)))
        currencies_rates = self._parse_response(response)
        return currencies_rates.get(currency)

    def _get_all_latest(self):
        """
        :rtype: dict[str,decimal.Decimal]
        """
        symbols = {self.SYMBOLS_PATTERN.format(self.base_currency, currency) for currency in self.get_supported_currencies()}
        response = self._get(self.BASE_URL.format(",".join(symbols)))
        currency_rates = self._parse_response(response)

        return currency_rates

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

                except (KeyError, IndexError):
                    self.logger.warning("Cannot get rate for {}.".format(currency))

        return rates

    def get_historical(self, origin_date, currencies):
        return {}

    def __str__(self):
        return self.name
