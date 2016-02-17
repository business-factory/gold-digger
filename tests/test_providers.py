# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal
from gold_digger.data_providers import *


def test_get_by_date_GrandTrunk():
    p = GrandTrunk()
    record = p.get_by_date(date(2016, 2, 12), "EUR")

    assert isinstance(record, Decimal)


def test_get_by_date_CurrencyLayer():
    p = CurrencyLayer()
    record = p.get_by_date(date(2016, 2, 12), "EUR")

    assert isinstance(record, Decimal)


def test_get_by_date_Yahoo():
    p = Yahoo()
    record = p.get_by_date(date.today(), "EUR")

    assert isinstance(record, Decimal)
