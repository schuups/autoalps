import torch
import torchvision
import torchvision.transforms as transforms

from settings import settings

testtransforms = transforms.Compose([transforms.ToTensor()])
testset = torchvision.datasets.CIFAR10(
    root=settings.cache_path,
    train=False,
    download=False,
    transform=testtransforms,
)
testloader = torch.utils.data.DataLoader(
    testset,
    batch_size=settings.batch_size,
    shuffle=False,
    num_workers=2,
)


def evaluate(net_ddp):
    """Evaluate the model and return accuracy."""
    net_ddp.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for inputs, labels in testloader:
            inputs, labels = inputs.to("cuda:0"), labels.to("cuda:0")
            outputs = net_ddp(inputs)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    return 100 * correct / total
