# -*- coding: utf-8 -*-
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from gold_digger.database.db_model import ExchangeRate, Provider


def insert_to_db(session, records):
    for record in records:
        try:
            session.add(ExchangeRate(**record))
            session.flush()
        except IntegrityError:
            session.rollback()
    session.commit()


def get_or_create_provider_by_name(session, name):
    provider = session.query(Provider).filter(Provider.name == name).first()
    if not provider:
        provider = Provider(name=name)
        session.add(provider)
        session.commit()
    return provider


def get_rates_by_date_currency(session, date_of_exchange, currency):
    return session.query(ExchangeRate).filter(
        and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency)
    ).all()


def get_rate_by_date_currency_provider(session, date_of_exchange, currency, provider_name):
    return session.query(ExchangeRate).filter(
        and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency, ExchangeRate.provider.has(name=provider_name))
    ).first()


def insert_new_rate(session, date_of_exchange, provider_name, currency, rate):
    """
    Insert new exchange rate for the specified date by specified provider.
    Date, currency and provider must be unique, therefore if record is already in database return it (without any update or insert)
    """
    db_provider = get_or_create_provider_by_name(session, provider_name)
    db_record = ExchangeRate(date=date_of_exchange, provider_id=db_provider.id, currency=currency, rate=rate)
    try:
        session.add(db_record)
        session.commit()
    except IntegrityError:  # rate for this currency, date and provider is already in database
        db_record = get_rate_by_date_currency_provider(session, date_of_exchange, currency, provider_name)
    return db_record


def get_sum_of_rates_in_period(session, start_date, end_date, currency):
    """
    SELECT provider_id, count(*), SUM(rate) FROM "USD_exchange_rates" WHERE date >= '%Y-%m-%d' AND date <= '%Y-%m-%d' GROUP BY provider_id
    """
    return session.query(ExchangeRate.provider_id, func.count(), func.sum(ExchangeRate.rate)).filter(
        and_(ExchangeRate.date >= start_date, ExchangeRate.date <= end_date, ExchangeRate.currency == currency, ExchangeRate.rate.isnot(None))
    ).group_by(ExchangeRate.provider_id).all()
