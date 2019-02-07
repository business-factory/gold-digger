# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from requests import Response


YAHOO_RESPONSE = b"""
{
  "spark": {
    "result": [
      {
        "symbol": "USDEUR=X",
        "response": [
          {
            "meta": {
              "currency": "EUR",
              "symbol": "USDEUR=X",
              "exchangeName": "CCY",
              "instrumentType": "CURRENCY",
              "firstTradeDate": 1070236800,
              "gmtoffset": 0,
              "timezone": "GMT",
              "exchangeTimezoneName": "Europe/London",
              "chartPreviousClose": 0.8816,
              "priceHint": 4,
              "currentTradingPeriod": {
                "pre": {
                  "timezone": "GMT",
                  "start": 1541980800,
                  "end": 1541980800,
                  "gmtoffset": 0
                },
                "regular": {
                  "timezone": "GMT",
                  "start": 1541980800,
                  "end": 1542067140,
                  "gmtoffset": 0
                },
                "post": {
                  "timezone": "GMT",
                  "start": 1542067140,
                  "end": 1542067140,
                  "gmtoffset": 0
                }
              },
              "dataGranularity": "1d",
              "validRanges": [
                "1d",
                "5d",
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "2y",
                "5y",
                "10y",
                "ytd",
                "max"
              ]
            },
            "timestamp": [
              1542021900
            ],
            "indicators": {
              "quote": [
                {
                  "close": [
                    0.8884
                  ]
                }
              ],
              "adjclose": [
                {
                  "adjclose": [
                    0.8884
                  ]
                }
              ]
            }
          }
        ]
      },
      {
        "symbol": "EURCZK=X",
        "response": [
          {
            "meta": {
              "currency": "CZK",
              "symbol": "EURCZK=X",
              "exchangeName": "CCY",
              "instrumentType": "CURRENCY",
              "firstTradeDate": 1497913200,
              "gmtoffset": 0,
              "timezone": "GMT",
              "exchangeTimezoneName": "Europe/London",
              "chartPreviousClose": 25.904,
              "priceHint": 3,
              "currentTradingPeriod": {
                "pre": {
                  "timezone": "GMT",
                  "start": 1541980800,
                  "end": 1541980800,
                  "gmtoffset": 0
                },
                "regular": {
                  "timezone": "GMT",
                  "start": 1541980800,
                  "end": 1542067140,
                  "gmtoffset": 0
                },
                "post": {
                  "timezone": "GMT",
                  "start": 1542067140,
                  "end": 1542067140,
                  "gmtoffset": 0
                }
              },
              "dataGranularity": "1d",
              "validRanges": [
                "1d",
                "5d",
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "2y",
                "ytd",
                "max"
              ]
            },
            "timestamp": [
              1542021967
            ],
            "indicators": {
              "quote": [
                {
                  "close": [
                    25.959
                  ]
                }
              ],
              "adjclose": [
                {
                  "adjclose": [
                    25.959
                  ]
                }
              ]
            }
          }
        ]
      }
    ],
    "error": null
  }
}
"""


def test_yahoo_get_by_date(yahoo, logger):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE
    yahoo._get = lambda *a, **kw: sample

    assert yahoo.get_by_date(date.today(), "CZK", logger) == Decimal("25.959")


def test_yahoo_get_by_date__unsupported_currency(yahoo, logger):
    sample = Response()
    sample.status_code = 404
    sample._content = "404 Not Found"
    yahoo._get = lambda *a, **kw: sample
    assert yahoo.get_by_date(date.today(), "XXX", logger) is None  # unsupported currency


def test_yahoo_get_all_by_date(yahoo, logger):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE

    yahoo._get = lambda url, **kw: sample

    rates = yahoo.get_all_by_date(date.today(), {"EUR", "CZK", "AED"}, logger)

    assert rates == {
        "EUR": Decimal("0.8884"),
        "CZK": Decimal("25.959"),
    }
