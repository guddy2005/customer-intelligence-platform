import logging
from typing import List, Dict, Any, Optional, Tuple, Union
# pyrefly: ignore [missing-import]
import mysql.connector
# pyrefly: ignore [missing-import]
from mysql.connector import Error as MySQLError
from backend.app.modules.ingestion.connectors.base import (
    BaseConnector,
    ConnectorConnectionError,
    ConnectorFetchError,
    ConnectorDataError,
)

logger = logging.getLogger("db_connector")


class DBConnector(BaseConnector):
    """
    Modular database connector for querying relational MySQL databases
    and retrieving tabular records as structured dictionaries.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 3306,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        query: Optional[str] = None,
        params: Optional[Union[Tuple[Any, ...], Dict[str, Any], List[Any]]] = None,
        source_name: str = "MYSQL_DB_SOURCE"
    ):
        super().__init__(source_name=source_name)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.query = query
        self.params = params
        self._connection = None

    def connect(self) -> bool:
        """
        Establishes a connection to the MySQL database.
        """
        if not self.host or not self.user or not self.database:
            raise ConnectorConnectionError(
                "Missing required DB connection parameters (host, user, database).",
                details={"host": self.host, "user": self.user, "database": self.database}
            )

        try:
            self._connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password or "",
                database=self.database,
                connect_timeout=10
            )
            self.is_connected = self._connection.is_connected()
            return self.is_connected
        except MySQLError as e:
            self.is_connected = False
            raise ConnectorConnectionError(
                f"Failed to connect to MySQL database: {e.msg}",
                details={"errno": e.errno, "sqlstate": e.sqlstate}
            )
        except Exception as e:
            self.is_connected = False
            raise ConnectorConnectionError(
                f"Unexpected database connection failure: {str(e)}",
                details={"error": str(e)}
            )

    def fetch(self, query: Optional[str] = None, params: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Executes SELECT query with dictionary cursor and returns list of rows.
        Guarantees that cursors and connections are properly handled and cleaned up.
        """
        active_query = query or self.query
        active_params = params if params is not None else self.params

        if not active_query or not active_query.strip():
            raise ConnectorDataError("No SQL query provided to DBConnector for data extraction.")

        # Disallow dangerous non-read queries in ingestion connector
        trimmed_query = active_query.strip().upper()
        if not (trimmed_query.startswith("SELECT") or trimmed_query.startswith("SHOW") or trimmed_query.startswith("DESCRIBE") or trimmed_query.startswith("EXPLAIN")):
            raise ConnectorDataError(
                "DBConnector only permits read-only queries (SELECT, SHOW, DESCRIBE).",
                details={"query": active_query}
            )

        # Auto connect if not connected
        if not self.is_connected or not self._connection or not self._connection.is_connected():
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor(dictionary=True)
            if active_params:
                cursor.execute(active_query, active_params)
            else:
                cursor.execute(active_query)

            rows = cursor.fetchall()
            
            # Sanitize dates/decimals to python-friendly primitives/strings if needed
            formatted_records: List[Dict[str, Any]] = []
            for row in rows:
                formatted_row = {}
                for k, v in row.items():
                    # Handle bytes, decimals, or datetime conversions gracefully
                    if isinstance(v, bytes):
                        try:
                            formatted_row[k] = v.decode("utf-8")
                        except Exception:
                            formatted_row[k] = str(v)
                    else:
                        formatted_row[k] = v
                formatted_records.append(formatted_row)

            return formatted_records

        except MySQLError as e:
            raise ConnectorFetchError(
                f"MySQL execution error: {e.msg}",
                details={"errno": e.errno, "sqlstate": e.sqlstate, "query": active_query}
            )
        except Exception as e:
            raise ConnectorFetchError(
                f"Failed to fetch rows from MySQL: {str(e)}",
                details={"error": str(e), "query": active_query}
            )
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

    def close(self) -> None:
        """
        Closes the active database connection safely.
        """
        if self._connection and self._connection.is_connected():
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Error closing MySQL connection: {e}")
        self._connection = None
        self.is_connected = False
