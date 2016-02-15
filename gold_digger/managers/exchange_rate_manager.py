# -*- coding: utf-8 -*-

from sqlalchemy import and_
from datetime import date, timedelta
from collections import defaultdict
from ..database.db_handler import update_db
from ..database.db_model import ExchangeRate


def update_rates(container, all_days=False):
    if all_days:
        for data_provider in container.data_providers:
            day_rates = data_provider.get_historical(ExchangeRate.currencies(), container["origin_date"])
            for day, rates in day_rates:
                update_db(container.db_session, day, str(data_provider), rates)
    else:
        update_data_from_providers(container.db_session, date.today(), ExchangeRate.currencies(), container.data_providers)


def get_rates(db_session, date_of_exchange, query, currencies, data_providers):
    p = [getattr(ExchangeRate, currency).isnot(None) for currency in currencies]
    rates = db_session.query(*query).filter(and_(ExchangeRate.date == date_of_exchange, *p)).all()
    if not rates:
        rates = update_data_from_providers(db_session, date_of_exchange, currencies, data_providers)
    return rates[0]


def get_range_rates(db_session, start_date, end_date, query, currencies, data_providers):
    date_range = [start_date]
    while date_range[-1] != end_date:
        date_range.append(date_range[-1] + timedelta(1))

    p = [getattr(ExchangeRate, currency).isnot(None) for currency in currencies]
    rates = db_session.query(ExchangeRate).filter(ExchangeRate.date.in_(date_range), *p).all()
    if len(rates) != len(date_range):
        print("warning: some days miss")

    rates_per_date = defaultdict(list)
    for rate in rates:
        rates_per_date[rate.date].append(rate)

    rates_per_date = [rate[0] for rate in rates_per_date.values()]
    average_rates = defaultdict(int)
    for rate in rates_per_date:
        for currency in currencies:
            average_rates[currency] += getattr(rate, currency)
    average_exchange_rate = ExchangeRate()
    number_of_days = len(rates_per_date)
    for currency, value in average_rates.items():
        setattr(average_exchange_rate, currency, value / number_of_days)
    return average_exchange_rate


def update_data_from_providers(db_session, date_of_exchange, currencies, data_providers):
    all_rates = []
    for data_provider in data_providers:
        rates = data_provider.get_by_date(date_of_exchange, currencies)
        if rates:
            update_db(db_session, date_of_exchange, str(data_provider), rates)
            all_rates.append(ExchangeRate(date=date_of_exchange, provider=str(data_provider), **rates))
        print(date_of_exchange, data_provider, rates)
    return all_rates

