# -*- coding: utf-8 -*-

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import create_database, database_exists, drop_database

from gold_digger.database.db_model import Base


@pytest.fixture(scope="module")
def db_connection(db_connection_string):
    """
    Create one test database for all database tests.
    """
    engine = create_engine(db_connection_string)
    if not database_exists(engine.url):
        create_database(engine.url)
    connection = engine.connect()

    yield connection
    connection.close()
    engine.dispose()
    drop_database(engine.url)


@pytest.fixture()
def db_session(db_connection):
    """
    Drop and create all tables for every test, ie. every test starts with empty tables and new session.
    """
    db_connection.execute("DROP TABLE IF EXISTS statistics_base CASCADE")
    Base.metadata.drop_all(db_connection)
    Base.metadata.create_all(db_connection)
    session = scoped_session(sessionmaker(db_connection))

    yield session

    session.remove()
