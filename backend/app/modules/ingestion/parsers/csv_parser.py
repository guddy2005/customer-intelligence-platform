import csv
import io
from typing import Generator, Dict, Any
from backend.app.modules.ingestion.parsers.base import BaseParser


class CSVParser(BaseParser):
    def parse(self, file_content: str) -> Generator[Dict[str, Any], None, None]:
        """
        Parses raw CSV text line-by-line yielding sanitized dicts.
        """
        # Handle UTF-8 BOM if present
        if file_content.startswith("\ufeff"):
            file_content = file_content[1:]

        stream = io.StringIO(file_content)
        reader = csv.DictReader(stream)

        if not reader.fieldnames:
            return

        for row in reader:
            # Strip key and value whitespace
            clean_row = {}
            for k, v in row.items():
                if k is not None:
                    clean_row[k.strip()] = v.strip() if isinstance(v, str) else v
            yield clean_row
