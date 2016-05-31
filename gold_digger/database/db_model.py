# -*- coding: utf-8 -*-
from sqlalchemy import UniqueConstraint, Column, Date, String, DECIMAL, Integer, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Provider(Base):
    __tablename__ = "provider"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    rates = relationship("ExchangeRate", backref="provider", cascade_backrefs=False, cascade="merge,expunge")


class ExchangeRate(Base):
    __tablename__ = "USD_exchange_rates"
    __table_args__ = (
        UniqueConstraint("date", "provider_id", "currency"),
    )

    id = Column(BigInteger, primary_key=True)
    date = Column(Date)
    provider_id = Column(Integer, ForeignKey("provider.id"))
    currency = Column(String, nullable=False)
    rate = Column(DECIMAL)
    change_in_percents = Column(DECIMAL)
