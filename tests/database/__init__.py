# -*- coding: utf-8 -*-

import pytest

database_test = pytest.mark.skipif(not pytest.config.getoption("--database-tests"), reason="need --database option to run")

