import unittest
import os
from backend.app.modules.ingestion.connectors import CSVConnector
from backend.app.modules.ingestion.parsers.sms_parser import SMSParser


class TestEndToEndDatasets(unittest.TestCase):

    def test_sms_sample_dataset(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(root_dir, "sample_data", "sms_data.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()

        connector = CSVConnector(file_content=content)
        records = connector.fetch()
        self.assertEqual(len(records), 8)
        self.assertTrue(SMSParser.is_sms_record(records[0]))
        parsed = SMSParser.parse_sms_record(records[0])
        self.assertEqual(parsed["customer_id"], "C001")
        self.assertEqual(parsed["amount"], 50000.0)

    def test_real_sms_data_file_format(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(root_dir, "sample_data", "SMS-Data.csv")
        if not os.path.exists(csv_path):
            self.skipTest("SMS-Data.csv not present in sample_data")

        # Read small sample chunk from SMS-Data.csv
        sample_lines = []
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(25):
                line = f.readline()
                if not line:
                    break
                sample_lines.append(line)

        connector = CSVConnector(file_content="".join(sample_lines))
        records = connector.fetch()
        self.assertTrue(len(records) > 0)
        self.assertTrue(SMSParser.is_sms_record(records[0]))

        parsed = SMSParser.parse_sms_record(records[0])
        self.assertEqual(parsed["customer_id"], "xx39973810")
        self.assertEqual(parsed["amount"], 95.15)
        self.assertEqual(parsed["merchant_or_provider"], "Zomato")


if __name__ == "__main__":
    unittest.main()
