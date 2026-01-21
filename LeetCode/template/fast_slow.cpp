// 模板：Floyd's 判圈演算法 (Tortoise and Hare)
bool hasCycle(ListNode *head) {
    if (!head || !head->next) return false;
    
    ListNode *slow = head;
    ListNode *fast = head;
    
    while (fast && fast->next) {
        slow = slow->next;          // 走 1 步
        fast = fast->next->next;    // 走 2 步
        
        if (slow == fast) {         // 相遇代表有環
            return true;
        }
    }
    return false;
}
