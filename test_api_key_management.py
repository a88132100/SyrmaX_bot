#!/usr/bin/env python
"""
API金鑰管理功能測試腳本
"""
import os
import sys
import django
import requests
import json

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from trading_api.api_key_models import ExchangeAPIKey
from trading_api.models import TradingConfig

User = get_user_model()

def test_database_models():
    """測試數據庫模型"""
    print("=== 1. 測試數據庫模型 ===")
    
    # 檢查模型是否可以正常導入
    try:
        from trading_api.api_key_models import ExchangeAPIKey
        from trading_api.models import TradingConfig
        print("✅ 模型導入成功")
    except Exception as e:
        print(f"❌ 模型導入失敗: {e}")
        return False
    
    # 檢查表是否存在
    try:
        api_key_count = ExchangeAPIKey.objects.count()
        trading_config_count = TradingConfig.objects.count()
        print(f"✅ ExchangeAPIKey 表: {api_key_count} 條記錄")
        print(f"✅ TradingConfig 表: {trading_config_count} 條記錄")
    except Exception as e:
        print(f"❌ 數據庫查詢失敗: {e}")
        return False
    
    return True

def test_api_endpoints():
    """測試API端點"""
    print("\n=== 2. 測試API端點 ===")
    
    base_url = "http://localhost:8000/api"
    
    # 測試端點列表
    endpoints = [
        "/api-keys/",
        "/api-key-summary/",
        "/trading-config/",
        "/user-profile/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 401:
                print(f"✅ {endpoint} - 需要認證 (正常)")
            elif response.status_code == 200:
                print(f"✅ {endpoint} - 可訪問")
            else:
                print(f"⚠️ {endpoint} - 狀態碼: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - 服務器未運行")
        except Exception as e:
            print(f"❌ {endpoint} - 錯誤: {e}")

def test_model_creation():
    """測試模型創建"""
    print("\n=== 3. 測試模型創建 ===")
    
    try:
        # 創建測試用戶
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print("✅ 創建測試用戶成功")
        else:
            print("✅ 測試用戶已存在")
        
        # 創建測試API金鑰
        api_key, created = ExchangeAPIKey.objects.get_or_create(
            user=user,
            exchange='BINANCE',
            network='TESTNET',
            defaults={
                'api_key': 'test_api_key_123',
                'api_secret': 'test_secret_456',
                'is_active': True,
                'is_verified': False
            }
        )
        if created:
            print("✅ 創建API金鑰成功")
        else:
            print("✅ API金鑰已存在")
        
        # 創建測試交易配置
        trading_config, created = TradingConfig.objects.get_or_create(
            user=user,
            defaults={
                'default_exchange': 'BINANCE',
                'default_network': 'TESTNET',
                'default_leverage': 1.0,
                'max_position_ratio': 0.3,
                'min_position_ratio': 0.01
            }
        )
        if created:
            print("✅ 創建交易配置成功")
        else:
            print("✅ 交易配置已存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型創建失敗: {e}")
        return False

def test_frontend_integration():
    """測試前端集成"""
    print("\n=== 4. 測試前端集成 ===")
    
    # 檢查前端文件是否存在
    frontend_files = [
        "frontend/src/pages/ApiKeysPage.tsx",
        "frontend/src/services/api.ts",
        "frontend/src/types/index.ts"
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")

def main():
    """主測試函數"""
    print("🔍 API金鑰管理功能測試開始")
    print("=" * 50)
    
    # 運行所有測試
    tests = [
        test_database_models,
        test_api_endpoints,
        test_model_creation,
        test_frontend_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！API金鑰管理功能正常")
    else:
        print("⚠️ 部分測試失敗，請檢查相關功能")
    
    print("\n📋 如何手動測試:")
    print("1. 啟動Django服務器: python manage.py runserver 8000")
    print("2. 啟動前端服務器: cd frontend && npm run dev")
    print("3. 訪問: http://localhost:5173/login")
    print("4. 登入後訪問: http://localhost:5173/api-keys")

if __name__ == "__main__":
    main()
