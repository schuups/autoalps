import os
import torchvision

from settings import settings

for train in [True, False]:
    torchvision.datasets.CIFAR10(root=settings.cache_path, train=train, download=True)
