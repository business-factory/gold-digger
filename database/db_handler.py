# -*- coding: utf-8 -*-
from database.db_model import ExchangeRate


def update_db(session, day, provider, rates):
    db_day = session.query(ExchangeRate).filter(ExchangeRate.date == day, ExchangeRate.provider == provider).first()
    if db_day:
        session.query(ExchangeRate).filter(ExchangeRate.date == db_day.date, ExchangeRate.provider == provider).update(rates)
    else:
        session.add(ExchangeRate(date=day, provider=provider, **rates))
    session.commit()
