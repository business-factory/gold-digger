# -*- coding: utf-8 -*-

import logging


class IncludeFilter:
    """
    The same as `logging.Filter` class. It is used for filtering logs which are interesting for us,
    i.e. log name has to match at least one provided logging facility.
    """

    _instance = None

    class __IncludeFilter:
        logger_names = tuple()

        def __init__(self, name=""):
            """
            :type name: str
            """
            if name:
                self.logger_names += (name,)

    def __init__(self, name=""):
        """
        :type name: str
        """
        if not IncludeFilter._instance:
            IncludeFilter._instance = self.__IncludeFilter(name)
        else:
            IncludeFilter._instance.logger_names += (name,)

    @staticmethod
    def filter(record):
        """
        :type record: logging.LogRecord
        :rtype: bool
        """
        # by default all records are processed
        if not IncludeFilter._instance.logger_names:
            return True

        # if logger is not created by GoldDigger app we want to see only >=warnings logs
        if not record.name.startswith(IncludeFilter._instance.logger_names):
            return record.levelno >= logging.WARNING

        # record is from GoldDigger app
        return True
