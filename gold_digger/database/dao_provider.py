# -*- coding: utf-8 -*-

from gold_digger.database.db_model import Provider


class DaoProvider:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_or_create_provider_by_name(self, name):
        """
        :type name: str
        :rtype: Provider
        """

        provider = self.db_session.query(Provider).filter(Provider.name == name).first()

        if not provider:
            provider = Provider(name=name)
            self.db_session.add(provider)
            self.db_session.commit()

        return provider
