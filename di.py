# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from params import DEFAULT_CONFIG_PARAMS


class DiContainer:

    def __init__(self):
        self.params = DEFAULT_CONFIG_PARAMS
        self._db_connection = None
        self._db_session = None

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
        self._db_connection = create_engine("postgres://gold-digger:digdig@localhost:5433/gold-digger")
        return self._db_connection

    @property
    def db_session(self):
        self._db_session = scoped_session(sessionmaker(self.db_connection))
        return self._db_session()
