# -*- coding: utf-8 -*-

import requests
import requests.exceptions

from abc import ABCMeta, abstractmethod
from decimal import Decimal, InvalidOperation


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
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: set
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_date(self, date_of_exchange, currency, logger):
        """
        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: decimal.Decimal | None
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_by_date(self, date_of_exchange, currencies, logger):
        """
        :type date_of_exchange: datetime.date
        :type currencies: [str]
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical(self, origin_date, currencies, logger):
        """
        :type origin_date: datetime.date
        :type currencies: list[str]
        :type logger: gold_digger.utils.context_logger.ContextLogger
        :rtype: dict[str, decimal.Decimal | None]
        """
        raise NotImplementedError

    def _get(self, url, params=None, *, logger):
        """
        :type url: str
        :type params: dict[str, str]
        :type logger: gold_digger.utils.context_logger.ContextLogger
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

    @staticmethod
    def _to_decimal(value):
        """
        :type value: str
        :rtype: decimal.Decimal | None
        """
        if value is None:
            return None

        try:
            return Decimal(value)
        except InvalidOperation:
            return None
