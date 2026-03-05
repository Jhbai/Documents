"""
穩態增益估計模組
用於估計控制系統中控制動作對目標變數的穩態增益（Steady-State Gain）

在化學製程控制中，了解控制閥門的開通率與目標變數（如 pH 值、溫度等）
之間的增益關係至關重要。本模組使用普通最小平方法（OLS, Ordinary Least Squares）
進行線性迴歸分析，量化「等效開通率」每增加一個單位，目標變數會變化多少。

參數說明：
    df : pd.DataFrame
        輸入資料表，需包含時間序列資料
    trg : str
        目標變數（y）的欄位名稱，例如 'pH' 或 'temperature'
    cycle : List[str]
        控制週期變數（u）的欄位名稱列表，例如 ['acid_valve', 'base_valve']
        這些欄位應為已經過 duty_cycle 轉換的等效開通率
    best_delay : int
        系統的純延遲時間（Dead Time），即控制動作到實際反應所需的時間步數
        可通過 delay_alignment.py 中的 align() 函數計算得出

回傳值：
    dict : 包含以下資訊
        - 'gain_coefficients': 各控制變數的穩態增益係數（OLS 迴歸係數）
        - 'r_squared': 模型的決定係數（R²），表示模型解釋力
        - 'X': 用於迴歸的特徵矩陣（已考慮延遲對齊）
        - 'y': 用於迴歸的目標變數向量
        - 'model': 訓練完成的線性迴歸模型
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Any


def gain(df: pd.DataFrame, trg: str, cycle: List[str], best_delay: int) -> Dict[str, Any]:
    duty_cycle_cols = [f"{col}_duty" for col in cycle]
    
    data = df[[trg] + duty_cycle_cols].dropna()
    
    if len(data) <= best_delay:
        raise ValueError("資料筆數不足以進行延遲對齊分析")
    
    y = data[trg].values[best_delay:].values
    X = data[duty_cycle_cols].iloc[:-best_delay if best_delay > 0 else len(data)].values
    
    if len(y) != len(X):
        min_len = min(len(y), len(X))
        y = y[:min_len]
        X = X[:min_len]
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    gain_coefficients = {col: coef for col, coef in zip(cycle, model.coef_)}
    
    plt.figure(figsize=(10, 8))
    plt.scatter(X[:, 0], y, alpha=0.6, s=50, label='Data points', color='blue')
    
    x_range = np.linspace(X[:, 0].min(), X[:, 0].max(), 100)
    y_range = model.intercept_ + model.coef_[0] * x_range
    plt.plot(x_range, y_range, 'r-', linewidth=2, label='OLS fitted line')
    
    plt.xlabel(f'{cycle[0]} Duty Cycle (Equivalent On-rate)', fontsize=12)
    plt.ylabel(f'{trg} (Target Variable)', fontsize=12)
    plt.title(f'Steady-State Gain Estimation: {trg} vs {cycle[0]} Duty Cycle\nR² = {r_squared:.4f}', fontsize=14)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    gain_text = "Gain Coefficients:\n"
    for col, coef in gain_coefficients.items():
        gain_text += f"{col}: {coef:.6f}\n"
    plt.figtext(0.15, 0.01, gain_text.strip(), fontsize=10, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('steady_state_gain_plot.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    result = {
        'gain_coefficients': gain_coefficients,
        'r_squared': r_squared,
        'X': X,
        'y': y,
        'model': model
    }
    
    return result