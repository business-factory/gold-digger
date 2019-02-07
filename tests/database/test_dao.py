# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

import pytest

from gold_digger.database.dao_exchange_rate import DaoExchangeRate
from gold_digger.database.dao_provider import DaoProvider

from . import database_test


@pytest.fixture
def dao_exchange_rate(db_session):
    return DaoExchangeRate(db_session)


@pytest.fixture
def dao_provider(db_session):
    return DaoProvider(db_session)


@database_test
def test_insert_new_rate(dao_exchange_rate, dao_provider):
    assert dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD") == []

    provider1 = dao_provider.get_or_create_provider_by_name("test1")
    dao_exchange_rate.insert_new_rate(date.today(), provider1, "USD", Decimal(1))

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 1

    dao_exchange_rate.insert_new_rate(date.today(), provider1, "USD", Decimal(1))

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 1


@database_test
def test_insert_exchange_rate_to_db(dao_exchange_rate, dao_provider, logger):
    assert dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD") == []

    provider1 = dao_provider.get_or_create_provider_by_name("test1")
    provider2 = dao_provider.get_or_create_provider_by_name("test2")

    records = [
        {"date": date.today(), "currency": "USD", "provider_id": provider1.id, "rate": Decimal(1)},
        {"date": date.today(), "currency": "USD", "provider_id": provider2.id, "rate": Decimal(1)},
        {"date": date.today(), "currency": "USD", "provider_id": provider1.id, "rate": Decimal(1)}
    ]
    dao_exchange_rate.insert_exchange_rate_to_db(records, logger)

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 2


@database_test
def test_get_sum_of_rates_in_period(dao_exchange_rate, dao_provider):
    start_date = date(2016, 1, 1)
    end_date = date(2016, 1, 10)
    assert dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, "USD") == []

    provider1 = dao_provider.get_or_create_provider_by_name("test1")
    dao_exchange_rate.insert_new_rate(date(2016, 1, 1), provider1, "USD", Decimal(1))
    dao_exchange_rate.insert_new_rate(date(2016, 1, 2), provider1, "USD", Decimal(2))
    dao_exchange_rate.insert_new_rate(date(2016, 1, 3), provider1, "USD", Decimal(3))

    records = dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, "USD")
    assert records == [(provider1.id, 3, 6)]
