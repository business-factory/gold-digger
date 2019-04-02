# -*- coding: utf-8 -*-

from decimal import Decimal


def test_unicredit_conversion_to_base_currency(unicredit, logger):
    """
    Unicredit has CZK as a base currency. It has to be converted firstly to USD.

    Example of Unicredit response:
        [
           {
              'CardsMiddleRate':8.08,
              'CardsPurchaseRate':7.858,
              'CardsSaleRate':8.302,
              'CardsVarianceIndicator':'D',
              'CashMiddleRate':0,
              'CashPurchaseRate':0,
              'CashSaleRate':0,
              'CashVarianceIndicator':'N',
              'CurrencyCode':'HUF',
              'ExchangeRateUpdatedTimestamp':'2019-03-26T23:00:00Z',
              'MiddleRate':8.153 # 1 CZK = 8.153 HUF
           },
           {
              'CardsMiddleRate':22.827,
              'CardsPurchaseRate':22.199,
              'CardsSaleRate':23.455,
              'CardsVarianceIndicator':'U',
              'CashMiddleRate':22.827,
              'CashPurchaseRate':21.686,
              'CashSaleRate':23.968,
              'CashVarianceIndicator':'U',
              'CurrencyCode':'USD',
              'ExchangeRateUpdatedTimestamp':'2019-03-26T23:00:00Z',
              'MiddleRate':22.823 # 1 CZK = 22.823 HUF
           },
           {
              'CurrencyCode':'CZK',
              'CardsMiddleRate':1.0
           }
        ]
    """

    converted_rate = unicredit._conversion_to_base_currency(Decimal(22.823), Decimal(8.153), logger)
    assert converted_rate == Decimal('186.0759190000000139471438842')
