# -*- coding: utf-8 -*-

from hashlib import md5
from logging import LoggerAdapter


class ContextLogger(LoggerAdapter):
    """
    Acts like logging.LoggerAdapter but instead of overwriting message extra
    it merges it together so that message extra has higher priority.
    """

    @property
    def flow_id(self):
        return self.extra.get("flow_id")

    def process(self, msg, kwargs):
        extra = self.extra.copy()
        extra.update(kwargs.get("extra") or {})
        extra["message_hash"] = md5(msg.encode("utf-8")).hexdigest()
        kwargs["extra"] = extra
        return msg, kwargs

    def with_context(self, **extra):
        extra_ = self.extra.copy()
        extra_.update(extra)
        return ContextLogger(self.logger, extra_)
