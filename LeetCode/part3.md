## **1\. 雜湊表與陣列操作 (Hash Map & Array)**

**核心數學概念：** 集合論 (Set Theory)、映射 (Mapping $f: key \\to value$)、頻率分佈。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 1 | 兩數之和 (Two Sum) | 在陣列中找到 $a \+ b \= target$ 的索引。 | 我們需要尋找 $b \= target \- a$ 是否存在。暴力法 $O(N^2)$ 太慢，需要快速查找。 | **Hash Map (Complement Search)** 遍歷陣列時，將 target \- current\_val 作為 Key 查詢 Map。若存在則回傳，否則將 current\_val 存入 Map。時間複雜度 $O(N)$。 |
| 387 | 字串中的第一個唯一字元 (First Unique Character) | 找到第一個不重複出現的字元索引。 | "唯一" 意味著頻率 $f(c) \= 1$。需要先統計全域資訊。 | **Frequency Array / Hash Map** 第一次遍歷統計所有字元頻率；第二次遍歷檢查頻率是否為 1。 |
| 128 | 最長連續序列 (Longest Consecutive Sequence) | 在無序陣列中找最長連續整數序列長度 (如 1, 2, 3, 4)。 | 要求 $O(N)$。排序需要 $O(N \\log N)$，所以**不能排序**。需要 $O(1)$ 判斷 $x+1$ 是否存在。 | **Hash Set \+ 邊界判斷** 將所有數存入 Set。遍歷每個數 $x$，若 $x-1$ 不在 Set 中，表示 $x$ 是序列起點，開始用 while 迴圈計數 $x+1, x+2...$。 |
| 451 | 根據字元出現頻率排序 (Sort Characters By Frequency) | 依字元出現次數由多到少重組字串。 | 本質是排序問題，但排序鍵值是「頻率」。 | **Hash Map \+ Bucket Sort / Priority Queue** 1\. 統計頻率。 2\. 用 Max-Heap 存 (freq, char) 取出；或用 Bucket Sort (index=頻率) 來重組，達到優於 $O(N \\log N)$ 的線性時間。 |
| 380 | O(1) 時間插入、刪除和獲取隨機元素 (Insert Delete GetRandom O(1)) | 設計一個資料結構滿足上述三個操作均為 $O(1)$。 | Array 支援 $O(1)$ Random Access，但刪除是 $O(N)$；Hash Map 支援 $O(1)$ 查找刪除，但不支援 Random Access。 | **Hash Map \+ Dynamic Array (Swap technique)** Map 存 val \-\> index。Array 存 val。 刪除時，將要刪除的元素與 Array **最後一個元素交換**，然後 pop\_back，並更新 Map。 |

## **2\. 二元樹遍歷與遞迴 (Binary Tree & DFS/BFS)**

**核心數學概念：** 遞迴關係 (Recurrence Relation)、圖論 (無環連通圖)、深度/廣度優先搜尋。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 144 | 前序遍歷 (Preorder) | 遍歷順序：根 $\\to$ 左 $\\to$ 右。 | 典型的遞迴結構。若需迭代，需模擬 Stack。 | **DFS (Recursion / Stack)** Stack 放入 Root，Pop 後先 Push 右子，再 Push 左子 (因為 Stack 是 LIFO)。 |
| 94 | 中序遍歷 (Inorder) | 遍歷順序：左 $\\to$ 根 $\\to$ 右。 | BST 的中序遍歷結果是**有序數列**。 | **DFS (Recursion / Stack)** 一路將左子節點 Push 入 Stack 直到 Null，Pop 處理當前節點，轉向右子節點。 |
| 145 | 後序遍歷 (Postorder) | 遍歷順序：左 $\\to$ 右 $\\to$ 根。 | 根節點最後處理，常從下往上回傳資訊 (如子樹高度)。 | **DFS (Recursion)** 適合處理需要子樹資訊彙總後才能計算的問題 (如計算目錄大小)。 |
| 102 | 層序遍歷 (Level Order) | 逐層由左至右訪問。 | "層" 的概念暗示距離根節點的步數固定。 | **BFS (Queue)** 使用 Queue。每一輪迴圈處理當前 Queue 中所有元素 (即同一層)，並將下一層子節點加入 Queue。 |
| 543 | 二元樹的直徑 (Diameter of Binary Tree) | 兩節點間最長路徑 (不一定經過 Root)。 | 路徑長度 \= 左子樹深度 \+ 右子樹深度。需要在遍歷過程中不斷更新最大值。 | **DFS (Post-order) \+ Global Max** 遞迴函數回傳「該節點的最大深度」。在遞迴過程中計算 L\_depth \+ R\_depth 並更新全域最大值 ans。 |
| 124 | 二元樹中的最大路徑和 (Max Path Sum) | 尋找路徑節點值之和的最大值 (節點值可為負)。 | 路徑可由任意節點開始與結束。局部最優解 (經過某節點單邊最大和) vs 全域最優解 (跨越某節點的拱形路徑)。 | **DFS (Post-order)** 遞迴函數回傳 max(0, left\_gain, right\_gain) \+ node.val (貢獻給父節點)。 同時在函數內計算 left\_gain \+ right\_gain \+ node.val 更新全域最大路徑和。 |

## **3\. 二元搜尋樹 (BST)**

**核心數學概念：** 排序與檢索 (Ordering)、區間限制 ($L \< Root \< R$)、中序遍歷單調性。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 98 | 驗證二元搜尋樹 (Validate BST) | 判斷一棵樹是否符合 BST 定義。 | 左子樹**所有**節點 \< 根；右子樹**所有**節點 \> 根。單純比較子節點與父節點是不夠的。 | **DFS with Range Constraint** 遞迴帶入區間 (min, max)。左子樹區間變為 (min, root.val)，右子樹變為 (root.val, max)。 |
| 450 | 刪除二元搜尋樹中的節點 (Delete Node in a BST) | 維持 BST 性質下刪除節點。 | 若刪除葉子：直接刪。若刪除單子樹：子接父。若刪除雙子樹：結構會破壞，需要找替身。 | **Find Successor/Predecessor** 找到欲刪節點後，找其**右子樹的最小節點 (Successor)** 或左子樹最大節點取代它，再遞迴刪除該 Successor。 |
| 108 | 將有序陣列轉換為二元搜尋樹 (Sorted Array to BST) | 建立一棵**高度平衡**的 BST。 | "有序陣列" \= 中序遍歷結果。"高度平衡" \= 每次都要選中間元素當根。 | **Divide & Conquer** 取陣列中間點 mid 作為 Root，遞迴 \[left, mid-1\] 建左子樹，\[mid+1, right\] 建右子樹。 |

## **4\. 圖論：拓樸排序與搜尋 (Graph & Topological Sort)**

**核心數學概念：** 有向無環圖 (DAG)、入度/出度 (In/Out-degree)、連通分量。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 207 | 課程表 (Course Schedule) | 判斷是否能修完所有課 (有無依賴衝突)。 | 依賴關係 \= 有向邊。修完 \= 無環。 | **Cycle Detection (Topological Sort / DFS)** 1\. Kahn's Algorithm (BFS): 統計入度，入度為 0 入 Queue。若最後處理課程數 \< 總數，則有環。 2\. DFS: 使用 visited 狀態 (0:未訪, 1:訪問中, 2:已訪)。若遇 1 則有環。 |
| 210 | 課程表 II (Course Schedule II) | 輸出修課順序。 | 這就是求拓樸排序的結果序列。 | **Topological Sort (Kahn's Algo)** 同上，只是在 BFS 從 Queue 取出節點時，將其加入結果 List。 |
| 133 | 複製圖 (Clone Graph) | 深拷貝 (Deep Copy) 一個圖。 | 圖可能有環，普通的遞迴會無限循環。需要紀錄已複製過的節點。 | **DFS/BFS \+ Hash Map** 使用 Map old\_node \-\> new\_node。遍歷鄰居時，若 Map 有則直接連接，無則創建並遞迴/入 Queue。 |
| 200 | 島嶼數量 (Number of Islands) | 計算二維網格中 '1' 的連通區塊數。 | 格子看作圖的節點，上下左右是邊。遍歷過要標記以免重複算。 | **DFS / BFS / Union-Find** 雙層迴圈遍歷 Grid。遇到 '1' 時 count++，並啟動 DFS/BFS 將相鄰的 '1' 全部設為 '0' (沈島策略)。 |

## **5\. 圖論：併查集 (Union-Find / Disjoint Set)**

**核心數學概念：** 等價關係 (Equivalence Relation)、集合劃分 (Partition)、動態連通性。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 547 | 省份數量 (Number of Provinces) | 城市間是否連通，求連通分量個數。 | 這是標準的「求連通分量」問題。 | **Union-Find** 初始化 N 個集合。遍歷鄰接矩陣，若 M\[i\]\[j\]=1，則執行 Union(i, j)。最後計算有多少個 root (即 parent\[i\] \== i)。 |
| 684 | 冗餘連接 (Redundant Connection) | 在樹中加入一條邊變成有環圖，找出該邊。 | 樹是無環連通圖。當加入一條邊 (u, v) 時，若 u 和 v 已經連通，這條邊就是多餘的。 | **Union-Find** 遍歷每條邊。若 Find(u) \== Find(v)，回傳該邊；否則 Union(u, v)。 |
| 305 | 島嶼數量 II (Number of Islands II) | 動態加陸地，即時求島嶼數。 | 靜態圖用 DFS/BFS，**動態**加點合併適合 Union-Find。 | **Union-Find (Dynamic)** 每加一個地塊，count++。檢查四周鄰居，若鄰居也是陸地且不屬同一集合，則 Union 並 count--。 |
| 399 | 除法求值 (Evaluate Division) | 給定 $a/b=2.0, b/c=3.0$，求 $a/c$。 | 除法具傳遞性。可看作有向帶權圖路徑乘積，或帶權併查集。 | **Union-Find with Weights / DFS** 維護每個節點到 root 的權重 (倍率)。Union(a, b) 時更新權重關係。查詢時計算 (a-\>root) / (b-\>root)。 |

## **6\. 前綴樹 (Trie)**

**核心數學概念：** 字串集合、前綴共享、樹狀檢索。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 208 | 實作 Trie (Implement Trie) | 實作 insert, search, startsWith。 | 樹的每個節點包含長度 26 的子節點陣列 (對應 a-z) 和一個 isEnd 標記。 | **Trie Node Structure** 利用陣列索引 char \- 'a' 直接定位子節點。 |
| 211 | 添加與搜尋單詞 (Design Add and Search Words) | 搜尋支援 '.' 通配符 (wildcard)。 | '.' 代表需遍歷當前節點的所有非空子節點。 | **Trie \+ DFS** 遇到一般字元依 Trie 走；遇到 '.' 則對當前節點的所有子節點遞迴呼叫 Search。 |
| 212 | 單詞搜尋 II (Word Search II) | 在字元網格中找出所有出現在字典中的單詞。 | 字典很大，對每個單詞跑 DFS 會超時。應反過來：跑一次網格 DFS，同時查字典。 | **Trie \+ Backtracking** 將所有單詞建成 Trie。在網格上 DFS，同步在 Trie 上移動。若走到 isEnd 則找到單字。優化：找到單字後從 Trie 刪除 (Pruning) 以免重複搜尋。 |

## **7\. 線段樹與二進位索引樹 (Segment Tree & BIT)**

**核心數學概念：** 區間運算 (Range Query)、二進位拆分、結合律 (Associativity)。

| 編號 | 題目名稱 (English) | 題目重點 (Problem) | 解題線索 (Clues) | 核心解法 (Solution) |
| :---- | :---- | :---- | :---- | :---- |
| 303 | 區域和檢索 \- 不可變 (Range Sum \- Immutable) | 多次查詢區間和，陣列不變。 | 查詢頻繁，但無修改。適合預處理。 | **Prefix Sum (前綴和)** 建立 $P\[i\] \= \\sum\_{0}^{i} nums\[k\]$。區間和 $sum(i, j) \= P\[j\] \- P\[i-1\]$。查詢 $O(1)$。 |
| 307 | 區域和檢索 \- 可修改 (Range Sum \- Mutable) | 多次查詢區間和，**支援單點修改**。 | 前綴和修改需 $O(N)$ 太慢。需要 $O(\\log N)$ 修改與查詢。 | **Binary Indexed Tree (BIT) / Segment Tree** 利用樹狀結構維護區間和。BIT 實作較簡單 (利用 lowbit)，Segment Tree 擴展性強 (可支援 Range Min/Max)。 |
| 315 | 計算右側小於當前元素的個數 (Count Smaller) | 對每個元素，算右邊有幾個比它小。 | 等同於動態維護「已出現過的數字頻率」，並查詢「區間和」。 | **BIT / Merge Sort** 倒序遍歷陣列。將當前數加入 BIT (Update)，查詢 BIT 中比它小的範圍和 (Query)。需先離散化 (Discretization) 數值以縮小空間。 |
| 327 | 區間和的個數 (Count of Range Sum) | 求區間和落在 $\[lower, upper\]$ 的子陣列數量。 | 區間和 $S\[j\] \- S\[i-1\]$。問題轉化為：對每個 $j$，找有幾個 $i$ 滿足條件。 | **Merge Sort / Segment Tree / BIT** 利用前綴和陣列。類似 Merge Sort 過程中的逆序對計數，在 Merge 階段統計滿足條件的配對數。 |

