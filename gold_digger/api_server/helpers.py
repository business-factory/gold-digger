# -*- coding: utf-8 -*-

import json
from functools import wraps
from time import time

import falcon

from ..di import DiContainer


class ContextMiddleware:
    def process_resource(self, req, *_):
        req.context["flow_id"] = DiContainer.flow_id()


def http_api_logger(func):
    """
    :type func: types.FunctionType
    :rtype: types.FunctionType
    """
    @wraps(func)
    def wrapper(object, req, resp, *args, **kwargs):
        """
        :type object: object
        :type req: falcon.request.Request
        :type resp: falcon.request.Response
        """
        start = time()

        logger = DiContainer.logger(flow_id=req.context["flow_id"])
        logger.info("Received API request %s.", func.__name__, extra={
            "request_method": req.method,
            "request_url": req.url,
            "request_user_agent": req.user_agent,
            "request_referer": req.referer,
            "request_func": func.__name__,
        })

        try:
            func(object, req, resp, *args, logger=logger, **kwargs)
            logger.info("Completed API request %s.", func.__name__, extra={
                "request_method": req.method,
                "request_url": req.url,
                "request_func": func.__name__,
                "request_user_agent": req.user_agent,
                "request_referer": req.referer,
                "duration_in_secs": time() - start,
            })

        except Exception:
            logger.exception("Exception raised on API request %s.", func.__name__, extra={
                "request_method": req.method,
                "request_url": req.url,
                "request_func": func.__name__,
                "request_user_agent": req.user_agent,
                "request_referer": req.referer,
                "duration_in_secs": time() - start,
            })

            resp.status = falcon.HTTP_500
            resp.body = json.dumps(
                {
                    "error":
                        "Unexpected error. If the problem persists contact our support with trace ID 'golddigger." + logger.extra["flow_id"] + "' please."
                }
            )

    return wrapper
