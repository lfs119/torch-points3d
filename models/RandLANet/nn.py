
import torch.nn.functional as F
from models.unet_base import UnetBasedModel
from models.core_modules import FPModule
from models.base_model import *

class SegmentationModel(UnetBasedModel):
    def __init__(self, option, model_name, num_classes, modules):
        """Initialize this model class.
        Parameters:
            opt -- training/test options
        A few things can be done here.
        - (required) call the initialization function of BaseModel
        - define loss function, visualization images, model names, and optimizers
        """
        UnetBasedModel.__init__(self, option, model_name, num_classes, modules)  # call the initialization method of UnetBasedModel
    
        nn = option.mlp_cls.nn
        self.dropout = option.mlp_cls.get('dropout')
        self.lin1 = torch.nn.Linear(nn[0], nn[1])
        self.lin2 = torch.nn.Linear(nn[2], nn[3])
        self.lin3 = torch.nn.Linear(nn[4], num_classes)

    def set_input(self, data):
        self.input = (data.x if data.x is not None else data.pos, data.pos, data.batch)
        self.labels = data.y

    def forward(self):
        """Standard forward"""
        x, _, _  = self.model(self.input)
        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.lin2(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.lin3(x)
        self.output = F.log_softmax(x, dim=-1)   

    def backward(self):
        self.loss_seg = F.nll_loss(self.output, self.labels)
        self.loss_seg.backward()
