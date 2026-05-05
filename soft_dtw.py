import torch
import torch.nn as nn
import torch.nn.functional as F

class SoftDTWFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, D, gamma):
        B, N, M = D.shape
        device = D.device
        dtype = D.dtype
        
        # 建立累積成本矩陣 R，加入 Padding 以簡化邊界條件判斷
        R = torch.full((B, N+2, M+2), float('inf'), device=device, dtype=dtype)
        R[:, 0, 0] = 0.0
        
        # 前向反對角線運算
        for k in range(1, N + M):
            start_i = max(1, k + 1 - M)
            end_i = min(N, k)
            if start_i > end_i:
                continue
                
            i = torch.arange(start_i, end_i + 1, device=device)
            j = k + 1 - i
            
            a = R[:, i-1, j-1]
            b = R[:, i-1, j]
            c = R[:, i, j-1]
            
            # 數值穩定的 softmin: -gamma * logsumexp(-[a, b, c] / gamma)
            stacked = torch.stack([-a/gamma, -b/gamma, -c/gamma], dim=-1)
            s = -gamma * torch.logsumexp(stacked, dim=-1)
            
            R[:, i, j] = D[:, i-1, j-1] + s
            
        ctx.save_for_backward(D, R)
        ctx.gamma = gamma
        ctx.N = N
        ctx.M = M
        
        # 回傳向量：每個 Batch 對應的 Soft-DTW 距離 (Shape: (B,))
        return R[:, N, M]

    @staticmethod
    def backward(ctx, grad_output):
        """
        當外層調用 loss.mean().backward() 時，grad_output 的 shape 會是 (B,)
        其數值會自動帶入 1.0 / B，完美契合此處的梯度分配。
        """
        D, R = ctx.saved_tensors
        gamma = ctx.gamma
        N = ctx.N
        M = ctx.M
        B = D.shape[0]
        device = D.device
        dtype = D.dtype
        
        # 建立期望對齊矩陣 E
        E = torch.zeros((B, N+2, M+2), device=device, dtype=dtype)
        # 直接賦予頂端梯度。利用 PyTorch 廣播機制，將 (B,) 賦值到 (B,)
        E[:, N, M] = grad_output
        
        # 反向反對角線運算
        for k in range(N + M - 2, 0, -1):
            start_i = max(1, k + 1 - M)
            end_i = min(N, k)
            if start_i > end_i:
                continue
                
            i = torch.arange(start_i, end_i + 1, device=device)
            j = k + 1 - i
            
            # 使用原生 F.softmax 替換手刻邏輯，完美處理 inf 邊界且效能更好
            # 從 (i, j) 走向 (i+1, j+1) 的機率 (對應前驅 a)
            stacked_a = torch.stack([-R[:, i, j]/gamma, -R[:, i, j+1]/gamma, -R[:, i+1, j]/gamma], dim=-1)
            pa = F.softmax(stacked_a, dim=-1)[..., 0]
            term_a = E[:, i+1, j+1] * pa
            
            # 從 (i, j) 走向 (i+1, j) 的機率 (對應前驅 b)
            stacked_b = torch.stack([-R[:, i, j-1]/gamma, -R[:, i, j]/gamma, -R[:, i+1, j-1]/gamma], dim=-1)
            pb = F.softmax(stacked_b, dim=-1)[..., 1]
            term_b = E[:, i+1, j] * pb
            
            # 從 (i, j) 走向 (i, j+1) 的機率 (對應前驅 c)
            stacked_c = torch.stack([-R[:, i-1, j]/gamma, -R[:, i-1, j+1]/gamma, -R[:, i, j]/gamma], dim=-1)
            pc = F.softmax(stacked_c, dim=-1)[..., 2]
            term_c = E[:, i, j+1] * pc
            
            E[:, i, j] = term_a + term_b + term_c
            
        grad_D = E[:, 1:N+1, 1:M+1]
        
        # Function forward 有兩個參數 (D, gamma)，因此 backward 需回傳兩個梯度
        return grad_D, None


class SoftDTWLoss(nn.Module):
    def __init__(self, gamma=1.0, reduction='mean'):
        """
        Soft Dynamic Time Warping 損失函數
        :param gamma: 平滑參數。
        :param reduction: 'mean', 'sum' 或 'none'。決定輸出的純量形式。
        """
        super(SoftDTWLoss, self).__init__()
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, yhat, y):
        # 計算 Batch 中每個時間步的成對歐氏距離平方
        D = torch.sum((yhat.unsqueeze(2) - y.unsqueeze(1)) ** 2, dim=-1)
        
        # 取得每個 batch 的距離向量 (Shape: (B,))
        distances = SoftDTWFunction.apply(D, self.gamma)
        
        # 依照 reduction 參數決定最終的純量輸出
        if self.reduction == 'mean':
            return distances.mean()
        elif self.reduction == 'sum':
            return distances.sum()
        else:
            return distances
