import os
import unittest
from unittest.mock import patch, MagicMock
import io
import json

from backend.app.modules.ingestion.connectors import (
    CSVConnector,
    APIConnector,
    DBConnector,
    ConnectorConnectionError,
    ConnectorFetchError,
    ConnectorDataError,
)
from backend.app.modules.ingestion.normalizer import Normalizer
from backend.app.modules.ingestion.validator import validate_customer_record, validate_transaction_record
from backend.app.modules.ingestion.classifier import classify_record
from backend.app.core.constants import DomainEnum, TransactionTypeEnum


class TestCSVConnector(unittest.TestCase):
    def test_csv_connector_from_text(self):
        csv_text = "customer_id,trade_id,date,platform,investment_type,scheme_name,amount,payment_mode\nCUST_1001,INV_01,2026-08-05 09:30:00,Zerodha,SIP,Nifty 50,10000.00,AUTO_DEBIT"
        connector = CSVConnector(file_content=csv_text)
        connector.connect()
        records = connector.fetch()
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["customer_id"], "CUST_1001")
        self.assertEqual(records[0]["platform"], "Zerodha")
        self.assertEqual(records[0]["amount"], "10000.00")

    def test_csv_connector_missing_file_raises_error(self):
        connector = CSVConnector(file_path="non_existent_file_12345.csv")
        with self.assertRaises(ConnectorConnectionError):
            connector.connect()

    def test_csv_connector_empty_content(self):
        connector = CSVConnector(file_content="")
        connector.connect()
        records = connector.fetch()
        self.assertEqual(records, [])


class TestAPIConnector(unittest.TestCase):
    def test_api_connector_invalid_url(self):
        connector = APIConnector(url="ftp://invalid-url.com")
        with self.assertRaises(ConnectorConnectionError):
            connector.connect()

    @patch("urllib.request.urlopen")
    def test_api_connector_successful_fetch(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps([
            {"customer_id": "CUST_2001", "order_id": "ORD_99", "amount": 1500.0, "date": "2026-08-10"}
        ]).encode("utf-8")
        mock_response.headers.get_content_charset.return_value = "utf-8"
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        connector = APIConnector(url="https://api.example.com/transactions")
        records = connector.fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["customer_id"], "CUST_2001")
        self.assertEqual(records[0]["order_id"], "ORD_99")

    @patch("urllib.request.urlopen")
    def test_api_connector_invalid_json(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b"<html>Not JSON</html>"
        mock_response.headers.get_content_charset.return_value = "utf-8"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        connector = APIConnector(url="https://api.example.com/bad-data")
        with self.assertRaises(ConnectorDataError):
            connector.fetch()


class TestDBConnector(unittest.TestCase):
    def test_db_connector_missing_params(self):
        connector = DBConnector()
        with self.assertRaises(ConnectorConnectionError):
            connector.connect()

    def test_db_connector_rejects_non_select(self):
        connector = DBConnector(host="localhost", user="root", database="test_db", query="DROP TABLE customers")
        connector.is_connected = True
        connector._connection = MagicMock()
        with self.assertRaises(ConnectorDataError):
            connector.fetch()


class TestNormalizerAndValidation(unittest.TestCase):
    def test_normalize_investment_transaction(self):
        raw_row = {
            "customer_id": "CUST_1001",
            "trade_id": "INV_I01",
            "date": "2026-08-05 09:30:00",
            "platform": "Zerodha",
            "investment_type": "SIP",
            "scheme_name": "Nifty 50 Index Fund",
            "amount": "10000.00",
            "payment_mode": "AUTO_DEBIT"
        }
        domain, source_name, txn_type = classify_record(raw_row, domain_hint="AUTO_DETECT")
        self.assertEqual(domain, DomainEnum.INVESTMENT.value)

        cdm_row = Normalizer.normalize_transaction(raw_row, domain, source_name, txn_type)
        self.assertEqual(cdm_row["customer_id"], "CUST_1001")
        self.assertEqual(cdm_row["transaction_id"], "INV_I01")
        self.assertEqual(cdm_row["amount"], 10000.0)
        self.assertEqual(cdm_row["currency"], "INR")
        self.assertTrue(len(cdm_row["record_hash"]) > 10)

        cleaned_record, errors = validate_transaction_record(raw_row, 1, domain, source_name, txn_type)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(cleaned_record)
        self.assertEqual(cleaned_record["amount"], 10000.0)

    def test_validation_rejects_bad_date_and_amount(self):
        bad_row = {
            "customer_id": "CUST_9999",
            "txn_id": "TXN_ERR",
            "txn_date": "NOT_A_DATE",
            "amount": "NOT_AN_AMOUNT"
        }
        domain, source_name, txn_type = classify_record(bad_row)
        cleaned_record, errors = validate_transaction_record(bad_row, 1, domain, source_name, txn_type)
        self.assertIsNone(cleaned_record)
        self.assertTrue(len(errors) >= 2)


if __name__ == "__main__":
    unittest.main()
