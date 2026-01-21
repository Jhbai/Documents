#include <unordered_map>
#include <vector>

// 模板：補數搜尋與狀態記錄
return_type solveArrayHashMap(vector<int>& nums, int target) {
    unordered_map<int, int> map; // value -> index (或 count)
    
    for (int i = 0; i < nums.size(); ++i) {
        int complement = target - nums[i]; // 定義代數關係
        
        // 1. 檢查是否存在於 Map 中
        if (map.find(complement) != map.end()) {
            return {map[complement], i};
        }
        
        // 2. 更新 Map 狀態
        map[nums[i]] = i;
    }
    return {};
}
