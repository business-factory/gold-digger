# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from requests import Response


@pytest.fixture
def response():
    return Response()


def test_fixer_conversion_to_base_currency(fixer, logger):
    """
    Fixer has EUR as a base currency. It has to be converted firstly to USD.

    Example of Fixer response:
    {
      "success": true,
      "timestamp": 1553731199,
      "historical": true,
      "base": "EUR",
      "date": "2019-03-27",
      "rates": {
        "HUF": 319.899055,
        "USD": 1.125138
      }
    }
    """

    converted_rate = fixer._conversion_to_base_currency(Decimal(1.125138), Decimal(319.899055), logger)
    assert converted_rate == Decimal('284.3198389886396014034013616')


def test_fixer_reach_monthly_limit(fixer, response, logger):
    """
    Fixer free API has monthly requests limit. After the limit is reached, no calls to API should be made until the beginning of the next month.
    Case: Firstly block upcoming requests by sending 104 error, then set today for the first day of a month and unblock requests.
    """
    response.status_code = 200
    response._content = b"""
    {
        "success": false,
        "error": {
            "code": 104,
            "type": "requests amount reached"
        }
    }
    """

    fixer._get = Mock()
    fixer._get.return_value = response

    fixer.is_first_day_of_month = Mock()
    fixer.is_first_day_of_month.return_value = False

    rate = fixer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert fixer.request_limit_reached is True
    assert fixer._get.call_count == 1
    assert rate is None

    rate = fixer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert fixer._get.call_count == 1
    assert rate is None

    response._content = b"""
        {
            "success": true,
            "timestamp": 1553731199,
            "historical": true,
            "base": "EUR",
            "date": "2019-03-27",
            "rates": {
                "HUF": 319.899055,
                "USD": 1.125138
            }
        }
        """

    fixer.is_first_day_of_month.return_value = True

    rate = fixer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert fixer.request_limit_reached is False
    assert fixer._get.call_count == 2
    assert rate == Decimal('1')

