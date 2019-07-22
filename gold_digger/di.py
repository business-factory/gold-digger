# -*- coding: utf-8 -*-

import logging
from functools import lru_cache
from os.path import abspath, dirname, normpath
from uuid import uuid4

import graypy
from cached_property import cached_property as service
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from . import settings
from .data_providers import *
from .database.dao_exchange_rate import DaoExchangeRate
from .database.dao_provider import DaoProvider
from .managers.exchange_rate_manager import ExchangeRateManager
from .utils import ContextLogger


class DiContainer:
    def __init__(self, main_file_path):
        self._file_path = normpath(abspath(main_file_path))

        self._db_connection = None
        self._db_session = None

    def __enter__(self):
        return self

    def __exit__(self, e, _, traceback):
        if self._db_session is not None:
            self._db_session.remove()
            self._db_session = None
        if self._db_connection is not None:
            self._db_connection.dispose()
            self._db_connection = None

    @staticmethod
    def flow_id():
        return str(uuid4())

    @service
    def base_dir(self):
        return dirname(self._file_path)

    @service
    def db_connection(self):
        self._db_connection = create_engine("{dialect}://{user}:{password}@{host}:{port}/{name}".format(
            dialect=settings.DATABASE_DIALECT,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            name=settings.DATABASE_NAME
        ))
        return self._db_connection

    @service
    def db_session(self):
        """
        :rtype: sqlalchemy.orm.Session
        """
        self._db_session = scoped_session(sessionmaker(self.db_connection))
        return self._db_session()

    @property
    def base_currency(self):
        return "USD"

    @service
    def data_providers(self):
        providers = (
            GrandTrunk(self.base_currency),
            CurrencyLayer(settings.SECRETS_CURRENCY_LAYER_ACCESS_KEY, self.logger(), self.base_currency),
            Yahoo(self.base_currency, settings.SUPPORTED_CURRENCIES),
            Fixer(settings.SECRETS_FIXER_ACCESS_KEY, self.logger(), self.base_currency),
            RatesAPI(self.base_currency),
        )
        return {provider.name: provider for provider in providers}

    @service
    def exchange_rate_manager(self):
        return ExchangeRateManager(
            DaoExchangeRate(self.db_session),
            DaoProvider(self.db_session),
            list(self.data_providers.values()),
            self.base_currency,
            settings.SUPPORTED_CURRENCIES,
        )

    @classmethod
    def logger(cls, **extra):
        """
        :rtype: gold_digger.utils.ContextLogger
        """
        logger_ = cls.setup_logger("gold-digger")

        extra_ = {"flow_id": cls.flow_id()}
        extra_.update(extra or {})

        return ContextLogger(logger_, extra_)

    @staticmethod
    @lru_cache(maxsize=None)
    def setup_logger(name="gold-digger"):
        """
        :type name: str
        :rtype: logging.Logger
        """
        logger_ = logging.getLogger(name)
        logger_.setLevel(logging.DEBUG)
        logger_.propagate = False

        if not settings.DEVELOPMENT_MODE:
            handler = graypy.GELFHandler(settings.GRAYLOG_ADDRESS, settings.GRAYLOG_PORT)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(levelname)s] %(asctime)s at %(filename)s:%(lineno)d (%(processName)s) -- %(message)s",
                "%Y-%m-%d %H:%M:%S"
            ))

        logger_.addHandler(handler)
        return logger_
