# -*- coding: utf-8 -*-

import pytest
import logging
from datetime import date
from decimal import Decimal
from gold_digger.data_providers import *


@pytest.fixture
def logger():
    return logging.getLogger("gold-digger.tests")


def test_get_by_date_GrandTrunk(logger):
    p = GrandTrunk(logger)
    record = p.get_by_date(date(2016, 2, 12), "EUR")

    assert isinstance(record, Decimal)


def test_get_by_date_CurrencyLayer(logger):
    p = CurrencyLayer(logger)
    record = p.get_by_date(date(2016, 2, 12), "EUR")

    assert isinstance(record, Decimal)


def test_get_by_date_Yahoo(logger):
    p = Yahoo(logger)
    record = p.get_by_date(date.today(), "EUR")

    assert isinstance(record, Decimal)
