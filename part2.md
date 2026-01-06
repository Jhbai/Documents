## **1\. 鏈結串列 (Linked List) \- Test01.csv**

**核心數學概念**：拓樸結構變換、指標操作 (Pointer Manipulation)、雙指標逼近 (Two Pointers)、快慢指標 (Floyd's Cycle-Finding)。 **共同線索**：由於鏈結串列無法隨機存取 (No Random Access)，所有解法必然依賴「遍歷」與「指標重導向」。

| 編號 | 題目名稱 | 關鍵線索 (Clues) | 數學/邏輯重點 (Key Points) | 解題思路 (Solution Strategy) |
| :---- | :---- | :---- | :---- | :---- |
| **206** | **反轉鏈結串列** | "Reverse", "In-place" | **拓樸反轉**：將有向圖 $A \\to B$ 改為 $B \\to A$。需要暫存 $Next$ 節點以防斷鏈。 | **Iterative**：使用 prev, curr, next 三指標滾動更新。 **Recursive**：利用遞迴堆疊回溯特性，從尾部開始反轉指標。 |
| **92** | **反轉鏈結串列 II** | "Range \[left, right\]" | **局部拓樸變換**：只改變第 $m$ 到 $n$ 個節點的指向，頭尾需重新接合。 | **Dummy Node**：使用虛擬頭節點處理 $left=1$ 的邊界情況。定位到 $left-1$ 後，進行固定次數的插入/反轉操作。 |
| **21** | **合併兩個有序鏈結串列** | "Sorted", "Merge" | **有序性 (Ordering)**：若 $L1.val \< L2.val$，則 $L1$ 先行。保持單調非遞減性質。 | **Two Pointers**：比較兩指標當前值，小的接入結果鏈。 **Recursion**：$f(L1, L2) \= L1 \+ f(L1.next, L2)$ (若 $L1$ 較小)。 |
| **23** | **合併 K 個有序鏈結串列** | "K lists", "Sorted" | **多路歸併**：從 $K$ 個候選者中選最小值的極值問題。$O(N \\log K)$ 優於 $O(NK)$。 | **Min-Heap (Priority Queue)**：將 $K$ 個鏈結的頭節點放入 Heap，每次 Pop 最小值並 Push 該節點的 Next。 |
| **141** | **環形鏈結串列** | "Cycle", "Repeat" | **週期性 (Periodicity)**：若存在環，$x\_{i}$ 與 $x\_{2i}$ 必在某時刻模運算同餘 (相遇)。 | **快慢指標 (Floyd's)**：Slow 走 1 步，Fast 走 2 步。若有環，Fast 必追上 Slow；若無環，Fast 到達 Null。 |
| **142** | **環形鏈結串列 II** | "Start of Cycle" | **幾何距離關係**：設起點到環口距離 $a$，環口到相遇點 $b$，剩餘環長 $c$。相遇時 $2(a+b) \= a+b+n(b+c)$，推導出 $a \= (n-1)(b+c) \+ c$。 | **雙階段指標**：1. 快慢指標相遇。 2\. 新指標從 Head 出發，與 Slow 同速前進，相遇點即為環入口 (Entry Point)。 |

## **2\. 單調堆疊 (Monotonic Stack) \- Test02.csv**

**核心數學概念**：單調性 (Monotonicity)、最近更值 (Nearest Greater/Smaller Element)、不變量 (Invariant)。 **共同線索**：題目詢問「下一個更大/更小」或涉及「區間極值擴展」，通常暗示 $O(N)$ 解法，需維護一個有序的候選集合。

| 編號 | 題目名稱 | 關鍵線索 (Clues) | 數學/邏輯重點 (Key Points) | 解題思路 (Solution Strategy) |
| :---- | :---- | :---- | :---- | :---- |
| **496** | **下一個更大元素 I** | "Next Greater", "Subset" | **單調遞減不變量**：為了找到右邊第一個比自己大的，堆疊內應保持遞減。一旦遇到大值，破壞單調性，即觸發「結算」。 | **單調堆疊 \+ Hash Map**：遍歷陣列，維護遞減堆疊。當 curr \> stack.top，則 stack.top 的 Next Greater 是 curr (存入 Map)。 |
| **739** | **每日溫度** | "Wait days", "Distance" | **索引距離**：本質同 496，但存的是 Index 以計算 $Index\_{curr} \- Index\_{top}$。 | **單調遞減堆疊 (存 Index)**：當 T\[i\] \> T\[stack.top\]，說明 stack.top 這天的升溫日找到了，計算距離並 Pop。 |
| **503** | **下一個更大元素 II** | "Circular Array" | **模運算 (Modulo)**：環形陣列可視為 $A$ 接在 $A$ 之後 ($A \+ A$)。索引映射為 $i \\% n$。 | **虛擬兩倍長度遍歷**：迴圈跑 $2N$ 次，利用 $i \\% N$ 存取元素，其餘邏輯同 496/739。 |
| **84** | **柱狀圖中最大的矩形** | "Rectangle Area", "Max" | **邊界擴展**：對每一根柱子 $h$，其最大矩形面積取決於左右兩側「第一個比它矮」的柱子位置 ($L, R$)。$Area \= h \\times (R \- L \- 1)$。 | **單調遞增堆疊**：維護遞增高度。當 h\[i\] \< h\[stack.top\]，表示 top 的右邊界確定是 $i$。Pop 出 top 計算面積 (其左邊界即為新的 stack.top)。 |

## **3\. Heap 與 Top K 問題 \- Test03.csv**

**核心數學概念**：偏序關係 (Partial Order)、機率統計 (Frequency)、選擇演算法 (Selection Algorithm)。 **共同線索**：出現 "Kth Largest", "Top K Frequent"，這類問題不需要完全排序 ($O(N \\log N)$)，只需維護局部有序 ($O(N \\log K)$)。

| 編號 | 題目名稱 | 關鍵線索 (Clues) | 數學/邏輯重點 (Key Points) | 解題思路 (Solution Strategy) |
| :---- | :---- | :---- | :---- | :---- |
| **215** | **陣列中的第 K 個最大元素** | "Kth Largest", "Unsorted" | **集合縮減**：只需知道前 K 大，不關心具體順序；或者利用 Partition 快速定位。 | **Min-Heap (Size K)**：維護大小為 K 的 Min-Heap。遍歷完後，堆頂即為第 K 大。 **Quick Select**：利用 Quick Sort 的 Partition 步驟，期望時間 $O(N)$。 |
| **347** | **前 K 個高頻元素** | "Frequency", "Top K" | **映射與排序**：先將資料映射到頻率域 (Value $\\to$ Count)，再對 Count 做 Top K 篩選。 | **Hash Map \+ Min-Heap**：1. Map 統計頻率。 2\. 維護大小為 K 的 Min-Heap (依頻率排序)。 |
| **692** | **前 K 個高頻單字** | "Frequency", "Lexicographical" | **多重排序條件**：頻率相同時，需依字典序排列。這改變了比較函數 (Comparator) 的邏輯。 | **Hash Map \+ Custom Heap**：同 347，但在 Heap 的 Comparator 中加入邏輯：頻率不同比大小，頻率相同比字串字典序 (注意 Min/Max Heap 的反向邏輯)。 |

## **4\. 考試總結 (Takeaway)**

針對這些題目，我們可以歸納出通用優化法則：

1. **空間換時間 (Space-Time Tradeoff)**：  
   * 在 **Linked List** 中，我們常利用常數空間 $O(1)$ 指標來優化遞迴的 $O(N)$ 堆疊空間。  
   * 在 **Top K** 問題中，利用 Hash Map 預處理是標準起手式。  
2. **不變量思維 (Invariant Thinking)**：  
   * **Monotonic Stack** 的精髓在於：「只要堆疊性質被破壞，就是計算答案的時機」。這是一個非常強的邏輯觸發點。  
3. **邊界條件的數學處理**：  
   * Linked List 的 Dummy Node 其實是將邊界情況 ($Head$ 變動) 歸納為一般情況的數學技巧。  
   * Circular Array 利用 $i \\% N$ 將線性空間映射為環狀群結構。

希望這份統整能幫助你在數學分析與演算法開發上更上一層樓！
