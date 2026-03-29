"""CIFAR-10 DDP training — compatible with torchrun (PyTorch Elastic).

Environment variables (set automatically by torchrun):
    WORLD_SIZE   total number of processes  (replaces SLURM_NTASKS)
    RANK         global process rank        (replaces SLURM_PROCID)
    LOCAL_RANK   GPU index within the node
    MASTER_ADDR  rendezvous address         (set by training operator)
    MASTER_PORT  rendezvous port            (set by training operator)
"""

import os
import time
import numpy as np
import torch
import torch.distributed as dist
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.nn.parallel import DistributedDataParallel as DDP

from settings import settings
from evaluate import evaluate


class SEBlock(nn.Module):
    def __init__(self, channels, r=16):
        super().__init__()
        self.fc1 = nn.Linear(channels, max(1, channels // r))
        self.fc2 = nn.Linear(max(1, channels // r), channels)

    def forward(self, x):
        s = x.mean(dim=(2, 3))
        s = F.relu(self.fc1(s))
        s = torch.sigmoid(self.fc2(s)).view(x.size(0), x.size(1), 1, 1)
        return x * s


class WideBlock(nn.Module):
    def __init__(self, in_planes, planes, stride=1):
        super().__init__()
        self.bn1 = nn.BatchNorm2d(in_planes)
        self.conv1 = nn.Conv2d(in_planes, planes, 3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, 3, padding=1, bias=False)
        self.se = SEBlock(planes)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != planes:
            self.shortcut = nn.Conv2d(in_planes, planes, 1, stride=stride, bias=False)

    def forward(self, x):
        out = self.conv1(F.relu(self.bn1(x)))
        out = self.conv2(F.relu(self.bn2(out)))
        out = self.se(out)
        out += self.shortcut(x)
        return out


class Net(nn.Module):
    """SE-WideResNet-28-8 for CIFAR-10."""
    def __init__(self, n=4, k=8):
        super().__init__()
        c = [16, 16 * k, 32 * k, 64 * k]  # [16, 128, 256, 512]
        self.conv0 = nn.Conv2d(3, c[0], 3, padding=1, bias=False)
        self.group1 = self._make_group(c[0], c[1], n, stride=1)
        self.group2 = self._make_group(c[1], c[2], n, stride=2)
        self.group3 = self._make_group(c[2], c[3], n, stride=2)
        self.bn = nn.BatchNorm2d(c[3])
        self.fc = nn.Linear(c[3], 10)

    def _make_group(self, in_planes, planes, n, stride):
        blocks = [WideBlock(in_planes, planes, stride=stride)]
        for _ in range(n - 1):
            blocks.append(WideBlock(planes, planes))
        return nn.Sequential(*blocks)

    def forward(self, x):
        x = self.conv0(x)
        x = self.group1(x)
        x = self.group2(x)
        x = self.group3(x)
        x = F.relu(self.bn(x))
        x = F.adaptive_avg_pool2d(x, 1)
        x = torch.flatten(x, 1)
        return self.fc(x)


def cutmix(inputs, labels, alpha=1.0):
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(inputs.size(0), device=inputs.device)
    H, W = inputs.size(2), inputs.size(3)
    cut_h = int(H * (1 - lam) ** 0.5)
    cut_w = int(W * (1 - lam) ** 0.5)
    cy, cx = np.random.randint(H), np.random.randint(W)
    y1, y2 = max(cy - cut_h // 2, 0), min(cy + cut_h // 2, H)
    x1, x2 = max(cx - cut_w // 2, 0), min(cx + cut_w // 2, W)
    lam = 1 - (y2 - y1) * (x2 - x1) / (H * W)
    mixed = inputs.clone()
    mixed[:, :, y1:y2, x1:x2] = inputs[idx, :, y1:y2, x1:x2]
    return mixed, labels, labels[idx], lam


def train(net_ddp, trainloader, trainsampler, criterion, optimizer, scheduler, device, epochs):
    """Train the model for specified epochs."""
    for epoch in range(epochs):
        trainsampler.set_epoch(epoch)
        for inputs, labels in trainloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            inputs, ya, yb, lam = cutmix(inputs, labels)
            optimizer.zero_grad()
            outputs = net_ddp(inputs)
            loss = lam * criterion(outputs, ya) + (1 - lam) * criterion(outputs, yb)
            loss.backward()
            optimizer.step()
        scheduler.step()


def main(world_size, rank, local_rank, batch_size):
    dist.init_process_group(
        backend="nccl",
        init_method="env://",
        world_size=world_size,
        rank=rank,
        device_id=torch.device("cuda", local_rank),
    )

    dist.barrier()  # wait for all ranks to be in the group before proceeding

    traintransforms = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
    ])
    trainset = torchvision.datasets.CIFAR10(
        root=settings.cache_path, train=True, download=False, transform=traintransforms
    )
    trainsampler = torch.utils.data.distributed.DistributedSampler(trainset)
    trainloader = torch.utils.data.DataLoader(
        trainset, batch_size=batch_size, sampler=trainsampler, num_workers=2
    )

    # LOCAL_RANK selects the GPU within the node (replaces rank % cuda_count)
    device = torch.device("cuda", local_rank)
    torch.cuda.set_device(device)

    net = Net().to(device)
    net_ddp = DDP(net, device_ids=[local_rank])
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1).to(device)
    optimizer = optim.SGD(net_ddp.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    warmup = optim.lr_scheduler.LinearLR(optimizer, start_factor=0.01, total_iters=5)
    cosine = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=settings.epochs - 5)
    scheduler = optim.lr_scheduler.SequentialLR(optimizer, [warmup, cosine], milestones=[5])

    dist.barrier()
    start_time = time.perf_counter()

    train(
        net_ddp,
        trainloader,
        trainsampler,
        criterion,
        optimizer,
        scheduler,
        device,
        settings.epochs,
    )

    dist.barrier()
    end_time = time.perf_counter()
    training_duration = end_time - start_time

    if rank == 0:
        accuracy = evaluate(net_ddp)
        print("---")
        print(f"accuracy:         {accuracy / 100:.6f}")
        print(f"execution_secs:   {training_duration:.1f}")

    dist.destroy_process_group()


if __name__ == "__main__":
    main(
        world_size=int(os.environ["SLURM_NTASKS"]),
        rank=int(os.environ["SLURM_PROCID"]),
        local_rank=int(os.environ["SLURM_LOCALID"]),
        batch_size=settings.batch_size,
    )
