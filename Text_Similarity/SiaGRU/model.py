"""
@file   : model.py
@author : xiaolu
@email  : luxiaonlp@163.com
@time   : 2021-05-07
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class Model(nn.Module):
    def __init__(self, embeddings, hidden_size=300, num_layer=2):
        super(Model, self).__init__()
        self.embeds_dim = embeddings.shape[1]
        self.word_emb = nn.Embedding(embeddings.shape[0], embeddings.shape[1])
        self.word_emb.weight = nn.Parameter(torch.from_numpy(embeddings))
        self.word_emb.float()
        self.word_emb.weight.requires_grad = True
        self.hidden_size = hidden_size
        self.num_layer = num_layer
        self.gru = nn.LSTM(self.embeds_dim, self.hidden_size, batch_first=True, bidirectional=True, num_layers=2)
        self.h0 = self.init_hidden((2 * self.num_layer, 1, self.hidden_size))
        self.pred_fc = nn.Linear(40, 2)

    def init_hidden(self, size):
        h0 = nn.Parameter(torch.randn(size))
        nn.init.xavier_normal_(h0)
        return h0

    def forward_once(self, x):
        output, hidden = self.gru(x)
        return output

    def dropout(self, v):
        return F.dropout(v, p=0.2, training=self.training)

    def forward(self, sent1, sent2):
        # embeds: batch_size * seq_len => batch_size * seq_len * dim
        p_encode = self.word_emb(sent1)
        h_endoce = self.word_emb(sent2)
        p_encode = self.dropout(p_encode)
        h_endoce = self.dropout(h_endoce)

        encoding1 = self.forward_once(p_encode)
        encoding2 = self.forward_once(h_endoce)
        sim = torch.exp(-torch.norm(encoding1 - encoding2, p=2, dim=-1, keepdim=True))
        # print(sim.size())   # torch.Size([32, 40, 1])

        x = self.pred_fc(sim.squeeze(dim=-1))
        probabilities = torch.softmax(x, dim=-1)
        return x, probabilities