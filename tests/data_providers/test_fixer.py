# -*- coding: utf-8 -*-

from decimal import Decimal


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
