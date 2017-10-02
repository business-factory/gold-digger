# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal
from itertools import combinations
from collections import defaultdict, Counter


class ExchangeRateManager:
    def __init__(self, dao_exchange_rate, dao_provider, data_providers, supported_currencies, logger):
        """
        :type dao_exchange_rate: gold_digger.database.DaoExchangeRate
        :type dao_provider: gold_digger.database.DaoProvider
        :type data_providers: list[gold_digger.data_providers._provider.Provider]
        :type supported_currencies: set[str]
        :type logger: logging.Logger
        """
        self._dao_exchange_rate = dao_exchange_rate
        self._dao_provider = dao_provider
        self._data_providers = data_providers
        self._supported_currencies = supported_currencies
        self._logger = logger

    def update_all_rates_by_date(self, date_of_exchange):
        """
        :type date_of_exchange: datetime.date
        """
        for data_provider in self._data_providers:
            try:
                self._logger.info("Updating all today rates from %s provider" % data_provider)
                day_rates = data_provider.get_all_by_date(date_of_exchange, self._supported_currencies)
                if day_rates:
                    provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
                    records = [dict(currency=currency, rate=rate, date=date_of_exchange, provider_id=provider.id) for currency, rate in
                               day_rates.items()]
                    self._dao_exchange_rate.insert_exchange_rate_to_db(records)
            except Exception:
                self._logger.exception("Updating of all today rates from %s provider failed.")

    def update_all_historical_rates(self, origin_date):
        """
        :type origin_date: datetime.date
        """
        for data_provider in self._data_providers:
            self._logger.info("Updating all historical rates from %s provider" % data_provider)
            date_rates = data_provider.get_historical(origin_date, self._supported_currencies)
            provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
            for day, day_rates in date_rates.items():
                records = [dict(currency=currency, rate=rate, date=day, provider_id=provider.id) for currency, rate in day_rates.items()]
                self._dao_exchange_rate.insert_exchange_rate_to_db(records)

    def get_or_update_rate_by_date(self, date_of_exchange, currency):
        """
        Get records of exchange rates for the date from all data providers.
        If rates are missing for the date from some providers request data only from these providers to update database.

        :type date_of_exchange: datetime.date
        :type currency: str
        :rtype: list[gold_digger.database.db_model.ExchangeRate]
        """
        today = date.today()
        exchange_rates = self._dao_exchange_rate.get_rates_by_date_currency(date_of_exchange, currency)
        exchange_rates_providers = set(r.provider.name for r in exchange_rates)
        missing_provider_rates = [provider for provider in self._data_providers if provider.name not in exchange_rates_providers]
        for data_provider in missing_provider_rates:
            if currency not in data_provider.get_supported_currencies(today):
                continue
            rate = data_provider.get_by_date(date_of_exchange, currency)
            if rate:
                db_provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
                exchange_rate = self._dao_exchange_rate.insert_new_rate(date_of_exchange, db_provider, currency, rate)
                exchange_rates.append(exchange_rate)
        return exchange_rates

    @staticmethod
    def pick_the_best(rates_records):
        """
        Compare rates to each other and group then by absolute difference.
        If there is group with minimal difference of two rates, choose one of them according the order of providers.
        If there is group with minimal difference with more than two rates, choose rate in the middle / aka most common rate in the list.

        :type rates_records: list[gold_digger.database.db_model.ExchangeRate]
        :rtype: gold_digger.database.db_model.ExchangeRate
        """
        if len(rates_records) in (1, 2):
            return rates_records[0]

        differences = defaultdict(list)
        for a, b in combinations(rates_records, 2):
            differences[abs(a.rate - b.rate)].extend((a, b))  # if (a,b)=1 and (b,c)=1 then differences[1]=[a,b,b,c]

        minimal_difference, rates = min(differences.items())
        if len(rates) == 2:
            return rates[0]
        else:
            return Counter(rates).most_common(1)[0][0]  # [(ExchangeRate, occurrences)]

    def future_date_to_today(self, date_of_exchange):
        """
        :type date_of_exchange: datetime.date
        :rtype: datetime.date
        """
        today = date.today()
        if date_of_exchange > today:
            self._logger.warning("Request for future date %s. Exchange rate of today will be returned instead.", date_of_exchange)
            return today
        return date_of_exchange

    def get_exchange_rate_by_date(self, date_of_exchange, from_currency, to_currency):
        """
        Compute exchange rate between 'from_currency' and 'to_currency'.
        If the date is missing request data providers to update database.

        :type date_of_exchange: datetime.date
        :type from_currency: str
        :type to_currency: str
        :rtype: Decimal
        """
        date_of_exchange = self.future_date_to_today(date_of_exchange)

        _from_currency_all_available = self.get_or_update_rate_by_date(date_of_exchange, from_currency)
        _to_currency_all_available = self.get_or_update_rate_by_date(date_of_exchange, to_currency)

        _from_currency = self.pick_the_best(_from_currency_all_available)
        _to_currency = self.pick_the_best(_to_currency_all_available)

        self._logger.debug("Pick best rate for %s: %s of [%s]",
                           from_currency, _from_currency.rate, ", ".join(str(r.rate) for r in _from_currency_all_available))
        self._logger.debug("Pick best rate for %s: %s of [%s]",
                           to_currency, _to_currency.rate, ", ".join(str(r.rate) for r in _to_currency_all_available))

        conversion = 1 / _from_currency.rate
        return Decimal(_to_currency.rate * conversion)

    def get_average_exchange_rate_by_dates(self, start_date, end_date, from_currency, to_currency):
        """
        Compute average exchange rate of currency in specified period.
        Log warnings for missing days.

        :type start_date: datetime.date
        :type end_date: datetime.date
        :type from_currency: str
        :type to_currency: str
        :rtype: Decimal
        """
        today_or_past_date = self.future_date_to_today(start_date)
        if today_or_past_date != start_date:
            return self.get_exchange_rate_by_date(today_or_past_date, from_currency, to_currency)

        number_of_days = abs((end_date - start_date).days) + 1  # we want interval <start_date, end_date>
        _from_currency = self._dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, from_currency)
        _to_currency = self._dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, to_currency)

        for (from_provider, from_count, from_sum), (to_provider, to_count, to_sum) in zip(_from_currency, _to_currency):

            self._logger.info("Sum of currencies %s (%s records) = %s, %s (%s records) = %s in period %s - %s by (%s, %s)" %
                              (from_currency, from_count, from_sum, to_currency, to_count, to_sum, start_date, end_date, from_provider,
                              to_provider))
            if from_count != number_of_days:
                self._logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                                     (from_provider, number_of_days - from_count, from_currency, start_date, end_date))
            if to_count != number_of_days:
                self._logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                                     (to_provider, number_of_days - to_count, to_currency, start_date, end_date))

            if from_count and from_sum and to_count and to_sum:
                from_average = from_sum / from_count
                to_average = to_sum / to_count
                conversion = 1 / from_average
                return Decimal(to_average * conversion)
            self._logger.error("Date range 'count' and/or 'sum' are empty")

        self._logger.debug("Range request failed: from %s to %s" % (_from_currency, _to_currency))
