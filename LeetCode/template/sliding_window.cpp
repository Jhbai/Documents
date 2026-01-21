#include <string>
#include <unordered_map>

int slidingWindowVariable(string s) {
    unordered_map<char, int> window;
    int left = 0, right = 0;
    int res = 0; // 或 INT_MAX
    
    while (right < s.size()) {
        char c = s[right];
        right++; // 1. 右擴張：將字元加入視窗
        window[c]++;
        
        // 2. 判斷是否需要左縮：根據題目條件（例如重複、Sum > Target）
        while (window[c] > 1 /* 滿足特定收縮條件 */) {
            char d = s[left];
            left++; // 左縮
            window[d]--;
        }
        
        // 3. 更新全域最佳解
        res = max(res, right - left);
    }
    return res;
}
