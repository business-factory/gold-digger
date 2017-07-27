# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from requests import Response

from gold_digger.data_providers.google import Google


def test_google_find_rate_in_html(logger):
    google = Google(logger)

    sample = Response()
    sample.status_code = 200
    sample._content = b"""
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
        <html>
        <head>
            <title>Currency Converter - Google Finance</title>
            <meta name="Description" content="Get real-time stock quotes & charts, financial news, currency conversions, or track your portfolio with Google Finance.">
            <link rel="stylesheet" type="text/css" href="/finance/s/OVd9g2P4lGg/styles/finance_us.css">
            <link rel="icon" type="image/vnd.microsoft.icon" href="/finance/favicon.ico">
        </head>
            <body style="margin-left: 6px; min-width: 0px;">
                <div class=g-doc>
                <form action="/finance/converter" method="get" name="f">
                <div class=sfe-break-top>
                <input name=a maxlength=12 size=5 autocomplete=off value="1">
                </div>
                <div class=sfe-break-top>
                <select name=from value="EUR">
                    <option  value="ETB">Ethiopian Birr (ETB)</option>
                    <option SELECTED value="EUR">Euro (&#8364;)</option>
                    <option  value="FIM">Finnish Markka (FIM)</option>
                </select>
                    <select name=to value="CZK">
                    <option  value="CVE">Cape Verdean Escudo (CVE)</option>
                    <option SELECTED value="CZK">Czech Koruna (CZK)</option>
                    <option  value="DEM">German Mark (DEM)</option>
                </select>
                </div>
                &nbsp;
                <div id=currency_converter_result>1 EUR = <span class=bld>26.0434 CZK</span>
                <input type=submit value="Convert">
                </div>
                <input type=hidden name=meta value=ei&#61;lOB5Wfm3CsGCsgGshZOQDg>
                </form>
            </body>
        </div>
        </html>
        """
    google._get = lambda x: sample

    rate = google.get_by_date(date.today(), "EUR")

    assert isinstance(rate, Decimal)
    assert float(rate) == 26.0434
