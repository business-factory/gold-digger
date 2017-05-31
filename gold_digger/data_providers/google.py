from ._provider import Provider
from bs4 import BeautifulSoup


class Google(Provider):
    """Simple API for currency conversion."""

    BASE_URL = 'https://www.google.com/finance/converter'
    BASE_CURRENCY = "USD"
    name = 'google'

    def get_all_by_date(self, date_of_exchange, currencies):
        return {}

    def get_historical(self, origin_date, currencies):
        return {}

    def get_by_date(self, date_of_exchange, currency):
        return {}

    def _convert_value(self, value, currency):
        response = self._get('{}?a={}&from={}&to={}').format(self.BASE_URL, value, self.BASE_CURRENCY, currency)
        if not response:
            self.logger.warning("Google error. Status: %s", response.status_code,
                                extra={"currency": currency, "value": value})
            return None
        parsed_html = BeautifulSoup(response.text)
        res = parsed_html.body.find('span', attrs={'class': 'bld'}).text.split(' ')
        return self._to_decimal(res[0], currency) if value is not None else None

    def _get_rates(self, currencies):
        res = {}
        for c in currencies:
            res[c] = self._convert_value(1, c)
        return res

    def __str__(self):
        return self.name
