import json
import requests
from ._provider import Provider


class Fixer(Provider):
    BASE_URL = "http://api.fixer.io"
    BASE_CURRENCY = "USD"
    name = "fixer.io"

    def get_by_date(self, date_of_exchange, currency):
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")
        self.logger.debug("Requesting Fixer for %s (%s)", currency, date_str,
                          extra={"currency": currency, "date": date_str})

        request = "{url}/{date}?base={from_currency}".format(
            url=self.BASE_URL, date=date_str, from_currency=self.BASE_CURRENCY)
        response = (requests.get(request)).json()
        if response:
            try:
               decimal_value = self._to_decimal(response['rates'][currency])
            except KeyError:
                return None
            return decimal_value

    def get_all_by_date(self, date_of_exchange, currencies):
        day_rates = {}
        date_str = date_of_exchange.strftime(format="%Y-%m-%d")

        for currency in currencies:
            self.logger.debug("Requesting Fixer for %s (%s)", currency, date_str,
                              extra={"currency": currency, "date": date_str})
            request = "{url}/{date}?base={from_currency}".format(
                url=self.BASE_URL, date=date_str, from_currency=self.BASE_CURRENCY)
            response = (requests.get(request)).json()
            if response:
                try:
                    decimal_value = self._to_decimal(response['rates'][currency])
                except KeyError:
                    continue
                if decimal_value:
                    day_rates[currency] = decimal_value
        return day_rates

    def get_historical(self, origin_date, currencies):
        return {}
