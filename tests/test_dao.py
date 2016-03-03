# -*- coding: utf-8 -*-
from decimal import Decimal

import pytest
from datetime import date

from gold_digger.database.dao_provider import DaoProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from gold_digger.database.dao_exchange_rate import DaoExchangeRate
from gold_digger.database.db_model import Base
from gold_digger.config.params import DEFAULT_CONFIG_PARAMS


@pytest.fixture(scope="module")
def connection(request):
    """ Create one test database for all tests. """
    test_db_name = "gd-test"
    params = DEFAULT_CONFIG_PARAMS["database"]

    # we want connect to default database (existing database)
    # eg. postgres://postgres:postgres@localhost:5432/postgres
    _engine = create_engine("{dialect}://{user}:{pass}@{host}:{port}/{name}".format(**params))
    _connection = _engine.connect()
    _connection.execute("commit")
    _connection.execute('create database "%s"' % test_db_name)

    params["name"] = test_db_name
    _test_engine = create_engine("{dialect}://{user}:{pass}@{host}:{port}/{name}".format(**params))
    _test_connection = _test_engine.connect()

    def fin():
        _test_connection.close()
        _test_engine.dispose()

        _connection.execute("commit")
        _connection.execute('drop database "%s"' % test_db_name)
        _connection.close()

    request.addfinalizer(fin)
    return _test_connection


@pytest.fixture()
def session(request, connection):
    """ Drop and create all tables for every test, ie. every test starts with empty tables and new session. """
    Base.metadata.drop_all(connection)
    Base.metadata.create_all(connection)
    _session = scoped_session(sessionmaker(connection))

    def fin():
        _session.remove()

    request.addfinalizer(fin)
    return _session


@pytest.fixture()
def dao_exchange_rate(session):
    return DaoExchangeRate(session)


@pytest.fixture()
def dao_provider(session):
    return DaoProvider(session)


def test_insert_new_rate(dao_exchange_rate, dao_provider):
    assert dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD") == []

    provider1 = dao_provider.get_or_create_provider_by_name("test1")
    dao_exchange_rate.insert_new_rate(date.today(), provider1, "USD", Decimal(1))

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 1

    dao_exchange_rate.insert_new_rate(date.today(), provider1, "USD", Decimal(1))

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 1


def test_insert_exchange_rate_to_db(dao_exchange_rate, dao_provider):
    assert dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD") == []

    provider1 = dao_provider.get_or_create_provider_by_name("test1")
    provider2 = dao_provider.get_or_create_provider_by_name("test2")

    records = [
        {"date": date.today(), "currency": "USD", "provider_id": provider1.id, "rate": Decimal(1)},
        {"date": date.today(), "currency": "USD", "provider_id": provider2.id, "rate": Decimal(1)},
        {"date": date.today(), "currency": "USD", "provider_id": provider1.id, "rate": Decimal(1)}
    ]
    dao_exchange_rate.insert_exchange_rate_to_db(records)

    assert len(dao_exchange_rate.get_rates_by_date_currency(date.today(), "USD")) == 2


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
