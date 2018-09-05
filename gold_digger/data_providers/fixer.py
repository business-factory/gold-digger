# -*- coding: utf-8 -*-

from datetime import date, timedelta

from ._provider import Provider


class Fixer(Provider):
    """
    Base currency is in EUR and cannot be changed in free subscription.
    We have to convert exchange rates to base currency (USD) before returning the rates from the provider.
    """
    BASE_URL = "http://data.fixer.io/api/{date}?access_key=%s"
    name = "fixer.io"

    def __init__(self, access_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if access_key:
            self._url = self.BASE_URL % access_key
        else:
            self.logger.critical("You need an access token to use Fixer provider!")
            self._url = self.BASE_URL % ""
        self._supported_currencies = {}

    def get_supported_currencies(self, date_of_exchange):
        """
        :type date_of_exchange: datetime.date
        :rtype: set
        """
        currencies = self._supported_currencies.get(date_of_exchange)
        if currencies:
            return currencies

        currencies = set()
        response = self._get(self._url.format(date=date_of_exchange.isoformat()))
        if response:
            response = response.json()
            if response.get("success"):
                currencies = set((response.get("rates") or {}).keys())
            elif response["error"]["type"] == "invalid_date":
                # Fixer returns error `invalid_date` if the date is in future
                # We refresh supported currencies at midnight and Fixer thinks that today date is future date
                # We should not cache such wrong result and try again later
                return currencies
            else:
                self.logger.error("Fixer supported currencies not found. Error: %s. Date: %s", response, date_of_exchange.isoformat())
        else:
            self.logger.error("Fixer unexpected response. Response: %s", response)

        if currencies:
            self.logger.debug("Fixer supported currencies: %s", currencies)

        self._supported_currencies = {date_of_exchange: currencies}

        return currencies

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
        self.logger.debug("Fixer.io - get all for date %s", date_of_exchange)
        date_of_exchange_string = date_of_exchange.strftime("%Y-%m-%d")
        day_rates_in_eur = {}

        url = self._url.format(date=date_of_exchange_string)
        response = self._get(url)

        if response:
            try:
                response = response.json()
                if not response.get("success"):
                    self.logger.error("Fixer.io - Unsuccessful response. Response: %s", response)
                    return {}

                rates = response.get("rates", {})

                for currency in currencies:
                    if currency in rates:
                        decimal_value = self._to_decimal(rates[currency])
                        if decimal_value is not None:
                            day_rates_in_eur[currency] = decimal_value
            except Exception:
                self.logger.exception("Fixer.io - Exception while parsing of the HTTP response.")
                return {}

        day_rates = {}
        base_currency_rate = day_rates_in_eur.get(self.base_currency)
        if base_currency_rate is not None:
            for currency, day_rate in day_rates_in_eur.items():
                day_rates[currency] = self._conversion_to_base_currency(base_currency_rate, day_rate)

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

        url = self._url.format(date=date_of_exchange)
        response = self._get(url, params={"symbols": "%s,%s" % (self.base_currency, currency)})
        if response:
            try:
                response = response.json()
                if not response.get("success"):
                    self.logger.error("Fixer.io - Unsuccessful response. Response: %s", response)
                    return None

                rates = response.get("rates", {})
                if currency in rates and self.base_currency in rates:
                    return self._conversion_to_base_currency(
                        self._to_decimal(rates[self.base_currency]),
                        self._to_decimal(rates[currency])
                     )

            except Exception:
                self.logger.exception("Fixer.io - Exception while parsing of the HTTP response.")

        return None

    def _conversion_to_base_currency(self, base_currency_rate, currency_rate):
        """
        :type base_currency_rate: decimal.Decimal
        :type currency_rate: decimal.Decimal
        :rtype: decimal.Decimal
        """
        conversion = 1 / base_currency_rate
        return self._to_decimal(currency_rate * conversion)

    def __str__(self):
        return self.name
