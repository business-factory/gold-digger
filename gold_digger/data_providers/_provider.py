# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from decimal import Decimal, InvalidOperation

import requests
import requests.exceptions


class Provider(metaclass=ABCMeta):
    DEFAULT_REQUEST_TIMEOUT = 15  # 15 seconds for both connect & read timeouts

    def __init__(self, base_currency):
        """
        :type base_currency: str
        """
        self._base_currency = base_currency

    @property
    def base_currency(self):
        return self._base_currency

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def get_supported_currencies(self, date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: set[str]
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: set[str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[date, dict[str, decimal.Decimal]]
        """
        raise NotImplementedError

    def _get(self, url, params=None, *, logger):
        """
        :type url: str
        :type params: dict[str, str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: requests.Response | None
        """
        try:
            response = requests.get(url, params=params, timeout=self.DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            else:
                logger.error("%s - status code: %s, URL: %s, Params: %s", self, response.status_code, url, params)
        except requests.exceptions.RequestException as e:
            logger.error("%s - exception: %s, URL: %s, Params: %s", self, e, url, params)

    def _post(self, url, headers=None, data=None, *, logger):
        """
        :type url: str
        :type headers: dict[str, str]
        :type data: dict[str, str]
        :type logger: gold_digger.utils.ContextLogger
        :rtype: requests.Response | None
        """
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response
            else:
                logger.error("%s - status code: %s, URL: %s, Headers: %s, Data: %s", self, response.status_code, url, headers, data)
        except requests.exceptions.RequestException as e:
            logger.error("%s - exception: %s, URL: %s, Headers: %s, Data: %s", self, e, url, headers, data)

    def _to_decimal(self, value, currency=None, *, logger):
        """
        :type value: str | float
        :type currency: str | None
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal | None
        """
        try:
            return Decimal(value)
        except InvalidOperation:
            logger.error("%s - Invalid operation: value %s is not a number (currency %s)", self, value, currency)
