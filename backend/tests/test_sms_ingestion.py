import unittest
from unittest.mock import patch, MagicMock
from backend.app.modules.ingestion.parsers.sms_parser import SMSParser
from backend.app.modules.ingestion.service import process_records_pipeline


class TestSMSParserAndIngestion(unittest.TestCase):

    def test_sms_field_extraction(self):
        raw_row = {
            "customer_id": "C001",
            "sender": "AD-HDFCBK",
            "message": "Your A/C ending 4321 is credited with Rs 50,000.00 on 05-Aug-2026. Info: Salary",
            "timestamp": "2026-08-05 09:30:00"
        }
        self.assertTrue(SMSParser.is_sms_record(raw_row))
        parsed = SMSParser.parse_sms_record(raw_row)

        self.assertEqual(parsed["customer_id"], "C001")
        self.assertEqual(parsed["source_name"], "HDFC")
        self.assertEqual(parsed["amount"], 50000.0)
        self.assertEqual(parsed["transaction_type"], "CREDIT")

    def test_sms_food_delivery_extraction(self):
        raw_row = {
            "customer_id": "C002",
            "sender": "BP-SWIGGY",
            "message": "Order delivered! Enjoy your meal from Domino's Pizza. Total paid: Rs 650.00 via UPI.",
        }
        parsed = SMSParser.parse_sms_record(raw_row)
        self.assertEqual(parsed["customer_id"], "C002")
        self.assertEqual(parsed["source_name"], "SWIGGY")
        self.assertEqual(parsed["amount"], 650.0)
        self.assertEqual(parsed["payment_method"], "UPI")

    @patch("backend.app.modules.ingestion.service.get_db_connection")
    def test_mixed_source_sms_batch_pipeline(self, mock_get_db):
        # Mock MySQL connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No duplicates or missing cust
        mock_get_db.return_value = mock_conn

        sms_records = [
            {"customer_id": "C001", "sender": "AD-HDFCBK", "message": "Rs 50,000 credited. Salary."},
            {"customer_id": "C001", "sender": "VM-AMAZON", "message": "Your order for Rs 2,499 placed."},
            {"customer_id": "C002", "sender": "BP-SWIGGY", "message": "Order delivered from Domino's. Rs 650 paid."},
            {"customer_id": "C003", "sender": "VK-IRCTC", "message": "Ticket booked. Fare: Rs 800."},
            {"customer_id": "C004", "sender": "BZ-ZEPTO", "message": "Amount paid: Rs 340."},
        ]

        result = process_records_pipeline(
            records=sms_records,
            source_identifier="SMS-Data.csv",
            input_type="SMS"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"]["total_records"], 5)
        self.assertEqual(result["summary"]["valid_records"], 5)
        self.assertEqual(result["summary"]["rejected_records"], 0)
        self.assertEqual(result["domain"], "MULTI_SOURCE")
        self.assertIn("FINANCIAL", result["domain_breakdown"])
        self.assertIn("COMMERCE", result["domain_breakdown"])
        self.assertIn("FOOD_DELIVERY", result["domain_breakdown"])
        self.assertIn("TRAVEL", result["domain_breakdown"])
        self.assertIn("QUICK_COMMERCE", result["domain_breakdown"])


if __name__ == "__main__":
    unittest.main()
