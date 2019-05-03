# -*- coding: utf-8 -*-

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError

from .db_model import ExchangeRate


class DaoExchangeRate:
    def __init__(self, db_session):
        """
        :type db_session: sqlalchemy.orm.Session
        """
        self.db_session = db_session

    def insert_exchange_rate_to_db(self, records, logger):
        """
        It would be much faster to call session.bulk_insert_mappings(ExchangeRate, records)
        but we have to handle IntegrityError because API requests can perform rate update;
        so in the case of explicit update some rates could be already in database and they
        can also come at random times while updating explicitly.

        :type records: list[dict[str, decimal.Decimal | None | datetime.datetime | int]]
        :type logger: gold_digger.utils.ContextLogger
        """
        duplicates = set()
        for record in records:
            try:
                # TODO: use Postgres feature ON CONFLICT DO UPDATE instead of this
                self.db_session.add(ExchangeRate(**record))
                self.db_session.commit()
            except IntegrityError:
                self.db_session.rollback()
                duplicates.add(record["currency"])

        if duplicates:
            logger.info(
                "Exchange rates of following currencies were not updated because rates from this provider are already in DB. Currencies: %s", duplicates
            )

        self.db_session.commit()

    def get_rates_by_date_currency(self, date_of_exchange, currency):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :rtype: list[gold_digger.database.db_model.ExchangeRate]
        """
        return self.db_session.query(ExchangeRate).filter(
            and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency)
        ).all()

    def get_rate_by_date_currency_provider(self, date_of_exchange, currency, provider_name):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type provider_name: str
        :rtype: gold_digger.database.db_model.ExchangeRate
        """
        return self.db_session.query(ExchangeRate).filter(
            and_(ExchangeRate.date == date_of_exchange, ExchangeRate.currency == currency, ExchangeRate.provider.has(name=provider_name))
        ).first()

    def insert_new_rate(self, date_of_exchange, db_provider, currency, rate):
        """
        Insert new exchange rate for the specified date by specified provider.
        Date, currency and provider must be unique, therefore if record is already in database return it (without any update or insert)

        :type date_of_exchange: datetime.date
        :type db_provider: gold_digger.database.db_model.Provider
        :type currency: str
        :type rate: decimal.Decimal
        :rtype: gold_digger.database.db_model.ExchangeRate
        """
        db_record = ExchangeRate(date=date_of_exchange, provider_id=db_provider.id, currency=currency, rate=rate)
        try:
            self.db_session.add(db_record)
            self.db_session.commit()
        except IntegrityError:  # rate for this currency, date and provider is already in database
            self.db_session.rollback()
            db_record = self.get_rate_by_date_currency_provider(date_of_exchange, currency, db_provider.name)
        return db_record

    def get_sum_of_rates_in_period(self, start_date, end_date, currency):
        """
        SELECT provider_id, count(*), SUM(rate) FROM "USD_exchange_rates" WHERE date >= '%Y-%m-%d' AND date <= '%Y-%m-%d' GROUP BY provider_id

        :type start_date: datetime.date
        :type end_date: datetime.date
        :type currency: str
        :rtype: list[tuple[int, int, decimal.Decimal]]
        """
        return self.db_session\
            .query(ExchangeRate.provider_id, func.count(), func.sum(ExchangeRate.rate))\
            .filter(
                and_(ExchangeRate.date >= start_date,
                     ExchangeRate.date <= end_date,
                     ExchangeRate.currency == currency,
                     ExchangeRate.rate.isnot(None))
            )\
            .group_by(ExchangeRate.provider_id)\
            .order_by(ExchangeRate.provider_id)\
            .all()

    def get_rates_by_dates_for_currency_in_period(self, currency, start_date, end_date):
        """
        :type currency: str
        :type start_date: datetime.date
        :type end_date: datetime.date
        :rtype: dict[datetime.date, list[decimal.Decimal]]
        """
        result = self.db_session\
            .query(ExchangeRate.date, func.array_agg(ExchangeRate.rate))\
            .filter(
                and_(
                    ExchangeRate.date >= start_date,
                    ExchangeRate.date <= end_date,
                    ExchangeRate.currency == currency,
                    ExchangeRate.rate.isnot(None)
                )
            )\
            .group_by(ExchangeRate.date)\
            .order_by(ExchangeRate.date)\
            .all()

        return {r[0]: list(r[1]) for r in result}
