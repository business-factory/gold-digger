import logging
import re
from enum import Enum

from coalib.bears.LocalBear import LocalBear
from coalib.results.Diff import Diff
from coalib.results.TextRange import TextRange


class ImportType(Enum):
    DEFAULT = "default"
    MULTI_LINE_SLASH = "multi_line_slash"
    MULTI_LINE_PARENTHESIS = "multi_line_parenthesis"


class PySortImportsBear(LocalBear):
    LANGUAGES = {"Python"}
    _LINE_IMPORTS_SPLIT = re.compile(r"\s*,\s+")

    def run(self, filename, file):
        """
        Sorts imports in source code.

        :type filename: str
        :type file: tuple
        :rtype: types.GeneratorType
        """
        logging.debug("PySortImportsBear checking imports order in file %s.", filename)

        import_groups = self._get_imports_from_file(file)
        group_diff = self._check_imports_group_order(import_groups, file)
        line_diff = self._check_imports_line_order([i for imports in import_groups for i in imports], file)

        for diff in [group_diff, line_diff]:
            additions, deletions = diff.stats()
            if additions or deletions:
                yield self.new_result(
                    message="Import sort error.",
                    diffs={filename: diff},
                    file=filename
                )

    @staticmethod
    def _get_imports_from_file(file):
        """
        Returns a list of lists of tuples containing imports from file.
        Inner lists are import groups separated by lines not starting with from/import keyword.
        Each tuple contains import itself, start line number of import and end line number

        :type file: tuple
        :rtype: list[list[tuple[str, int, int]]]
        """
        imports = []
        import_groups = [imports]
        import_type = ImportType.DEFAULT
        multi_line_import_start = 0
        multi_line_import_parts = []

        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if import_type == ImportType.DEFAULT:
                if line.startswith(("from ", "import ")):
                    if not line.endswith(("(", "\\")):
                        imports.append((line, line_number, line_number))
                        continue

                    multi_line_import_parts.append(line[:-1].rstrip())
                    multi_line_import_start = line_number
                    import_type = ImportType.MULTI_LINE_PARENTHESIS if line.endswith("(") else ImportType.MULTI_LINE_SLASH
                elif imports:
                    imports = []
                    import_groups.append(imports)
            else:
                if import_type == ImportType.MULTI_LINE_PARENTHESIS and not line.endswith(")"):
                    multi_line_import_parts.append(line)
                elif import_type == ImportType.MULTI_LINE_SLASH and line.endswith("\\"):
                    multi_line_import_parts.append(line[:-1].rstrip())
                else:
                    if import_type == ImportType.MULTI_LINE_PARENTHESIS:
                        line = line[:-1].rstrip()

                    multi_line_import_parts.append(line)
                    imports.append((" ".join(p for p in multi_line_import_parts if p), multi_line_import_start, line_number))
                    multi_line_import_parts = []
                    import_type = ImportType.DEFAULT

        return import_groups

    @staticmethod
    def _check_imports_group_order(import_groups, file):
        """
        Check order of imports in line and returns diff of expected changes.

        :type import_groups: list[list[tuple[str, int, int]]]
        :type file: tuple
        :rtype: coalib.results.Diff.Diff
        """
        def sort_func(item):
            full_import_ = item[0]
            # `import` keyword has priority over `from` keyword
            prefer_import = full_import_.startswith("from")
            module_path = full_import_.split(" ", 3)[1]
            stripped_module_path = module_path.lstrip(".")
            # number of dots determines priority (absolute path over relative path and closer relative path over further relative path)
            relative_level = len(module_path) - len(stripped_module_path)
            return prefer_import, relative_level, stripped_module_path

        diff = Diff(file)
        for imports in import_groups:
            sorted_imports = sorted(imports, key=sort_func)
            if imports == sorted_imports:
                continue

            for (full_import, import_start, import_end), (sorted_full_import, _, _) in zip(imports, sorted_imports):
                if full_import != sorted_full_import:
                    text_range = TextRange.from_values(import_start, 1, import_end, len(full_import) + 1)
                    diff.replace(text_range, sorted_full_import)

        return diff

    @classmethod
    def _check_imports_line_order(cls, imports, file):
        """
        Check order of imports in line and returns diff of expected changes.

        :type imports: list[tuple[str, int, int]]
        :type file: tuple
        :rtype: coalib.results.Diff.Diff
        """
        diff = Diff(file)
        for full_import, import_start, import_end in imports:
            if full_import.startswith("import"):
                continue
            import_parts = full_import.split(" ", 3)
            current_order = cls._LINE_IMPORTS_SPLIT.split(import_parts[3].strip())
            expected_order = sorted(current_order)
            if current_order != expected_order:
                text_range = TextRange.from_values(import_start, 1, import_end, len(full_import) + 1)
                diff.replace(text_range, " ".join(import_parts[:3]) + " " + ", ".join(expected_order))

        return diff
