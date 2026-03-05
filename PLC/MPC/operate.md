# 低採樣率系統分析操作指南

本文件說明如何使用提供的 Python 模組，對低採樣率的 PLC 控制系統進行分析。這些工具旨在根據統計學的大數法則，將離散的 0/1 控制訊號轉換為連續的等效開通率，進而分析系統的穩態增益、延遲特性與控制效能。

---

## 假設的資料格式

假設您有一個 pandas DataFrame，其結構如下：

| 欄位名稱 | 類型 | 說明 |
|---------|------|------|
| `dateTime` | datetime | 時間戳記 |
| `observe_data` | float | 觀測資料 |
| `control_data1` | float | 控制資料 1（0/1 開關訊號） |
| `control_data2` | float | 控制資料 2（0/1 開關訊號） |

```python
import pandas as pd

# 範例資料結構
# df 的 columns: ["dateTime", "observe_data", "control_data1", "control_data2"]
# 所有 element 都是 float
```

---

## 分析流程

### 步驟一：計算等效開通率（Duty Cycle）

**目的**：將離散的 0/1 控制訊號透過滾動視窗（Sliding Window）轉換為連續的等效開通率。

**模組**：`duty_cycle.py`

```python
from duty_cycle import transform

# 參數設定
target_var = "observe_data"           # 目標變數欄位名稱
control_vars = ["control_data1", "control_data2"]  # 控制變數欄位名稱
window_length = 10                     # 滾動視窗長度（分鐘）

# 執行轉換
result_df = transform(
    df=df,
    trg=target_var,
    control=control_vars,
    win_len=window_length
)
```

**輸出結果**：
- `result_df` 包含原始資料及新增的欄位：
  - `control_data1_duty`: control_data1 的等效開通率
  - `control_data2_duty`: control_data2 的等效開通率
  - `observe_data_delta`: 目標變數的變化量（diff）

---

### 步驟二：尋找純延遲時間（Delay Alignment）

**目的**：計算控制動作與目標變數變化之間的最佳延遲步數（Dead Time）。

**模組**：`delay_alignment.py`

```python
from delay_alignment import align

# 對 control_data1 進行延遲分析
delay_result_1 = align(
    df=result_df,
    trg="observe_data",
    cycle="control_data1_duty",
    n_delay=20  # 搜尋 1~20 步的延遲
)

# 對 control_data2 進行延遲分析
delay_result_2 = align(
    df=result_df,
    trg="observe_data",
    cycle="control_data2_duty",
    n_delay=20
)

# 取得最佳延遲
best_delay_1 = delay_result_1['best_delay']
best_delay_2 = delay_result_2['best_delay']
print(f"control_data1 最佳延遲：{best_delay_1} 步")
print(f"control_data2 最佳延遲：{best_delay_2} 步")
```

**輸出結果**：
- `best_delay`: 最佳延遲步數
- `best_correlation`: 最佳相關係數
- `all_correlations`: 所有延遲的相關係數字典
- `analysis_summary`: 分析摘要文字

---

### 步驟三：估計系統穩態增益（Steady-State Gain）

**目的**：量化控制動作對目標變數的增益影響（例如：開通率每增加 10%，目標變數會變化多少）。

**模組**：`steady_state_gain.py`

```python
from steady_state_gain import gain

# 使用步驟二找到的最佳延遲
best_delay = max(best_delay_1, best_delay_2)  # 或取平均值

gain_result = gain(
    df=result_df,
    trg="observe_data",
    cycle=control_vars,  # ["control_data1", "control_data2"]
    best_delay=best_delay
)

# 取得增益係數
print("增益係數：")
for var, coef in gain_result['gain_coefficients'].items():
    print(f"  {var}: {coef:.6f}")

print(f"R² = {gain_result['r_squared']:.4f}")
```

**輸出結果**：
- `gain_coefficients`: 各控制變數的穩態增益係數
- `r_squared`: 模型的決定係數（R²）
- 自動儲存迴歸分析圖表 `steady_state_gain_plot.png`

---

### 步驟四：計算 Harris Index（控制效能評估）

**目的**：量化當前系統變異數與理論最小變異數的差距，評估可壓縮的誤差空間。

**模組**：`harris_index.py`

```python
from harris_index import harris_index

# 設定 Setpoint（目標設定值）
setpoint_value = 7.0  # 例如 pH 目標值為 7.0

harris_result = harris_index(
    df=result_df,
    trg="observe_data",
    cycle=control_vars,
    setpoint=setpoint_value
)

# 輸出結果
print(harris_result['analysis_summary'])
```

**輸出結果**：
- `current_variance`: 當前系統總變異數
- `minimum_variance`: 理論最小變異數（MVC Benchmark）
- `harris_index`: 可壓縮誤差空間
- `harris_ratio`: 可壓縮比例（%）
- `dead_time`: 估計的純延遲步數
- `white_noise_variance`: 白雜訊變異數

---

## 完整範例程式碼

```python
import pandas as pd
from duty_cycle import transform
from delay_alignment import align
from steady_state_gain import gain
from harris_index import harris_index

# ============================================
# 1. 準備資料
# ============================================
# 假設 df 已經載入，columns 為:
# ["dateTime", "observe_data", "control_data1", "control_data2"]

# 設定參數
target_var = "observe_data"
control_vars = ["control_data1", "control_data2"]
window_length = 10  # 10 分鐘滾動視窗
setpoint_value = 7.0  # 目標設定值

# ============================================
# 2. 計算等效開通率
# ============================================
result_df = transform(
    df=df,
    trg=target_var,
    control=control_vars,
    win_len=window_length
)

# ============================================
# 3. 尋找最佳延遲
# ============================================
delay_results = {}
for ctrl in control_vars:
    duty_col = f"{ctrl}_duty"
    delay_result = align(
        df=result_df,
        trg=target_var,
        cycle=duty_col,
        n_delay=20
    )
    delay_results[ctrl] = delay_result
    print(f"{ctrl} 最佳延遲：{delay_result['best_delay']} 步")

# 取最大延遲作為系統延遲
best_delay = max([r['best_delay'] for r in delay_results.values()])

# ============================================
# 4. 估計穩態增益
# ============================================
gain_result = gain(
    df=result_df,
    trg=target_var,
    cycle=control_vars,
    best_delay=best_delay
)

print("\n=== 穩態增益分析 ===")
for var, coef in gain_result['gain_coefficients'].items():
    print(f"{var}: {coef:.6f}")
print(f"R² = {gain_result['r_squared']:.4f}")

# ============================================
# 5. 計算 Harris Index
# ============================================
harris_result = harris_index(
    df=result_df,
    trg=target_var,
    cycle=control_vars,
    setpoint=setpoint_value
)

print("\n=== Harris Index 分析 ===")
print(harris_result['analysis_summary'])
```

---

## 數學基礎

### 等效開通率（Duty Cycle）

$$D_k = \frac{1}{W} \sum_{i=k-W+1}^k v_i$$

其中 $v_k \in \{0, 1\}$ 為離散控制訊號，$W$ 為滾動視窗大小。

### 系統增益模型

$$\Delta y_k = \beta_{actionA} \times D_{actionA, k-d} + \beta_{actionB} \times D_{actionB, k-d}$$

其中 $d$ 為純延遲步數。

---

## 注意事項

1. **資料品質**：確保資料沒有過多的缺失值，必要時先進行插補或過濾。
2. **視窗長度**：滾動視窗長度需根據系統特性調整，通常為系統反應時間的 1-2 倍。
3. **Setpoint 設定**：Harris Index 需要正確的設定值才能得到準確的誤差評估。
4. **延遲解讀**：延遲步數需乘以採樣間隔（例如 1 分鐘）才是實際的延遲時間。