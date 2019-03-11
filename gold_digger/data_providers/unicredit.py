# -*- coding: utf-8 -*-

from datetime import date, timedelta
from functools import lru_cache

from ._provider import Provider


class Unicredit(Provider):
    BASE_URL = "https://www.unicreditbank.cz/cwa/GetExchangeRates"
    HEADERS = {
        "Content-Type": "application/json",
        "EntityCode": "CZ",
        "Language": "CS",
        "SourceSystem": "PWS",
        "User-Agent": "ROI Hunter /Currency Downloader; https://www.roihunter.com/"
    }
    name = "unicredit"

    @lru_cache(maxsize=1)
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        currencies = set()
        response = self._get_rates_from_unicredit(date_of_exchange, logger)
        if response:
            currencies = set(item["CurrencyCode"] for item in response)
        if currencies:
            logger.debug("Unicredit supported currencies: %s", currencies)
        else:
            logger.error("Unicredit supported currencies not found.")
        return currencies

    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        date_str = date_of_exchange.strftime("%Y-%m-%d")
        logger.debug("Requesting Unicredit for %s (%s)", currency, date_str, extra={"currency": currency, "date": date_str})

        rates = self._get_rates_from_unicredit(date_of_exchange, logger)
        if rates:
            base_currency_rate = self._get_currency_rate(rates, self.base_currency)
            target_currency_rate = self._get_currency_rate(rates, currency)
            if base_currency_rate is not None and target_currency_rate is not None:
                return self._conversion_to_base_currency(
                    self._to_decimal(base_currency_rate, self.base_currency, logger=logger),
                    self._to_decimal(target_currency_rate, currency, logger=logger),
                    logger=logger,
                )

    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        supported_currencies = self.get_supported_currencies(date_of_exchange, logger)
        rates = self._get_rates_from_unicredit(date_of_exchange, logger)
        if rates is None:
            return {}

        day_rates = {}
        for currency in currencies:
            if currency not in supported_currencies:
                continue

            base_currency_rate = self._get_currency_rate(rates, self.base_currency)
            target_currency_rate = self._get_currency_rate(rates, currency)
            if base_currency_rate is not None and target_currency_rate is not None:
                day_rates[currency] = self._conversion_to_base_currency(
                    self._to_decimal(base_currency_rate, self.base_currency, logger=logger),
                    self._to_decimal(target_currency_rate, currency, logger=logger),
                    logger=logger,
                )

        return day_rates

    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
        date_of_exchange = origin_date
        date_of_today = date.today()

        historical_rates = {}
        while date_of_exchange != date_of_today:
            day_rates = self.get_all_by_date(date_of_exchange, currencies, logger)
            if day_rates:
                historical_rates[date_of_exchange] = day_rates
            date_of_exchange += timedelta(days=1)

        return historical_rates

    def _get_rates_from_unicredit(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :param logger: gold_digger.utils.ContextLogger
        :rtype: list[dict[str, str | float]] | None
        """
        date_str = date_of_exchange.strftime("%Y%m%dT00:00:00.000+0000")
        data = {"Currency": "*ALL", "DateFrom": date_str, "DateTo": date_str}

        rates = self._post(self.BASE_URL, headers=self.HEADERS, data=data, logger=logger)

        if rates:
            rates = [rate for rate in rates.json() if rate["CardsMiddleRate"] != 0]
            rates.append({"CurrencyCode": "CZK", "CardsMiddleRate": 1.0})
            return rates

    @staticmethod
    def _get_currency_rate(all_rates, currency):
        """
        :type all_rates: list[dict[str, str | float]]
        :type currency: str
        :rtype: float | None
        """
        for currency_rate in all_rates:
            if currency_rate["CurrencyCode"] == currency:
                return currency_rate["CardsMiddleRate"]

        return None
