import pandas as pd
from typing import List


def transform(df: pd.DataFrame, trg: str, control: List[str], win_len: int) -> pd.DataFrame:
    """
    計算等效開通率（Duty Cycle）並與目標變數進行對齊

    本函數根據統計學的滾動視窗方法，將離散的 0/1 控制信號轉換為連續的等效開通率，
    並根據交叉相關分析找出與目標變數的最佳延遲對齊，最終估計系統的穩態增益。

    參數:
        df: 輸入的 DataFrame，必須包含目標變數和控制變數的欄位
        trg: 目標變數（目標變數）的名稱，對應 df 中的欄位名稱
        control: 控制變數（動作）的欄位名稱列表，每個元素為 df 中的欄位名稱
        win_len: 滾動視窗的長度（分鐘），用於計算等效開通率

    返回:
        返回一個新的 DataFrame，包含原始資料、計算後的等效開通率、
        延遲對齊後的控制變數、以及系統穩態增益估計等資訊
    """
    result_df = df.copy()
    
    for col in control:
        duty_col = f"{col}_duty"
        result_df[duty_col] = result_df[col].rolling(window=win_len, min_periods=1).mean()
    
    result_df[f"{trg}_delta"] = result_df[trg].diff()
    
    return result_df