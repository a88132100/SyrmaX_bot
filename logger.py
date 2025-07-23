# logger.py
import os
import shutil
import logging
from datetime import datetime, timedelta


def setup_logger():
    """
    建立 logs 資料夾、備份昨日交易紀錄、設定 logging 輸出
    """
    # 日誌資料夾名稱
    log_dir = "logs"
    
    # 若 logs 資料夾不存在則建立
    os.makedirs(log_dir, exist_ok=True)

    # 檢查是否存在 trade_log.csv（昨日交易紀錄）
    log_file = os.path.join(log_dir, "trade_log.csv")
    if os.path.exists(log_file):
        # 建立備份檔名，如 trade_log_20240519.csv
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        backup_name = f"trade_log_{yesterday}.csv"
        backup_path = os.path.join(log_dir, backup_name)

        # 若備份檔尚不存在，才執行備份
        if not os.path.exists(backup_path):
            shutil.copyfile(log_file, backup_path)

    # 設定 logging：INFO 以上級別會顯示
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            # 寫入檔案 logs/trading.log
            logging.FileHandler(os.path.join(log_dir, "trading.log")),
            # 同時輸出到終端畫面
            logging.StreamHandler()
        ]
    )
