# -*- coding: utf-8 -*-

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from itertools import combinations

from ..database.db_model import ExchangeRate


class ExchangeRateManager:
    def __init__(self, dao_exchange_rate, dao_provider, data_providers, base_currency, supported_currencies):
        """
        :type dao_exchange_rate: gold_digger.database.DaoExchangeRate
        :type dao_provider: gold_digger.database.DaoProvider
        :type data_providers: list[gold_digger.data_providers.Provider]
        :type base_currency: str
        :type supported_currencies: set[str]
        """
        self._dao_exchange_rate = dao_exchange_rate
        self._dao_provider = dao_provider
        self._data_providers = data_providers
        self._base_currency = base_currency
        self._supported_currencies = supported_currencies

    def update_all_rates_by_date(self, date_of_exchange, data_providers, logger):
        """
        :type date_of_exchange: datetime.date
        :type data_providers: list[gold_digger.data_providers.Provider]
        :type logger: gold_digger.utils.ContextLogger
        """
        for data_provider in data_providers:
            try:
                logger.info("Update started: Provider %s, date %s.", data_provider, date_of_exchange)
                day_rates = data_provider.get_all_by_date(date_of_exchange, self._supported_currencies, logger)
                if day_rates:
                    provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
                    records = [dict(currency=currency, rate=rate, date=date_of_exchange, provider_id=provider.id) for currency, rate in day_rates.items()]
                    self._dao_exchange_rate.insert_exchange_rate_to_db(records, logger)
                    logger.info("Update succeeded: Provider %s, date %s.", data_provider, date_of_exchange)
                else:
                    logger.error("Update failed: Provider %s did not return any exchange rates, date %s.", data_provider, date_of_exchange)
            except Exception:
                logger.exception("Update failed: Provider %s raised unexpected exception, date %s.", data_provider, date_of_exchange)

    def update_all_historical_rates(self, origin_date, logger):
        """
        :type origin_date: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        """
        for data_provider in self._data_providers:
            logger.info("Updating all historical rates from %s provider", data_provider)
            date_rates = data_provider.get_historical(origin_date, self._supported_currencies, logger)
            provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
            for day, day_rates in date_rates.items():
                records = [dict(currency=currency, rate=rate, date=day, provider_id=provider.id) for currency, rate in day_rates.items()]
                self._dao_exchange_rate.insert_exchange_rate_to_db(records, logger)

    def get_or_update_rate_by_date(self, date_of_exchange, currency, logger):
        """
        Get records of exchange rates for the date from all data providers.
        If rates are missing for the date from some providers request data only from these providers to update database.
        If the requested date is today and there are missing rates, try to fetch data from yesterday, if even those are missing, request for today's data.

        :type date_of_exchange: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: list[gold_digger.database.db_model.ExchangeRate]
        """
        if currency == self._base_currency:
            return [ExchangeRate.base(self._base_currency)]

        today = date.today()
        exchange_rates = self._dao_exchange_rate.get_rates_by_date_currency(date_of_exchange, currency)
        exchange_rates_providers = set(r.provider.name for r in exchange_rates)
        missing_provider_rates = [provider for provider in self._data_providers if provider.name not in exchange_rates_providers]
        for data_provider in missing_provider_rates:
            if date_of_exchange == today:
                logger.info("Today's rates for provider %s aren't ready yet, Using yesterday's rates.", data_provider.name)
                previous_day = date_of_exchange - timedelta(1)
                rate = self._dao_exchange_rate.get_rate_by_date_currency_provider(previous_day, currency, data_provider.name)
                if rate:
                    exchange_rates.append(rate)
                    continue
                else:
                    logger.info("Yesterday's rates for provider %s not found. Requesting API.", data_provider.name)
            elif data_provider.has_request_limit:
                #  For providers with request limit we don't want to request rates from API for historical data, because it can easily generate hundreds
                #  of requests at once and the limit is then soon exceeded.
                logger.info("Rates for provider %s aren't in database and provider has disabled requests for historical data.", data_provider.name)
                continue

            try:
                if currency not in data_provider.get_supported_currencies(today, logger):
                    continue
                rate = data_provider.get_by_date(date_of_exchange, currency, logger)
                if rate:
                    db_provider = self._dao_provider.get_or_create_provider_by_name(data_provider.name)
                    exchange_rate = self._dao_exchange_rate.insert_new_rate(date_of_exchange, db_provider, currency, rate)
                    exchange_rates.append(exchange_rate)

            except Exception:
                logger.exception("Requesting exchange rate for %s (%s) from provider '%s' failed.", currency, date_of_exchange, data_provider)

        return exchange_rates

    @staticmethod
    def pick_the_best(rates):
        """
        Compare rates to each other and group then by absolute difference.
        If there is group with minimal difference of two rates, choose one of them according the order of providers.
        If there is group with minimal difference with more than two rates, choose rate in the middle / aka most common rate in the list.

        :type rates: None | list[float | decimal.Decimal]
        :rtype: float | decimal.Decimal
        """
        if not rates:
            raise ValueError("Missing exchange rate.")

        if len(rates) in (1, 2):
            return rates[0]

        differences = defaultdict(list)
        for a, b in combinations(rates, 2):
            differences[abs(a - b)].extend((a, b))  # if (a,b)=1 and (b,c)=1 then differences[1]=[a,b,b,c]

        minimal_difference, rates = min(differences.items())
        if len(rates) == 2:
            return rates[0]
        else:
            return Counter(rates).most_common(1)[0][0]  # [(decimal.Decimal, occurrences)]

    @staticmethod
    def future_date_to_today(date_of_exchange, logger):
        """
        :type date_of_exchange: datetime.date
        :type logger: gold_digger.utils.ContextLogger
        :rtype: datetime.date
        """
        today = date.today()
        if date_of_exchange > today:
            logger.warning("Request for future date %s. Exchange rate of today will be returned instead.", date_of_exchange)
            return today
        return date_of_exchange

    def get_exchange_rate_by_date(self, date_of_exchange, from_currency, to_currency, logger):
        """
        Compute exchange rate between 'from_currency' and 'to_currency'.
        If the date is missing request data providers to update database.

        :type date_of_exchange: datetime.date
        :type from_currency: str
        :type to_currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: Decimal
        """
        date_of_exchange = self.future_date_to_today(date_of_exchange, logger)

        _from_currency_all_available = self.get_or_update_rate_by_date(date_of_exchange, from_currency, logger)
        _to_currency_all_available = self.get_or_update_rate_by_date(date_of_exchange, to_currency, logger)

        _from_currency_rates = [r.rate for r in _from_currency_all_available]
        _to_currency_rates = [r.rate for r in _to_currency_all_available]

        _from_currency = self.pick_the_best(_from_currency_rates)
        _to_currency = self.pick_the_best(_to_currency_rates)

        logger.debug("Pick best rate for %s: %s of [%s]", from_currency, _from_currency, ", ".join(map(str, _from_currency_rates)))
        logger.debug("Pick best rate for %s: %s of [%s]", to_currency, _to_currency, ", ".join(map(str, _to_currency_rates)))

        return Decimal(_to_currency / _from_currency)

    def get_exchange_rates_by_dates(self, start_date, end_date, from_currency, to_currency, logger):
        """
        Return exchange rate for each date in range.
        If one day is missing exchange rate, use average from yesterday and tomorrow date.
        If more days after each other are missing exchange rate, ignore them.

        :type start_date: datetime.date
        :type end_date: datetime.date
        :type from_currency: str
        :type to_currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: dict[str, str]
        """
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        if from_currency == to_currency:
            return {d.strftime(format="%Y-%m-%d"): "1.0" for d in dates}

        exchange_rates_by_dates = {}

        if from_currency == self._base_currency:
            db_rates_by_dates_for_from_currency = {d: [Decimal(1)] for d in dates}
        else:
            db_rates_by_dates_for_from_currency = self._dao_exchange_rate.get_rates_by_dates_for_currency_in_period(from_currency, start_date, end_date)

        if to_currency == self._base_currency:
            db_rates_by_dates_for_to_currency = {d: [Decimal(1)] for d in dates}
        else:
            db_rates_by_dates_for_to_currency = self._dao_exchange_rate.get_rates_by_dates_for_currency_in_period(to_currency, start_date, end_date)

        for date_ in dates:
            try:
                best_from_currency_rate = self._calculate_best_exchange_rate(db_rates_by_dates_for_from_currency, date_, from_currency, logger)
                best_to_currency_rate = self._calculate_best_exchange_rate(db_rates_by_dates_for_to_currency, date_, to_currency, logger)
            except ValueError:  # missing exchange rate for given date
                logger.warning("Could not determine exchange rate. Date: %s. From currency: %s. To currency: %s", date_, from_currency, to_currency)
                pass
            else:
                exchange_rates_by_dates[date_.strftime(format="%Y-%m-%d")] = str(best_to_currency_rate / best_from_currency_rate)

        return exchange_rates_by_dates

    def _calculate_best_exchange_rate(self, db_rates_by_dates_for_currency, date_, currency, logger):
        """
        :type db_rates_by_dates_for_currency: dict[datetime.date, list[decimal.Decimal]]
        :type date_: datetime.date
        :type currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: decimal.Decimal
        """
        db_rates = db_rates_by_dates_for_currency.get(date_)
        if db_rates:
            return self.pick_the_best(db_rates)

        yesterday_db_rates = db_rates_by_dates_for_currency.get(date_ - timedelta(days=1))
        tomorrow_db_rates = db_rates_by_dates_for_currency.get(date_ + timedelta(days=1))

        # raises ValueError if any rates are missing
        best_yesterday_rate = self.pick_the_best(yesterday_db_rates)
        best_tomorrow_rate = self.pick_the_best(tomorrow_db_rates)

        logger.warning("Using average of yesterday's and tomorrow's rate. Date: %s. Currency: %s.", date_, currency)

        # return average from yesterday and tomorrow rate
        return (best_yesterday_rate + best_tomorrow_rate) / 2

    def _get_sum_of_rates_in_period(self, start_date, end_date, currency):
        """
        :type start_date: datetime.date
        :type end_date: datetime.date
        :type currency: str
        :rtype: list[tuple[int, int, Decimal]]
        """
        if currency == self._base_currency:
            return [("BASE", 1, ExchangeRate.base(self._base_currency).rate), ]

        return self._dao_exchange_rate.get_sum_of_rates_in_period(start_date, end_date, currency)

    def get_average_exchange_rate_by_dates(self, start_date, end_date, from_currency, to_currency, logger):
        """
        Compute average exchange rate of currency in specified period.
        Log warnings for missing days.

        :type start_date: datetime.date
        :type end_date: datetime.date
        :type from_currency: str
        :type to_currency: str
        :type logger: gold_digger.utils.ContextLogger
        :rtype: Decimal
        """
        today_or_past_date = self.future_date_to_today(start_date, logger)
        if today_or_past_date != start_date:
            return self.get_exchange_rate_by_date(today_or_past_date, from_currency, to_currency, logger)

        number_of_days = abs((end_date - start_date).days) + 1  # we want interval <start_date, end_date>
        _from_currency = self._get_sum_of_rates_in_period(start_date, end_date, from_currency)
        _to_currency = self._get_sum_of_rates_in_period(start_date, end_date, to_currency)

        for (from_provider, from_count, from_sum), (to_provider, to_count, to_sum) in zip(_from_currency, _to_currency):

            logger.info(
                "Sum of currencies %s (%s records) = %s, %s (%s records) = %s in period %s - %s by (%s, %s)",
                from_currency, from_count, from_sum, to_currency, to_count, to_sum, start_date, end_date, from_provider, to_provider
            )
            if from_count != number_of_days and from_currency != self._base_currency:
                logger.warning(
                    "Provider %s is missing %s days with currency %s while range request on %s - %s",
                    from_provider, number_of_days - from_count, from_currency, start_date, end_date
                )
            if to_count != number_of_days and to_currency != self._base_currency:
                logger.warning(
                    "Provider %s is missing %s days with currency %s while range request on %s - %s",
                    to_provider, number_of_days - to_count, to_currency, start_date, end_date
                )

            if from_count and from_sum and to_count and to_sum:
                from_average = from_sum / from_count
                to_average = to_sum / to_count
                conversion = 1 / from_average
                return Decimal(to_average * conversion)

            logger.error("Date range 'count' and/or 'sum' are empty")

        logger.error("Range request failed: from %s to %s", from_currency, to_currency)
