// 模板：疊代法反轉
ListNode* reverseList(ListNode* head) {
    ListNode *prev = nullptr;
    ListNode *curr = head;
    
    while (curr) {
        ListNode *nextTemp = curr->next; // 暫存下一個節點
        curr->next = prev;               // 核心反轉動作
        prev = curr;                     // 指針後移
        curr = nextTemp;
    }
    return prev; // 新的頭節點
}
