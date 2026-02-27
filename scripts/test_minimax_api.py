import os
import requests
import json

if 'MINIMAX_API_KEY' not in os.environ:
    env = 'memory/minimax.env'
    if os.path.isfile(env):
        with open(env) as f:
            for line in f:
                if line.startswith('MINIMAX_API_KEY='):
                    os.environ['MINIMAX_API_KEY'] = line.split('=',1)[1].strip()

API_KEY = os.environ.get('MINIMAX_API_KEY')
assert API_KEY and API_KEY.startswith('sk-'), 'No valid MINIMAX_API_KEY found'

url = 'https://api.minimaxi.com/v1/chat/completions'
headers = { 'Authorization': f'Bearer {API_KEY}' }
payload = {
  "model": "MiniMax-M2.5",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "ping"}
  ]
}
r = requests.post(url, headers=headers, json=payload, timeout=20)
try:
    result = r.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception:
    print('Non-JSON response:', r.status_code, r.text[:300])
