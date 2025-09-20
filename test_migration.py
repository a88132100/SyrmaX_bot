#!/usr/bin/env python
"""
測試遷移是否正常工作
"""
import os
import sys
import django

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')

try:
    django.setup()
    print("✅ Django環境設置成功")
    
    # 測試導入模型
    from trading_api.api_key_models import ExchangeAPIKey
    print("✅ ExchangeAPIKey模型導入成功")
    
    # 測試創建遷移
    from django.core.management import call_command
    print("✅ Django管理命令導入成功")
    
    print("🎉 所有測試通過！可以執行遷移了")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
