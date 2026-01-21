// 模板：處理節點刪除或合併
ListNode* solveWithDummy(ListNode* head) {
    ListNode* dummy = new ListNode(0);
    dummy->next = head;
    ListNode* prev = dummy;
    ListNode* curr = head;

    while (curr) {
        if (/* 滿足特定條件，例如刪除節點 */) {
            prev->next = curr->next;
            // delete curr; // 若需釋放記憶體
        } else {
            prev = curr;
        }
        curr = curr->next;
    }
    
    ListNode* res = dummy->next;
    delete dummy;
    return res;
}
