# -*- coding: utf-8 -*-

import pytest

from gold_digger.data_providers import Google, Yahoo


@pytest.fixture
def google(base_currency, logger):
    return Google(base_currency, logger)


@pytest.fixture
def yahoo(base_currency, currencies, logger):
    return Yahoo(base_currency, currencies, logger)
