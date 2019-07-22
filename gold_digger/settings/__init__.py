# -*- coding: utf-8 -*-

from os import environ, path

from ._settings_default import *
from ..exceptions import ImproperlyConfigured

PROFILE = environ.get("GOLD_DIGGER_PROFILE", "local")

if PROFILE == "master":
    from ._settings_master import *
elif PROFILE == "local":
    try:
        from ._settings_local import *
    except ImportError:
        raise ImproperlyConfigured(
            f"Local configuration not found. Create file _settings_local.py in {path.abspath(path.join(__file__, path.pardir))} directory according to README."
        )
else:
    raise ValueError(f"Unsupported settings profile. Got: {PROFILE}. Use one of: master, staging, local.")
