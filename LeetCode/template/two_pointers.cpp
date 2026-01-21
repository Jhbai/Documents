#include <vector>
#include <algorithm>

// 模板：碰撞雙指針 (Collision Pointers)
return_type solveTwoPointers(vector<int>& nums) {
    // 若題目未排序，通常需先排序以利用單調性
    sort(nums.begin(), nums.end());
    
    int left = 0, right = nums.size() - 1;
    while (left < right) {
        int current_val = nums[left] + nums[right];
        
        if (current_val == target) {
            return {left, right}; // 找到解
        } else if (current_val < target) {
            left++; // 數值太小，左指針右移
        } else {
            right--; // 數值太大，右指針左移
        }
    }
    return {};
}
