# -*- coding: utf-8 -*-
"""
Related article: https://sebest.github.io/post/protips-using-gunicorn-inside-a-docker-image/

Parameters you might want to override:
  GUNICORN_WORKERS=4
  GUNICORN_BIND="0.0.0.0:8000"
"""

import os
import sys


sys.path.append(".")

timeout = 300  # 5 minutes in seconds
bind = "0.0.0.0:8000"
workers = 4

# Overwrite some Gunicorns params by ENV variables
for k, v in os.environ.items():
    if k.startswith("GUNICORN_"):
        key = k.split('_', 1)[1].lower()
        locals()[key] = v
