# -*- coding: utf-8 -*-

import pytest

from gold_digger.data_providers import Google, Yahoo


@pytest.fixture
def google(base_currency, logger):
    return Google(base_currency, logger)


@pytest.fixture
def yahoo(currencies, base_currency, logger):
    return Yahoo(currencies, base_currency, logger)