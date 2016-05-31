# -*- coding: utf-8 -*-
from datetime import timedelta
from decimal import Decimal


class ExchangeRateManager:
    def __init__(self, dao_exchange_rate, dao_provider, data_providers, supported_currencies, logger):
        self.dao_exchange_rate = dao_exchange_rate
        self.dao_provider = dao_provider
        self.data_providers = data_providers
        self.supported_currencies = supported_currencies
        self.logger = logger

    @staticmethod
    def get_percent_change(today_rate, yesterday_rate):
        """
        Check change of new number against another in percents.
        http://www.skillsyouneed.com/num/percent-change.html
        """
        return abs((today_rate - yesterday_rate) / yesterday_rate * 100)

    def compute_change_in_percents(self, today_records, date_of_exchange, provider_id):
        """
        Compute change in percents for today rates against rates from yesterday.
        """
        yesterday_records = self.dao_exchange_rate.get_all_currencies_by_provider_and_date(provider_id, date_of_exchange - timedelta(days=1))
        yesterday_records = {r.currency: r for r in yesterday_records}

        for record in today_records:
            yesterday_record = yesterday_records.get(record["currency"])
            if yesterday_record:
                record["change_in_percents"] = self.get_percent_change(record["rate"], yesterday_record.rate)

    def compute_change_in_percents_for_one_rate(self, today_rate, currency, date_of_exchange, provider_id):
        """
        Compute change in percents for today rate against rate from yesterday.
        """
        yesterday_record = self.dao_exchange_rate.get_rate_by_date_currency_provider_id(provider_id, date_of_exchange - timedelta(days=1), currency)
        if yesterday_record:
            return self.get_percent_change(today_rate, yesterday_record.rate)

    def update_all_rates_by_date(self, date_of_exchange):
        for data_provider in self.data_providers:
            self.logger.info("Updating all today rates from %s provider" % data_provider)
            day_rates = data_provider.get_all_by_date(date_of_exchange, self.supported_currencies)
            if day_rates:
                provider = self.dao_provider.get_or_create_provider_by_name(data_provider.name)
                records = [
                    dict(currency=currency, rate=rate, date=date_of_exchange, provider_id=provider.id) for currency, rate in day_rates.items()
                ]
                self.compute_change_in_percents(records, date_of_exchange, provider.id)
                self.dao_exchange_rate.insert_exchange_rate_to_db(records)

    def update_all_historical_rates(self, origin_date):
        for data_provider in self.data_providers:
            self.logger.info("Updating all historical rates from %s provider" % data_provider)
            date_rates = data_provider.get_historical(origin_date, self.supported_currencies)
            provider = self.dao_provider.get_or_create_provider_by_name(data_provider.name)
            for day, day_rates in date_rates.items():
                records = [
                    dict(currency=currency, rate=rate, date=day, provider_id=provider.id) for currency, rate in day_rates.items()
                ]
                self.dao_exchange_rate.insert_exchange_rate_to_db(records)

    def get_or_update_rate_by_date(self, date_of_exchange, currency):
        """
        Get records of exchange rates for the date from all data providers.
        If rates are missing for the date from some providers request data only from these providers to update database.
        """
        exchange_rates = self.dao_exchange_rate.get_rates_by_date_currency(date_of_exchange, currency)
        exchange_rates_providers = set(r.provider.name for r in exchange_rates)
        missing_provider_rates = [provider for provider in self.data_providers if provider.name not in exchange_rates_providers]
        for data_provider in missing_provider_rates:
            rate = data_provider.get_by_date(date_of_exchange, currency)
            if rate:
                db_provider = self.dao_provider.get_or_create_provider_by_name(data_provider.name)
                change_in_percents = self.compute_change_in_percents_for_one_rate(rate, currency, date_of_exchange, db_provider.id)
                exchange_rate = self.dao_exchange_rate.insert_new_rate(date_of_exchange, db_provider, currency, rate, change_in_percents)
                exchange_rates.append(exchange_rate)
        return exchange_rates

    def get_exchange_rate_by_date(self, date_of_exchange, from_currency, to_currency):
        """
        Compute exchange rate between 'from_currency' and 'to_currency'.
        If the date is missing request data providers to update database.
        """
        _from_currency = self.get_or_update_rate_by_date(date_of_exchange, from_currency)
        _to_currency = self.get_or_update_rate_by_date(date_of_exchange, to_currency)
        for from_, to_ in zip(_from_currency, _to_currency):
            if from_.rate and to_.rate:
                conversion = 1 / from_.rate
                return Decimal(to_.rate * conversion)

    def get_average_exchange_rate_by_dates(self, start_date, end_date, from_currency, to_currency):
        """
        Compute average exchange rate of currency in specified period.
        Log warnings for missing days.
        """
        number_of_days = abs((end_date - start_date).days) + 1  # we want interval <start_date, end_date>
        _from_currency = self.dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, from_currency)
        _to_currency = self.dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, to_currency)

        for (from_provider, from_count, from_sum), (to_provider, to_count, to_sum) in zip(_from_currency, _to_currency):

            self.logger.info("Sum of currencies %s (%s records) = %s, %s (%s records) = %s in period %s - %s by (%s, %s)" %
                             (from_currency, from_count, from_sum, to_currency, to_count, to_sum, start_date, end_date, from_provider,
                              to_provider))
            if from_count != number_of_days:
                self.logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                                    (from_provider, number_of_days - from_count, from_currency, start_date, end_date))
            if to_count != number_of_days:
                self.logger.warning("Provider %s miss %s days with currency %s while range request on %s - %s" %
                                    (to_provider, number_of_days - to_count, to_currency, start_date, end_date))

            if from_count and from_sum and to_count and to_sum:
                from_average = from_sum / from_count
                to_average = to_sum / to_count
                conversion = 1 / from_average
                return Decimal(to_average * conversion)
            self.logger.error("Date range 'count' and/or 'sum' are empty")

        self.logger.debug("Range request failed: from %s to %s" % (_from_currency, _to_currency))
