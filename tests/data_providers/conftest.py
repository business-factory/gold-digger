# -*- coding: utf-8 -*-

import pytest

from gold_digger.data_providers import Yahoo


@pytest.fixture
def yahoo(base_currency, currencies):
    return Yahoo(base_currency, currencies)
