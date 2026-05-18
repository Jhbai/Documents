***

# 📖 連續式水質與流體系統：基於 Attention-LSTM 的 pH 動態預測模型設計

**應用場景**：預測具備高度非線性（中性區間滴定曲線）、管線傳輸延遲（Transport Delay）與槽體混合（Mixing）動態特徵的連續式水質系統之出口 pH 值。

---

## 1. 特徵工程與資料前處理 (Feature Engineering & Preprocessing)

在純粹的時間序列資料輸入神經網路前，必須進行物理特徵轉換與時間維度的對齊，這是降低模型學習難度的最關鍵步驟。

### 1.1 輸入張量維度 (Input Tensor Definition)
模型輸入的標準張量維度為 `(n_batch, seq_len, n_features)`。
假設設定滑動窗口長度 `seq_len` 為 60（如一分鐘內的每秒取樣），Batch Size 為 32，則單次輸入形狀為 `(32, 60, 7)`。

**7 個核心特徵 (`n_features = 7`) 詳細定義：**
* **連續特徵 (Continuous Features)**：需進行 Z-score 標準化（$\mu=0, \sigma=1$）。
  1. `Feature 1`：入口 pH 值 (Inlet pH)
  2. `Feature 2`：源水 pH 值 (Source Water pH)
  3. `Feature 3`：Source 流量 (Source Flow Rate) — *決定傳輸延遲與槽體沖刷速率的關鍵變數。*
* **離散控制訊號 (Discrete Signals)**：保持 0 與 1，**不需**正規化。
  4. `Feature 4`：酸閥開關訊號 (Acid Valve Signal)
  5. `Feature 5`：鹼閥開關訊號 (Alkali Valve Signal)
* **物理衍生特徵 (Engineered Physics Features)**：將指數非線性的 pH 轉換為線性濃度的質量平衡空間，數值極小，**強烈建議**進行 Z-score 或 Min-Max 縮放防範梯度下溢。
  6. `Feature 6`：入口氫離子濃度 $[H^+] = 10^{-Feature\_1}$
  7. `Feature 7`：入口氫氧根離子濃度 $[OH^-] = 10^{-(14-Feature\_1)}$

### 1.2 傳輸延遲對齊 (Transport Delay Alignment / Dead Time)
閥門動作與出口 pH 變化存在時間差 $\tau$。可透過交相關函數 (CCF) 找出最大延遲 $\tau_{max}$：

$$R_{xy}(\tau) = \lim_{T \to \infty} \frac{1}{T} \int_{0}^{T} x(t)y(t+\tau) dt$$

> **工程設計**：滑動窗口長度 $W$ (`seq_len`) 必須嚴格大於 $\tau_{max}$，否則模型將無法看見導致當前狀態變化的「觸發特徵」。

---

## 2. 模型架構設計 (Model Architecture Design)

採用結合**加性時間注意力機制 (Additive Temporal Attention)** 的 LSTM 架構，以精準捕捉流體系統的隱含狀態與邊際效應。

### 2.1 LSTM 核心與物理意義
LSTM 透過閘控 (Gating) 機制運作：

$$f_t = \sigma(W_f \cdot [\mathbf{h}_{t-1}, \mathbf{x}_t] + b_f)$$
$$i_t = \sigma(W_i \cdot [\mathbf{h}_{t-1}, \mathbf{x}_t] + b_i)$$
$$\tilde{c}_t = \tanh(W_c \cdot [\mathbf{h}_{t-1}, \mathbf{x}_t] + b_c)$$
$$c_t = f_t \odot c_{t-1} + i_t \odot \tilde{c}_t$$
$$o_t = \sigma(W_o \cdot [\mathbf{h}_{t-1}, \mathbf{x}_t] + b_o)$$
$$\mathbf{h}_t = o_t \odot \tanh(c_t)$$

> **物理對應**：細胞狀態 (Cell State) $c_t$ 可視為「槽體內當前累積的酸鹼離子濃度」的潛在空間表徵；而遺忘閘 (Forget Gate) $f_t$ 則完美模擬了流體的「沖刷與稀釋 (Wash-out)」效應。

### 2.2 時間注意力機制 (Temporal Attention / Bahdanau Variant)
為解決 LSTM 最後一步需記住所有歷史的「資訊瓶頸」，引入 Attention 重新分配時間維度權重：

1. **特徵空間投影與計算對齊分數 (Alignment Score / Energy)**：
   $$e_{t,i} = \mathbf{v}^T \tanh(\mathbf{W}_h \mathbf{h}_i)$$
   * $\mathbf{W}_h \mathbf{h}_i$：將隱藏狀態投影至注意力潛在空間。
   * $\tanh$：提供非線性轉換。
   * $\mathbf{v}^T$：可學習的參數向量，透過內積將高維矩陣降維成一個「純量分數 $e_{t,i}$」，代表時間步 $i$ 訊號（如閥門開啟瞬間）的重要性。

2. **分數正規化 (Softmax Normalization)**：
   $$\alpha_{t,i} = \frac{\exp(e_{t,i})}{\sum_{j=1}^{W} \exp(e_{t,j})}$$
   將 $W$ 個時間步的分數轉換為 $(0, 1)$ 區間的權重機率分佈。

3. **生成上下文向量 (Context Vector Extraction)**：
   $$\mathbf{context}_t = \sum_{i=1}^{W} \alpha_{t,i} \mathbf{h}_i$$
   將窗口內的隱藏狀態依權重進行線性組合。這能讓模型在預測當下，自動聚焦於「閥門狀態切換」的那幾個關鍵時間步，強化捕捉離散訊號與延遲的能力。

---

## 3. 物理知識啟發損失函數 (Physics-Informed Loss Function)

單純的 MSE 無法滿足工控需求（若預測方向錯誤將導致控制系統反向補償引發震盪）。設計複合損失函數：

$$\mathcal{L}_{total} = \lambda_1 \mathcal{L}_{MSE} + \lambda_2 \mathcal{L}_{dir} + \lambda_3 \mathcal{L}_{smooth}$$

* **基礎準確度 (MSE Loss)**：$\mathcal{L}_{MSE} = \frac{1}{N}\sum (\hat{y}_t - y_t)^2$
* **方向性懲罰 (Directional Penalty Loss)**：
  $$\mathcal{L}_{dir} = \frac{1}{N}\sum \max(0, - \Delta \hat{y}_t \cdot \Delta y_t)$$
  * 定義 $\Delta y_t = y_t - y_{t-1}$ 為真實變化梯度，$\Delta \hat{y}_t$ 為預測梯度。
  * **目的**：若預測方向與真實方向相反（如真水質變酸，模型預測變鹼），內積為負，產生巨大正向懲罰，強迫模型精準抓到閥門開啟後的變化趨勢。
* **平滑度懲罰 (Smoothness Penalty Loss / 二階差分)**：
  $$\mathcal{L}_{smooth} = \frac{1}{N}\sum (\hat{y}_t - 2\hat{y}_{t-1} + \hat{y}_{t-2})^2$$
  * **目的**：即使輸入端有高頻閥門切換，真實流體 pH 變化依然連續且具慣性。此項可抑制不符合流體力學的高頻震盪或突刺 (Spikes)。

---

## 4. 訓練策略與優化 (Training Process Design)

* **資料切分 (Data Splitting)**
  嚴格遵守**時序切分 (Chronological Split)**（如 70% 訓練、15% 驗證、15% 測試）。**嚴禁**使用 Random Shuffle 或傳統 K-Fold，避免未來資訊外洩 (Data Leakage) 破壞動態因果關係。

* **優化器配置 (Optimizer)**
  採用 **AdamW** 搭配 **餘弦退火學習率 (Cosine Annealing LR)**：
  $$\theta_t = \theta_{t-1} - \eta_t \left( \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} + \gamma \theta_{t-1} \right)$$
  AdamW 分離了權重衰減 ($\gamma$)，能更有效避免模型死記硬背感測器高頻雜訊，提升對未見流體動態的泛化能力。

* **推論與訓練的偏移處理 (Exposure Bias & Scheduled Sampling)**
  若進行多步預測 (Multi-step forecasting)：
  建議採用 **Scheduled Sampling**。訓練初期使用真實歷史 $pH_{out}$ 作為狀態參考；隨著 Epoch 增加，以機率 $p$ 逐漸使用「模型上一步的預測值 $\hat{y}_{t-1}$」餵入當前步，迫使模型學會在自身誤差累積的情況下進行自我校正。
