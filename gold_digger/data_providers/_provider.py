# -*- coding: utf-8 -*-

import requests
import requests.exceptions

from abc import ABCMeta, abstractmethod
from decimal import Decimal, InvalidOperation


class Provider(metaclass=ABCMeta):
    DEFAULT_REQUEST_TIMEOUT = 15  # 15 seconds for both connect & read timeouts

    def __init__(self, logger):
        self.logger = logger

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_supported_currencies(self, date_of_exchange):
        pass

    @abstractmethod
    def get_by_date(self, date_of_exchange, currency):
        pass

    @abstractmethod
    def get_all_by_date(self, date_of_exchange, currencies):
        pass

    @abstractmethod
    def get_historical(self, origin_date, currencies):
        pass

    def _get(self, url, params=None):
        try:
            response = requests.get(url, params=params, timeout=self.DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            else:
                self.logger.error("%s - status code: %s, URL: %s, Params: %s", self, response.status_code, url, params)
        except requests.exceptions.RequestException as e:
            self.logger.error("%s - exception: %s, URL: %s, Params: %s", self, e, url, params)

    def _post(self, url, params=None):
        try:
            response = requests.post(url, params=params, timeout=self.DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            else:
                self.logger.error("%s - status code: %s, URL: %s, Params: %s", self, response.status_code, url, params)
        except requests.exceptions.RequestException as e:
            self.logger.error("%s - exception: %s, URL: %s, Params: %s", self, e, url, params)

    def _to_decimal(self, value, currency=None):
        try:
            return Decimal(value)
        except InvalidOperation:
            self.logger.error("%s - Invalid operation: value %s is not a number (currency %s)", self, value, currency)
