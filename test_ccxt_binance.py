import ccxt

exchange = ccxt.binance({
    'apiKey': 'b68f1727f53dc69e6ba79b087292fd092b9a95e8b6f11f59a2e9f35462d0c396',
    'secret': '521158d85eefd7641b8f6fd94ab424ed404dbd047a9e1f4e5c22dc13047cc788',
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)

try:
    print(exchange.fetch_balance({'type': 'future'}))
    print('測試網 API Key 正常')
except Exception as e:
    print('測試網 API Key 失敗:', e)
