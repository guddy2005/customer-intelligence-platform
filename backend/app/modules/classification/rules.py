import re
from typing import Dict, Any, Tuple, Optional, List
from backend.app.modules.classification.constants import (
    ClassificationDomainEnum as Domain,
    ConfidenceLevel,
)

# 1. Exact Merchant / Provider / Platform Mapping
# Format: "MERCHANT_KEY": (domain, category, subcategory, confidence)
EXACT_MERCHANT_RULES: Dict[str, Tuple[str, str, str, float]] = {
    # Financial & Banking Institutions
    "HDFC": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "HDFC BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "SBI": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "STATE BANK OF INDIA": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "ICICI": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "ICICI BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "AXIS": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "AXIS BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "KOTAK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "KOTAK MAHINDRA": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "PNB": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "PUNJAB NATIONAL BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "YES BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "INDUSIND": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "BANK OF BARODA": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "CANARA BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "UNION BANK": (Domain.FINANCIAL.value, "BANKING", "ACCOUNT", ConfidenceLevel.EXACT_MATCH),
    "CRED": (Domain.FINANCIAL.value, "BANKING", "CREDIT_CARD", ConfidenceLevel.EXACT_MATCH),
    "PAYTM": (Domain.FINANCIAL.value, "BANKING", "WALLET", ConfidenceLevel.EXACT_MATCH),
    "PHONEPE": (Domain.FINANCIAL.value, "BANKING", "UPI_PAYMENT", ConfidenceLevel.EXACT_MATCH),
    "GOOGLE PAY": (Domain.FINANCIAL.value, "BANKING", "UPI_PAYMENT", ConfidenceLevel.EXACT_MATCH),
    "GPAY": (Domain.FINANCIAL.value, "BANKING", "UPI_PAYMENT", ConfidenceLevel.EXACT_MATCH),

    # Food Delivery & Quick Commerce
    "SWIGGY": (Domain.FOOD_DELIVERY.value, "FOOD", "FOOD_DELIVERY", ConfidenceLevel.EXACT_MATCH),
    "ZOMATO": (Domain.FOOD_DELIVERY.value, "FOOD", "FOOD_DELIVERY", ConfidenceLevel.EXACT_MATCH),
    "EATSURE": (Domain.FOOD_DELIVERY.value, "FOOD", "FOOD_DELIVERY", ConfidenceLevel.EXACT_MATCH),
    "DOMINOS": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "DOMINO'S PIZZA": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "MCDONALDS": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "KFC": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "BURGER KING": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "HALDIRAM'S": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "HALDIRAMS": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "BEHROUZ BIRYANI": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "TRUFFLES": (Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.EXACT_MATCH),
    "BLINKIT": (Domain.QUICK_COMMERCE.value, "GROCERY", "QUICK_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "ZEPTO": (Domain.QUICK_COMMERCE.value, "GROCERY", "QUICK_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "INSTAMART": (Domain.QUICK_COMMERCE.value, "GROCERY", "QUICK_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "BIGBASKET": (Domain.COMMERCE.value, "GROCERY", "ONLINE_GROCERY", ConfidenceLevel.EXACT_MATCH),

    # E-Commerce & Retail
    "AMAZON": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "FLIPKART": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "MYNTRA": (Domain.RETAIL.value, "APPAREL", "FASHION", ConfidenceLevel.EXACT_MATCH),
    "AJIO": (Domain.RETAIL.value, "APPAREL", "FASHION", ConfidenceLevel.EXACT_MATCH),
    "NYKAA": (Domain.LIFESTYLE.value, "BEAUTY", "COSMETICS", ConfidenceLevel.EXACT_MATCH),
    "MEESHO": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "TATA CLiQ": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.EXACT_MATCH),
    "TATACLIQ": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.EXACT_MATCH),

    # Investments & Wealth
    "ZERODHA": (Domain.INVESTMENTS.value, "INVESTMENT", "STOCK_BROKING", ConfidenceLevel.EXACT_MATCH),
    "GROWW": (Domain.INVESTMENTS.value, "INVESTMENT", "MUTUAL_FUNDS", ConfidenceLevel.EXACT_MATCH),
    "ANGELONE": (Domain.INVESTMENTS.value, "INVESTMENT", "STOCK_TRADING", ConfidenceLevel.EXACT_MATCH),
    "ANGEL ONE": (Domain.INVESTMENTS.value, "INVESTMENT", "STOCK_TRADING", ConfidenceLevel.EXACT_MATCH),
    "UPSTOX": (Domain.INVESTMENTS.value, "INVESTMENT", "STOCK_TRADING", ConfidenceLevel.EXACT_MATCH),
    "KITE": (Domain.INVESTMENTS.value, "INVESTMENT", "STOCK_TRADING", ConfidenceLevel.EXACT_MATCH),
    "INDMONEY": (Domain.INVESTMENTS.value, "INVESTMENT", "WEALTH_MANAGEMENT", ConfidenceLevel.EXACT_MATCH),
    "KUVERA": (Domain.INVESTMENTS.value, "INVESTMENT", "MUTUAL_FUNDS", ConfidenceLevel.EXACT_MATCH),
    "PAYTM MONEY": (Domain.INVESTMENTS.value, "INVESTMENT", "MUTUAL_FUNDS", ConfidenceLevel.EXACT_MATCH),
    "COIN": (Domain.INVESTMENTS.value, "INVESTMENT", "MUTUAL_FUNDS", ConfidenceLevel.EXACT_MATCH),

    # Travel & Commute
    "MAKEMYTRIP": (Domain.TRAVEL.value, "TRAVEL", "TRAVEL_BOOKING", ConfidenceLevel.EXACT_MATCH),
    "GOIBIBO": (Domain.TRAVEL.value, "TRAVEL", "TRAVEL_BOOKING", ConfidenceLevel.EXACT_MATCH),
    "EASEMYTRIP": (Domain.TRAVEL.value, "TRAVEL", "TRAVEL_BOOKING", ConfidenceLevel.EXACT_MATCH),
    "YATRA": (Domain.TRAVEL.value, "TRAVEL", "TRAVEL_BOOKING", ConfidenceLevel.EXACT_MATCH),
    "IRCTC": (Domain.TRAVEL.value, "TRAVEL", "TRAIN", ConfidenceLevel.EXACT_MATCH),
    "INDIGO": (Domain.TRAVEL.value, "TRAVEL", "FLIGHT", ConfidenceLevel.EXACT_MATCH),
    "AIR INDIA": (Domain.TRAVEL.value, "TRAVEL", "FLIGHT", ConfidenceLevel.EXACT_MATCH),
    "SPICEJET": (Domain.TRAVEL.value, "TRAVEL", "FLIGHT", ConfidenceLevel.EXACT_MATCH),
    "VISTARA": (Domain.TRAVEL.value, "TRAVEL", "FLIGHT", ConfidenceLevel.EXACT_MATCH),
    "UBER": (Domain.TRAVEL.value, "COMMUTE", "CAB_RIDES", ConfidenceLevel.EXACT_MATCH),
    "OLA": (Domain.TRAVEL.value, "COMMUTE", "CAB_RIDES", ConfidenceLevel.EXACT_MATCH),
    "RAPIDO": (Domain.TRAVEL.value, "COMMUTE", "BIKE_TAXI", ConfidenceLevel.EXACT_MATCH),

    # Utilities, Telecom & DTH
    "BSES RAJDHANI": (Domain.UTILITIES.value, "UTILITIES", "ELECTRICITY", ConfidenceLevel.EXACT_MATCH),
    "BSES YAMUNA": (Domain.UTILITIES.value, "UTILITIES", "ELECTRICITY", ConfidenceLevel.EXACT_MATCH),
    "TATA POWER": (Domain.UTILITIES.value, "UTILITIES", "ELECTRICITY", ConfidenceLevel.EXACT_MATCH),
    "ADANI ELECTRICITY": (Domain.UTILITIES.value, "UTILITIES", "ELECTRICITY", ConfidenceLevel.EXACT_MATCH),
    "AIRTEL": (Domain.TELECOM.value, "UTILITIES", "MOBILE_RECHARGE", ConfidenceLevel.EXACT_MATCH),
    "AIRTEL XSTREAM": (Domain.UTILITIES.value, "UTILITIES", "BROADBAND", ConfidenceLevel.EXACT_MATCH),
    "JIO": (Domain.TELECOM.value, "UTILITIES", "MOBILE_RECHARGE", ConfidenceLevel.EXACT_MATCH),
    "JIO PREPAID": (Domain.TELECOM.value, "UTILITIES", "MOBILE_RECHARGE", ConfidenceLevel.EXACT_MATCH),
    "JIO FIBER": (Domain.UTILITIES.value, "UTILITIES", "BROADBAND", ConfidenceLevel.EXACT_MATCH),
    "INDANE GAS": (Domain.UTILITIES.value, "UTILITIES", "GAS", ConfidenceLevel.EXACT_MATCH),
    "BHARAT GAS": (Domain.UTILITIES.value, "UTILITIES", "GAS", ConfidenceLevel.EXACT_MATCH),
    "HP GAS": (Domain.UTILITIES.value, "UTILITIES", "GAS", ConfidenceLevel.EXACT_MATCH),
    "TATA PLAY": (Domain.ENTERTAINMENT.value, "DTH", "SUBSCRIPTION", ConfidenceLevel.EXACT_MATCH),

    # Entertainment & Subscriptions
    "NETFLIX": (Domain.ENTERTAINMENT.value, "STREAMING", "SUBSCRIPTION", ConfidenceLevel.EXACT_MATCH),
    "SPOTIFY": (Domain.ENTERTAINMENT.value, "STREAMING", "MUSIC", ConfidenceLevel.EXACT_MATCH),
    "DISNEY+ HOTSTAR": (Domain.ENTERTAINMENT.value, "STREAMING", "SUBSCRIPTION", ConfidenceLevel.EXACT_MATCH),
    "HOTSTAR": (Domain.ENTERTAINMENT.value, "STREAMING", "SUBSCRIPTION", ConfidenceLevel.EXACT_MATCH),
    "BOOKMYSHOW": (Domain.ENTERTAINMENT.value, "MOVIES", "EVENT_TICKETING", ConfidenceLevel.EXACT_MATCH),
    "PVR": (Domain.ENTERTAINMENT.value, "MOVIES", "CINEMA", ConfidenceLevel.EXACT_MATCH),
    "INOX": (Domain.ENTERTAINMENT.value, "MOVIES", "CINEMA", ConfidenceLevel.EXACT_MATCH),

    # Healthcare & Pharmacy
    "APOLLO HOSPITALS": (Domain.HEALTHCARE.value, "HEALTHCARE", "HOSPITAL", ConfidenceLevel.EXACT_MATCH),
    "APOLLO PHARMACY": (Domain.HEALTHCARE.value, "PHARMACY", "MEDICINE", ConfidenceLevel.EXACT_MATCH),
    "FORTIS": (Domain.HEALTHCARE.value, "HEALTHCARE", "HOSPITAL", ConfidenceLevel.EXACT_MATCH),
    "MAX HEALTHCARE": (Domain.HEALTHCARE.value, "HEALTHCARE", "HOSPITAL", ConfidenceLevel.EXACT_MATCH),
    "1MG": (Domain.HEALTHCARE.value, "PHARMACY", "ONLINE_PHARMACY", ConfidenceLevel.EXACT_MATCH),
    "TATA 1MG": (Domain.HEALTHCARE.value, "PHARMACY", "ONLINE_PHARMACY", ConfidenceLevel.EXACT_MATCH),
    "PHARMEASY": (Domain.HEALTHCARE.value, "PHARMACY", "ONLINE_PHARMACY", ConfidenceLevel.EXACT_MATCH),
    "LAL PATHLABS": (Domain.HEALTHCARE.value, "DIAGNOSTIC", "LAB_TEST", ConfidenceLevel.EXACT_MATCH),

    # Education & EdTech
    "BYJUS": (Domain.EDUCATION.value, "EDUCATION", "EDTECH", ConfidenceLevel.EXACT_MATCH),
    "UNACADEMY": (Domain.EDUCATION.value, "EDUCATION", "EDTECH", ConfidenceLevel.EXACT_MATCH),
    "PHYSICS WALLAH": (Domain.EDUCATION.value, "EDUCATION", "EDTECH", ConfidenceLevel.EXACT_MATCH),
    "COURSERA": (Domain.EDUCATION.value, "EDUCATION", "ONLINE_COURSE", ConfidenceLevel.EXACT_MATCH),
    "UDEMY": (Domain.EDUCATION.value, "EDUCATION", "ONLINE_COURSE", ConfidenceLevel.EXACT_MATCH),
}


# 2. Keyword Rules (Regex pattern, Domain, Category, Subcategory, Confidence)
KEYWORD_RULES: List[Tuple[str, str, str, str, float]] = [
    # Financial / Banking
    (r"\b(SALARY|PAYROLL|STIPEND|BONUS CREDIT)\b", Domain.FINANCIAL.value, "INCOME", "SALARY", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(ATM|CASH WDL|CASH WITHDRAWAL|ATM CASH)\b", Domain.FINANCIAL.value, "BANKING", "ATM_WITHDRAWAL", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(CREDIT CARD|CC EMI|CARD PAYMENT|HDFC CC|ICICI CC|SBI CARD)\b", Domain.FINANCIAL.value, "BANKING", "CREDIT_CARD", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(FIXED DEPOSIT|FD BOOKING|RECURRING DEPOSIT|RD INSTALLMENT)\b", Domain.FINANCIAL.value, "BANKING", "DEPOSITS", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(PERSONAL LOAN|HOME LOAN|AUTO LOAN|LOAN EMI|LOAN REPAYMENT)\b", Domain.FINANCIAL.value, "BANKING", "LOAN", ConfidenceLevel.STRONG_KEYWORD),

    # Investment
    (r"\b(SIP|SYSTEMATIC INVESTMENT|NIFTY|SENSEX|MUTUAL FUND|FLEXI CAP|INDEX FUND|ELSS|PARAG PARIKH)\b", Domain.INVESTMENTS.value, "INVESTMENT", "SIP", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(STOCK|DEMAT|EQUITY|SHARES|TRADING|TATA MOTORS SHARES|RELIANCE SHARES|IPO)\b", Domain.INVESTMENTS.value, "INVESTMENT", "STOCK", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(SOVEREIGN GOLD BOND|SGB|DIGITAL GOLD|GOLD ETF)\b", Domain.INVESTMENTS.value, "INVESTMENT", "DIGITAL_GOLD", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(PPF|NPS|PROVIDENT FUND|GOVT BOND|TREASURY BILL)\b", Domain.INVESTMENTS.value, "INVESTMENT", "RETIREMENT_SCHEME", ConfidenceLevel.STRONG_KEYWORD),

    # Automotive & Fuel
    (r"\b(PETROL|DIESEL|FUEL|PETROL PUMP|IOCL|BPCL|HPCL|SHELL PETROL|EV CHARGER)\b", Domain.AUTOMOTIVE.value, "AUTOMOTIVE", "FUEL", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(FASTAG|TOLL PLAZA|NHAI TOLL|HIGHWAY TOLL)\b", Domain.AUTOMOTIVE.value, "AUTOMOTIVE", "FASTAG", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(CAR SERVICE|VEHICLE REPAIR|TYRE CHANGE|WHEEL ALIGNMENT|MARUTI SERVICE|HYUNDAI SERVICE)\b", Domain.AUTOMOTIVE.value, "AUTOMOTIVE", "VEHICLE_SERVICE", ConfidenceLevel.STRONG_KEYWORD),

    # Travel & Commute
    (r"\b(FLIGHT|AIRLINES|AIRWAYS|BOARDING PASS|AIRPORT)\b", Domain.TRAVEL.value, "TRAVEL", "FLIGHT", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(HOTEL|RESORT|HOMESTAY|ROOM BOOKING|LODGING)\b", Domain.TRAVEL.value, "TRAVEL", "HOTEL", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(TRAIN TICKET|RAILWAY|METRO RECHARGE|BUS TICKET)\b", Domain.TRAVEL.value, "TRAVEL", "COMMUTE", ConfidenceLevel.STRONG_KEYWORD),

    # Utilities
    (r"\b(ELECTRICITY|POWER BILL|DISCOM|ELECTRIC BOARD)\b", Domain.UTILITIES.value, "UTILITIES", "ELECTRICITY", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(WATER BILL|WATER TAX|JAL BOARD|SEWAGE TAX)\b", Domain.UTILITIES.value, "UTILITIES", "WATER", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(GAS BILL|CYLINDER BOOKING|PNG BILL|LPG CYLINDER)\b", Domain.UTILITIES.value, "UTILITIES", "GAS", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(BROADBAND|FIBER NET|WIFI BILL|INTERNET BILL)\b", Domain.UTILITIES.value, "UTILITIES", "BROADBAND", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(MOBILE RECHARGE|PREPAID RECHARGE|POSTPAID BILL|DTH RECHARGE)\b", Domain.TELECOM.value, "UTILITIES", "MOBILE_RECHARGE", ConfidenceLevel.STRONG_KEYWORD),

    # Healthcare
    (r"\b(HOSPITAL|CLINIC|CONSULTATION|DOCTOR VISIT|MEDICAL CENTRE)\b", Domain.HEALTHCARE.value, "HEALTHCARE", "HOSPITAL", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(PHARMACY|CHEMIST|DRUG STORE|MEDICINE PURCHASE|TABLETS)\b", Domain.HEALTHCARE.value, "PHARMACY", "MEDICINE", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(DIAGNOSTIC|BLOOD TEST|LAB TEST|MRI SCAN|CT SCAN|X-RAY)\b", Domain.HEALTHCARE.value, "DIAGNOSTIC", "LAB_TEST", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(HEALTH INSURANCE|MEDICLAIM|INSURANCE CLAIM)\b", Domain.INSURANCE.value, "HEALTHCARE", "INSURANCE_CLAIM", ConfidenceLevel.STRONG_KEYWORD),

    # Education
    (r"\b(SCHOOL FEE|COLLEGE FEE|UNIVERSITY|TUITION|COACHING INSTITUTE|SEMESTER FEE)\b", Domain.EDUCATION.value, "EDUCATION", "TUITION", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(EDTECH|ONLINE COURSE|EXAM REGISTRATION|CERTIFICATION)\b", Domain.EDUCATION.value, "EDUCATION", "ONLINE_LEARNING", ConfidenceLevel.STRONG_KEYWORD),

    # Real Estate
    (r"\b(HOUSE RENT|FLAT RENT|RENTAL PAYMENT|SOCIETY MAINTENANCE|MAINTENANCE CHARGES)\b", Domain.REAL_ESTATE.value, "HOUSING", "RENTAL", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(PROPERTY TAX|STAMP DUTY|REGISTRY FEE)\b", Domain.REAL_ESTATE.value, "HOUSING", "PROPERTY_TAX", ConfidenceLevel.STRONG_KEYWORD),

    # Food Delivery & Dining
    (r"\b(RESTAURANT|DINING|PIZZA|BURGER|BIRYANI|CAFE|BAKERY|SWEET HOUSE|FOOD COURT)\b", Domain.FOOD_DELIVERY.value, "FOOD", "RESTAURANT", ConfidenceLevel.STRONG_KEYWORD),

    # Commerce & Retail Categories
    (r"\b(ELECTRONICS|LAPTOP|SMARTPHONE|HEADPHONES|CAMERA|GADGET)\b", Domain.COMMERCE.value, "SHOPPING", "ELECTRONICS", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(APPAREL|CLOTHING|JEANS|SHIRT|DRESS|FOOTWEAR|SNEAKERS|JACKET|FASHION)\b", Domain.RETAIL.value, "APPAREL", "FASHION", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(BEAUTY|SKINCARE|COSMETICS|MAKEUP|PERFUME|LIPSTICK)\b", Domain.LIFESTYLE.value, "BEAUTY", "COSMETICS", ConfidenceLevel.STRONG_KEYWORD),
    (r"\b(GROCERY|VEGETABLES|SUPERMARKET|PROVISIONS|KIRANA)\b", Domain.COMMERCE.value, "GROCERY", "GROCERY", ConfidenceLevel.STRONG_KEYWORD),
]


# 3. Domain Normalization Mapping (for CDM source_domain hints)
DOMAIN_FALLBACKS: Dict[str, Tuple[str, str, str, float]] = {
    "BANKING": (Domain.FINANCIAL.value, "BANKING", "GENERAL_BANKING", ConfidenceLevel.INFERRED),
    "INVESTMENT": (Domain.INVESTMENTS.value, "INVESTMENT", "GENERAL_INVESTMENT", ConfidenceLevel.INFERRED),
    "E_COMMERCE": (Domain.COMMERCE.value, "SHOPPING", "E_COMMERCE", ConfidenceLevel.INFERRED),
    "FOOD_DELIVERY": (Domain.FOOD_DELIVERY.value, "FOOD", "FOOD_DELIVERY", ConfidenceLevel.INFERRED),
    "TRAVEL": (Domain.TRAVEL.value, "TRAVEL", "GENERAL_TRAVEL", ConfidenceLevel.INFERRED),
    "AUTOMOBILE": (Domain.AUTOMOTIVE.value, "AUTOMOTIVE", "GENERAL_AUTOMOTIVE", ConfidenceLevel.INFERRED),
    "REAL_ESTATE": (Domain.REAL_ESTATE.value, "REAL_ESTATE", "GENERAL_HOUSING", ConfidenceLevel.INFERRED),
    "UTILITIES": (Domain.UTILITIES.value, "UTILITIES", "GENERAL_UTILITIES", ConfidenceLevel.INFERRED),
    "HEALTHCARE": (Domain.HEALTHCARE.value, "HEALTHCARE", "GENERAL_HEALTHCARE", ConfidenceLevel.INFERRED),
    "EDUCATION": (Domain.EDUCATION.value, "EDUCATION", "GENERAL_EDUCATION", ConfidenceLevel.INFERRED),
    "RETAIL_LIFESTYLE": (Domain.RETAIL.value, "RETAIL", "GENERAL_RETAIL", ConfidenceLevel.INFERRED),
}
