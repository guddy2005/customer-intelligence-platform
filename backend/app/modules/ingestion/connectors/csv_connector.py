import csv
import io
import os
import logging
from typing import List, Dict, Any, Optional, Iterator
from backend.app.modules.ingestion.connectors.base import (
    BaseConnector,
    ConnectorConnectionError,
    ConnectorFetchError,
    ConnectorDataError,
)

logger = logging.getLogger("csv_connector")


class CSVConnector(BaseConnector):
    """
    Modular connector for reading and parsing CSV datasets
    from local file paths or raw text/in-memory content.

    Supports two access patterns:
    - fetch()         → loads all rows into memory (for small structured files)
    - stream_batches(batch_size) → generator yielding rows in chunks (for large files)
    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[str] = None,
        source_name: str = "CSV_SOURCE"
    ):
        super().__init__(source_name=source_name)
        self.file_path = file_path
        self.file_content = file_content
        self._detected_encoding: str = "utf-8"

    def connect(self) -> bool:
        """
        Validates that either the file exists on the filesystem or raw content is provided.
        """
        if self.file_content is not None:
            self.is_connected = True
            return True

        if not self.file_path:
            raise ConnectorConnectionError("Neither file_path nor file_content was provided to CSVConnector.")

        if not os.path.exists(self.file_path):
            raise ConnectorConnectionError(
                f"CSV file not found at path: {self.file_path}",
                details={"file_path": self.file_path}
            )

        if not os.path.isfile(self.file_path):
            raise ConnectorConnectionError(
                f"Specified path is not a file: {self.file_path}",
                details={"file_path": self.file_path}
            )

        if not os.access(self.file_path, os.R_OK):
            raise ConnectorConnectionError(
                f"Cannot read CSV file: permission denied for {self.file_path}",
                details={"file_path": self.file_path}
            )

        self.is_connected = True
        return True

    def _open_file_stream(self):
        """
        Opens the CSV file as a text stream, detecting encoding.
        Returns an open file object — caller must close it.
        """
        if not self.file_path:
            raise ConnectorFetchError("file_path is required for streaming. Use fetch() for in-memory content.")

        # Try UTF-8 with BOM first, fall back to latin-1
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                f = open(self.file_path, "r", encoding=enc, errors="replace")
                self._detected_encoding = enc
                return f
            except (UnicodeDecodeError, LookupError):
                continue

        raise ConnectorFetchError(f"Cannot decode CSV file at {self.file_path} with any known encoding.")

    def _detect_dialect(self, sample: str) -> csv.Dialect:
        """Sniff CSV dialect from a small sample, fall back to standard comma."""
        try:
            return csv.Sniffer().sniff(sample)
        except Exception:
            return csv.excel

    @staticmethod
    def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """Strips whitespace from all keys and string values."""
        clean = {}
        for k, v in row.items():
            if k is not None:
                clean_k = str(k).strip()
                clean_v = v.strip() if isinstance(v, str) else v
                clean[clean_k] = clean_v
        return clean

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Reads ALL CSV lines and returns records as a list of dictionaries.
        Use for small structured files only.
        For large files (>10k rows) use stream_batches() instead.
        """
        if not self.is_connected:
            self.connect()

        text_to_parse = self.file_content

        if text_to_parse is None and self.file_path:
            try:
                with self._open_file_stream() as f:
                    text_to_parse = f.read()
            except ConnectorFetchError:
                raise
            except Exception as e:
                raise ConnectorFetchError(
                    f"Failed to read CSV file content from {self.file_path}: {str(e)}",
                    details={"file_path": self.file_path, "error": str(e)}
                )

        if not text_to_parse or not text_to_parse.strip():
            logger.warning("CSV data is empty.")
            return []

        # Handle UTF-8 BOM if present in string content
        if text_to_parse.startswith("\ufeff"):
            text_to_parse = text_to_parse[1:]

        try:
            stream = io.StringIO(text_to_parse)
            dialect = self._detect_dialect(text_to_parse[:4096])
            reader = csv.DictReader(stream, dialect=dialect)

            if not reader.fieldnames:
                raise ConnectorDataError("CSV file has no header row or invalid format.")

            records: List[Dict[str, Any]] = []
            for row in reader:
                records.append(self._clean_row(row))

            return records

        except ConnectorDataError:
            raise
        except Exception as e:
            raise ConnectorDataError(
                f"Error parsing CSV rows: {str(e)}",
                details={"error": str(e)}
            )

    def stream_batches(self, batch_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        """
        Generator that streams the CSV file in chunks of `batch_size` rows.
        Does NOT load the entire file into memory at once.

        Yields:
            List[Dict[str, Any]] — a batch of up to batch_size rows.

        Usage:
            for batch in connector.stream_batches(batch_size=1000):
                process(batch)  # process, insert, commit, free memory
        """
        if not self.is_connected:
            self.connect()

        if self.file_content is not None:
            # In-memory path: still efficient for small content
            text = self.file_content
            if text.startswith("\ufeff"):
                text = text[1:]
            stream = io.StringIO(text)
            dialect = self._detect_dialect(text[:4096])
            reader = csv.DictReader(stream, dialect=dialect)

            if not reader.fieldnames:
                raise ConnectorDataError("CSV file has no header row or invalid format.")

            batch: List[Dict[str, Any]] = []
            for row in reader:
                batch.append(self._clean_row(row))
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch

        elif self.file_path:
            # File-based path: true streaming, never loads whole file
            try:
                with self._open_file_stream() as f:
                    # Read first 4096 bytes to detect dialect, then rewind
                    sample = f.read(4096)
                    f.seek(0)
                    dialect = self._detect_dialect(sample)

                    reader = csv.DictReader(f, dialect=dialect)

                    if not reader.fieldnames:
                        raise ConnectorDataError("CSV file has no header row or invalid format.")

                    batch: List[Dict[str, Any]] = []
                    for row in reader:
                        batch.append(self._clean_row(row))
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []  # Free memory for this batch

                    if batch:
                        yield batch

            except ConnectorDataError:
                raise
            except Exception as e:
                raise ConnectorFetchError(
                    f"Error streaming CSV file {self.file_path}: {str(e)}",
                    details={"file_path": self.file_path, "error": str(e)}
                )
        else:
            raise ConnectorConnectionError("No file_path or file_content available for streaming.")

    def count_rows(self) -> int:
        """
        Efficiently counts total rows in a CSV file without loading all data.
        Uses file_path only.
        """
        if not self.file_path:
            return 0
        try:
            count = 0
            with self._open_file_stream() as f:
                for _ in f:
                    count += 1
            return max(0, count - 1)  # Subtract header row
        except Exception as e:
            logger.warning(f"Could not count CSV rows: {e}")
            return 0
