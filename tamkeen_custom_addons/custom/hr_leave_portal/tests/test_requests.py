import requests
import pprint

TOKEN = 'abcdefg'
SESSION_URL = 'http://localhost:8069/web?db=tamkeen_crm'
URL = 'http://localhost:8069/hr/leave/requests'


def wrap_jsonrpc(data):
    return {
        'jsonrpc': '2.0',
        'method': 'call',
        'id': None,
        'params': data,
    }

data = wrap_jsonrpc({
    'user_id': 'admin',
    'auth': TOKEN,
})

cookie = None

resp = requests.get(SESSION_URL)
cookie = resp.cookies
result = requests.post(URL, json=data, cookies=cookie)

if result.status_code == 200:
    pprint.pprint(result.json())
    pprint.pprint(result.cookies)
else:
    print('Failed ', result.status_code)
    pprint.pprint(result.content.decode('utf-8'))
