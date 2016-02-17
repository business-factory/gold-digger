# -*- coding: utf-8 -*-
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError

from gold_digger.database.db_model import ExchangeRate


class DaoExchangeRate:
    def __init__(self, db_session):
        self.db_session = db_session

    def insert_exchange_rate_to_db(self, records):
        """
        It would be much faster to call session.bulk_insert_mappings(ExchangeRate, records)
        but we have to handle IntegrityError because API requests can perform rate update;
        so in the case of explicit update some rates could be already in database and they
        can also come at random times while updating explicitly.
        """
        for record in records:
            try:
                self.db_session.add(ExchangeRate(**record))
                self.db_session.flush()
            except IntegrityError:
                self.db_session.rollback()
        self.db_session.commit()

    def get_rates_by_date_currency(self, date_of_exchange, currency):
        return self.db_session.query(ExchangeRate).filter(
            and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency)
        ).all()

    def get_rate_by_date_currency_provider(self, date_of_exchange, currency, provider_name):
        return self.db_session.query(ExchangeRate).filter(
            and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency, ExchangeRate.provider.has(name=provider_name))
        ).first()

    def insert_new_rate(self, date_of_exchange, db_provider, currency, rate):
        """
        Insert new exchange rate for the specified date by specified provider.
        Date, currency and provider must be unique, therefore if record is already in database return it (without any update or insert)
        """
        db_record = ExchangeRate(date=date_of_exchange, provider_id=db_provider.id, currency=currency, rate=rate)
        try:
            self.db_session.add(db_record)
            self.db_session.commit()
        except IntegrityError:  # rate for this currency, date and provider is already in database
            db_record = self.get_rate_by_date_currency_provider(date_of_exchange, currency, db_provider.name)
        return db_record

    def get_sum_of_rates_in_period(self, start_date, end_date, currency):
        """
        SELECT provider_id, count(*), SUM(rate) FROM "USD_exchange_rates" WHERE date >= '%Y-%m-%d' AND date <= '%Y-%m-%d' GROUP BY provider_id
        """
        return self.db_session.query(ExchangeRate.provider_id, func.count(), func.sum(ExchangeRate.rate)).filter(
            and_(ExchangeRate.date >= start_date, ExchangeRate.date <= end_date, ExchangeRate.currency == currency, ExchangeRate.rate.isnot(None))
        ).group_by(ExchangeRate.provider_id).all()
