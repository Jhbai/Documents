"""
延遲對齊分析模組

用於尋找控制系統中的純延遲時間（Dead Time / Delay Time）。
在化學製程控制中，由於管路傳輸與混合反應需要時間，
控制動作（如閥門開關）不會立即反映在感測器讀值上，
而是會有一段固定的時間延遲。

本模組通過計算不同延遲步數下的相關係數，
找出使控制動作與目標變數變化量相關性最大的延遲參數，
此即為系統的純延遲時間。

參數說明：
    df : pd.DataFrame
        輸入資料表，需包含時間序列資料
    trg : str
        目標變數（y）的欄位名稱，例如 'pH' 或 'temperature'
    cycle : str
        控制週期變數（u）的欄位名稱，例如 'duty_cycle' 或 'valve_action'
    n_delay : int
        最大搜尋延遲範圍，預設會遍歷 1 到 n_delay 的所有可能延遲

回傳值：
    dict : 包含以下資訊
        - 'best_delay': 最佳延遲步數
        - 'best_correlation': 最佳相關係數
        - 'all_correlations': 所有延遲的相關係數字典
        - 'analysis_summary': 分析摘要文字
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


def align(df: pd.DataFrame, trg: str, cycle: str, n_delay: int) -> Dict[str, Any]:
    """
    計算控制動作的純延遲時間

    透過遍歷 1 到 n_delay 的所有可能延遲，
    計算每個延遲下控制週期與目標變數的相關係數，
    找出相關性最高的延遲作為系統純延遲時間。

    參數:
        df : pd.DataFrame
            輸入資料表
        trg : str
            目標變數欄位名稱
        cycle : str
            控制週期變數欄位名稱
        n_delay : int
            最大延遲搜尋範圍

    回傳:
        dict : 包含最佳延遲、相關係數及完整分析結果
    """
    correlations = {}
    
    for delay in range(1, n_delay + 1):
        shifted_cycle = df[cycle].shift(delay)
        correlation = df[trg].corr(shifted_cycle)
        correlations[delay] = correlation
    
    best_delay = max(correlations, key=lambda k: abs(correlations[k]))
    best_correlation = correlations[best_delay]
    
    summary = (
        f"延遲對齊分析完成\n"
        f"目標變數：{trg}\n"
        f"控制變數：{cycle}\n"
        f"搜尋範圍：1 ~ {n_delay} 步\n"
        f"最佳延遲：{best_delay} 步\n"
        f"最佳相關係數：{best_correlation:.4f}"
    )
    
    result = {
        'best_delay': best_delay,
        'best_correlation': best_correlation,
        'all_correlations': correlations,
        'analysis_summary': summary
    }
    
    return result