# -*- coding: utf-8 -*-

from os import environ, path

from ._settings_default import *
from ..exceptions import ImproperlyConfigured


profile = environ.get("GOLD_DIGGER_PROFILE", "local")

if profile == "master":
    from ._settings_master import *
elif profile == "local":
    try:
        from ._settings_local import *
    except ImportError:
        raise ImproperlyConfigured(
            "Local configuration not found. Create file _settings_local.py in {} directory according to README.".format(
                path.abspath(path.join(__file__, path.pardir))
            )
        )
else:
    raise ValueError("Unsupported settings profile. Got: {}. Use one of: master, staging, local.".format(profile))
