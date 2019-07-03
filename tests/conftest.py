# -*- coding: utf-8 -*-

import logging

import pytest


rerun_started = False


def pytest_addoption(parser):
    parser.addoption("--database-tests", action="store_true", help="Run database tests on real temporary database")
    parser.addoption("--db-connection", action="store", help="Database connection string")


def pytest_deselected():
    """
    Called when --run-failed was issued
    """
    global rerun_started
    rerun_started = True


def pytest_collection_modifyitems(config, items):
    slow_marker = pytest.mark.skipif(not config.getoption("--database-tests") and not rerun_started, reason="need --database-tests option to run")

    for item in items:
        if "slow" in item.keywords:
            item.add_marker(slow_marker)


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
