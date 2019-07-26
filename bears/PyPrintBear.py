# -*- coding: utf-8 -*-

import logging
import re

from coalib.bears.LocalBear import LocalBear


class PyPrintBear(LocalBear):
    LANGUAGES = {"Python"}
    _PRINT_REGEX = re.compile(r"\bp?print\(")

    def run(self, filename, file):
        """
        Find prints in source code.

        :type filename: str
        :type file: tuple
        :rtype: types.GeneratorType
        """
        logging.debug("PyPrintBear checking file %s.", filename)
        yield from self._find_prints_in_file(filename, file)

    def _find_prints_in_file(self, filename, file):
        """
        :type filename: str
        :type file: tuple
        :rtype: types.GeneratorType
        """
        for line_number, line in enumerate(file, start=1):
            if self._PRINT_REGEX.search(line):
                yield self.new_result(message="Print found in file.", file=filename, line=line_number)
