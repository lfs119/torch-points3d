
import torch 
from torch.nn import Linear
from torch_geometric.nn import global_max_pool

from models.core_modules import * 
from models.core_transforms import BaseLinearTransformSTNkD

class MiniPointNet(torch.nn.Module):

    def __init__(self, local_nn, global_nn):
        super(MiniPointNet, self).__init__()

        self.local_nn = MLP(local_nn)
        self.global_nn = MLP(global_nn)

    def forward(self, x, batch):
        
        x = self.local_nn(x)
        x = global_max_pool(x, batch)
        x = self.global_nn(x)

        return x

class PointNetSTN3D(BaseLinearTransformSTNkD):

    def __init__(self, local_nn = [3, 64, 128, 1024], global_nn = [1024, 512, 256], batch_size=1):
        super().__init__(
            MiniPointNet(local_nn, global_nn),
            global_nn[-1],
            3,
            batch_size
        )

    def forward(self, x, batch):
        return super().forward(x, x, batch)

class PointNetSTNkD(BaseLinearTransformSTNkD):

    def __init__(self, k = 64, local_nn = [64, 64, 128, 1024], global_nn = [1024, 512, 256], batch_size = 1):
        super().__init__(
            MiniPointNet(local_nn, global_nn),
            global_nn[-1],
            k, 
            batch_size
        )

    def forward(self, x, batch):
        return super().forward(x, x, batch)

class PointNetGlobalFeat(torch.nn.Module):

    def __init__(self, 
        local_nn_1 = [3, 64, 64],
        stn3d_local_nn = [3, 64, 128, 1024],
        stn3d_global_nn = [1024, 512, 256], 
        local_nn_2 = [64, 64, 128, 1024],
        stnkd_k = 64,
        stnkd_local_nn = [64, 64, 128, 1024],
        stnkd_global_nn = [1024, 512, 256],
        global_nn = [1024, 512, 265],
        batch_size = 1,
        ):

        self.local_nn_1 = MLP(local_nn_1)
        self.local_nn_2 = MLP(local_nn_2)

        self.stn3d = PointNetSTN3D(stn3d_local_nn, stn3d_global_nn, batch_size)
        self.stnkd = PointNetSTNkD(stnkd_k, stnkd_local_nn, stnkd_global_nn, batch_size)

        self.global_nn = MLP(global_nn) if global_nn is not None else None

    def forward(self, x, batch):

        x = self.stn3d(x)

        x = self.local_nn_1(x)

        x = self.stnkd(x)

        x = self.local_nn_2(x)

        feat = global_max_pool(x, batch)

        if self.global_nn is not None:
            x = self.global_nn(x)

        return x

class PointNetSeg(torch.nn.Module):

    def __init__(self, 
        input_stn_local_nn = [3, 64, 128, 1024],
        input_stn_global_nn = [1024, 512, 256], 
        local_nn_1 = [3, 64, 64],
        feat_stn_k = 64,
        feat_stn_local_nn = [64, 64, 128, 1024],
        feat_stn_global_nn = [1024, 512, 256],
        local_nn_2 = [64, 64, 128, 1024],
        seg_nn = [1088, 512, 256, 128, 4],
        batch_size = 1, *args, **kwargs):
        super().__init__()

        self.batch_size = batch_size

        self.input_stn = PointNetSTN3D(input_stn_local_nn, input_stn_global_nn, batch_size)
        self.local_nn_1 = MLP(local_nn_1)
        self.feat_stn = PointNetSTNkD(feat_stn_k, feat_stn_local_nn, feat_stn_global_nn, batch_size)
        self.local_nn_2 = MLP(local_nn_2)
        self.seg_nn = MLP(seg_nn)

    def forward(self, x, batch):

        # apply pointnet classification network to get per-point
        # features and global feature
        x = self.input_stn(x, batch)
        x = self.local_nn_1(x)
        x_feat_trans = self.feat_stn(x, batch)
        x3 = self.local_nn_2(x_feat_trans)
        global_feature = global_max_pool(x3, batch)

        # concat per-point and global feature and regress to get
        # per-point scores
        feat_concat = torch.cat([x_feat_trans, global_feature[batch]], dim = 1)
        out = self.seg_nn(feat_concat)

        return out


        

