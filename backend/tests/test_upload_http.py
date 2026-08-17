import urllib.request

url = 'http://127.0.0.1:8000/api/v1/ingestion/upload'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

with open('backend/sample_data/sms_data.csv', 'rb') as f:
    file_bytes = f.read()

part1 = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sms_data.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode('utf-8')
part2 = f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="input_type"\r\n\r\nSMS\r\n--{boundary}--\r\n'.encode('utf-8')

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
