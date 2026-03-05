import pandas as pd
import numpy as np
from typing import List, Dict, Any
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import acf, pacf


def harris_index(df: pd.DataFrame, trg: str, cycle: List[str], setpoint: float) -> Dict[str, Any]:
    """
    計算 Harris Index 以評估控制系統的可壓縮誤差空間

    本函數根據 rough_analysis.md 中描述的方法，計算當前系統變異數與理論最小變異數
    的差值，作為高採樣率 MPC 可以徹底消滅的誤差空間。

    計算流程：
    1. 計算當下變異數：歷史資料中實際目標變數值偏離目標值（Setpoint）的均方誤差
    2. 估計理論最小變異數：利用時間序列分析分離出白雜訊，計算純延遲內的雜訊累積量
    3. 計算可壓縮空間：當前變異數減去理論最小變異數

    參數:
        df: 輸入的 DataFrame，包含時間序列資料
        trg: 目標變數（y）的欄位名稱，例如 'pH' 或 'temperature'
        cycle: 控制週期變數（u）的欄位名稱列表，例如 ['acid_valve', 'base_valve']
        setpoint: 目標設定值（Setpoint），作為計算誤差的基準

    回傳:
        dict: 包含以下資訊
            - 'current_variance': 當前系統總變異數
            - 'minimum_variance': 理論最小變異數（MVC Benchmark）
            - 'harris_index': Harris Index（可壓縮誤差空間）
            - 'harris_ratio': Harris Ratio（可壓縮比例）
            - 'dead_time': 估計的純延遲步數
            - 'white_noise_variance': 白雜訊變異數
            - 'analysis_summary': 分析摘要文字
    """
    result_df = df.copy()
    
    target_series = result_df[trg].dropna()
    
    if len(target_series) < 10:
        raise ValueError("資料筆數不足，無法進行時間序列分析")
    
    error = target_series - setpoint
    
    current_variance = np.var(error, ddof=1)
    
    n = len(target_series)
    max_lag = min(50, n // 4)
    acf_values = acf(target_series, nlags=max_lag, fft=True)
    
    pacf_values = pacf(target_series, nlags=max_lag)
    
    ar_order = 0
    for i in range(1, len(pacf_values)):
        if abs(pacf_values[i]) > 1.96 / np.sqrt(n):
            ar_order = i + 1
        else:
            break
    
    ma_order = 0
    for i in range(1, len(acf_values)):
        if abs(acf_values[i]) > 1.96 / np.sqrt(n):
            ma_order = i
        else:
            break
    
    ma_order = max(1, ma_order)
    
    try:
        model = ARIMA(target_series, order=(ar_order, 0, ma_order))
        fitted_model = model.fit()
        
        white_noise = fitted_model.resid
        white_noise_variance = np.var(white_noise, ddof=1)
        
        dead_time = 1
        for i in range(1, len(acf_values)):
            if abs(acf_values[i]) < 1.96 / np.sqrt(n):
                dead_time = i
                break
        else:
            dead_time = max(1, ar_order)
        
        minimum_variance = dead_time * white_noise_variance
        
    except Exception:
        diff_series = target_series.diff().dropna()
        if len(diff_series) > 10:
            white_noise_variance = np.var(diff_series, ddof=1)
            dead_time = 3
            minimum_variance = dead_time * white_noise_variance
        else:
            white_noise_variance = current_variance * 0.1
            dead_time = 1
            minimum_variance = white_noise_variance
    
    if current_variance > minimum_variance:
        harris_index_value = current_variance - minimum_variance
    else:
        harris_index_value = 0.0
    
    if current_variance > 0:
        harris_ratio = harris_index_value / current_variance
    else:
        harris_ratio = 0.0
    
    summary = f"Harris Index 分析完成\n"
    summary += f"目標變數：{trg}\n"
    summary += f"設定點 (Setpoint): {setpoint}\n"
    summary += f"當前變異數：{current_variance:.6f}\n"
    summary += f"理論最小變異數：{minimum_variance:.6f}\n"
    summary += f"Harris Index (可壓縮空間): {harris_index_value:.6f}\n"
    summary += f"Harris Ratio (可壓縮比例): {harris_ratio:.2%}\n"
    summary += f"估計純延遲步數：{dead_time}\n"
    summary += f"白雜訊變異數：{white_noise_variance:.6f}\n"

    result = {
        'current_variance': current_variance,
        'minimum_variance': minimum_variance,
        'harris_index': harris_index_value,
        'harris_ratio': harris_ratio,
        'dead_time': dead_time,
        'white_noise_variance': white_noise_variance,
        'analysis_summary': summary
    }
    
    return result