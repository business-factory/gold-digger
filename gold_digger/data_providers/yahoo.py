from datetime import date

from ._provider import Provider
from ..utils.helpers import batches


class Yahoo(Provider):
    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/spark?symbols={}&range=1d&interval=1d"
    SYMBOLS_PATTERN = "{}{}%3DX"
    SYMBOLS_BATCH_SIZE = 20  # Yahoo has recently started returning error for more
    name = "yahoo"

    def __init__(self, base_currency, supported_currencies):
        super().__init__(base_currency)
        self._downloaded_rates = {}
        self._supported_currencies = supported_currencies - {
            "ATS", "BEF", "BYR", "CUC", "CYP", "DEM", "EEK", "ESP", "FIM", "FRF", "GGP", "GRD", "IEP",
            "IMP", "ITL", "JEP", "KGS", "LTL", "LUF", "LVL", "MCF", "MGA", "MTL", "NLG", "PTE", "SIT",
            "SML", "VAL", "VEB", "VEF", "ZMK", "ZWL"
        }

    def get_supported_currencies(self, date_of_exchange=date.today(), *_):
        """
        :type date_of_exchange: datetime.date
        :rtype: set[str]
        """
        return self._supported_currencies

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        if date_of_exchange == date.today():
            date_str = date_of_exchange.strftime("%Y-%m-%d")
            logger.debug("%s - Requesting for %s (%s)", self, currency, date_str, extra={"currency": currency, "date": date_str})

            return self._get_latest(currency, logger)

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: {str: decimal.Decimal | None}
        """
        if date_of_exchange == date.today():
            date_str = date_of_exchange.strftime("%Y-%m-%d")
            logger.debug("%s - Requesting rates for all currencies (%s)", self, date_str, extra={"date": date_str})

            rates = self._get_all_latest(logger)
            return {currency: rate for currency, rate in rates.items() if currency in currencies}

    def _get_latest(self, currency, logger):
        """
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        response = self._get(self.BASE_URL.format(self.SYMBOLS_PATTERN.format(self.base_currency, currency)), logger=logger)
        currencies_rates = self._parse_response(response, logger=logger)
        return currencies_rates.get(currency)

    def _get_all_latest(self, logger):
        """
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal]
        """
        currency_rates = {}
        symbols = {self.SYMBOLS_PATTERN.format(self.base_currency, currency) for currency in self.get_supported_currencies()}

        for symbols_batch in batches(symbols, self.SYMBOLS_BATCH_SIZE):
            response = self._get(self.BASE_URL.format(",".join(symbols_batch)), logger=logger)
            currency_rates.update(self._parse_response(response, logger))

        return currency_rates

    def _parse_response(self, response, logger):
        """
        :type response: requests.Response | None
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        rates = {}
        if response:
            data = response.json()
            for i in data["spark"]["result"]:
                currency = ""
                try:
                    currency = i["response"][0]["meta"]["currency"]
                    rate = i["response"][0]["indicators"]["quote"][0]["close"][0]
                    rate = self._to_decimal(str(rate), currency, logger=logger)

                    if currency in self._supported_currencies:
                        rates[currency] = rate

                except (KeyError, IndexError):
                    logger.warning("%s - Cannot get rate for %s.", self, currency)

        return rates

    def get_historical(self, *_):
        """
        :rtype: dict
        """
        return {}
