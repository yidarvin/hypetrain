from absl import flags
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

import submodules

FLAGS = flags.FLAGS


class ResNetIm2Value(nn.Module):

    def __init__(self, out_dim=None, use_softmax=True):
        super(ResNetIm2Value, self).__init__()

        self.use_softmax = use_softmax
        self.out_dim = FLAGS.num_actions
        if out_dim is not None:
            self.out_dim = out_dim
        self.H = FLAGS.image_height
        self.W = FLAGS.image_width
        self.C = FLAGS.image_channels
        self.context_frames = FLAGS.context_frames

        fc_input = 7 * 13 * 256

        layer_defs = []
        layer_defs_linear = []
        layer_defs.append(submodules.convbn(self.context_frames*self.C, 64, kernel_size=5, stride=2))
        layer_defs.append(submodules.convbn(64, 64, kernel_size=3, stride=2))
        layer_defs.append(submodules.convbn(64, 64, kernel_size=3, stride=2))

        for i in range(3):
            layer_defs.append(submodules.ResNetModule(64, 64, kernel_size=3, pad=1))
        layer_defs.append(submodules.convbn(64, 128, kernel_size=3, stride=2))

        for i in range(3):
            layer_defs.append(submodules.ResNetModule(128, 128, kernel_size=3, pad=1))
        layer_defs.append(submodules.convbn(128, 256, kernel_size=3, stride=2))

        for i in range(3):
            layer_defs.append(submodules.ResNetModule(256, 256, kernel_size=3, pad=1))

        layer_defs.append(submodules.convbn(256, 256, kernel_size=3, stride=2))

        layer_defs_linear.append(nn.Linear(fc_input, 512))
        #layer_defs_linear.append(nn.BatchNorm1d(512))
        layer_defs_linear.append(nn.ReLU())
        layer_defs_linear.append(nn.Linear(512, 256))
        #layer_defs_linear.append(nn.BatchNorm1d(256))
        layer_defs_linear.append(nn.ReLU())
        layer_defs_linear.append(nn.Linear(256, self.out_dim))

        self.operation_stack = nn.Sequential(*layer_defs)
        self.operation_stack_linear = nn.Sequential(*layer_defs_linear)

    def forward(self, inputs):
        out = self.operation_stack(inputs)
        out = out.view(inputs.shape[0], -1)
        out = self.operation_stack_linear(out)
        if self.use_softmax:
            out = F.softmax(out, 1)
        return out







