# -*- coding: utf-8 -*-

from datetime import date, timedelta

from ._provider import Provider


class Fixer(Provider):
    BASE_CURRENCY = "USD"
    BASE_URL = "https://api.fixer.io/{date}?base=" + BASE_CURRENCY
    name = "fixer.io"

    def get_by_date(self, date_of_exchange, currency):
        """
        :type date_of_exchange: date
        :type currency: str
        :rtype: decimal.Decimal | None
        """
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        return self._get_by_date(date_of_exchange_string, currency)

    def get_all_by_date(self, date_of_exchange, currencies):
        """
        :type date_of_exchange: date
        :type currencies: list[str]
        :rtype: dict[str, decimal.Decimal]
        """
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        day_rates = {}

        for currency in currencies:
            decimal_value = self._get_by_date(date_of_exchange_string, currency)
            if decimal_value is not None:
                day_rates[currency] = decimal_value

        return day_rates

    def get_historical(self, origin_date, currencies):
        """
        :type origin_date: date
        :type currencies: list[str]
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
        date_of_exchange = origin_date
        date_of_today = date.today()
        if date_of_exchange > date_of_today:
            date_of_exchange, date_of_today = date_of_today, date_of_exchange

        step_by_day = timedelta(days=1)
        historical_rates = {}

        while date_of_exchange != date_of_today:
            day_rates = self.get_all_by_date(date_of_exchange, currencies)
            if day_rates:
                historical_rates[date_of_exchange] = day_rates
            date_of_exchange += step_by_day

        return historical_rates

    def _get_by_date(self, date_of_exchange, currency):
        """
        :type date_of_exchange: str
        :type currency: str
        :rtype: decimal.Decimal | None
        """
        self.logger.debug("Requesting Fixer for %s (%s)", currency, date_of_exchange, extra={"currency": currency, "date": date_of_exchange})

        try:
            request_url = self.BASE_URL.format(date=date_of_exchange)
            response = self._get(request_url)
            if response:
                response = response.json()
                return self._to_decimal(response['rates'][currency])
        except:
            self.logger.exception("Fixer request failed.")

        return None
