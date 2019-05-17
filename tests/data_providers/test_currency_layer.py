# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from requests import Response


@pytest.fixture
def response():
    return Response()


def test_currency_layer__reach_monthly_limit(currency_layer, response, logger):
    """
    Currency layer free API has monthly requests limit. After the limit is reached, no calls to API should be made until the beginning of the next month.
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

    currency_layer._get = Mock()
    currency_layer._get.return_value = response

    currency_layer.is_first_day_of_month = Mock()
    currency_layer.is_first_day_of_month.return_value = False

    rate = currency_layer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert currency_layer.request_limit_reached is True
    assert currency_layer._get.call_count == 1
    assert rate is None

    rate = currency_layer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert currency_layer._get.call_count == 1
    assert rate is None

    response._content = b"""
        {
            "success": true,
            "quotes": {
                "USDUSD": 1
            }
        }
        """

    currency_layer.is_first_day_of_month.return_value = True

    rate = currency_layer.get_by_date(date(2019, 4, 29), "USD", logger)

    assert currency_layer.request_limit_reached is False
    assert currency_layer._get.call_count == 2
    assert rate == Decimal('1')
