# -*- coding: utf-8 -*-

import graypy
import logging
import collections
from os.path import dirname, normpath, abspath
from cached_property import cached_property as service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from ..data_providers import *
from ..database.dao_provider import DaoProvider
from ..database.dao_exchange_rate import DaoExchangeRate
from ..managers.exchange_rate_manager import ExchangeRateManager


class DiContainer:
    def __init__(self, main_file_path, *params_set):
        self._file_path = normpath(abspath(main_file_path))

        self._db_connection = None
        self._db_session = None

        self._params = {}
        for params in params_set:
            self._params = self._merge_params(self._params, params)

        self._logger = logging.getLogger("gold-digger")
        self.setup_logger(self._logger)

    def _merge_params(self, dest, src):
        for key, value in src.items():
            if isinstance(value, collections.Mapping):
                nested_params = dest.get(key, {})
                value = self._merge_params(nested_params, value)
            elif isinstance(value, str):
                value = value.format(base_dir=self.base_dir)

            dest[key] = value

        return dest

    def __getitem__(self, item):
        return self._params.get(item)

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
        self._db_connection = create_engine("{dialect}://{user}:{pass}@{host}:{port}/{name}".format(**self["database"]))
        return self._db_connection

    @service
    def db_session(self):
        self._db_session = scoped_session(sessionmaker(self.db_connection))
        return self._db_session()

    @service
    def data_providers(self):
        return GrandTrunk(self.logger), CurrencyLayer(self.logger), Yahoo(self.logger)

    @service
    def exchange_rate_manager(self):
        return ExchangeRateManager(
            DaoExchangeRate(self.db_session),
            DaoProvider(self.db_session),
            self.data_providers,
            self["supported_currencies"],
            self.logger
        )

    @service
    def logger(self):
        return self._logger

    def setup_logger(self, logger, level=None):
        if isinstance(logger, str):
            logger = logging.getLogger(logger)

        if level is None:
            logger.setLevel(logging.DEBUG if self["development_mode"] else logging.INFO)
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

        if not self["development_mode"]:
            handler = graypy.GELFHandler(self["graylog"]["address"], self["graylog"]["port"])
            logger.addHandler(handler)

        return logger
