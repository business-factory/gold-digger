# -*- coding: utf-8 -*-

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, call

import pytest

from gold_digger.data_providers import CurrencyLayer, Fixer, GrandTrunk
from gold_digger.database.dao_exchange_rate import DaoExchangeRate
from gold_digger.database.dao_provider import DaoProvider
from gold_digger.database.db_model import ExchangeRate, Provider
from gold_digger.managers.exchange_rate_manager import ExchangeRateManager


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
def currency_layer(currencies):
    provider = Mock(CurrencyLayer)
    provider.name = "currency_layer"
    provider.get_all_by_date.return_value = {"EUR": Decimal(0.77), "USD": Decimal(1)}
    provider.get_supported_currencies.return_value = currencies
    provider.has_request_limit = True
    return provider


@pytest.fixture
def fixer(currencies):
    provider = Mock(Fixer)
    provider.name = "fixer.io"
    provider.get_supported_currencies.return_value = currencies
    provider.has_request_limit = True
    return provider


@pytest.fixture
def grandtrunk(currencies):
    provider = Mock(GrandTrunk)
    provider.name = "grandtrunk"
    provider.get_all_by_date.return_value = {"EUR": Decimal(0.75), "USD": Decimal(1)}
    provider.get_supported_currencies.return_value = currencies
    provider.has_request_limit = False
    return provider


def test_update_all_rates_by_date(dao_exchange_rate, dao_provider, currency_layer, base_currency, currencies, logger):
    """
    Update rates of all providers for the specified date.
    """
    _date = date(2016, 2, 17)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer], base_currency, currencies)
    exchange_rate_manager.update_all_rates_by_date(_date, [currency_layer], logger)

    (actual_records, _), _ = dao_exchange_rate.insert_exchange_rate_to_db.call_args
    (provider_name,), _ = dao_provider.get_or_create_provider_by_name.call_args

    assert provider_name == currency_layer.name
    assert sorted(actual_records, key=lambda x: x["currency"]) == [
        {"provider_id": 1, "date": _date, "currency": "EUR", "rate": Decimal(0.77)},
        {"provider_id": 1, "date": _date, "currency": "USD", "rate": Decimal(1)}
    ]


def test_get_or_update_rate_by_date(dao_exchange_rate, dao_provider, currency_layer, grandtrunk, base_currency, currencies, logger):
    """
    Get all rates by date.

    Case: 2 providers, rate of provider 'currency_layer' is in DB, rate of provider 'grandtrunk' miss.
          Get rate for missing provider and update DB. Finally return list of all rates of the day (all provider rates).
    """
    _date = date(2016, 2, 17)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer, grandtrunk], base_currency, currencies)

    grandtrunk.get_by_date.return_value = Decimal(0.75)
    dao_exchange_rate.get_rates_by_date_currency.return_value = [
        ExchangeRate(provider=Provider(name="currency_layer"), date=_date, currency="EUR", rate=Decimal(0.77))
    ]
    dao_exchange_rate.insert_new_rate.return_value = [
        ExchangeRate(provider=Provider(name="grandtrunk"), date=_date, currency="EUR", rate=Decimal(0.75))
    ]

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(_date, currency="EUR", logger=logger)
    insert_new_rate_args, _ = dao_exchange_rate.insert_new_rate.call_args

    assert dao_exchange_rate.insert_new_rate.call_count == 1
    assert insert_new_rate_args[1].name == "grandtrunk"
    assert len(exchange_rates) == 2


def test_get_or_update_rate_by_date__today_after_cron_update(dao_exchange_rate, dao_provider, currency_layer, grandtrunk, base_currency, currencies, logger):
    """
    Get all rates by date.

    Case: 2 providers, both rates are in DB as well as yesterday's data. No requests for yesterday should be made.

    """
    today = date.today()

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer, grandtrunk], base_currency, currencies)

    grandtrunk.get_by_date.return_value = Decimal(0.75)
    dao_exchange_rate.get_rates_by_date_currency.return_value = [
        ExchangeRate(provider=Provider(name="currency_layer"), date=today, currency="EUR", rate=Decimal(0.77)),
        ExchangeRate(provider=Provider(name="grandtrunk"), date=today, currency="EUR", rate=Decimal(0.75)),
    ]
    dao_exchange_rate.get_rate_by_date_currency_provider.return_value = []

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(today, currency="EUR", logger=logger)

    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_count == 0
    assert len(exchange_rates) == 2


def test_get_or_update_rate_by_date__today_before_cron_update(dao_exchange_rate, dao_provider, currency_layer, grandtrunk, base_currency, currencies, logger):
    """
    Get all rates by date.

    Case: 2 providers, rate of provider 'currency_layer' is in DB, rate of provider 'grandtrunk' miss, the date is today, yesterday's rates are in DB.
          Get rate for missing provider from yesterday. Finally return list of all rates of the day (all provider rates).
    """
    today = date.today()
    yesterday = today - timedelta(1)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer, grandtrunk], base_currency, currencies)

    grandtrunk.get_by_date.return_value = Decimal(0.75)
    dao_exchange_rate.get_rates_by_date_currency.return_value = [
        ExchangeRate(provider=Provider(name="currency_layer"), date=today, currency="EUR", rate=Decimal(0.77))
    ]
    dao_exchange_rate.get_rate_by_date_currency_provider.return_value = [
        ExchangeRate(provider=Provider(name="grandtrunk"), date=yesterday, currency="EUR", rate=Decimal(0.75))
    ]

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(today, currency="EUR", logger=logger)

    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_count == 1
    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_args[0] == (yesterday, "EUR", "grandtrunk")
    assert len(exchange_rates) == 2


def test_get_or_update_rate_by_date__today_before_cron_update_no_yesterday_rates(
    dao_exchange_rate, dao_provider, currency_layer, grandtrunk, base_currency, currencies, logger
):
    """
    Get all rates by date.

    Case: 2 providers, rate of provider 'currency_layer' is in DB, rate of provider 'grandtrunk' miss, the date is today, yesterday's rates aren't in DB.
          Try to get rate for missing provider from yesterday, fail and request from API, store to DB.
          Finally return list of all rates of the day (all provider rates).
    """
    today = date.today()
    yesterday = today - timedelta(1)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [currency_layer, grandtrunk], base_currency, currencies)

    grandtrunk.get_by_date.return_value = Decimal(0.75)
    dao_exchange_rate.get_rates_by_date_currency.return_value = [
        ExchangeRate(provider=Provider(name="currency_layer"), date=today, currency="EUR", rate=Decimal(0.77))
    ]
    dao_exchange_rate.get_rate_by_date_currency_provider.return_value = []
    dao_exchange_rate.insert_new_rate.return_value = [
        ExchangeRate(provider=Provider(name="grandtrunk"), date=today, currency="EUR", rate=Decimal(0.75))
    ]

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(today, currency="EUR", logger=logger)
    insert_new_rate_args, _ = dao_exchange_rate.insert_new_rate.call_args

    assert dao_exchange_rate.insert_new_rate.call_count == 1
    assert insert_new_rate_args[1].name == "grandtrunk"
    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_count == 1
    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_args[0] == (yesterday, "EUR", "grandtrunk")
    assert len(exchange_rates) == 2


def test_get_or_update_rate_by_date__no_api_requests_for_historical_data_on_limited_providers(
    dao_exchange_rate, dao_provider, fixer, currency_layer, grandtrunk, base_currency, currencies, logger
):
    """
    In case historical data are requested and they are not in database we don't want to request API if the provider has request limit
    """
    yesterday = date.today() - timedelta(1)  # yesterday's rates are treated as historical rates

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [fixer, currency_layer, grandtrunk], base_currency, currencies)

    dao_exchange_rate.get_rates_by_date_currency.return_value = []

    exchange_rates = exchange_rate_manager.get_or_update_rate_by_date(yesterday, currency="EUR", logger=logger)

    assert dao_exchange_rate.get_rates_by_date_currency.call_count == 1
    assert dao_exchange_rate.get_rate_by_date_currency_provider.call_count == 0
    assert grandtrunk.get_by_date.call_count == 1
    assert currency_layer.get_by_date.call_count == 0
    assert fixer.get_by_date.call_count == 0
    assert len(exchange_rates) == 1


def test_get_exchange_rate_by_date(dao_exchange_rate, dao_provider, base_currency, logger):
    _date = date(2016, 2, 17)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_date_currency(_, currency):
        return {
            "EUR": [ExchangeRate(id=1, currency="EUR", rate=Decimal(0.89), provider=Provider(name="currency_layer"))],
            "CZK": [ExchangeRate(id=2, currency="CZK", rate=Decimal(24.20), provider=Provider(name="currency_layer"))]
        }.get(currency)

    dao_exchange_rate.get_rates_by_date_currency.side_effect = _get_rates_by_date_currency
    exchange_rate = exchange_rate_manager.get_exchange_rate_by_date(_date, "EUR", "CZK", logger)

    assert exchange_rate == Decimal(24.20) / Decimal(0.89)


def test_get_exchange_rates_by_date__same_currencies_returns_immediately(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(date(2016, 2, 17), date(2016, 2, 19), "EUR", "EUR", logger)

    assert exchange_rates_by_dates == {
        "2016-02-17": "1.0",
        "2016-02-18": "1.0",
        "2016-02-19": "1.0",
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_not_called()


def test_get_exchange_rates_by_date__use_default_rate_for_base_from_currency(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    _start_date = date(2016, 2, 17)
    _end_date = date(2016, 2, 18)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_dates_for_currency_in_period(currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        return {
            "CZK": {
                start_date: [Decimal(24.19), Decimal(24.19), Decimal(24.20)],
                end_date: [Decimal(24.19), Decimal(24.20), Decimal(24.20)],
            },
        }[currency]

    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.side_effect = _get_rates_by_dates_for_currency_in_period

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(_start_date, _end_date, base_currency, "CZK", logger)

    assert exchange_rates_by_dates == {
        "2016-02-17": str(Decimal(24.19) / Decimal(1)),
        "2016-02-18": str(Decimal(24.20) / Decimal(1)),
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_has_calls([
        call("CZK", _start_date, _end_date),
    ])


def test_get_exchange_rates_by_date__use_default_rate_for_base_to_currency(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    _start_date = date(2016, 2, 17)
    _end_date = date(2016, 2, 18)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_dates_for_currency_in_period(currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        return {
            "EUR": {
                start_date: [Decimal(0.88), Decimal(0.88), Decimal(0.89)],
                end_date: [Decimal(0.88), Decimal(0.89), Decimal(0.89)],
            },
        }[currency]

    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.side_effect = _get_rates_by_dates_for_currency_in_period

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(_start_date, _end_date, "EUR", base_currency, logger)

    assert exchange_rates_by_dates == {
        "2016-02-17": str(Decimal(1) / Decimal(0.88)),
        "2016-02-18": str(Decimal(1) / Decimal(0.89)),
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_has_calls([
        call("EUR", _start_date, _end_date),
    ])


def test_get_exchange_rates_by_date__pick_best_rate_for_all_dates(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    _start_date = date(2016, 2, 17)
    _end_date = date(2016, 2, 18)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_dates_for_currency_in_period(currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        return {
            "EUR": {
                start_date: [Decimal(0.88), Decimal(0.88), Decimal(0.89)],
                end_date: [Decimal(0.88), Decimal(0.89), Decimal(0.89)],
            },
            "CZK": {
                start_date: [Decimal(24.19), Decimal(24.19), Decimal(24.20)],
                end_date: [Decimal(24.19), Decimal(24.20), Decimal(24.20)],
            },
        }[currency]

    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.side_effect = _get_rates_by_dates_for_currency_in_period

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(_start_date, _end_date, "EUR", "CZK", logger)

    assert exchange_rates_by_dates == {
        "2016-02-17": str(Decimal(24.19) / Decimal(0.88)),
        "2016-02-18": str(Decimal(24.20) / Decimal(0.89)),
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_has_calls([
        call("EUR", _start_date, _end_date),
        call("CZK", _start_date, _end_date),
    ])


def test_get_exchange_rates_by_date__pick_average_rate_for_dates_missing_one_day(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    _start_date = date(2016, 2, 17)
    _end_date = date(2016, 2, 19)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_dates_for_currency_in_period(currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        return {
            "EUR": {
                start_date: [Decimal(0.88), Decimal(0.88), Decimal(0.89)],
                end_date: [Decimal(0.88), Decimal(0.89), Decimal(0.89)],
            },
            "CZK": {
                start_date: [Decimal(24.19), Decimal(24.19), Decimal(24.20)],
                end_date: [Decimal(24.19), Decimal(24.20), Decimal(24.20)],
            },
        }[currency]

    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.side_effect = _get_rates_by_dates_for_currency_in_period

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(_start_date, _end_date, "EUR", "CZK", logger)

    # we use average from best yesterday and best tomorrow rates
    best_to_currency_rate = (Decimal(24.19) + Decimal(24.20)) / 2
    best_from_currency_rate = (Decimal(0.88) + Decimal(0.89)) / 2
    assert exchange_rates_by_dates == {
        "2016-02-17": str(Decimal(24.19) / Decimal(0.88)),
        "2016-02-18": str(best_to_currency_rate / best_from_currency_rate),
        "2016-02-19": str(Decimal(24.20) / Decimal(0.89)),
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_has_calls([
        call("EUR", _start_date, _end_date),
        call("CZK", _start_date, _end_date),
    ])


def test_get_exchange_rates_by_date__ignore_dates_missing_for_more_than_one_day(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    :param dao_exchange_rate: Mock of gold_digger.database.DaoExchangeRate
    :param dao_provider: Mock of gold_digger.database.DaoProvider
    :type base_currency: str
    :type logger: logging.Logger
    """
    _start_date = date(2016, 2, 17)
    _end_date = date(2016, 2, 20)

    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_rates_by_dates_for_currency_in_period(currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        return {
            "EUR": {
                start_date: [Decimal(0.88), Decimal(0.88), Decimal(0.89)],
                end_date: [Decimal(0.88), Decimal(0.89), Decimal(0.89)],
            },
            "CZK": {
                start_date: [Decimal(24.19), Decimal(24.19), Decimal(24.20)],
                end_date: [Decimal(24.19), Decimal(24.20), Decimal(24.20)],
            },
        }[currency]

    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.side_effect = _get_rates_by_dates_for_currency_in_period

    exchange_rates_by_dates = exchange_rate_manager.get_exchange_rates_by_dates(_start_date, _end_date, "EUR", "CZK", logger)

    assert exchange_rates_by_dates == {
        "2016-02-17": str(Decimal(24.19) / Decimal(0.88)),
        "2016-02-20": str(Decimal(24.20) / Decimal(0.89)),
    }
    dao_exchange_rate.get_rates_by_dates_for_currency_in_period.assert_has_calls([
        call("EUR", _start_date, _end_date),
        call("CZK", _start_date, _end_date),
    ])


def test_get_average_exchange_rate_by_dates(dao_exchange_rate, dao_provider, base_currency, logger):
    """
    Get average exchange rate within specified period.

    Case: 10 days period, 10 'EUR' rates but only 9 'CZK' rates in DB, 1 provider
          exchange rate is computed as average rate within the period and 'warning' is logged for missing 'CZK' rate
    """
    _start_date = date(2016, 2, 7)
    _end_date = date(2016, 2, 17)

    mock_logger = Mock(logger)
    exchange_rate_manager = ExchangeRateManager(dao_exchange_rate, dao_provider, [], base_currency, set())

    def _get_sum_of_rates_in_period(_, __, currency):
        return {
            "EUR": [[Provider(name="currency_layer"), 11, Decimal(8.9)]],
            "CZK": [[Provider(name="currency_layer"), 9, Decimal(217.8)]],
        }.get(currency)

    dao_exchange_rate.get_sum_of_rates_in_period.side_effect = _get_sum_of_rates_in_period

    exchange_rate = exchange_rate_manager.get_average_exchange_rate_by_dates(_start_date, _end_date, "EUR", "CZK", mock_logger)
    eur_average = Decimal(8.9) / 11
    czk_average = Decimal(217.8) / 9

    assert exchange_rate == czk_average * (1 / eur_average)
    assert mock_logger.warning.call_count == 1


def test_pick_rate_from_any_provider_if_rates_are_same():
    best = ExchangeRateManager.pick_the_best([Decimal(0.5), Decimal(0.5), Decimal(0.5)])

    assert best == 0.5


def test_pick_middle_rate_if_it_exists():
    best = ExchangeRateManager.pick_the_best([Decimal(0.0), Decimal(0.5), Decimal(1.0)])

    assert best == 0.5


def test_pick_middle_rate_if_it_exists2():
    best = ExchangeRateManager.pick_the_best([Decimal(1.5), Decimal(0.5), Decimal(1.0)])

    assert best == 1.0


def test_pick_rate_from_pair_of_same_rates_by_order_of_providers():
    best = ExchangeRateManager.pick_the_best([Decimal(0.0), Decimal(0.7), Decimal(0.7)])

    assert best == 0.7


def test_pick_rate_from_most_similar_pair_of_rates_by_order_of_providers():
    best = ExchangeRateManager.pick_the_best([Decimal(0.02), Decimal(0.72), Decimal(0.74)])

    assert best == 0.72
