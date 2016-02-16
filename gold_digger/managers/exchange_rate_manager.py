# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import Decimal

from ..database.db_handler import (
    get_rates_by_date_currency,
    get_sum_of_rates_in_period,
    insert_to_db,
    get_or_create_provider_by_name,
    insert_new_rate
)
from ..database.db_model import ExchangeRate


def update_all_rates_by_date(container, date_of_exchange):
    date_of_exchange = datetime.strptime(date_of_exchange, "%Y-%m-%d") if date_of_exchange else date.today()
    for data_provider in container.data_providers:
        container.logger.info("Updating all today rates from %s provider" % data_provider)
        day_rates = data_provider.get_all_by_date(date_of_exchange, container["supported_currencies"])
        if day_rates:
            provider = get_or_create_provider_by_name(container.db_session, data_provider.name)
            records = [dict(currency=currency, rate=rate, date=date_of_exchange, provider_id=provider.id) for currency, rate in day_rates.items()]
            insert_to_db(container.db_session, records)


def update_all_historical_rates(container, origin_date):
    for data_provider in container.data_providers:
        date_rates = data_provider.get_historical(ExchangeRate.currencies(), origin_date)
        provider = get_or_create_provider_by_name(container.db_session, data_provider.name)
        for day, day_rates in date_rates.items():
            records = [dict(currency=currency, rate=rate, date=day, provider_id=provider.id) for currency, rate in day_rates.items()]
            insert_to_db(container.db_session, records)


def get_or_update_rate_by_date(db_session, date_of_exchange, currency, data_providers):
    """
    Get records of exchange rates for the date from all data providers.
    If the date is missing request data providers to update database.
    """
    exchange_rates = get_rates_by_date_currency(db_session, date_of_exchange, currency)
    if len(exchange_rates) != len(data_providers):
        for data_provider in data_providers:    # TODO update only not existing
            rate = data_provider.get_by_date(date_of_exchange, currency)
            if rate:
                exchange_rate = insert_new_rate(db_session, date_of_exchange, data_provider.name, currency, rate)
                exchange_rates.append(exchange_rate)
    return exchange_rates


def get_exchange_rate_by_date(db_session, date_of_exchange, from_currency, to_currency, data_providers):
    """
    Compute exchange rate between 'from_currency' and 'to_currency'.
    If the date is missing request data providers to update database.
    """
    _from_currency = get_or_update_rate_by_date(db_session, date_of_exchange, from_currency, data_providers)
    _to_currency = get_or_update_rate_by_date(db_session, date_of_exchange, to_currency, data_providers)
    for from_, to_ in zip(_from_currency, _to_currency):
        if from_.rate and to_.rate:
            conversion = 1 / from_.rate
            return Decimal(to_.rate * conversion)


def get_average_exchange_rate_by_dates(db_session, start_date, end_date, from_currency, to_currency, data_providers, logger):
    """
    Compute average exchange rate of currency in specified period.
    Log warnings for missing days.
    """
    number_of_days = abs((end_date - start_date).days)
    _from_currency = get_sum_of_rates_in_period(db_session, start_date, end_date, from_currency)
    _to_currency = get_sum_of_rates_in_period(db_session, start_date, end_date, to_currency)
    for (from_provider, from_count, from_sum), (to_provider, to_count, to_sum) in zip(_from_currency, _to_currency):

        logger.info("Sum of currencies %s (%s records) = %s, %s (%s records) = %s in period %s - %s by (%s, %s)" %
                    (from_currency, from_count, from_sum, to_currency, to_count, to_sum, start_date, end_date, from_provider, to_provider))
        if from_count != number_of_days:
            logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                           (from_provider, number_of_days - from_count, from_currency, start_date, end_date))
        if to_count != number_of_days:
            logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                           (to_provider, number_of_days - to_count, to_currency, start_date, end_date))

        if from_count and from_sum and to_count and to_sum:
            from_average = from_sum / from_count
            to_average = to_sum / to_count
            conversion = 1 / from_average
            return Decimal(to_average * conversion)
        logger.error("Date range 'count' and/or 'sum' are empty")
