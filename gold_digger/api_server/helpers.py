# -*- coding: utf-8 -*-

from ..di import DiContainer


class ContextMiddleware:
    def process_resource(self, req, *_):
        req.context["flow_id"] = DiContainer.flow_id()
