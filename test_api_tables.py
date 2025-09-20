#!/usr/bin/env python
import os
import sys
import django

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')
django.setup()

from django.db import connection

def check_tables():
    """檢查數據庫表"""
    print("=== 檢查API金鑰管理相關表 ===")
    
    cursor = connection.cursor()
    
    # 檢查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [row[0] for row in cursor.fetchall()]
    print(f"所有表: {all_tables}")
    
    # 檢查API相關表
    api_tables = [table for table in all_tables if 'api' in table.lower()]
    print(f"API相關表: {api_tables}")
    
    # 檢查trading_api相關表
    trading_tables = [table for table in all_tables if table.startswith('trading_api_')]
    print(f"trading_api表: {trading_tables}")
    
    # 檢查特定表是否存在
    required_tables = [
        'trading_api_exchangeapikey',
        'trading_api_tradingconfig',
        'trading_api_traderconfig'
    ]
    
    print("\n=== 必需表檢查 ===")
    for table in required_tables:
        exists = table in all_tables
        print(f"{table}: {'✅ 存在' if exists else '❌ 不存在'}")

if __name__ == "__main__":
    check_tables()

