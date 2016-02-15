# -*- coding: utf-8 -*-

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from gold_digger.config.params import DEFAULT_CONFIG_PARAMS
from ..data_providers import *


class DiContainer:

    def __init__(self):
        self.params = DEFAULT_CONFIG_PARAMS
        self._db_connection = None
        self._db_session = None

        self._logger = logging.getLogger("gold-digger")
        self.setup_logger(self._logger)

    def __getitem__(self, item):
        return self.params.get(item)

    def __enter__(self):
        return self

    def __exit__(self, e, _, traceback):
        if self._db_session is not None:
            self._db_session.remove()
            self._db_session = None
        if self._db_connection is not None:
            self._db_connection.dispose()
            self._db_connection = None

    @property
    def db_connection(self):
        self._db_connection = create_engine("{dialect}://{user}:{pass}@{host}:{port}/{name}".format(**self["database"]))
        return self._db_connection

    @property
    def db_session(self):
        self._db_session = scoped_session(sessionmaker(self.db_connection))
        return self._db_session()

    @property
    def data_providers(self):
        return GrandTrunk(), CurrencyLayer(), Yahoo()

    @property
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
        return logger
