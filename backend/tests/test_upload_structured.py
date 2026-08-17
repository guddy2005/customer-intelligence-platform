import urllib.request

url = 'http://127.0.0.1:8000/api/v1/ingestion/upload'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

# Sample CSV string
csv_data = """customer_id,trade_id,date,platform,investment_type,scheme_name,amount,payment_mode
CUST_2001,INV_T01,2026-08-05 09:30:00,Zerodha,SIP,Nifty 50 Index Fund,10000.00,AUTO_DEBIT
CUST_2002,INV_T02,2026-08-05 10:00:00,Groww,SIP,Parag Parikh Flexi Cap,15000.00,AUTO_DEBIT
CUST_2003,INV_T03,2026-08-07 14:15:00,AngelOne,Stock Trading,TATA MOTORS SHARES,25000.00,UPI
CUST_2004,INV_T04,10/08/2026 11:00:00,Zerodha,Digital Gold,Sovereign Gold Bond,5000.00,NET_BANKING
"""

file_bytes = csv_data.encode('utf-8')
part1 = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="investments_test.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode('utf-8')
part2 = f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="input_type"\r\n\r\nAUTO_DETECT\r\n--{boundary}--\r\n'.encode('utf-8')

body = part1 + file_bytes + part2

req = urllib.request.Request(
    url,
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        print('HTTP STATUS:', resp.status)
        print('HTTP RESPONSE:', resp.read().decode('utf-8'))
except Exception as e:
    print('ERROR:', e)
