# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from requests import Response


YAHOO_RESPONSE = b"""
{
   "spark":{
      "result":[
         {
            "symbol":"NOK=X",
            "response":[
               {
                  "meta":{
                     "currency":"NOK",
                     "symbol":"NOK=X",
                     "exchangeName":"CCY",
                     "instrumentType":"CURRENCY",
                     "firstTradeDate":995238000,
                     "gmtoffset":0,
                     "timezone":"GMT",
                     "exchangeTimezoneName":"Europe/London",
                     "chartPreviousClose":8.3756,
                     "priceHint":5,
                     "currentTradingPeriod":{
                        "pre":{
                           "timezone":"GMT",
                           "start":1541721600,
                           "end":1541721600,
                           "gmtoffset":0
                        },
                        "regular":{
                           "timezone":"GMT",
                           "start":1541721600,
                           "end":1541807940,
                           "gmtoffset":0
                        },
                        "post":{
                           "timezone":"GMT",
                           "start":1541807940,
                           "end":1541807940,
                           "gmtoffset":0
                        }
                     },
                     "dataGranularity":"1d",
                     "validRanges":[
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
                  "timestamp":[
                     1541759519
                  ],
                  "indicators":{
                     "quote":[
                        {
                           "close":[
                              8.44
                           ]
                        }
                     ],
                     "adjclose":[
                        {
                           "adjclose":[
                              8.44
                           ]
                        }
                     ]
                  }
               }
            ]
         },
         {
            "symbol":"NIO=X",
            "response":[
               {
                  "meta":{
                     "currency":"NIO",
                     "symbol":"NIO=X",
                     "exchangeName":"CCY",
                     "instrumentType":"CURRENCY",
                     "firstTradeDate":1070236800,
                     "gmtoffset":0,
                     "timezone":"GMT",
                     "exchangeTimezoneName":"Europe/London",
                     "chartPreviousClose":31.96,
                     "priceHint":3,
                     "currentTradingPeriod":{
                        "pre":{
                           "timezone":"GMT",
                           "start":1541721600,
                           "end":1541721600,
                           "gmtoffset":0
                        },
                        "regular":{
                           "timezone":"GMT",
                           "start":1541721600,
                           "end":1541807940,
                           "gmtoffset":0
                        },
                        "post":{
                           "timezone":"GMT",
                           "start":1541807940,
                           "end":1541807940,
                           "gmtoffset":0
                        }
                     },
                     "dataGranularity":"1d",
                     "validRanges":[
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
                  "timestamp":[
                     1541743835
                  ],
                  "indicators":{
                     "quote":[
                        {
                           "close":[
                              32.106
                           ]
                        }
                     ],
                     "adjclose":[
                        {
                           "adjclose":[
                              32.106
                           ]
                        }
                     ]
                  }
               }
            ]
         }
      ],
      "error":null
   }
}
"""


def test_yahoo_get_by_date(yahoo):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE
    yahoo._get = lambda *a, **kw: sample

    assert yahoo.get_by_date(date.today(), "NOK") == Decimal("8.44")


def test_yahoo_get_by_date__unsupported_currency(yahoo):
    sample = Response()
    sample.status_code = 404
    sample._content = "404 Not Found"
    yahoo._get = lambda *a, **kw: sample
    assert yahoo.get_by_date(date.today(), "XXX") is None  # unsupported currency


def test_yahoo_get_all_by_date(yahoo):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE

    yahoo._get = lambda url, **kw: sample

    rates = yahoo.get_all_by_date(date.today(), {"NOK", "NIO", "EUR"})

    assert rates == {
        "NOK": Decimal("8.44"),
        "NIO": Decimal("32.106"),
        "EUR": None
    }
