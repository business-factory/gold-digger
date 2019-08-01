# -*- coding: utf-8 -*-

import logging
from functools import lru_cache
from os.path import abspath, dirname, normpath
from urllib.parse import quote
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
from .utils.custom_logging import IncludeFilter


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
        :type extra: None | dict
        :rtype: gold_digger.utils.ContextLogger
        """
        logger_ = cls.set_up_logger("gold-digger")
        logger_.setLevel(settings.LOGGING_LEVEL)

        extra_ = {"flow_id": cls.flow_id()}
        extra_.update(extra or {})

        return ContextLogger(logger_, extra_)

    @staticmethod
    @lru_cache(maxsize=None)
    def add_logger_to_root_filter(name):
        """
        :type name: str
        """
        IncludeFilter(name)

    @classmethod
    @lru_cache(maxsize=None)
    def set_up_logger(cls, name):
        """
        :type name: str
        :rtype: logging.Logger
        """
        logger_ = logging.getLogger(name)
        cls.add_logger_to_root_filter(name)

        return logger_

    @staticmethod
    @lru_cache(maxsize=1)
    def set_up_root_logger():
        """
        Function for setting root logger. Should be called only once.
        """
        logger_ = logging.getLogger()
        if settings.LOGGING_GRAYLOG_ENABLED:
            handler = graypy.GELFRabbitHandler(
                url=f"amqp://beaver:{quote(settings.LOGGING_AMQP_PASSWORD, safe='')}@{settings.LOGGING_AMQP_HOST}:{settings.LOGGING_AMQP_PORT}",
                exchange="golddigger-logs-exchange",
                exchange_type="direct",
                routing_key="golddigger-logs",
            )
            handler.setLevel(settings.LOGGING_LEVEL)
            handler.addFilter(IncludeFilter())
            logger_.addHandler(handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(settings.LOGGING_FORMAT, "%Y-%m-%d %H:%M:%S"))

        stream_handler.setLevel(settings.LOGGING_LEVEL)
        stream_handler.addFilter(IncludeFilter())

        logger_.addHandler(stream_handler)
