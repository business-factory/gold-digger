# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

import pytest
from requests import Response

API_RESPONSE_USD = b"""
{
  "base": "USD",
  "rates": {
    "BGN": 1.7288075665,
    "NZD": 1.4787412711,
    "ILS": 3.5618315213,
    "RUB": 64.2633253779,
    "CAD": 1.3312118801,
    "USD": 1,
    "PHP": 51.6892071069,
    "CHF": 1.0028286043,
    "AUD": 1.3931759922,
    "JPY": 111.9596923893,
    "TRY": 5.8019093079,
    "HKD": 7.8392115266,
    "MYR": 4.1167683196,
    "HRK": 6.5729691505,
    "CZK": 22.6509325555,
    "IDR": 14060.0017678777,
    "DKK": 6.5976310439,
    "NOK": 8.4874038717,
    "HUF": 283.0814107664,
    "GBP": 0.7628834085,
    "MXN": 18.7834349863,
    "THB": 31.7652258464,
    "ISK": 119.8621055423,
    "ZAR": 13.9832051622,
    "BRL": 3.8880049501,
    "SGD": 1.3523380182,
    "PLN": 3.7781313533,
    "INR": 69.4249977902,
    "KRW": 1132.6527004331,
    "RON": 4.2091399275,
    "CNY": 6.7061787324,
    "SEK": 9.2467073279,
    "EUR": 0.8839388314
  },
  "date": "2019-04-15"
}
"""

API_RESPONSE_EUR = b"""
{
  "base": "EUR",
  "rates": {
    "BGN": 1.9558,
    "NZD": 1.6729,
    "ILS": 4.0295,
    "RUB": 72.7011,
    "CAD": 1.506,
    "USD": 1.1313,
    "PHP": 58.476,
    "CHF": 1.1345,
    "ZAR": 15.8192,
    "AUD": 1.5761,
    "JPY": 126.66,
    "TRY": 6.5637,
    "HKD": 8.8685,
    "MYR": 4.6573,
    "THB": 35.936,
    "HRK": 7.436,
    "NOK": 9.6018,
    "IDR": 15906.08,
    "DKK": 7.4639,
    "CZK": 25.625,
    "HUF": 320.25,
    "GBP": 0.86305,
    "MXN": 21.2497,
    "KRW": 1281.37,
    "ISK": 135.6,
    "SGD": 1.5299,
    "BRL": 4.3985,
    "PLN": 4.2742,
    "INR": 78.5405,
    "RON": 4.7618,
    "CNY": 7.5867,
    "SEK": 10.4608
  },
  "date": "2019-04-15"
}
"""


@pytest.fixture
def response():
    return Response()


def test_get_by_date__available(rates_api, response, logger):
    """
    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE_USD

    rates_api._get = lambda url, **kw: response

    converted_rate = rates_api.get_by_date(date(2019, 4, 15), "CZK", logger)
    assert converted_rate == Decimal(22.6509325555)


def test_get_by_date__date_unavailable(rates_api, response, logger):
    """
    Rates API returns rates from last available date when asked for an unavailable one.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE_USD

    rates_api._get = lambda url, **kw: response

    converted_rate = rates_api.get_by_date(date(2019, 4, 16), "CZK", logger)
    assert converted_rate == Decimal(22.6509325555)


def test_get_by_date__date_too_old(rates_api, response, logger):
    """
    Rates API returns error when the specified date is before 1999-01-04.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_by_date(date(1000, 1, 11), "CZK", logger)
    assert converted_rates is None


def test_get_by_date__currency_unavailable(rates_api, response, logger):
    """
    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_by_date(date(2019, 4, 16), "XXX", logger)
    assert converted_rates is None


def test_get_all_by_date__available(rates_api, response, logger):
    """
    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE_USD

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 15), {"CZK", "EUR"}, logger)
    assert converted_rates == {
        "CZK": Decimal(22.6509325555),
        "EUR": Decimal(0.8839388314)
    }


def test_get_all_by_date__date_unavailable(rates_api, response, logger):
    """
    Rates API returns rates from last available date when asked for an unavailable one.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE_USD

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 16), {"CZK", "EUR"}, logger)
    assert converted_rates == {
        "CZK": Decimal(22.6509325555),
        "EUR": Decimal(0.8839388314)
    }


def test_get_all_by_date__date_too_old(rates_api, response, logger):
    """
    Rates API returns error when the specified date is before 1999-01-04.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(1000, 1, 11), {"CZK"}, logger)
    assert converted_rates == {}


def test_get_all_by_date__currency_unavailable(rates_api, response, logger):
    """
    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 16), {"XXX"}, logger)
    assert converted_rates == {}


def test_get_by_date__eur_base_eur_target(rates_api, response, logger):
    """
    Rates API has a bug where it returns error when base currency is EUR and the target currency is also EUR. The data should be manually added to the result.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    rates_api._base_currency = "EUR"

    converted_rates = rates_api.get_by_date(date(2019, 4, 16), "EUR", logger)
    assert converted_rates == Decimal('1')


def test_get_all_by_date__eur_base_eur_target(rates_api, response, logger):
    """
    Rates API has a bug where it doesn't return EUR rates when it is base currency. The data should be manually added to the result.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger: logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE_EUR

    rates_api._base_currency = "EUR"

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 16), {"EUR", "CZK"}, logger)
    assert converted_rates == {
        "CZK": Decimal(25.663000000000000255795384873636066913604736328125),
        "EUR": Decimal(1)
    }

