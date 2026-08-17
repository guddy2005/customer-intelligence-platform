import unittest
from backend.app.modules.classification.classifier import classification_engine
from backend.app.modules.classification.constants import (
    ClassificationDomainEnum as Domain,
    ConfidenceLevel,
)


class TestClassificationEngine(unittest.TestCase):

    def test_amazon_ecommerce(self):
        record = {
            "customer_id": "C002",
            "source_name": "AMAZON",
            "transaction_type": "PURCHASE",
            "merchant_or_provider": "Amazon",
            "category": "Electronics",
            "amount": 25000
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.COMMERCE.value)
        self.assertEqual(res["category"], "SHOPPING")
        self.assertEqual(res["subcategory"], "ELECTRONICS")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_flipkart_ecommerce(self):
        record = {
            "customer_id": "C003",
            "source_name": "FLIPKART",
            "merchant_or_provider": "Flipkart",
            "amount": 3200
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.COMMERCE.value)
        self.assertEqual(res["category"], "SHOPPING")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_swiggy_food_delivery(self):
        record = {
            "customer_id": "C001",
            "source_name": "SWIGGY",
            "transaction_type": "PURCHASE",
            "merchant_or_provider": "Swiggy",
            "amount": 650
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.FOOD_DELIVERY.value)
        self.assertEqual(res["category"], "FOOD")
        self.assertEqual(res["subcategory"], "FOOD_DELIVERY")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_zomato_food_delivery(self):
        record = {
            "customer_id": "C004",
            "source_name": "ZOMATO",
            "merchant_or_provider": "Zomato",
            "amount": 420
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.FOOD_DELIVERY.value)
        self.assertEqual(res["category"], "FOOD")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_blinkit_quick_commerce(self):
        record = {
            "customer_id": "C005",
            "source_name": "BLINKIT",
            "merchant_or_provider": "Blinkit",
            "amount": 540
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.QUICK_COMMERCE.value)
        self.assertEqual(res["category"], "GROCERY")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_banking_salary(self):
        record = {
            "customer_id": "CUST_1001",
            "transaction_id": "TXN_B01",
            "merchant_or_provider": "TATA CONSULTANCY SALARY",
            "transaction_type": "CREDIT",
            "amount": 75000.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.FINANCIAL.value)
        self.assertEqual(res["category"], "INCOME")
        self.assertEqual(res["subcategory"], "SALARY")
        self.assertEqual(res["confidence"], ConfidenceLevel.STRONG_KEYWORD)

    def test_investment_sip(self):
        record = {
            "customer_id": "CUST_1001",
            "source_name": "Zerodha",
            "merchant_or_provider": "Nifty 50 Index Fund",
            "category": "SIP",
            "amount": 10000.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.INVESTMENTS.value)
        self.assertEqual(res["category"], "INVESTMENT")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_flight_booking(self):
        record = {
            "customer_id": "CUST_1009",
            "merchant_or_provider": "IndiGo Flight Booking",
            "amount": 4500.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.TRAVEL.value)
        self.assertEqual(res["category"], "TRAVEL")
        self.assertEqual(res["subcategory"], "FLIGHT")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_automotive_fuel(self):
        record = {
            "customer_id": "CUST_1004",
            "merchant_or_provider": "PETROL PUMP HYDERABAD",
            "amount": 2000.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.AUTOMOTIVE.value)
        self.assertEqual(res["category"], "AUTOMOTIVE")
        self.assertEqual(res["subcategory"], "FUEL")
        self.assertEqual(res["confidence"], ConfidenceLevel.STRONG_KEYWORD)

    def test_utilities_electricity(self):
        record = {
            "customer_id": "CUST_1001",
            "merchant_or_provider": "BSES Rajdhani",
            "amount": 3450.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.UTILITIES.value)
        self.assertEqual(res["category"], "UTILITIES")
        self.assertEqual(res["subcategory"], "ELECTRICITY")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_healthcare_hospital(self):
        record = {
            "customer_id": "CUST_1010",
            "merchant_or_provider": "Apollo Hospitals Consultation",
            "amount": 1200.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.HEALTHCARE.value)
        self.assertEqual(res["category"], "HEALTHCARE")
        self.assertEqual(res["confidence"], ConfidenceLevel.EXACT_MATCH)

    def test_education(self):
        record = {
            "customer_id": "CUST_1011",
            "merchant_or_provider": "Delhi Public School Fee",
            "amount": 15000.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.EDUCATION.value)
        self.assertEqual(res["category"], "EDUCATION")
        self.assertEqual(res["subcategory"], "TUITION")
        self.assertEqual(res["confidence"], ConfidenceLevel.STRONG_KEYWORD)

    def test_unknown_merchant(self):
        record = {
            "customer_id": "CUST_9999",
            "merchant_or_provider": "RANDOM_UNRECOGNIZED_XYZ_12345",
            "amount": 100.00
        }
        res = classification_engine.classify(record)
        self.assertEqual(res["source_domain"], Domain.UNKNOWN.value)
        self.assertEqual(res["category"], "UNKNOWN")
        self.assertIsNone(res["subcategory"])
        self.assertEqual(res["confidence"], 0.0)

    def test_malformed_and_empty_records(self):
        self.assertEqual(classification_engine.classify(None)["source_domain"], "UNKNOWN")
        self.assertEqual(classification_engine.classify({})["source_domain"], "UNKNOWN")
        self.assertEqual(classification_engine.classify("not a dict")["source_domain"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
