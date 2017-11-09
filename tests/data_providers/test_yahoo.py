# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from requests import Response


YAHOO_RESPONSE = b"""
{
    "list": {
        "meta": {
            "type": "resource-list",
            "start": 0,
            "count": 188
        },
        "resources": [
            {
                "resource": {
                    "classname": "Quote",
                    "fields": {
                        "vname": "USD/EUR",
                        "price": "0.861800",
                        "symbol": "EUR=X",
                        "ts": "1510220668",
                        "type": "currency",
                        "utctime": "2017-11-09T09:44:28+0000",
                        "volume": "0"
                    }
                }
            },
            {
                "resource": {
                    "classname": "Quote",
                    "fields": {
                        "name": "USD/CZK",
                        "price": "21.988899",
                        "symbol": "CZK=X",
                        "ts": "1510220626",
                        "type": "currency",
                        "utctime": "2017-11-09T09:43:46+0000",
                        "volume": "0"
                    }
                }
            }
        ]
    }
}
"""


def test_yahoo_get_by_date(yahoo):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE
    yahoo._get = lambda *a, **kw: sample

    assert yahoo.get_by_date(date.today(), "EUR") == Decimal("0.861800")
    assert yahoo.get_by_date(date.today(), "XXX") is None  # unsupported currency


def test_yahoo_get_all_by_date(yahoo):
    sample = Response()
    sample.status_code = 200
    sample._content = YAHOO_RESPONSE
    yahoo._get = lambda *a, **kw: sample

    rates = yahoo.get_all_by_date(date.today(), {"EUR", "CZK", "EEK"})

    assert rates == {
        "EUR": Decimal("0.861800"),
        "CZK": Decimal("21.988899"),
    }
