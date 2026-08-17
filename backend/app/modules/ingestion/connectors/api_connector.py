import json
import urllib.request
import urllib.error
import urllib.parse
import logging
from typing import List, Dict, Any, Optional
from backend.app.modules.ingestion.connectors.base import (
    BaseConnector,
    ConnectorConnectionError,
    ConnectorFetchError,
    ConnectorDataError,
)

logger = logging.getLogger("api_connector")


class APIConnector(BaseConnector):
    """
    Modular connector for fetching JSON datasets from REST API endpoints.
    Uses standard library urllib for zero-dependency reliability.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
        source_name: str = "API_SOURCE",
        results_key: Optional[str] = None
    ):
        super().__init__(source_name=source_name)
        self.url = url.strip()
        self.headers = headers or {}
        self.params = params or {}
        self.timeout = timeout
        self.results_key = results_key

    def _build_full_url(self) -> str:
        if not self.params:
            return self.url

        url_parts = list(urllib.parse.urlparse(self.url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update(self.params)
        url_parts[4] = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(url_parts)

    def connect(self) -> bool:
        """
        Validates URL syntax and sets connection ready state.
        """
        if not self.url or not (self.url.startswith("http://") or self.url.startswith("https://")):
            raise ConnectorConnectionError(
                f"Invalid or unsupported API URL scheme: '{self.url}'",
                details={"url": self.url}
            )

        self.is_connected = True
        return True

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Executes HTTP GET request and returns data as a list of dictionaries.
        """
        if not self.is_connected:
            self.connect()

        full_url = self._build_full_url()
        req_headers = {"User-Agent": "CustomerIntelligencePlatform/1.0", "Accept": "application/json"}
        req_headers.update(self.headers)

        req = urllib.request.Request(full_url, headers=req_headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                if status_code < 200 or status_code >= 300:
                    raise ConnectorFetchError(
                        f"API request failed with HTTP status {status_code}",
                        details={"status_code": status_code, "url": full_url}
                    )

                raw_bytes = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                text_content = raw_bytes.decode(encoding)

        except urllib.error.HTTPError as e:
            raise ConnectorFetchError(
                f"API returned HTTP {e.code}: {e.reason}",
                details={"status_code": e.code, "reason": str(e.reason), "url": full_url}
            )
        except urllib.error.URLError as e:
            raise ConnectorConnectionError(
                f"Failed to connect to API endpoint: {str(e.reason)}",
                details={"reason": str(e.reason), "url": full_url}
            )
        except TimeoutError:
            raise ConnectorFetchError(
                f"API request timed out after {self.timeout}s",
                details={"timeout": self.timeout, "url": full_url}
            )
        except Exception as e:
            raise ConnectorFetchError(
                f"Unexpected error fetching data from API: {str(e)}",
                details={"error": str(e), "url": full_url}
            )

        # Parse JSON
        try:
            data = json.loads(text_content)
        except Exception as e:
            raise ConnectorDataError(
                f"Response from API is not valid JSON: {str(e)}",
                details={"url": full_url, "preview": text_content[:200]}
            )

        # Extract list of records
        if self.results_key and isinstance(data, dict):
            data = data.get(self.results_key, [])

        if isinstance(data, list):
            # Ensure every item in list is a dict
            records = []
            for item in data:
                if isinstance(item, dict):
                    records.append(item)
                else:
                    records.append({"value": item})
            return records
        elif isinstance(data, dict):
            # If a single dictionary was returned, wrap it as a single record
            return [data]
        else:
            raise ConnectorDataError(
                f"Expected JSON object or list of objects, got {type(data).__name__}",
                details={"data_type": type(data).__name__}
            )
