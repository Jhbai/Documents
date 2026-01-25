# **高效能異構運算架構：CUDA C++ 程式設計、編譯工程與演算法優化之深度研究報告**

## **1\. 異構運算典範轉移與 CUDA 執行模型解析**

在當代高效能運算（HPC）與人工智慧（AI）的技術版圖中，運算架構已從單一的中央處理器（CPU）主導模式，徹底轉型為 CPU 與圖形處理單元（GPU）協同工作的異構運算（Heterogeneous Computing）模式。此典範轉移的核心動力來自於物理極限的突破與架構設計哲學的根本性差異。CPU 遵循「延遲導向（Latency-oriented）」的設計哲學，擁有龐大的快取記憶體（Cache）與複雜的分支預測（Branch Prediction）邏輯，旨在極小化單一執行緒的指令延遲；相對地，GPU 則採用「吞吐量導向（Throughput-oriented）」的設計，將絕大多數的晶體管資源投入於算術邏輯單元（ALU），透過大規模並行執行緒（Massive Parallelism）來隱藏記憶體存取延遲 1。

NVIDIA 推出的 CUDA（Compute Unified Device Architecture）平台，正是橋接此二元架構的關鍵技術。CUDA 並非一種全新的程式語言，而是標準 C++ 的超集與擴充。它引入了特定的語法擴充與運行時庫（Runtime API），使得開發者能夠直接調度 GPU 內部的數千個計算核心。本章將深入剖析 CUDA C++ 的底層語法機制、執行空間的劃分，以及記憶體層級的精密控制。

### **1.1 函數執行空間說明符的語意與編譯行為**

在 CUDA C++ 的編譯模型中，原始碼被嚴格劃分為「主機端（Host）」與「裝置端（Device）」兩大執行領域。為了指示編譯器（nvcc）正確地生成對應架構的指令集（Host 端的 x86-64/ARM 與 Device 端的 PTX/SASS），CUDA 引入了函數執行空間說明符（Function Execution Space Specifiers）。這些說明符不僅定義了函數在哪裡執行，還定義了函數可以從哪裡被呼叫。

#### **1.1.1 \_\_global\_\_：異步並行運算的入口點**

\_\_global\_\_ 關鍵字用於宣告核心函數（Kernel），這是 GPU 平行運算的起點。從系統架構的角度分析，Kernel 的啟動是一個複雜的跨裝置操作。當 Host 端的 CPU 執行緒呼叫一個 Kernel 時，它實際上是向 GPU 的指令流（Stream）提交了一個執行請求。

* **執行與呼叫語意**：\_\_global\_\_ 函數在裝置（GPU）上執行，但通常由主機（CPU）發起呼叫。值得注意的是，隨著動態並行（Dynamic Parallelism）技術的引入（Compute Capability 3.5+），Kernel 亦可從另一個在 GPU 上運行的 Kernel 啟動，這使得遞迴演算法與自適應網格細化（Adaptive Mesh Refinement）等複雜邏輯得以在 GPU 內部閉環完成 2。  
* **回傳值限制**：由於 Kernel 是由成千上萬個執行緒同時執行，邏輯上無法定義單一的「回傳值」來反饋給 Host。因此，\_\_global\_\_ 函數的回傳類型必須為 void。任何運算結果的傳回都必須透過寫入全域記憶體（Global Memory）來完成 3。  
* **異步特性（Asynchronous Execution）**：除了極少數例外（如透過 cudaDeviceSynchronize 顯式同步），Kernel 的啟動對 Host 而言是非阻塞（Non-blocking）的。這意味著 CPU 在發出 Kernel 啟動指令後，不會等待 GPU 計算完成，而是立即繼續執行下一行程式碼。這種設計允許 CPU 與 GPU 進行重疊執行（Overlapping），極大化系統整體的吞吐量。若程式邏輯依賴 Kernel 的計算結果，開發者必須在讀取結果前插入同步屏障。

#### **1.1.2 \_\_device\_\_：裝置端的封裝邏輯**

\_\_device\_\_ 函數是僅在 GPU 上執行，且僅能被其他 \_\_device\_\_ 或 \_\_global\_\_ 函數呼叫的輔助函數。

* **指令集生成**：這類函數會被編譯為 GPU 的 ISA（如 NVIDIA 的 SASS）。  
* **內聯優化（Inlining）**：為了減少函數呼叫的堆疊開銷（Stack Overhead），nvcc 編譯器預設傾向於將小型的 \_\_device\_\_ 函數進行內聯展開（Inline）。然而，在某些情況下，過度的內聯會導致指令快取（Instruction Cache）溢出或暫存器壓力過大。開發者可使用 \_\_noinline\_\_ 修飾符強制編譯器生成實際的函數呼叫指令，或使用 \_\_forceinline\_\_ 強制展開 4。

#### **1.1.3 \_\_host\_\_：傳統 C++ 的兼容性**

\_\_host\_\_ 關鍵字表示函數在 CPU 上執行。這是所有標準 C++ 函數的預設屬性。

* **混合編譯策略 (\_\_host\_\_ \_\_device\_\_)**：CUDA 允許將函數同時標記為 \_\_host\_\_ \_\_device\_\_。這是一個極為強大的特性，指示編譯器為該函數生成兩個版本的二進制碼：一個用於 CPU，一個用於 GPU。這在撰寫通用的數學庫（如向量加法、矩陣乘法核心邏輯）時至關重要，能確保同一套演算法邏輯在異構環境下的一致性，並大幅減少程式碼重複 2。在這種函數內部，若需針對 CPU 或 GPU 進行不同的實作（例如 CPU 使用 std::cout 而 GPU 使用 printf），可使用 \_\_CUDA\_ARCH\_\_ 巨集進行條件編譯判斷 2。

### **1.2 記憶體階層與變數屬性說明符**

CUDA 架構的效能優化在很大程度上取決於對記憶體階層（Memory Hierarchy）的精準控制。不同的記憶體空間擁有截然不同的頻寬、延遲與可見範圍。

| 說明符 (Specifier) | 記憶體空間 (Memory Space) | 生命週期 (Lifetime) | 可見範圍 (Scope) | 存取特性與用途 |
| :---- | :---- | :---- | :---- | :---- |
| **\_\_device\_\_** | Global Memory (DRAM) | 應用程式運行期間 | 所有執行緒 (Grid) \+ Host | 容量最大但延遲最高（\~400-800 cycles）。需透過 Coalescing 優化頻寬。 |
| **\_\_constant\_\_** | Constant Memory | 應用程式運行期間 | 所有執行緒 (Grid) \+ Host | 唯讀。具有專屬快取（Constant Cache），當所有執行緒讀取相同位址時（廣播）效能極佳。 |
| **\_\_shared\_\_** | Shared Memory (On-chip) | Block 執行期間 | 同一 Block 內的執行緒 | 晶片上記憶體，極低延遲（\~20-30 cycles）。可程式化控制的 L1 Cache，用於 Block 內資料交換。 |
| **\_\_managed\_\_** | Unified Memory | 應用程式運行期間 | Host \+ Device | 支援自動分頁遷移（Page Migration）。簡化記憶體管理，但在舊架構或特定存取模式下可能有效能懲罰。 |
| *(無修飾符/區域變數)* | Register / Local Memory | Thread 執行期間 | 單一 Thread | 速度最快。若暫存器溢出（Spill）則會使用 Local Memory（實際存於 DRAM），導致效能驟降。 |

**深入解析 \_\_shared\_\_ 的重要性**： \_\_shared\_\_ 變數存儲於每個串流多處理器（SM）內部的專屬記憶體庫中。其頻寬遠高於全域記憶體，且是實現執行緒間通訊（Inter-thread Communication）的唯一高效途徑。在矩陣乘法、卷積運算等演算法中，透過將全域記憶體的資料「預取（Prefetch）」至共享記憶體，可大幅減少對 DRAM 的重複存取，這是 CUDA 效能優化的核心模式 4。

### **1.3 程式碼架構範例：混合編譯的實踐**

一個標準的 CUDA C++ 程式通常由 .cu 檔案構成，內部混合了 Host 與 Device 程式碼。以下範例展示了完整的架構，包含記憶體管理、Kernel 啟動與異構函數的定義：

C++

\#**include** \<cuda\_runtime.h\>  
\#**include** \<iostream\>

// 數學核心函數  
// 使用 \_\_host\_\_ \_\_device\_\_ 使其可在 CPU 和 GPU 兩端共用  
\_\_host\_\_ \_\_device\_\_ inline float sigmoid(float x) {  
    return 1.0f / (1.0f \+ expf(-x));  
}

// \[Global Code\] Kernel 入口點  
// 負責計算並行邏輯  
\_\_global\_\_ void activationKernel(float\* d\_in, float\* d\_out, int n) {  
    // 計算全域唯一的執行緒索引 (Global Thread Index)  
    int idx \= blockIdx.x \* blockDim.x \+ threadIdx.x;  
      
    // 邊界檢查 (Boundary Check)，防止記憶體越界  
    if (idx \< n) {  
        d\_out\[idx\] \= sigmoid(d\_in\[idx\]);  
    }  
}

// \[Host Code\] 主程式邏輯  
void runCudaProcess() {  
    int N \= 1024 \* 1024;  
    size\_t bytes \= N \* sizeof(float);

    // 1\. Host 記憶體配置 (Pinned Memory 可優化傳輸速度)  
    float \*h\_in, \*h\_out;  
    cudaMallocHost(\&h\_in, bytes);  
    cudaMallocHost(\&h\_out, bytes);

    // 初始化數據...  
    for(int i=0; i\<N; i++) h\_in\[i\] \= static\_cast\<float\>(i);

    // 2\. Device 記憶體配置  
    float \*d\_in, \*d\_out;  
    cudaMalloc(\&d\_in, bytes);  
    cudaMalloc(\&d\_out, bytes);

    // 3\. 資料傳輸 Host \-\> Device  
    cudaMemcpy(d\_in, h\_in, bytes, cudaMemcpyHostToDevice);

    // 4\. Grid 與 Block 維度設計  
    // 每個 Block 256 個執行緒 (32 的倍數)  
    int blockSize \= 256;  
    // 計算所需的 Block 數量，向上取整  
    int gridSize \= (N \+ blockSize \- 1) / blockSize;

    // 5\. 啟動 Kernel  
    // \<\<\<GridDim, BlockDim, SharedMemSize, Stream\>\>\>  
    activationKernel\<\<\<gridSize, blockSize\>\>\>(d\_in, d\_out, N);

    // 6\. 資料傳輸 Device \-\> Host  
    // 此函數會隱式同步 (Implicit Synchronization)  
    cudaMemcpy(h\_out, d\_out, bytes, cudaMemcpyDeviceToHost);

    // 驗證與清理資源...  
    cudaFree(d\_in);  
    cudaFree(d\_out);  
    cudaFreeHost(h\_in);  
    cudaFreeHost(h\_out);  
}

## ---

**2\. 執行緒階層設計與硬體映射原則**

CUDA 的強大之處在於其可擴展的編程模型，該模型透過 Grid（網格）、Block（區塊）與 Thread（執行緒）三個抽象層次，完美映射了 GPU 的硬體架構。理解這種映射關係是設計高效 Kernel 的前提。

### **2.1 抽象層次與硬體單元的對應關係**

| 軟體抽象層 (Software Concept) | 硬體執行單元 (Hardware Unit) | 資源管理與調度特性 |
| :---- | :---- | :---- |
| **Thread (執行緒)** | CUDA Core / SP (Streaming Processor) | 擁有私有的暫存器 (Registers)。由硬體排程器以 Warp 為單位進行指令發送。 |
| **Block (區塊)** | SM (Streaming Multiprocessor) | 一個 Block 必須完整地被分配到一個 SM 上執行，不可跨 SM 分割。Block 內的執行緒共享 SM 的 Shared Memory 與 L1 Cache。 |
| **Grid (網格)** | GPU Device (Whole Chip) | Grid 中的 Blocks 被硬體動態分配到可用的 SM 上。Grid 內的 Blocks 之間沒有同步機制（除了 Global Memory 原子操作）。 |

此架構隱含了一個關鍵設計原則：**Block 的獨立性**。CUDA 編程模型要求 Grid 中的每個 Block 都能獨立執行，且執行順序是不確定的（可能並行，也可能序列）。這使得編譯後的程式能夠在不同規模的 GPU（例如從只有 2 個 SM 的嵌入式 Jetson 到擁有 100 個 SM 的資料中心 H100）上無縫運行，實現了硬體的可擴展性 6。

### **2.2 Grid 與 Block 的維度設計原則**

在定義 dim3 grid 與 dim3 block 時，需考量硬體限制與效能優化指標。

#### **2.2.1 Block Size 的設計：32 的倍數法則**

GPU 的指令執行並非以單一 Thread 為單位，而是以 **Warp（執行緒束）** 為單位。一個 Warp 包含 32 個連續的執行緒，它們以 SIMT（Single Instruction, Multiple Threads）模式運行，即在同一時刻執行相同的指令但處理不同的數據。

* **黃金法則**：Block 的大小（blockDim.x \* blockDim.y \* blockDim.z）應始終設為 **32 的倍數**。  
* **原因分析**：若 Block 大小為 33，硬體會分配 2 個 Warps（64 個執行緒槽位）。第一個 Warp 全滿，第二個 Warp 僅有 1 個活躍執行緒，其餘 31 個槽位閒置。這會導致硬體利用率顯著下降 7。  
* **推薦數值**：通常建議使用 128、256 或 512 個執行緒。  
  * **128/256**：通常能提供較好的細粒度調度，有助於隱藏延遲。  
  * **512/1024**：適合需要大量 Shared Memory 協作的演算法，但需注意暫存器壓力可能導致佔用率（Occupancy）下降。  
* **硬體上限**：現代架構（Compute Capability 2.0+）每個 Block 最多支援 1024 個執行緒。超過此限制將導致 Kernel 啟動失敗 9。

#### **2.2.2 Grid Size 的設計：數據覆蓋與 SM 飽和**

Grid 的大小通常由數據總量與 Block 大小決定。

* **基本公式**：GridDim \= (TotalElements \+ BlockDim \- 1\) / BlockDim。這個公式利用整數除法的特性實現了向上取整（Ceiling），確保即使數據量無法被 Block 大小整除，最後一個 Block 也能處理剩餘的邊界數據。  
* **SM 飽和度**：為了充分利用 GPU 的算力，Grid 中的 Block 數量應遠大於 GPU 的 SM 數量（例如至少 2-4 倍於 SM 數）。這讓硬體排程器（GigaThread Engine）能夠在某個 Block 等待記憶體讀取時，快速切換到另一個就緒的 Block 執行，從而隱藏記憶體延遲。

### **2.3 多維度索引計算與映射公式**

CUDA 支援 1D、2D、3D 的 Grid 和 Block 配置，主要是為了簡化圖像處理（2D）或體積渲染（3D）等領域的座標計算。然而，硬體記憶體本質上是線性的一維位址空間。因此，將多維執行緒 ID 映射回線性記憶體位址是 Kernel 撰寫的基本功。

#### **2.3.1 一維配置（1D Grid, 1D Block）**

適用於向量加法、訊號處理。

* **索引計算**：  
  C++  
  int tid \= blockIdx.x \* blockDim.x \+ threadIdx.x;  
  if (tid \< N) {... }

#### **2.3.2 二維配置（2D Grid, 2D Block）**

適用於矩陣運算、圖像濾鏡。通常將 X 軸對應圖像的寬（Width, Column），Y 軸對應高（Height, Row）。

* **Host 端設定**：  
  C++  
  dim3 block(16, 16); // 每個 Block 256 threads  
  dim3 grid((Width \+ block.x \- 1) / block.x, (Height \+ block.y \- 1) / block.y);

* **Device 端索引與線性化**：  
  C++  
  // 計算像素座標  
  int x \= blockIdx.x \* blockDim.x \+ threadIdx.x; // Column  
  int y \= blockIdx.y \* blockDim.y \+ threadIdx.y; // Row

  // 邊界檢查  
  if (x \< Width && y \< Height) {  
      // 線性化 (Row-major layout)  
      // Global Index \= Row \* RowStride \+ Column  
      int global\_idx \= y \* Width \+ x;

      // 處理 pixel\[global\_idx\]...  
  }

  **重要原則**：在 C/C++ 中，二維陣列通常是 Row-major 存儲的，因此計算索引時應確保 x（變化最快的分量）對應連續的記憶體位址，這對於實現 **記憶體合併存取（Memory Coalescing）** 至關重要。若 x 與 y 對調，將導致嚴重的頻寬浪費 12。

#### **2.3.3 三維配置（3D Grid, 3D Block）**

適用於醫學影像（MRI/CT）、流體動力學模擬。

* **索引計算**：  
  C++  
  int x \= blockIdx.x \* blockDim.x \+ threadIdx.x;  
  int y \= blockIdx.y \* blockDim.y \+ threadIdx.y;  
  int z \= blockIdx.z \* blockDim.z \+ threadIdx.z;

  // 假設記憶體佈局為 (Depth, Height, Width)  
  int global\_idx \= z \* (Height \* Width) \+ y \* Width \+ x;

## ---

**3\. 編譯鏈工程：NVCC、G++ 與分離式編譯操作**

CUDA 的編譯過程遠比標準 C++ 複雜，因為它涉及異構指令集的生成、封裝與連結。nvcc（NVIDIA CUDA Compiler Driver）是控制此流程的核心工具，它實際上是一個編譯器驅動程式，負責調度宿主機編譯器（如 g++ 或 cl.exe）與 NVIDIA 裝置編譯器（ptxas）。

### **3.1 雙重編譯流程與中間語言 PTX**

當 nvcc 處理一個 .cu 檔案時，會執行以下關鍵步驟 15：

1. **程式碼分離（Separation）**：預處理器將原始碼分為 Host C++ 代碼與 Device CUDA 代碼。  
2. **Device 編譯**：  
   * Device 代碼首先被編譯為 **PTX (Parallel Thread Execution)**。PTX 是一種類似組語的中間語言（Virtual ISA），它與具體的 GPU 硬體無關，保證了向前的相容性。  
   * 接著，ptxas 將 PTX 組譯為特定 GPU 架構的機器碼 **SASS (Streaming Assembler)**。這是真實硬體執行的二進制碼。  
3. **Host 編譯**：Host 代碼中的 Kernel 啟動語法（\<\<\<...\>\>\>）被替換為 CUDA Runtime API 的呼叫（如 cudaLaunchKernel），然後交由系統的 C++ 編譯器（g++）編譯為物件檔。  
4. **Fatbinary 嵌入**：編譯好的 PTX 與 SASS 被封裝成 Fatbinary 格式，並嵌入到 Host 物件檔的數據段中。這使得最終的可執行檔能夠在不同世代的 GPU 上運行（驅動程式可透過 JIT 即時編譯內含的 PTX）。

### **3.2 分離式編譯與連結（Separate Compilation & Linking）**

在早期 CUDA 版本中，所有的 Device 程式碼必須寫在同一個檔案內，這嚴重限制了大型專案的模組化。現代 CUDA（5.0+）引入了 **Relocatable Device Code (RDC)**，支援跨檔案的 \_\_device\_\_ 函數呼叫。這需要特定的編譯與連結步驟 16。

#### **3.2.1 操作指令詳解**

假設專案結構如下：

* a.cu：定義了 \_\_device\_\_ 函數 gpu\_func()。  
* b.cu：定義了 \_\_global\_\_ Kernel，並呼叫 a.cu 中的 gpu\_func()。  
* main.cpp：C++ 主程式，呼叫 b.cu 的 Kernel。

**步驟一：生成裝置可重定位物件（Device Compilation）**

使用 \-dc（Device Compile）或 \-rdc=true 旗標。這相當於 C++ 的 \-c，但保留了 Device 端的連結資訊。

Bash

\# 生成 a.o 與 b.o  
nvcc \-arch=sm\_75 \-dc a.cu \-o a.o  
nvcc \-arch=sm\_75 \-dc b.cu \-o b.o

**步驟二：裝置連結（Device Linking）**

這是最關鍵且常被忽略的一步。在將物件檔交給 g++ 連結之前，必須先用 nvcc 執行一次裝置連結，解析 GPU 函數的地址，生成一個包含連結表的中介物件檔（通常命名為 dlink.o 或 link.o）。

Bash

\# 連結 a.o 與 b.o，生成 link.o  
nvcc \-arch=sm\_75 \-dlink a.o b.o \-o link.o

**步驟三：Host 編譯**

編譯純 C++ 的主程式。

Bash

g++ \-c main.cpp \-o main.o

**步驟四：最終連結（Final Linking）**

將所有的物件檔（Device objects, Device link object, Host object）連結為可執行檔。

Bash

g++ a.o b.o link.o main.o \-lcudart \-L/usr/local/cuda/lib64 \-o my\_app

注意：最後一步通常需連結 cudart（CUDA Runtime Library）。

### **3.3 現代 CMake 建置系統整合**

手動撰寫 Makefile 處理上述 RDC 流程極為繁瑣且容易出錯。現代 CMake（3.8+）將 CUDA 視為原生支援的語言（First-class Language），大幅簡化了構建配置 19。

**標準 CMakeLists.txt 範本**：

CMake

cmake\_minimum\_required(VERSION 3.18) \# 建議使用較新版本以支援新架構  
project(CudaHPC LANGUAGES CXX CUDA)

\# 1\. 設定 C++ 與 CUDA 標準  
set(CMAKE\_CXX\_STANDARD 17)  
set(CMAKE\_CUDA\_STANDARD 17)

\# 2\. 設定目標 GPU 架構  
\# 例如：支援 Turing (75) 與 Ampere (86) 架構  
\# "native" 會自動偵測當前機器的 GPU  
set(CMAKE\_CUDA\_ARCHITECTURES 75 86) 

\# 3\. 啟用分離式編譯 (RDC)  
\# 這會自動處理 \-dc 與 \-dlink 的繁瑣步驟  
set(CMAKE\_CUDA\_SEPARABLE\_COMPILATION ON)

\# 4\. 定義執行檔  
add\_executable(cuda\_app  
    src/main.cpp  
    src/kernels.cu  
    src/device\_funcs.cu  
)

\# 5\. 連結必要的庫  
\# CMake 會自動處理 CUDA Runtime 的連結  
\# 若需使用 cuBLAS, cuFFT 等，需使用 FindPackage 或新的目標導向方式  
target\_link\_libraries(cuda\_app PRIVATE CUDA::cudart)

**關鍵參數解析**：

* project(..., LANGUAGES CUDA)：這行指令啟用了 CMake 的 CUDA 支援，它會自動尋找 nvcc 並設定相關的編譯變數。  
* CMAKE\_CUDA\_ARCHITECTURES：這是 CMake 3.18 引入的重要變數，用來替代過時的 CUDA\_NVCC\_FLAGS 手動設定 \-gencode。它確保編譯器生成正確的 SASS 代碼 23。

## ---

**4\. CUDA 核心演算法操作與設計模式**

掌握語法僅是入門，HPC 的精髓在於演算法的設計。在 GPU 上，演算法的優化核心在於「記憶體存取模式」與「執行緒協作」。本章將探討幾種最具代表性的 CUDA 演算法模式。

### **4.1 Grid-Stride Loops：解耦網格與數據規模**

初學者常犯的錯誤是假設 Grid 的總執行緒數（GridDim \* BlockDim）等於數據總量 N。然而，硬體對 Grid 大小有限制，且數據量可能遠超此限制。**Grid-Stride Loop（網格跨步迴圈）** 是解決此問題的標準模式。

**實作邏輯**：

並非讓每個執行緒只處理一個數據元素，而是讓執行緒在處理完當前元素後，跳過「整個 Grid 的寬度」去處理下一個元素，直到遍歷完所有數據。

C++

\_\_global\_\_ void saxpy\_grid\_stride(int n, float a, float \*x, float \*y) {  
    // 起始索引：當前執行緒在 Grid 中的唯一 ID  
    int idx \= blockIdx.x \* blockDim.x \+ threadIdx.x;  
    // 步長 (Stride)：整個 Grid 的總執行緒數  
    int stride \= blockDim.x \* gridDim.x;

    // 迴圈處理  
    for (int i \= idx; i \< n; i \+= stride) {  
        y\[i\] \= a \* x\[i\] \+ y\[i\];  
    }  
}

**設計優勢** 25：

1. **可擴展性（Scalability）**：此 Kernel 可以處理任意大小的 N，無論 N 是小於還是遠大於 Grid 大小。這使得程式碼在不同等級的 GPU 上都具備強健性。  
2. **指令級並行（ILP）**：當一個執行緒序列處理多個元素時，編譯器可以進行循環展開（Loop Unrolling），增加每個執行緒的獨立指令流，有助於掩蓋記憶體讀取的延遲。  
3. **除錯便利性**：開發者可以將 Grid 設定為 \<\<\<1, 1\>\>\>，強制 GPU 序列執行代碼，這在除錯複雜邏輯（如 Race Condition）時非常有用。

### **4.2 矩陣乘法優化：共享記憶體平鋪 (Shared Memory Tiling)**

矩陣乘法（![][image1]）是深度學習與科學計算的基石。樸素（Naive）實作中，計算 ![][image2] 的每個元素都需要從全域記憶體讀取 ![][image3] 的一整列與 ![][image4] 的一整行。這會導致極高的記憶體頻寬需求，且數據重複讀取率極高。

**Tiling 演算法原理**：

利用 Shared Memory 作為可程式化的 L1 Cache。將大矩陣分割為若干個小塊（Tile），例如 ![][image5]。

1. **協作載入**：Block 內的執行緒合作將 ![][image3] 的一個 Tile 和 ![][image4] 的一個 Tile 載入 Shared Memory。  
2. **計算**：執行緒在高速的 Shared Memory 上進行點積運算。  
3. **迭代**：移動到下一個 Tile，重複上述步驟。

**程式碼實作詳解** 28：

C++

// 假設 TILE\_WIDTH 為 16  
\#**define** TILE\_WIDTH 16

\_\_global\_\_ void matrixMulTiled(float\* A, float\* B, float\* C, int width) {  
    // 宣告 Shared Memory，用於存放子矩陣  
    \_\_shared\_\_ float ds\_A;  
    \_\_shared\_\_ float ds\_B;

    // 計算目標 C 元素的座標  
    int bx \= blockIdx.x; int by \= blockIdx.y;  
    int tx \= threadIdx.x; int ty \= threadIdx.y;

    int Row \= by \* TILE\_WIDTH \+ ty;  
    int Col \= bx \* TILE\_WIDTH \+ tx;  
      
    float Cvalue \= 0.0;

    // 核心迴圈：以 Tile 為單位遍歷矩陣  
    // m 代表當前處理的是第幾個 Tile  
    for (int m \= 0; m \< width / TILE\_WIDTH; \++m) {  
        // 1\. 協作載入數據：每個執行緒載入一個元素  
        // 需注意記憶體合併存取 (Coalescing)  
        ds\_A\[ty\]\[tx\] \= A;  
        ds\_B\[ty\]\[tx\] \= B;  
          
        // 2\. 同步屏障：確保所有執行緒都已完成載入  
        // 若無此同步，部分執行緒可能會讀到舊數據或未初始化的垃圾數據  
        \_\_syncthreads();

        // 3\. 計算部分積：完全在 Shared Memory 上進行  
        for (int k \= 0; k \< TILE\_WIDTH; \++k) {  
            Cvalue \+= ds\_A\[ty\]\[k\] \* ds\_B\[k\]\[tx\];  
        }

        // 4\. 同步屏障：確保所有執行緒都計算完畢，才能進入下一輪載入  
        // 否則新載入的數據會覆蓋掉尚未被其他執行緒使用完的數據  
        \_\_syncthreads();  
    }  
      
    // 寫回結果  
    if (Row \< width && Col \< width)  
        C \= Cvalue;  
}

**深度解析**：此演算法將全域記憶體的存取次數降低了 TILE\_WIDTH 倍（例如 16 倍）。這是因為每個元素從 DRAM 載入一次後，在 Shared Memory 中被重複使用了 16 次。這是提升算術強度（Arithmetic Intensity）的經典範例。

### **4.3 並行歸約 (Parallel Reduction)**

歸約操作（如 Sum, Max, Min）是將陣列化簡為單一數值的過程。在 CPU 上這是 ![][image6] 的序列操作，在 GPU 上則採用樹狀結構的並行歸約（Tree-based Reduction）。

**優化演進路徑** 30：

1. **交錯定址（Interleaved Addressing）**：使用 stride 進行折疊。初期版本常因使用模數運算（%）導致指令開銷大，且因記憶體存取不連續導致 **Warp Divergence**（部分執行緒活躍，部分閒置）。  
2. **連續定址（Sequential Addressing）**：修改索引邏輯，讓活躍的執行緒在 ID 上是連續的。這解決了 Divergence 問題，確保了 Warp 內的執行緒要麼全做，要麼全不做。  
3. **解決 Bank Conflict**：Shared Memory 被劃分為 32 個 Bank。若多個執行緒存取同一個 Bank 的不同地址，會發生衝突並導致序列化。透過適當的 Padding 或索引偏移可解決此問題。  
4. **Warp Shuffle 指令**：在最後的歸約階段（當剩餘元素少於 32 個時），不再需要讀寫 Shared Memory。利用 Kepler 架構引入的 \_\_shfl\_down\_sync 指令，執行緒可以直接讀取同一 Warp 內其他執行緒的暫存器數值。這完全消除了 Shared Memory 的延遲與 \_\_syncthreads() 的開銷，是極致優化的關鍵。

## ---

**5\. 基本 Template 與專案架構規範**

為了構建可維護、可擴展且符合現代軟體工程標準的 CUDA 專案，遵循嚴謹的檔案結構與介面設計模式（Interface Design Patterns）是必要的。

### **5.1 檔案類型與職責劃分**

混合編程最大的挑戰在於 C++ 編譯器（g++）無法理解 CUDA 語法，而 nvcc 雖然可以編譯 C++，但將所有代碼都交給 nvcc 編譯會增加編譯時間並可能引發相容性問題。因此，**關注點分離（Separation of Concerns）** 是最佳實踐 31。

| 副檔名 | 負責編譯器 | 內容與職責 |
| :---- | :---- | :---- |
| **.h / .hpp** | g++ & nvcc | **純 C++ 介面**。不可包含任何 CUDA 關鍵字（如 \_\_global\_\_, \<\<\<\>\>\>）。僅包含 extern "C" 宣告或 Pimpl 類別定義。 |
| **.cpp** | g++ | **Host 邏輯實作**。負責資料 I/O、流程控制。僅透過 .h 定義的介面呼叫 CUDA 功能。 |
| **.cuh** | nvcc | **CUDA 標頭檔**。包含 \_\_device\_\_ 函數宣告、Template Kernel 定義、Shared Memory 結構。類似 C++ 的 .hpp，但專供 CUDA 使用。 |
| **.cu** | nvcc | **CUDA 核心實作**。包含 Kernel 定義 (\_\_global\_\_) 與封裝函數（Wrapper Functions）。 |

### **5.2 推薦專案模板：Wrapper Pattern**

此模式透過一個純 C++ 的中介層（Wrapper）隱藏 GPU 實作細節，使得主程式 main.cpp 可以完全與 CUDA 解耦。

#### **1\. include/cuda\_kernels.cuh (Device 內部邏輯)**

這是僅供 .cu 檔案引用的標頭檔，定義具體的演算法邏輯。

C++

\#**pragma** once  
\#**include** \<cuda\_runtime.h\>

// 樣板化的 Device 函數，增加重用性  
template \<typename T\>  
\_\_device\_\_ T compute\_op(T a, T b) {  
    return a \* b \+ a;  
}

// 結構體定義，若需在 Kernel 中使用複雜結構  
struct PhysicsParams {  
    float gravity;  
    float friction;  
};

#### **2\. include/cuda\_api.h (對外 C++ 介面)**

這是 CPU 端看到的介面，完全標準的 C++。

C++

\#**pragma** once  
\#**include** \<vector\>

// 使用 extern "C" 避免 C++ Name Mangling，方便連結，也支援跨語言呼叫 (如 Python ctypes)  
extern "C" {  
    // 初始化 GPU 資源  
    void gpu\_init();  
      
    // 執行核心運算  
    // 參數使用原始指標，避免傳遞 STL 容器到邊界  
    void launch\_vector\_process(const float\* host\_in, float\* host\_out, int n);  
      
    // 釋放資源  
    void gpu\_finalize();  
}

// 或者使用更現代的 C++ 類別封裝 (RAII 風格)  
class CudaComputeEngine {  
public:  
    CudaComputeEngine();  
    \~CudaComputeEngine();  
    void process(const std::vector\<float\>& input, std::vector\<float\>& output);  
private:  
    void\* d\_buffer\_; // 使用 void\* 隱藏 float\* 等 device 指標，避免 header 汙染  
};

#### **3\. src/kernels.cu (實作層)**

連結 cuda\_api.h 與 cuda\_kernels.cuh 的橋樑。

C++

\#**include** "cuda\_api.h"  
\#**include** "cuda\_kernels.cuh"  
\#**include** \<cstdio\>  
\#**include** \<cassert\>

// 具體 Kernel 實作  
\_\_global\_\_ void process\_kernel(const float\* in, float\* out, int n) {  
    int idx \= blockIdx.x \* blockDim.x \+ threadIdx.x;  
    int stride \= blockDim.x \* gridDim.x;  
    for (int i \= idx; i \< n; i \+= stride) {  
        out\[i\] \= compute\_op(in\[i\], 2.0f); // 呼叫.cuh 中的 device 函數  
    }  
}

// C++ 介面實作  
void launch\_vector\_process(const float\* host\_in, float\* host\_out, int n) {  
    float \*d\_in, \*d\_out;  
    size\_t size \= n \* sizeof(float);

    // 錯誤處理巨集 (生產環境建議使用 checkCudaErrors)  
    cudaMalloc(\&d\_in, size);  
    cudaMalloc(\&d\_out, size);

    cudaMemcpy(d\_in, host\_in, size, cudaMemcpyHostToDevice);

    // 佔用率計算與啟動配置  
    int blockSize \= 256;  
    int numBlocks \= (n \+ blockSize \- 1) / blockSize;  
    // 限制最大 Block 數以避免過度排程開銷  
    numBlocks \= std::min(numBlocks, 65535); 

    process\_kernel\<\<\<numBlocks, blockSize\>\>\>(d\_in, d\_out, n);  
      
    // 檢查異步錯誤  
    cudaError\_t err \= cudaGetLastError();  
    if (err\!= cudaSuccess) {  
        fprintf(stderr, "Kernel launch failed: %s\\n", cudaGetErrorString(err));  
    }

    // 隱式同步  
    cudaMemcpy(host\_out, d\_out, size, cudaMemcpyDeviceToHost);

    cudaFree(d\_in);  
    cudaFree(d\_out);  
}

#### **4\. src/main.cpp (應用層)**

完全無 CUDA 依賴的主程式。

C++

\#**include** "cuda\_api.h"  
\#**include** \<vector\>  
\#**include** \<iostream\>

int main() {  
    const int N \= 1000000;  
    std::vector\<float\> data\_in(N, 1.0f);  
    std::vector\<float\> data\_out(N);

    // 呼叫封裝函數  
    launch\_vector\_process(data\_in.data(), data\_out.data(), N);

    std::cout \<\< "Result: " \<\< data\_out \<\< std::endl;  
    return 0;  
}

透過此架構，開發團隊可以讓演算法工程師專注於 .cu 的優化，而系統工程師專注於 .cpp 的業務邏輯，並透過 CMake 輕鬆整合雙方的工作成果。這不僅符合軟體工程的解耦原則，也為未來移植到其他加速器架構（如 AMD HIP 或 Intel SYCL）保留了最大的彈性。

#### **引用的著作**

1. CUDA C++ Programming Guide | NVIDIA Docs, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/pdf/CUDA\_C\_Programming\_Guide.pdf](https://docs.nvidia.com/cuda/pdf/CUDA_C_Programming_Guide.pdf)  
2. 2.1. Intro to CUDA C++ — CUDA Programming Guide \- NVIDIA Documentation, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html)  
3. What is the difference between \_\_global\_\_ and \_\_host\_\_ \_\_device\_\_? \- Stack Overflow, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/75844453/what-is-the-difference-between-global-and-host-device](https://stackoverflow.com/questions/75844453/what-is-the-difference-between-global-and-host-device)  
4. CUDA C++ Programming Guide (Legacy) \- NVIDIA Documentation, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-c-programming-guide/](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)  
5. CUDA C++ Best Practices Guide 13.1 documentation, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)  
6. 1.2. Programming Model — CUDA Programming Guide, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html](https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html)  
7. How to Choose the Grid Size and Block Size for a CUDA Kernel? | by OneFlow \- Medium, 檢索日期：1月 25, 2026， [https://oneflow2020.medium.com/how-to-choose-the-grid-size-and-block-size-for-a-cuda-kernel-d1ff1f0a7f92](https://oneflow2020.medium.com/how-to-choose-the-grid-size-and-block-size-for-a-cuda-kernel-d1ff1f0a7f92)  
8. Why launch a multiple of 32 number of threads in CUDA? \- Stack Overflow, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/26611241/why-launch-a-multiple-of-32-number-of-threads-in-cuda](https://stackoverflow.com/questions/26611241/why-launch-a-multiple-of-32-number-of-threads-in-cuda)  
9. Thread block (CUDA programming) \- Wikipedia, 檢索日期：1月 25, 2026， [https://en.wikipedia.org/wiki/Thread\_block\_(CUDA\_programming)](https://en.wikipedia.org/wiki/Thread_block_\(CUDA_programming\))  
10. CUDA Cheat sheet \- Obliczenia naukowe w ICM UW, 檢索日期：1月 25, 2026， [https://kdm.icm.edu.pl/Tutorials/GPU-intro/introduction.en/](https://kdm.icm.edu.pl/Tutorials/GPU-intro/introduction.en/)  
11. 5.1. Compute Capabilities — CUDA Programming Guide, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html)  
12. CUDA Thread Indexing Cheatsheet, 檢索日期：1月 25, 2026， [https://www.eecs.umich.edu/courses/eecs471/resources/materials/CUDA-Thread-Indexing-Cheatsheet.pdf](https://www.eecs.umich.edu/courses/eecs471/resources/materials/CUDA-Thread-Indexing-Cheatsheet.pdf)  
13. Analysis of Thread Blocks and Grids in CUDA Programming \- Oreate AI Blog, 檢索日期：1月 25, 2026， [https://www.oreateai.com/blog/analysis-of-thread-blocks-and-grids-in-cuda-programming/a10302da6f150b6ee62c89f00834744d](https://www.oreateai.com/blog/analysis-of-thread-blocks-and-grids-in-cuda-programming/a10302da6f150b6ee62c89f00834744d)  
14. CUDA estimating threads per blocks and block numbers for 2D grid data \- Stack Overflow, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/33245737/cuda-estimating-threads-per-blocks-and-block-numbers-for-2d-grid-data](https://stackoverflow.com/questions/33245737/cuda-estimating-threads-per-blocks-and-block-numbers-for-2d-grid-data)  
15. the CUDA compiler driver. \- NVCC \- NVIDIA Documentation, 檢索日期：1月 25, 2026， [https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/)  
16. CUDA Compiler Driver NVCC, 檢索日期：1月 25, 2026， [https://planets.utsc.utoronto.ca/\~pawel/PHYD57/CUDA\_Compiler\_Driver\_NVCC.pdf](https://planets.utsc.utoronto.ca/~pawel/PHYD57/CUDA_Compiler_Driver_NVCC.pdf)  
17. How to link host code with a static CUDA library after separable compilation?, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/16289086/how-to-link-host-code-with-a-static-cuda-library-after-separable-compilation](https://stackoverflow.com/questions/16289086/how-to-link-host-code-with-a-static-cuda-library-after-separable-compilation)  
18. Separate Compilation and Linking of CUDA C++ Device Code | NVIDIA Technical Blog, 檢索日期：1月 25, 2026， [https://developer.nvidia.com/blog/separate-compilation-linking-cuda-device-code/](https://developer.nvidia.com/blog/separate-compilation-linking-cuda-device-code/)  
19. A simple example — Modern CMake, 檢索日期：1月 25, 2026， [https://cliutils.gitlab.io/modern-cmake/chapters/basics/example.html](https://cliutils.gitlab.io/modern-cmake/chapters/basics/example.html)  
20. Building Cross-Platform CUDA Applications with CMake | NVIDIA Technical Blog, 檢索日期：1月 25, 2026， [https://developer.nvidia.com/blog/building-cuda-applications-cmake/](https://developer.nvidia.com/blog/building-cuda-applications-cmake/)  
21. Separate CUDA compilation with CMAKE \- c++ \- Stack Overflow, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/55265364/separate-cuda-compilation-with-cmake](https://stackoverflow.com/questions/55265364/separate-cuda-compilation-with-cmake)  
22. CUDA — Modern CMake, 檢索日期：1月 25, 2026， [https://cliutils.gitlab.io/modern-cmake/chapters/packages/CUDA.html](https://cliutils.gitlab.io/modern-cmake/chapters/packages/CUDA.html)  
23. CUDA\_ARCHITECTURES — CMake 4.2.1 Documentation, 檢索日期：1月 25, 2026， [https://cmake.org/cmake/help/latest/prop\_tgt/CUDA\_ARCHITECTURES.html](https://cmake.org/cmake/help/latest/prop_tgt/CUDA_ARCHITECTURES.html)  
24. Correct use of CMAKE\_CUDA\_ARCHITECTURES \- Code \- CMake Discourse, 檢索日期：1月 25, 2026， [https://discourse.cmake.org/t/correct-use-of-cmake-cuda-architectures/1250](https://discourse.cmake.org/t/correct-use-of-cmake-cuda-architectures/1250)  
25. Accelerating Data Processing with Grid Stride Loops in CUDA | by Victor Leung | Medium, 檢索日期：1月 25, 2026， [https://medium.com/@victorleungtw/accelerating-data-processing-with-grid-stride-loops-in-cuda-8adc810d188d](https://medium.com/@victorleungtw/accelerating-data-processing-with-grid-stride-loops-in-cuda-8adc810d188d)  
26. CUDA Week 2: Mastering Thread Organization and Grid-Stride Loops \- Gautam Sharma, 檢索日期：1月 25, 2026， [https://www.gsharma.dev/blog/gpu/week2-cuda-efficient-addition](https://www.gsharma.dev/blog/gpu/week2-cuda-efficient-addition)  
27. CUDA Pro Tip: Write Flexible Kernels with Grid-Stride Loops | NVIDIA Technical Blog, 檢索日期：1月 25, 2026， [https://developer.nvidia.com/blog/cuda-pro-tip-write-flexible-kernels-grid-stride-loops/](https://developer.nvidia.com/blog/cuda-pro-tip-write-flexible-kernels-grid-stride-loops/)  
28. How to Write High-Performance Matrix Multiply in NVIDIA CUDA Tile ..., 檢索日期：1月 25, 2026， [https://developer.nvidia.com/blog/how-to-write-high-performance-matrix-multiply-in-nvidia-cuda-tile/](https://developer.nvidia.com/blog/how-to-write-high-performance-matrix-multiply-in-nvidia-cuda-tile/)  
29. Mastering CUDA Matrix Multiplication: An Introduction to Shared Memory, Tile Memory Coalescing, and Bank Conflicts | by Dhanush | Medium, 檢索日期：1月 25, 2026， [https://medium.com/@dhanushg295/mastering-cuda-matrix-multiplication-an-introduction-to-shared-memory-tile-memory-coalescing-and-d7979499b9c5](https://medium.com/@dhanushg295/mastering-cuda-matrix-multiplication-an-introduction-to-shared-memory-tile-memory-coalescing-and-d7979499b9c5)  
30. 7 Step Optimization of Parallel Reduction with CUDA | by Rimika ..., 檢索日期：1月 25, 2026， [https://medium.com/@rimikadhara/7-step-optimization-of-parallel-reduction-with-cuda-33a3b2feafd8](https://medium.com/@rimikadhara/7-step-optimization-of-parallel-reduction-with-cuda-33a3b2feafd8)  
31. efficient way of cuda file organization: .cpp .h .cu .cuh .curnel files \- Stack Overflow, 檢索日期：1月 25, 2026， [https://stackoverflow.com/questions/15222071/efficient-way-of-cuda-file-organization-cpp-h-cu-cuh-curnel-files](https://stackoverflow.com/questions/15222071/efficient-way-of-cuda-file-organization-cpp-h-cu-cuh-curnel-files)  
32. How to organize a large project that uses CUDA \- Reddit, 檢索日期：1月 25, 2026， [https://www.reddit.com/r/CUDA/comments/1apghmc/how\_to\_organize\_a\_large\_project\_that\_uses\_cuda/](https://www.reddit.com/r/CUDA/comments/1apghmc/how_to_organize_a_large_project_that_uses_cuda/)  
33. CUDA project layout \- Kiui's notebook, 檢索日期：1月 25, 2026， [https://note.kiui.moe/cuda/project\_layout/](https://note.kiui.moe/cuda/project_layout/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAF8AAAAYCAYAAACcESEhAAADLUlEQVR4Xu2YW6gNURjH/3KJyLVccjsuL8iDiBIlUTyQkBfKeePBi1NyCZ2SB4ncSrlfHkREIbeXE0XxwptIDonyonR4IJf/3zfr7Jm1Z/aMLWar9atfzZ41e8+ab631rW82EAgEAg1FHzqHLqcTaNfofG86IjpuFIbRLbS/3/C/MZE+oB30PG2hZ+htOoneoPM6ry6fLnQHfYPyJsVAeot+oz8idaw+fYk+P6XLYP2tojvdCrt4E+2VbMZs+hHlPmQaU+mnSB2XiSbld9gqjKNYnoINyOJkkwX+MP0KG500etLrkTpuBPRQZ+lrWN9nJZv/ORthwU/LDItgK+C037A2atiMjGURoS/6o1omS+lu2EpV//WARRgJm3BZaF8b5J/MoRu9SNvp8GTTLzQw6mNr/OR4+pY+h3WqFseQPqplMJhegvXZPdjKxBXZrKL7kD4AQ+llOt1vyEEBb0d6ZmiiL+gTeCm7FdbxnfGTGfRDeofLYAMsiMItaQ1CEbS619GDSD5PvYEXSnlKfbtg1ZdTq/Ml7F59O6+GlZNtyM5T9bANloOLehNWLfwOqrqU69V/4YJfZAI5/AH4k8ALl+/1G0di3qNXYFVkAo3MK/qOjvXaGhUF6hCs+nK4WVe1meXgBuACvYr6A18r36u/J2FVZGKCu+BLHddCm/JM/2QJzEeyno6blm/z0J7xGPYuU29KrZXvhVuZ2jM7GUAfIT/42vlPwDa5PJQK4jkvT/2me3vOQ3vOOViREMdNojZUUlERtPkp7c2gzajeA4qSVd87tLoU/AN+wx7YFxf4DRFamnrLzar/fSbD/pIo6kJUv9BloX6s8U+iEnxVFEO8tixc4F2q0XM2o74BqFXfa+I+pB/oFK8No+kzehe26cRRULbT9ahd//9tdG/ldaWHUV6b0IrQXyJ5K9ihwF+j07zz9QyAe/lMe/MfA4ur8r2qnlSa6H36GfYavJruh+3Uc1Fu4LWxata4vK7iIF457EXl/xOp4+O0R+waH1VkfuAdelatyBV+g4dm9B0k7/0elSquI/IoqgelCt20iS6JHIfiuTgQCAQCgUAgEIjxE3BptRMSU/P8AAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAABEElEQVR4Xu3TvUoDQRSG4RMkEDEQQkAUIlliGvUOhIBICktBe9u0sdIgksbSwspGRO1yASKkCgpaeAdaBULsRSwUou9xZ9dxsu6WAfGDB4ZzdhjmZ0X+ZLJYwSYWMGHqUyia8UgWcYcXtLGNC3SwhCvUwq9N0tjDG3Yw+bMtVTyjL87KOvEY79iwG1YyuDR0HKaOD+wiZTecnKNpFyoY4BFzdiMiJ+LstyX+qgd28ZfkxN/iV/Q6uhhKxAkmZRY9PKHs9BITTFY6jose6rJdyONekicXcIppt3Eo/p7X3IaJXp2+ssj7L+EB15hxevrK9tGQmPv3cItXnGELR7jBqsRMDKIfeFg35uX7T/rPWPMJCSkp/c7RsHEAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAXCAYAAADUUxW8AAAA3ElEQVR4XmNgGNZAEoirgFgAXYIQYATiZiB+AsQyaHIEgTEQf4ViEJtowAnEi4H4ERD/BmIbVGn8IAiIu4G4Aoj/A7EvqjRuIAbEa4FYFojLGSCao1FU4AGlQBwDZYNsBGkGGUIQaDNA/MoD5cM0t8JV4ACsQDwFiG2RxEABBQqwhUhiGIAfiJcDsQqaOCiRPATiAwwI12CAIiBORxdkQGi+C8TiaHLgVARy2gUglkOTAwGQi44zQAwAGQQHIL+9Z4AECAg/B2ItJPk+IP6FJA9izwViNiQ1o2BwAwBqgCY8YTiPnwAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAYCAYAAADzoH0MAAABDElEQVR4XmNgGAXowAqIHwHxfyT8BYifQdl/gXgrEKvBNOACk4D4GxCboomrAvFdIL4OxDJocnDAA8QHgPgqEIugSoHBQgaIa3zRJWBACYifA/F8IGZEk4MZ/hOILVGlEMCPAWJDOroEEIQzQMJhChCzoMnBQSsDxAZPIJaEYnkgrgfil0AcCcTMcNVoAObE1wwQL8yC4rkMkDBpAWI+mGJsAJ//FRggMXAOiMVQpRAAn/9BABYDIO9hBbjiHwQ4gXgHEP8DYhc0OTAgFP+2DJDA3cUAUYsBNIH4LRAvZUD1PyjEQU5+D8RXGCAxggJAJj9kQKR9UDw/YYDkCRD9B4gfAHEuA8Qbo2D4AQDFDjxnJ33hQQAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAXCAYAAABTYvy6AAAB1klEQVR4Xu2WzytFQRTHv0L5VRZsLOSlkIVSlFhY2VgoxUJZWhClkI1kY4WdjUJKen8BFjZ6exspNlZK/AMsLMT3dN7NvPtj3nPfXJH7qU+vNzP3dM7cmbkDpKSk/DcydMrf6KOLbtN9OkErC7t/jAzKzLWbztNL+k6PzU6DarpOr2gfbaendM4clDBOc5Vg43SIPiI6mDx0D51pYZR+IHp8EiSSawt9QHhnKzTQrtHWCJ3VAaMtjApoAvIbRROt9zdacJqrLZjsJZmxaVoDHdtQMCKaKrpGlxBevLzFc9rm77DgNFdbMJk9CbZJT+gCvaZb0P1UDBmzQ1dRWHycogWnudqCSZsEy+Fr9jroM13J/y+Gv/i4RQtOcy0l2KzRJkFz9JY2G+02vOIPEL9owWmutmCH0GBjRpsX7BX6ySiVfvoEPWzkzcfBaa62YMv4ZrAIeukFdOltILjnS8VprrZgg/QNelJ6WJdPCF7R3vKWZR+3eKe5esGyCCZSC735yDKSz5NgPTB8SNFnCO7puMU7yXUEeguSK6AsEfGF3tAeY5ycwnf0iM7k+/cQ8YkwqIMeaP6iPeT+vAi9jRUj6VwjkQeH6STtRHC2fxN/KdeUlJSU8vkELl2ZJu7MtLwAAAAASUVORK5CYII=>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAYCAYAAAC8/X7cAAADAklEQVR4Xu2XS8hOQRjH/0IRktxyS2RB7okoLCSxYGWhWGNh5Rqrs7GwkVAK9a0kkWxcNxRZsFOikEiEEDspPL9vZj4zcy5O3peFvl/9O987z5w5zzzzzDPzSf38fww3DckbO6Cj8Uab1pg2mmaZBqbmEgtMPaaRuaEDppou+GcrBphWmu6Zrpo2e90wPTEt/tU1YbLppml2bjDGmG6bfnh9Ms1Jekh7vS3olWmut60wXVKLwAw2HTI9V9lRbCflPr4wszHpI6Yia8/ZYPos52CRmnohCHdNM7N2xj9u2pe1J+DgCdNH05LMFiCNPsgNxqABovnYP5soTNvkovvIND6xSvNNp0yDsnZYJvfOtNwQ2G767p91jDLdNz2US4sAkbms5s02zHRaLsoEgFXYlPRwqbozawuEb9OnxAzTa1VHJSYM8sI0wbfhNM4fCJ1qmC4XXfoTza+ma6ahUR/Sd3n0O4cAnFG6+r0UchE5mLXn4MQbpRPgye/1oVMN60x7/N84jfNMgskAwTmn5gCy0hSDEXEjdfaWXPqsjg0VYKdfPMgi01s1Rw4KpeOTPgQt7Cf2F3uwKv8DBCkOXi8hgmxOBmniqMoVhAm89M86Qv5PitqINCnLhmZjNuV/gAmQAWRCH2ECpZllTJE7B94rrfVtJhDnf0whF5Ad+n3+AxP4Ilet+qCaUFWaJsAS75f72K7M1mYC1H/ezwnFgxS8rrSyVVGZQuTcWdM31UeAc4EDjIOM8yKG6OIEm7SOQtX7KxxQBIbrQlP+A2n2TBUbnZMVB3tUdnCV6Z3psNKSFwgryAFVxVi56M7LDZ5QUuvej6FU1543XB2eyt2Bwv2Hu9ADuUmUaq+HdibOBo8ZJzdWfL85pvKFkKBcVP3qB1gdVqnxOsHgVCJun+TbRNU7HkNJxFlq+d+CSkXVCudGV+Hafce0Njd0kS1yB12e4l2DSnNe1fukUwjQFdVfMrsCqcZVAbVJu7YwViFXvrs5biUs727T0tzQAfxHuFX/wPl+/oSfdmCStdDzDykAAAAASUVORK5CYII=>