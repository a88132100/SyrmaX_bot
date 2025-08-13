# chart_generator.py
"""
圖表生成模組
為回測引擎提供各種視覺化圖表
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import warnings

# 忽略matplotlib的警告
warnings.filterwarnings('ignore')

# 設置中文字體支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置日誌
logger = logging.getLogger(__name__)

class ChartGenerator:
    """圖表生成器"""
    
    def __init__(self, output_dir: str = 'logs/charts'):
        self.output_dir = output_dir
        self.ensure_output_dir()
        
        # 設置seaborn樣式
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        logger.info("圖表生成器初始化完成")
    
    def ensure_output_dir(self):
        """確保輸出目錄存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"創建圖表輸出目錄: {self.output_dir}")
    
    def generate_equity_curve(self, trades_df: pd.DataFrame, 
                             save_path: Optional[str] = None) -> str:
        """
        生成權益曲線圖
        
        Args:
            trades_df: 交易數據DataFrame
            save_path: 保存路徑，如果為None則自動生成
        
        Returns:
            保存的文件路徑
        """
        try:
            if trades_df.empty:
                logger.warning("沒有交易數據，無法生成權益曲線")
                return ""
            
            # 按時間排序
            trades_df = trades_df.sort_values('timestamp')
            
            # 計算累積收益
            cumulative_pnl = trades_df['realized_pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 權益曲線
            ax1.plot(trades_df['timestamp'], cumulative_pnl, 
                    linewidth=2, color='blue', label='累積收益')
            ax1.plot(trades_df['timestamp'], running_max, 
                    linewidth=1, color='green', linestyle='--', label='歷史最高')
            ax1.fill_between(trades_df['timestamp'], cumulative_pnl, 
                           alpha=0.3, color='blue')
            ax1.set_title('權益曲線', fontsize=16, fontweight='bold')
            ax1.set_ylabel('收益 (USDT)', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 回撤圖
            ax2.fill_between(trades_df['timestamp'], drawdown, 0, 
                           alpha=0.7, color='red', label='回撤')
            ax2.set_title('回撤分析', fontsize=16, fontweight='bold')
            ax2.set_xlabel('時間', fontsize=12)
            ax2.set_ylabel('回撤 (USDT)', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 格式化x軸
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 保存圖表
            if save_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = os.path.join(self.output_dir, f'equity_curve_{timestamp}.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"權益曲線圖已保存: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"生成權益曲線圖失敗: {e}")
            return ""

# 創建全局實例
chart_generator = ChartGenerator()

# 便捷函數
def generate_equity_curve(trades_df: pd.DataFrame, save_path: Optional[str] = None) -> str:
    """便捷函數：生成權益曲線圖"""
    return chart_generator.generate_equity_curve(trades_df, save_path)
