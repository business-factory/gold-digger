# -*- coding: utf-8 -*-

import pytest
import logging
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import Mock
from gold_digger.database.db_model import ExchangeRate, Provider
from gold_digger.database.dao_exchange_rate import DaoExchangeRate
from gold_digger.database.dao_provider import DaoProvider
from gold_digger.managers.exchange_rate_manager import ExchangeRateManager
from gold_digger.data_providers import CurrencyLayer, GrandTrunk, Yahoo
from gold_digger.config.params import DEFAULT_CONFIG_PARAMS


@pytest.fixture
def logger():
    return logging.getLogger("gold-digger.tests")


@pytest.fixture
def currencies():
    return DEFAULT_CONFIG_PARAMS["supported_currencies"]


@pytest.fixture
def dao_exchange_rate():
    return Mock(DaoExchangeRate)


@pytest.fixture
def dao_provider():
    m = Mock(DaoProvider)

    def _get_or_create_provider_by_name(name):
        return {
            "currency_layer": Provider(id=1, name="currency_layer"),
            "grandtrunk": Provider(id=2, name="grandtrunk")
        }.get(name)

    m.get_or_create_provider_by_name.side_effect = _get_or_create_provider_by_name
    return m


@pytest.fixture
def currency_layer():
    m = Mock(CurrencyLayer)
    m.name = "currency_layer"
    m.get_all_by_date.return_value = {"EUR": Decimal(0.77), "USD": Decimal(1)}
    return m


@pytest.fixture
def grandtrunk():
    m = Mock(GrandTrunk)
    m.name = "grandtrunk"
    m.get_all_by_date.return_value = {"EUR": Decimal(0.75), "USD": Decimal(1)}
    return m


def test_update_all_rates_by_date_no_previous_rates(dao_exchange_rate, dao_provider, currency_layer, currencies, logger):
    """
    Update rates of all providers for the specified date.
    """
    _date = date(2016, 2, 17)

    dao_exchange_rate.get_all_currencies_by_provider_and_date.return_value = []

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer], currencies, logger)
    exchange_rate_manager.update_all_rates_by_date(_date)

    (actual_records,), _ = exchange_rate_manager.dao_exchange_rate.insert_exchange_rate_to_db.call_args
    (provider_name,), _ = exchange_rate_manager.dao_provider.get_or_create_provider_by_name.call_args

    assert provider_name == exchange_rate_manager.data_providers[0].name
    assert sorted(actual_records, key=lambda x: x["currency"]) == [
        {"provider_id": 1, "date": _date, "currency": "EUR", "rate": Decimal(0.77)},
        {"provider_id": 1, "date": _date, "currency": "USD", "rate": Decimal(1)}
    ]


def test_update_all_rates_by_date_with_respect_to_previous_rates(dao_exchange_rate, dao_provider, currency_layer, currencies, logger):
    """
    Update rates of all providers for the specified date with respect to previous rates.
    If there is a big change in rate compared to rate from previous day then do not insert this rate.
    """
    _date = date(2016, 2, 17)

    currency_layer.get_all_by_date.return_value = {"EUR": Decimal(0.8), "USD": Decimal(1)}
    dao_exchange_rate.get_all_currencies_by_provider_and_date.return_value = [
        ExchangeRate(**{"provider_id": 1, "date": _date - timedelta(days=1), "currency": "EUR", "rate": Decimal(0.5)}),
        ExchangeRate(**{"provider_id": 1, "date": _date - timedelta(days=1), "currency": "USD", "rate": Decimal(1.01)})
    ]

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer], currencies, logger)
    exchange_rate_manager.update_all_rates_by_date(_date)

    (actual_records,), _ = exchange_rate_manager.dao_exchange_rate.insert_exchange_rate_to_db.call_args
    (provider_name,), _ = exchange_rate_manager.dao_provider.get_or_create_provider_by_name.call_args

    assert provider_name == exchange_rate_manager.data_providers[0].name
    assert sorted(actual_records, key=lambda x: x["currency"]) == [
        {
            "provider_id": 1,
            "date": _date,
            "currency": "EUR",
            "rate": Decimal(0.8),
            "change_in_percents": exchange_rate_manager.get_percent_change(Decimal(0.8), Decimal(0.5))  # 60 %
        },
        {
            "provider_id": 1,
            "date": _date,
            "currency": "USD",
            "rate": Decimal(1),
            "change_in_percents": exchange_rate_manager.get_percent_change(Decimal(1), Decimal(1.01))  # 60 %
        }
    ]


def test_get_or_update_rate_by_date(dao_exchange_rate, dao_provider, currency_layer, grandtrunk, currencies, logger):
    """
    Get all rates by date.

    Case: 2 providers, rate of provider 'currency_layer' is in DB, rate of provider 'grandtrunk' miss.
          Get rate for missing provider and update DB. Finally return list of all rates of the day (all provider rates).
    """
    _date = date(2016, 2, 17)
    dao_exchange_rate.get_rate_by_date_currency_provider_id.return_value = None

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer, grandtrunk], currencies, logger)

    grandtrunk.get_by_date.return_value = Decimal(0.75)
    dao_exchange_rate.get_rates_by_date_currency.return_value = [ExchangeRate(provider=Provider(name="currency_layer"), date=_date, currency="EUR", rate=Decimal(0.77))]
    dao_exchange_rate.insert_new_rate.return_value = [ExchangeRate(provider=Provider(name="grandtrunk"), date=_date, currency="EUR", rate=Decimal(0.75))]

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(_date, currency="EUR")
    insert_new_rate_args, _ = dao_exchange_rate.insert_new_rate.call_args

    assert dao_exchange_rate.insert_new_rate.call_count == 1
    assert insert_new_rate_args[1].name == "grandtrunk"
    assert len(exchange_rates) == 2


def test_get_exchange_rate_by_date(dao_exchange_rate, dao_provider, logger):
    _date = date(2016, 2, 17)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], [], logger)

    def _get_rates_by_date_currency(date_of_exchange, currency):
        return {
            "EUR": [ExchangeRate(id=1, currency="EUR", rate=Decimal(0.89), provider=Provider(name="currency_layer"))],
            "CZK": [ExchangeRate(id=2, currency="CZK", rate=Decimal(24.20), provider=Provider(name="currency_layer"))]
        }.get(currency)

    dao_exchange_rate.get_rates_by_date_currency.side_effect = _get_rates_by_date_currency
    exchange_rate = exchange_rate_manager.get_exchange_rate_by_date(_date, "EUR", "CZK")

    assert exchange_rate == Decimal(24.20) * (1 / Decimal(0.89))


def test_get_average_exchange_rate_by_dates(dao_exchange_rate, dao_provider, logger):
    """
    Get average exchange rate within specified period.

    Case: 10 days period, 10 'EUR' rates but only 9 'CZK' rates in DB, 1 provider
          exchange rate is computed as average rate within the period and 'warning' is logged for missing 'CZK' rate
    """
    _start_date = date(2016, 2, 7)
    _end_date = date(2016, 2, 17)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], [], Mock(logger))

    def _get_sum_of_rates_in_period(start_date, end_date, currency):
        return {
            "EUR": [[Provider(name="currency_layer"), 11, Decimal(8.9)]],
            "CZK": [[Provider(name="currency_layer"), 9, Decimal(217.8)]],
        }.get(currency)

    dao_exchange_rate.get_sum_of_rates_in_period.side_effect = _get_sum_of_rates_in_period
    exchange_rate = exchange_rate_manager.get_average_exchange_rate_by_dates(_start_date, _end_date, "EUR", "CZK")

    eur_average = Decimal(8.9) / 11
    czk_average = Decimal(217.8) / 9

    assert exchange_rate == czk_average * (1 / eur_average)
    assert exchange_rate_manager.logger.warning.call_count == 1


def test_pick_the_best_all_same_change_in_percents_is_none():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.5), change_in_percents=None),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=None),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=None)
    ])

    assert best.id in (1, 2, 3)


def test_pick_the_best_all_same_change_in_percents_is_same():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.5), change_in_percents=Decimal(0.2)),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=Decimal(0.2)),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=Decimal(0.2))
    ])

    assert best.id in (1, 2, 3)


def test_pick_the_best_all_same_change_in_percents_significant_in_one():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.5), change_in_percents=Decimal(0.2)),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=Decimal(50)),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=Decimal(0.2))
    ])

    assert best.id in (1, 2, 3)


def test_pick_the_best_all_different_change_in_percents_is_none():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.0), change_in_percents=None),
        ExchangeRate(id=2, rate=Decimal(0.7), change_in_percents=None),
        ExchangeRate(id=3, rate=Decimal(1.4), change_in_percents=None)
    ])

    assert best.id in (1, 2, 3)


def test_pick_the_best_one_different_change_in_percents_is_none():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.0), change_in_percents=None),
        ExchangeRate(id=2, rate=Decimal(0.7), change_in_percents=None),
        ExchangeRate(id=3, rate=Decimal(0.7), change_in_percents=None)
    ])

    assert best.id in (2, 3)


def test_pick_the_best_all_same_change_in_percents_significant_in_two():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.5), change_in_percents=Decimal(50)),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=Decimal(50)),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=Decimal(0.2))
    ])

    assert best.id in (1, 2, 3)


def test_pick_the_best_one_different_change_in_percents_significant_in_one():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(2.3), change_in_percents=Decimal(50)),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=Decimal(0.4)),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=Decimal(0.2))
    ])

    assert best.id in (2, 3)


def test_pick_the_best_one_different_change_in_percents_significant_in_two():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(2.3), change_in_percents=Decimal(50)),
        ExchangeRate(id=2, rate=Decimal(0.5), change_in_percents=Decimal(50)),
        ExchangeRate(id=3, rate=Decimal(0.5), change_in_percents=Decimal(0.2))
    ])

    assert best.id in (2, 3)


def test_pick_the_best_all_slightly_different_change_in_percents_significant_in_two():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(0.65), change_in_percents=Decimal(50)),
        ExchangeRate(id=2, rate=Decimal(0.35), change_in_percents=Decimal(40)),
        ExchangeRate(id=3, rate=Decimal(0.41), change_in_percents=Decimal(10))
    ])

    assert best.id == 3


def test_pick_the_best_all_different_change_rate_probably_change_radically():
    best = ExchangeRateManager.pick_the_best([
        ExchangeRate(id=1, rate=Decimal(2.60), change_in_percents=Decimal(60)),
        ExchangeRate(id=2, rate=Decimal(2.56), change_in_percents=Decimal(58.9)),
        ExchangeRate(id=3, rate=Decimal(0.40), change_in_percents=Decimal(10))
    ])

    assert best.id in (1, 2)
