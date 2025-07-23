import sys
from trading.trader import MultiSymbolTrader  # 主類別
from logger import setup_logger  # 匯入我們剛剛寫的 logger.py 裡的函式
from config import TEST_MODE   # 引入設定

setup_logger()  # 執行：建立 logs 資料夾、備份日誌、設定 logging

if __name__ == "__main__":   
    # 初始化交易機器人，設置檢查間隔為 3 秒
    trader = MultiSymbolTrader(interval_seconds=3)
    
    try:
        # 啟動交易循環
        while True:
            trader.run_trading_cycle()
    except KeyboardInterrupt:
        print("\n交易機器人已停止")
    except Exception as e:
        print(f"發生錯誤: {e}")
