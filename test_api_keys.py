#!/usr/bin/env python
"""
測試API金鑰管理功能
"""
import os
import sys
import django
import requests
import json

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')
django.setup()

def test_api_key_management():
    """測試API金鑰管理功能"""
    print("🔑 測試API金鑰管理功能")
    print("=" * 50)
    
    # 測試數據
    test_data = {
        'exchange': 'BINANCE',
        'network': 'TESTNET',
        'api_key': 'test_api_key_12345678',
        'api_secret': 'test_secret_87654321',
        'is_active': True,
        'can_trade': True,
        'can_read': True,
        'can_withdraw': False,
        'notes': '測試API金鑰'
    }
    
    base_url = 'http://localhost:8000/api'
    
    try:
        # 1. 測試獲取API金鑰列表
        print("1. 測試獲取API金鑰列表...")
        response = requests.get(f'{base_url}/api-keys/')
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 獲取API金鑰列表成功")
            print(f"   響應: {response.json()}")
        else:
            print(f"   ❌ 獲取API金鑰列表失敗: {response.text}")
        
        # 2. 測試創建API金鑰
        print("\n2. 測試創建API金鑰...")
        response = requests.post(f'{base_url}/api-keys/', json=test_data)
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ 創建API金鑰成功")
            api_key_data = response.json()
            print(f"   創建的API金鑰ID: {api_key_data.get('id')}")
        else:
            print(f"   ❌ 創建API金鑰失敗: {response.text}")
        
        # 3. 測試獲取API金鑰摘要
        print("\n3. 測試獲取API金鑰摘要...")
        response = requests.get(f'{base_url}/api-key-summary/')
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 獲取API金鑰摘要成功")
            print(f"   摘要: {response.json()}")
        else:
            print(f"   ❌ 獲取API金鑰摘要失敗: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保Django服務器正在運行")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == '__main__':
    test_api_key_management()
