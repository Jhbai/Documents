將基因演算法（Genetic Algorithm, GA）與 LSTM-MPC 結合，是解決高度非線性控制問題非常強大且經典的策略。

在傳統的 MPC 中，如果系統模型是線性的，我們可以用數學解析方法（如二次規劃 QP）瞬間算出最佳解。但你的預測模型是 **LSTM（高度非線性的黑箱模型）**，這會讓優化目標的「地形」變得崎嶇不平（充滿局部最佳解）。如果用傳統的梯度下降法，很容易卡在半山腰；而 GA 是一種基於生物演化原理的**全局搜尋（Global Search）**演算法，它不依賴梯度，非常適合用來破解這種複雜的優化難題。

以下為你拆解 GA 在 LSTM-MPC 中最佳化 $[K_p, K_i, K_d]$ 參數的概念、步驟與核心原理。

### 一、 核心概念：GA 在 MPC 中的角色

在你的系統中，每過一秒鐘（或一個控制週期），MPC 都會啟動一次 GA。
GA 的任務是：**在有限的運算時間內，透過「模擬物競天擇」，找出一組能讓未來 $N_p$ 步 pH 值追蹤誤差最小的 $[K_p, K_i, K_d]$ 參數。**

你可以把 GA 想像成一個有幾十個平行宇宙的模擬器。它同時測試幾十種不同的 PID 設定，看看哪一種在 LSTM 預測出來的未來表現最好，然後留下好的，淘汰壞的，反覆迭代。

---

### 二、 GA 最佳化 PID 的運算步驟

#### 1. 編碼（Encoding）與設定邊界
在 GA 中，每一個「候選解」被稱為一條「染色體（Chromosome）」。在這個情境下，染色體非常簡單，就是一個包含三個實數的向量：$[K_p, K_i, K_d]$。
你必須為這三個參數設定合理的物理邊界（例如 $K_p \in [0, 10]$），避免演算法給出極端數值導致系統崩潰。

#### 2. 初始化族群（Initialization）
在 MPC 啟動的瞬間，GA 會隨機生成 $M$ 組（例如 50 組）PID 參數，這 50 組參數構成第一代「族群（Population）」。

#### 3. 適應度評估（Fitness Evaluation）— 結合 LSTM 的核心
這是最關鍵且最耗算力的一步。你需要評估這 50 組參數「有多好」。對於每一組候選參數 $[K_p, K_i, K_d]$，執行以下內部模擬：
* **啟動預測迴圈：** 從當前時間 $k$ 開始，模擬未來 $N_p$ 步（例如 10 步）。
* **虛擬控制：** 使用這組 PID 參數與當前的 pH 誤差，計算出虛擬的控制訊號（例如加酸/鹼的佔空比）。
* **LSTM 預測：** 將這個虛擬控制訊號輸入訓練好的 LSTM 模型，預測出下一秒的 $\text{pH}$ 值。
* **計算代價（Cost）：** 計算這 $N_p$ 步的總代價 $J$。代價函數通常包含「預測 pH 與目標 pH 的誤差」加上「控制訊號的劇烈程度」。
* **適應度（Fitness）：** 代價 $J$ 越小，適應度越高（通常設為 $\text{Fitness} = \frac{1}{J + \epsilon}$）。

#### 4. 選擇（Selection）
根據適應度進行「輪盤法（Roulette Wheel）」或「錦標賽（Tournament）」。適應度越高的 PID 參數組合，被選中成為「父母」的機率越大。表現差的參數就會被淘汰。

#### 5. 交配（Crossover）與突變（Mutation）
* **交配：** 將兩組被選中的父母參數進行混合。例如，產生一個新的後代，其 $K_p$ 來自父親，$K_i$ 與 $K_d$ 來自母親；或者取兩者的平均值。
* **突變：** 為了維持基因多樣性，避免提早收斂在局部最佳解，會有一個極小的機率（如 5%），隨機改變後代的某個參數值（例如在 $K_p$ 上加上一點高斯雜訊）。

#### 6. 迭代與滾動輸出（Iteration & Receding Horizon）
* 將產生出的新一代 50 組參數，重新回到**步驟 3** 進行評估。
* 重複這個過程 $G$ 代（例如 20 代）。
* **輸出：** 演化結束後，取出最後一代中適應度最高的那一組 $[K_p^*, K_i^*, K_d^*]$，這就是當下最佳的控制決策。將這組參數下發給實體的 PID 控制器執行**一步**。下一秒鐘，整個流程重頭來過。

---

### 三、 實務落地的「加速」秘訣（重要）

純粹的 GA 計算量非常龐大。如果要在秒級的控制系統中即時運行，你必須加入以下工程技巧：

* **熱啟動（Warm Start）：** 在每一秒鐘初始化第一代族群時，**絕對不要全部隨機生成**。你應該把「上一秒算出來的最佳 PID 參數」直接塞進這一秒的初始族群中。因為物理系統是連續的，上一秒的最佳解，通常非常接近這一秒的最佳解。這能讓 GA 的收斂速度呈指數級上升。
* **差值最佳化（Delta Search）：**與其讓 GA 搜尋絕對的 $[K_p, K_i, K_d]$，不如讓 GA 搜尋參數的**變化量** $[\Delta K_p, \Delta K_i, \Delta K_d]$。限制變化量的範圍（例如每秒 $K_p$ 最多變動 0.5），不僅能縮小搜索空間，還能保證實體 PID 控制器的平滑運作，避免參數突變導致閥門開關失控。

為了讓你更直觀地理解基因演算法如何在多代演化中找到最佳解，我準備了一個互動式的 GA 最佳化模擬器。你可以調整族群大小與突變率，觀察候選解如何向最佳區域收斂。

```json?chameleon
{"component":"LlmGeneratedComponent","props":{"height":"600px","prompt":"Objective: Visualize the Genetic Algorithm optimization process for finding optimal PID parameters.\nData State: Initial random population of candidate (Kp, Ki) parameter sets scattered across a 2D plane.\nStrategy: Standard Layout.\nInputs: '族群大小' (Population Size, slider 10-100), '突變率' (Mutation Rate, slider 0.01-0.2), '最大世代數' (Max Generations, slider 10-50), and a '開始演化' (Start Evolution) button.\nBehavior: Create a visual dashboard with two primary elements. First, a line chart tracking '最佳適應度' (Best Fitness) across generations to show convergence. Second, a 2D scatter plot representing the population of PID candidates (e.g., Kp on X-axis, Ki on Y-axis). Define a visually distinct target 'optimal zone' in the scatter plot. When 'Start' is pressed, animate the scatter plot points dynamically over the specified generations to illustrate selection, crossover, and mutation, showing the population progressively clustering towards the optimal zone. Update the fitness chart synchronously with the scatter plot animation. All text and labels must be in Traditional Chinese.","id":"im_50c0dbb12a901b99"}}
```
