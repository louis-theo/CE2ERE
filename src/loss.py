import torch
from torch import Tensor
from torch.nn import Module, LogSoftmax

from utils import log1mexp


class TransitionLoss(Module):
    def __init__(self):
        super().__init__()

    def forward(self, log_y_alpha, log_y_beta, log_y_gamma, alpha_index, beta_index, gamma_index):
        zero = torch.zeros(1).to(log_y_alpha.device)
        loss = torch.max(zero, log_y_alpha[:, alpha_index] + log_y_beta[:, beta_index] - log_y_gamma[:, gamma_index])
        return loss


class TransitionNotLoss(Module):
    def __init__(self):
        super().__init__()
        self.eps = 1e-8

    def forward(self, log_y_alpha, log_y_beta, log_y_gamma, alpha_index, beta_index, gamma_index):
        zero = torch.zeros(1).to(log_y_alpha.device)
        log_not_y_gamma = (1 - log_y_gamma.exp()).clamp(self.eps).log()
        loss = torch.max(zero, log_y_alpha[:, alpha_index] + log_y_beta[:, beta_index] - log_not_y_gamma[:, gamma_index])
        return loss


class TransitivityLoss(Module):
    def __init__(self):
        super().__init__()
        self.softmax = LogSoftmax(dim=1)
        self.transition_loss = TransitionLoss()
        self.transition_not_loss = TransitionNotLoss()

    def forward(self, alpha_logits: Tensor, beta_logits: Tensor, gamma_logits: Tensor):
        log_y_alpha = self.softmax(alpha_logits)
        log_y_beta = self.softmax(beta_logits)
        log_y_gamma = self.softmax(gamma_logits)

        loss = self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 0, 0)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 2, 0)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 1, 1)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 2, 1)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 0, 0)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 1, 1)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 2, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 3, 3)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 3, 2, 3)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 3, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 3, 2)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 3, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 3, 2)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 3, 0, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 3, 0, 2)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 3, 1, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 3, 1, 2)

        return loss

class CrossCategoryLoss(Module):
    def __init__(self):
        super().__init__()
        self.softmax = LogSoftmax(dim=1)
        self.transition_loss = TransitionLoss()
        self.transition_not_loss = TransitionNotLoss()

    def forward(self, alpha_logits: Tensor, beta_logits: Tensor, gamma_logits: Tensor):
        """
        The induction table for conjunctive constraints on temporal and subevent relations.
        Refer Table1 in the paper: "Joint Constrained Learning for Event-Event Relation Extraction"
        0 - PC (Parent-Child), 1 - CP (Child-Parent), 2 - CR (CoRef), 3 - NR (NoRel)
        4 - BF (Before), 5 - AF (After), 6 - EQ (Equal), 7 - VG (Vague)
        """
        log_y_alpha = self.softmax(alpha_logits)
        log_y_beta = self.softmax(beta_logits)
        log_y_gamma = self.softmax(gamma_logits)

        loss = self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 4, 4)      # (PC, BF) -> BF
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 4, 1) # (PC, BF) -> -CP
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 4, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 6, 4)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 6, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 0, 6, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 5, 5)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 5, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 5, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 6, 5)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 6, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 1, 6, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 4, 4)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 4, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 4, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 5, 5)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 5, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 5, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 6, 6)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 7, 7)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 2, 7, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 0, 4)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 0, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 0, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 2, 4)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 2, 1)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 4, 2, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 1, 5)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 1, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 1, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 2, 5)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 2, 0)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 5, 2, 2)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 6, 2, 6)
        loss += self.transition_loss(log_y_alpha, log_y_beta, log_y_gamma, 7, 2, 7)
        loss += self.transition_not_loss(log_y_alpha, log_y_beta, log_y_gamma, 7, 2, 2)
        return loss


class BCELossWithLog(Module):
    """
    binary cross entropy loss with log probabilities
    """
    def __init__(self):
        super().__init__()

    def loss_calculation(self, volume1, volume2, label1, label2):
        # loss = -(label1 * volume1 + (1 - label1) * log1mexp(volume1) + label2 * volume2 + (1 - label2) * log1mexp(volume2)).sum()
        vol1_pos_loss = (label1 * volume1).sum()
        vol1_neg_loss = ((1 - label1) * log1mexp(volume1)).sum()
        vol1_loss = vol1_pos_loss+vol1_neg_loss

        vol2_pos_loss = (label2 * volume2).sum()
        vol2_neg_loss = ((1 - label2) * log1mexp(volume2)).sum()
        vol2_loss = vol2_pos_loss + vol2_neg_loss

        loss = vol1_loss + vol2_loss
        return -loss

    def forward(self, volume1, volume2, labels, flag):
        """
        volume1: P(A|B); [batch_size, # of datasets]
        volume1: P(B|A); [batch_size, # of datasets]
        labels: [batch_size, 2]; PC: (1,0), CP: (0,1), CR: (1,1), VG: (0,0)
        flag:   [batch_size]; 0: HiEve, 1: MATRES
        -(labels[:, 0] * log volume1 + (1 - labels[:, 0]) * log(1 - volume1) + labels[:, 1] * log volume2 + (1 - labels[:, 1]) * log(1 - volume2)).sum()
        """
        if volume1.shape[-1] == 1:
            loss = self.loss_calculation(volume1, volume2, labels[:, 0].unsqueeze(-1), labels[:, 1].unsqueeze(-1))
        else:
            hieve_mask = (flag == 0).nonzero()
            hieve_loss = self.loss_calculation(volume1[:, 0][hieve_mask], volume2[:, 0][hieve_mask], labels[:, 0][hieve_mask], labels[:, 1][hieve_mask])
            matres_mask = (flag == 1).nonzero()
            matres_loss = self.loss_calculation(volume1[:, 1][matres_mask], volume2[:, 1][matres_mask], labels[:, 0][matres_mask], labels[:, 1][matres_mask])
            loss = hieve_loss + matres_loss
        return loss