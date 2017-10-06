# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from requests import Response

from gold_digger.data_providers.yahoo import Yahoo


def test_yahoo_get_by_date(currencies, logger):
    """
    https://query.yahooapis.com/v1/public/yql
    ?q=SELECT%20*%20FROM%20yahoo.finance.xchange%20WHERE%20pair%20IN%20(%27EUR%27)
    &env=store://datatables.org/alltableswithkeys
    &format=json
    """
    yahoo = Yahoo(currencies, logger)

    sample = Response()
    sample.status_code = 200
    sample._content = b"""        
        {
            "query": {
                "count": 2,
                "created": "2017-10-06T12:40:44Z",
                "lang": "en-US",
                "results": {
                    "rate": {
                        "id": "EUR=X",
                        "Name": "USD/EUR",
                        "Rate": "0.8555",
                        "Date": "10/6/2017",
                        "Time": "1:50pm",
                        "Ask": "0.8560",
                        "Bid": "0.8555"
                    }
                }
            }
        }
        """
    yahoo._post = lambda *a, **kw: sample
    rate_eur = yahoo.get_by_date(date.today(), "EUR")

    assert rate_eur == Decimal("0.8555")


def test_yahoo_get_by_date_unsupported_currency(currencies, logger):
    """
    https://query.yahooapis.com/v1/public/yql
    ?q=SELECT%20*%20FROM%20yahoo.finance.xchange%20WHERE%20pair%20IN%20(%27EEK%27)
    &env=store://datatables.org/alltableswithkeys
    &format=json
    """
    yahoo = Yahoo(currencies, logger)

    sample = Response()
    sample.status_code = 200
    sample._content = b"""        
        {
            "query": {
                "count": 2,
                "created": "2017-10-06T12:40:44Z",
                "lang": "en-US",
                "results": {
                    "rate": {
                        "id": "EEK=X",
                        "Name": "N/A",
                        "Rate": "N/A",
                        "Date": "N/A",
                        "Time": "N/A",
                        "Ask": "N/A",
                        "Bid": "N/A"
                    }
                }
            }
        }
        """
    yahoo._post = lambda *a, **kw: sample
    rate_eur = yahoo.get_by_date(date.today(), "EUR")

    assert rate_eur is None


def test_yahoo_get_all_by_date(currencies, logger):
    """
    https://query.yahooapis.com/v1/public/yql
    ?q=SELECT%20*%20FROM%20yahoo.finance.xchange%20WHERE%20pair%20IN%20(%27EUR,CZK,EEK%27)
    &env=store://datatables.org/alltableswithkeys
    &format=json
    """
    yahoo = Yahoo(currencies, logger)

    sample = Response()
    sample.status_code = 200
    sample._content = b"""        
        {
            "query": {
                "count": 2,
                "created": "2017-10-06T12:40:44Z",
                "lang": "en-US",
                "results": {
                    "rate": [
                        {
                            "id": "EUR=X",
                            "Name": "USD/EUR",
                            "Rate": "0.8555",
                            "Date": "10/6/2017",
                            "Time": "1:50pm",
                            "Ask": "0.8560",
                            "Bid": "0.8555"
                        },
                        {
                            "id": "CZK=X",
                            "Name": "USD/CZK",
                            "Rate": "22.0606",
                            "Date": "10/6/2017",
                            "Time": "2:02pm",
                            "Ask": "22.0660",
                            "Bid": "22.0606"
                        },
                         {
                            "id": "EEK=X",
                            "Name": "N/A",
                            "Rate": "N/A",
                            "Date": "N/A",
                            "Time": "N/A",
                            "Ask": "N/A",
                            "Bid": "N/A"
                        }
                    ]
                }
            }
        }
        """
    yahoo._post = lambda *a, **kw: sample

    rates = yahoo.get_all_by_date(date.today(), {"EUR", "CZK", "EEK"})

    assert rates == {
        "EUR": Decimal("0.8555"),
        "CZK": Decimal("22.0606"),
    }