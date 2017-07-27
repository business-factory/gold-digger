# -*- coding: utf-8 -*-

import requests
import requests.exceptions

from abc import ABCMeta, abstractmethod
from decimal import Decimal, InvalidOperation


class Provider(metaclass=ABCMeta):
    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def get_by_date(self, date_of_exchange, currency):
        pass

    @abstractmethod
    def get_all_by_date(self, date_of_exchange, currencies):
        pass

    @abstractmethod
    def get_historical(self, origin_date, currencies):
        pass

    def _get(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            else:
                self.logger.error("%s get %s status code on %s" % (self, response.status_code, url))
        except requests.exceptions.RequestException as e:
            self.logger.error("%s get %s exception on %s" % (self, e, url))

    def _post(self, url, **kwargs):
        try:
            response = requests.post(url, **kwargs)
            if response.status_code == 200:
                return response
            else:
                self.logger.error("%s get %s status code on %s" % (self, response.status_code, url))
        except requests.exceptions.RequestException as e:
            self.logger.error("%s get %s exception on %s" % (self, e, url))

    def _to_decimal(self, value, currency=""):
        try:
            return Decimal(value)
        except InvalidOperation:
            self.logger.error("%s - Invalid operation: value %s is not a number (currency %s)" % (self, value, currency))
