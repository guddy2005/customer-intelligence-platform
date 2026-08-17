from backend.app.modules.ingestion.service import process_csv_ingestion

csv_data = """customer_id,trade_id,date,platform,investment_type,scheme_name,amount,payment_mode
CUST_2001,INV_T01,2026-08-05 09:30:00,Zerodha,SIP,Nifty 50 Index Fund,10000.00,AUTO_DEBIT
CUST_2002,INV_T02,2026-08-05 10:00:00,Groww,SIP,Parag Parikh Flexi Cap,15000.00,AUTO_DEBIT
CUST_2003,INV_T03,2026-08-07 14:15:00,AngelOne,Stock Trading,TATA MOTORS SHARES,25000.00,UPI
CUST_2004,INV_T04,10/08/2026 11:00:00,Zerodha,Digital Gold,Sovereign Gold Bond,5000.00,NET_BANKING
"""

try:
    res = process_csv_ingestion(file_content=csv_data, filename="investments_test.csv", input_type="AUTO_DETECT")
    print("SUCCESS:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
