# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

import pytest
from requests import Response

API_RESPONSE = b"""
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


@pytest.fixture
def response():
    return Response()


def test_get_by_date__available(rates_api, response, logger):
    """
    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE

    rates_api._get = lambda url, **kw: response

    converted_rate = rates_api.get_by_date(date(2019, 4, 15), "CZK", logger)
    assert converted_rate == Decimal(22.6509325555)


def test_get_by_date__date_unavailable(rates_api, response, logger):
    """
    Rates API returns rates from last available date when asked for an unavailable one. These rates are not returned from the provider.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE

    rates_api._get = lambda url, **kw: response

    converted_rate = rates_api.get_by_date(date(2019, 4, 16), "CZK", logger)
    assert converted_rate is None


def test_get_by_date__date_too_old(rates_api, response, logger):
    """
    Rates API returns error when the specified date is before 1999-01-04.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_by_date(date(1000, 1, 11), "CZK", logger)
    assert converted_rates is None


def test_get_by_date__currency_unavailable(rates_api, response, logger):
    """
    Rates API returns last available date when asked for an unavailable one. This data are not returned from the provider.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
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
    :type logger:  logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 15), {"CZK", "EUR"}, logger)
    assert converted_rates == {
        "CZK": Decimal(22.6509325555),
        "EUR": Decimal(0.8839388314)
    }


def test_get_all_by_date__date_unavailable(rates_api, response, logger):
    """
    Rates API returns rates from last available date when asked for an unavailable one. These rates are not returned from the provider.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
    """
    response.status_code = 200
    response._content = API_RESPONSE

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 16), {"CZK", "EUR"}, logger)
    assert converted_rates == {}


def test_get_all_by_date__date_too_old(rates_api, response, logger):
    """
    Rates API returns error when the specified date is before 1999-01-04.

    :type rates_api: gold_digger.data_providers.rates_api.RatesAPI
    :type response: requests.Response
    :type logger:  logging.Logger
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
    :type logger:  logging.Logger
    """
    response.status_code = 400
    response._content = b"{'error': 'Error message'}"

    rates_api._get = lambda url, **kw: response

    converted_rates = rates_api.get_all_by_date(date(2019, 4, 16), {"XXX"}, logger)
    assert converted_rates == {}
