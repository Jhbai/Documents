## **1\. 核心數學概念總覽**

在進入詳細題目表列前，我們先定義這幾類問題背後的數學與邏輯架構：

* **映射與補數 (Mapping & Complement):** 利用 $f(x) \= target \- x$ 的關係，將搜尋複雜度從 $O(n)$ 降至 $O(1)$ (Hash Map)。  
* **單調性與極值 (Monotonicity & Extremum):** 當數據具有排序性質 ($x\_i \\le x\_{i+1}$)，利用雙指針逼近可將 $O(n^2)$ 搜索空間壓縮至 $O(n)$。  
* **拓樸結構 (Topology):** 鏈結串列中的環狀檢測實質上是圖論中對於有限狀態機 (FSM) 進入循環的判斷 (Floyd's Cycle Finding)。  
* **區間幾何 (Interval Geometry):** 處理一維數線上的集合覆蓋與合併問題。  
* **視窗不變性 (Window Invariant):** 在序列 $S$ 中，維護一個動態區間 $\[i, j\]$，使其滿足特定性質 $P(S\[i:j\])$，通常涉及滑動視窗 (Sliding Window)。

## **2\. 詳細題目分析表**

### **類別 A：陣列與雜湊映射 (Array & Hash Map)**

**重點：** 利用空間換取時間，尋找數值間的代數關係。

| ID | 題目名稱 (英文) | 數學/邏輯線索 (Clues) | 核心重點 (Key Points) | 解題演算法分析 |
| :---- | :---- | :---- | :---- | :---- |
| **1** | **Two Sum** | $a \+ b \= T \\implies b \= T \- a$。尋找 $b$ 是否存在。 | **補數關係**。與其中掃描陣列，不如紀錄「我需要誰」。 | **Hash Map** 遍歷陣列 $nums\[i\]$，查詢 $Target \- nums\[i\]$ 是否已存在於 Map 中。若有，即為解；若無，將 $nums\[i\]$ 存入 Map。 |
| **121** | **Best Time to Buy and Sell Stock** | 獲利 $P \= price\[j\] \- price\[i\]$，且 $j \> i$。求 $\\max(P)$。 | **歷史極值**。在第 $j$ 天賣出時，最大獲利取決於前 $j-1$ 天的最低價格。 | **Min-Max Tracking** 維護一個變數 min\_price。遍歷時更新 min\_price，並計算當前價格與 min\_price 的差值，更新最大獲利。 |
| **238** | **Product of Array Except Self** | $Ans\[i\] \= (\\prod\_{k=0}^{i-1} nums\[k\]) \\times (\\prod\_{k=i+1}^{n-1} nums\[k\])$ | **前綴與後綴**。除法被禁止，故拆解為「左半部積」乘「右半部積」。 | **Prefix/Suffix Sum** 兩次遍歷。第一次計算所有位置的「左積」存入陣列；第二次反向遍歷計算「右積」並乘回原陣列。 |
| **53** | **Maximum Subarray** | 子序列和 $S\_i$。若 $S\_{i-1} \< 0$，則 $S\_{i-1} \+ nums\[i\] \< nums\[i\]$。 | **貢獻度分析**。如果前面的累積是「負擔」(負數)，不如拋棄，從當前重新開始。 | **Kadane's Algorithm (DP)** 動態規劃：$dp\[i\] \= \\max(nums\[i\], dp\[i-1\] \+ nums\[i\])$。只需一個變數紀錄當前和，若小於 0 則歸零重算。 |
| **56** | **Merge Intervals** | 區間 $\[s1, e1\]$ 與 $\[s2, e2\]$ 重疊充要條件為 $s2 \\le e1$ (假設已排序)。 | **排序與邊界**。先排序起點，才能線性地判斷重疊。 | **Sorting \+ Greedy** 依 Start Time 排序。遍歷區間，若當前 Start $\\le$ 前一個 End，則合併 (更新 End 為兩者最大值)；否則推入新區間。 |
| **31** | **Next Permutation** | 辭典序 (Lexicographical Order)。找下一個「稍大」的排列。 | **遞減序列斷點**。從後往前找第一個「非遞增」的數，交換並反轉後續序列。 | **Math / Generating** 1\. 從右向左找第一個 $nums\[i\] \< nums\[i+1\]$。 2\. 從右向左找第一個 $\> nums\[i\]$ 的數交換。 3\. 將 $i+1$ 後的序列反轉 (使其變最小)。 |

### **類別 B：雙指針技術 (Two Pointers)**

**重點：** 利用問題的單調性或幾何限制，將搜尋維度從二維 $O(n^2)$ 降維。

| ID | 題目名稱 (英文) | 數學/邏輯線索 (Clues) | 核心重點 (Key Points) | 解題演算法分析 |
| :---- | :---- | :---- | :---- | :---- |
| **167** | **Two Sum II \- Input Array Is Sorted** | 陣列已排序 ($x\_i \\le x\_{i+1}$)。若 $sum \> target$，需減小；反之需增大。 | **單調性逼近**。排序是使用雙指針的前提。 | **Collision Pointers** 指針 L=0, R=n-1。若 $sum \> target \\to R$--；若 $sum \< target \\to L$++。 |
| **15** | **3Sum** | $a+b+c=0 \\implies a+b \= \-c$。固定一點，降維成 Two Sum II。 | **降維打擊**。固定 $i$，在 $i+1$ 到 $n$ 之間找兩數和為 $-nums\[i\]$。 | **Sorting \+ Two Pointers** 先排序。迴圈固定 $i$，利用雙指針找 $L, R$。注意去重 (Skip duplicates)。 |
| **11** | **Container With Most Water** | Area $= (R-L) \\times \\min(H\_L, H\_R)$。欲求 Max Area。 | **貪婪決策**。寬度 $R-L$ 必定縮小，若要面積變大，必須保留較高的邊，捨棄較短的邊。 | **Greedy Two Pointers** L, R 在兩端。每次計算面積後，移動高度較短的那一端 (意圖尋找更高的邊)。 |
| **42** | **Trapping Rain Water** | 水量由該位置左邊最高 ($L\_{max}$) 與右邊最高 ($R\_{max}$) 的較小者決定。 | **短板效應 (木桶理論)**。單個柱子的積水 $= \\min(L\_{max}, R\_{max}) \- H\_i$。 | **Two Pointers (Space Opt)** 維護 $L\_{max}, R\_{max}$。L, R 雙指針向內縮，誰的 Max 較小就結算誰 (因為短板決定水量)，然後移動該指針。 |
| **88** | **Merge Sorted Array** | 兩個已排序陣列合併至 A 陣列尾端 (有足夠空間)。 | **逆向思維**。從前往後填會覆蓋 A 的資料；從後往前填則是安全的。 | **Backward Two Pointers** 指針 p1 指向 A 有效尾端，p2 指向 B 尾端，p\_curr 指向 A 總長尾端。比較 p1, p2 較大者填入 p\_curr 並前移。 |
| **125** | **Valid Palindrome** | $S\[i\] \== S\[n-1-i\]$。忽略非字母數字。 | **對稱性**。頭尾向中間夾擠比對。 | **Collision Pointers** L, R 向中間移動，跳過非 Alphanumeric 字元，若字元不相等 (忽略大小寫) 則 False。 |

### **類別 C：鏈結串列與環 (Linked List & Cycle)**

**重點：** 處理非連續記憶體結構的拓樸問題，常用快慢指針。

| ID | 題目名稱 (英文) | 數學/邏輯線索 (Clues) | 核心重點 (Key Points) | 解題演算法分析 |
| :---- | :---- | :---- | :---- | :---- |
| **141** | **Linked List Cycle** | 若有環，跑得快的人終究會追上跑得慢的人 (同餘理論)。 | **速度差**。相對速度概念。 | **Floyd's Cycle Finding** Slow 走 1 步，Fast 走 2 步。若 Fast 遇到 Null $\\to$ 無環；若 Fast \== Slow $\\to$ 有環。 |
| **287** | **Find the Duplicate Number** | 陣列值 $1 \\sim n$，索引 $0 \\sim n$。視為 index $\\to$ value 的映射圖。 | **圖論映射**。重複的數值意味著多個節點指向同一個節點，形成環的入口。 | **Cycle Detection (Array as List)** 將陣列視為鏈結串列 ($i \\to nums\[i\]$)。使用快慢指針找相遇點，再從頭找環的入口 (即重複數)。 |
| **283** | **Move Zeroes** | 保持非零元素相對順序。 | **分區 (Partition)**。將陣列切分為「非零區」與「待處理區」。 | **Two Pointers (Fast/Slow)** Slow 指向非零區尾端。Fast 遍歷，遇到非零則與 Slow 交換，Slow++。 |

### **類別 D：滑動視窗 (Sliding Window)**

**重點：** 在線性序列中尋找滿足條件的子序列。分為「固定視窗」與「變動視窗」。

#### **1\. 固定大小視窗 / 字串排列**

| ID | 題目名稱 (英文) | 數學/邏輯線索 (Clues) | 核心重點 (Key Points) | 解題演算法分析 |
| :---- | :---- | :---- | :---- | :---- |
| **438** | **Find All Anagrams** | 異位詞 (Anagram) \= 字元頻率向量相同。視窗大小固定為 len(p)。 | **頻率統計**。比較視窗內的字元計數與目標是否一致。 | **Fixed Window \+ Hash Map** 維護一個大小為 len(p) 的視窗。右進一個字元，左出一個字元，動態更新計數陣列，若計數一致則記錄索引。 |
| **567** | **Permutation in String** | 同上，只需判斷是否存在。 | **存在性證明**。 | **Fixed Window** 邏輯同 ID 438，只要找到一組頻率吻合即回傳 True。 |
| **239** | **Sliding Window Maximum** | 求視窗內的 Max。新進來的較大值會「淘汰」前面較小的值。 | **單調佇列 (Monotonic Queue)**。若 $i \< j$ 且 $nums\[i\] \< nums\[j\]$，則 $i$ 永遠不可能成為未來的最大值。 | **Deque (Double-ended Queue)** 維持 Queue 內存索引，且對應數值遞減。視窗滑動時：1. 移除過期索引 2\. 移除尾端小於新值的元素 3\. 加入新值。隊頭即為 Max。 |

#### **2\. 變動大小視窗 (伸縮視窗)**

| ID | 題目名稱 (英文) | 數學/邏輯線索 (Clues) | 核心重點 (Key Points) | 解題演算法分析 |
| :---- | :---- | :---- | :---- | :---- |
| **3** | **Longest Substring Without Repeating Characters** | 子串內不能有重複。若 $R$ 加入造成重複，則 $L$ 需右移直到重複消除。 | **雜湊集與收縮**。維護視窗性質的有效性。 | **Variable Window \+ Set/Map** 右指針擴張，若 char 存在 Map 且 index $\\ge L$，則更新 $L$ 到重複字元的下一位。更新 Max Length。 |
| **209** | **Minimum Size Subarray Sum** | 子陣列和 $\\ge target$。求 Min Length。 | **單調性收縮**。當和達標，嘗試縮小左邊界以求最小長度。 | **Variable Window** 右指針擴張累加 Sum。當 $Sum \\ge Target$，While 迴圈縮小左邊界 ($Sum \-= nums\[L\], L++$) 並更新 Min Length。 |
| **76** | **Minimum Window Substring** | 視窗需包含 T 中所有字元。求 Min Length。 | **條件計數**。需要一個變數 count 追蹤「還缺幾個字元」。 | **Variable Window \+ Counter** 右擴張：若 char 是需要的，count--。當 count==0 (滿足條件)，嘗試左縮：若移出的 char 是必要的，count++，視窗失效，繼續右擴張。 |
| **424** | **Longest Repeating Character Replacement** | 視窗長度 \- 出現最多字元數 $\\le k$ (可替換次數)。 | **容錯機制**。我們希望視窗內「非主流」字元不超過 k 個。 | **Window \+ Max Frequency** 維護視窗內字元計數及 max\_count。若 (R-L+1) \- max\_count \> k，則視窗不合法，L 右移 (平移視窗)。 |
| **1004** | **Max Consecutive Ones III** | 最多將 K 個 0 翻成 1。即視窗內最多容許 K 個 0。 | **零的計數**。轉化為「包含最多 K 個 0 的最長子串」。 | **Variable Window** 右擴張：遇 0 則 zero\_count++。若 zero\_count \> K，左縮直到 zero\_count $\\le$ K。更新 Max Length。 |

## **3.解題策略總結 (Summary)**

可以將這些題目視為**資料流處理 (Stream Processing)** 問題：

1. **Preprocessing (預處理):**  
   * 需要快速查找關係？ $\\rightarrow$ 建立 **Hash Map** (索引)。  
   * 需要極值搜尋或區間合併？ $\\rightarrow$ 先 **Sort** (正規化)。  
2. **Runtime Strategy (執行策略):**  
   * **連續子區間 (Subarray/Substring) \+ 條件極值** $\\rightarrow$ **Sliding Window**。  
     * 問「最小長度」通常是 while 縮減視窗。  
     * 問「最大長度」通常是 if 平移視窗 (或 lazy 縮減)。  
   * **兩數關係 / 迴文 / 盛水** $\\rightarrow$ **Two Pointers**。  
     * 利用幾何邊界向內夾擠。  
   * **歷史狀態依賴 (如買賣股票、最大子序和)** $\\rightarrow$ **DP / Greedy**。  
     * 只需維護當前狀態與全域最佳解。
