# -*- coding: utf-8 -*-

import graypy
import logging
from os.path import dirname, normpath, abspath
from cached_property import cached_property as service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import gold_digger.settings as settings
from .data_providers import *
from .database.dao_exchange_rate import DaoExchangeRate
from .database.dao_provider import DaoProvider
from .managers.exchange_rate_manager import ExchangeRateManager


class DiContainer:
    def __init__(self, main_file_path):
        self._file_path = normpath(abspath(main_file_path))

        self._db_connection = None
        self._db_session = None

        self._logger = logging.getLogger("gold-digger")
        self.setup_logger(self._logger)

    def __enter__(self):
        return self

    def __exit__(self, e, _, traceback):
        if self._db_session is not None:
            self._db_session.remove()
            self._db_session = None
        if self._db_connection is not None:
            self._db_connection.dispose()
            self._db_connection = None

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
        self._db_session = scoped_session(sessionmaker(self.db_connection))
        return self._db_session()

    @property
    def base_currency(self):
        return "USD"

    @service
    def data_providers(self):
        return (
            GrandTrunk(self.base_currency, self.logger),
            CurrencyLayer(settings.SECRETS_CURRENCY_LAYER_ACCESS_KEY, self.base_currency, self.logger),
            Yahoo(self.base_currency, self.logger),
            Google(self.base_currency, self.logger),
            Fixer(self.base_currency, self.logger),
        )

    @service
    def exchange_rate_manager(self):
        return ExchangeRateManager(
            DaoExchangeRate(self.db_session, self.logger),
            DaoProvider(self.db_session),
            self.data_providers,
            self.base_currency,
            settings.SUPPORTED_CURRENCIES,
            self.logger
        )

    @service
    def logger(self):
        return self._logger

    def setup_logger(self, logger, level=None):
        if isinstance(logger, str):
            logger = logging.getLogger(logger)

        if level is None:
            logger.setLevel(logging.DEBUG if settings.DEVELOPMENT_MODE else logging.DEBUG)
        else:
            logger.setLevel(level)

        for handler in logging.root.handlers:
            handler.addFilter(logging.Filter("gold-digger"))

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(asctime)s at %(filename)s:%(lineno)d (%(processName)s) -- %(message)s",
            "%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)

        if not settings.DEVELOPMENT_MODE:
            handler = graypy.GELFHandler(settings.GRAYLOG_ADDRESS, settings.GRAYLOG_PORT)
            logger.addHandler(handler)

        return logger
