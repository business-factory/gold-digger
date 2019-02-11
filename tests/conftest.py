# -*- coding: utf-8 -*-

import logging

import pytest


def pytest_addoption(parser):
    parser.addoption("--database-tests", action="store_true", help="Run database tests on real temporary database")
    parser.addoption("--db-connection", action="store", help="Database connection string")


@pytest.fixture(scope="module")
def db_connection_string(request):
    cmd = request.config.getoption("--db-connection")
    return cmd if cmd else "postgres://postgres:postgres@localhost/gold-digger-test"


@pytest.fixture
def logger():
    return logging.getLogger("gold-digger.tests")


@pytest.fixture
def base_currency():
    return "USD"


@pytest.fixture
def currencies():
    return {"USD", "EUR", "CZK", "GBP"}
