"""
# author: shiyipaisizuo
# contact: shiyipaisizuo@gmail.com
# file: train.py
# time: 2018/8/24 17:52
# license: MIT
"""

import os

import time
import torch
import torchvision
from research.CALTECH.C154.net import Net
from torch import nn, optim
from torch.utils import data
from torchvision import transforms

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

WORK_DIR = '../../data/CALTECH/C154/'
NUM_EPOCHS = 10
BATCH_SIZE = 64
LEARNING_RATE = 1e-4
NUM_CLASSES = 154

MODEL_PATH = '../../../models/pytorch/CALTECH/'
MODEL_NAME = 'C154.pth'

# Create model
if not os.path.exists(MODEL_PATH):
    os.makedirs(MODEL_PATH)

transform = transforms.Compose([
    transforms.Resize(224),  # 将图像转化为224 * 224
    transforms.RandomHorizontalFlip(),  # 几率随机旋转
    transforms.ToTensor(),  # 将numpy数据类型转化为Tensor
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])  # 归一化
])


# Load data
train_dataset = torchvision.datasets.ImageFolder(root=WORK_DIR + 'train/',
                                                  transform=transform)

train_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                           batch_size=BATCH_SIZE,
                                           shuffle=True)


def main():
    print(f"Train numbers:{len(train_dataset)}")

    model = Net()
    # cast
    cast = nn.CrossEntropyLoss().to(device)
    # Optimization
    optimizer = optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-8)

    step = 1
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            # Forward pass
            outputs = model(images)
            loss = cast(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            end = time.time()
            print(f"Step [{step * BATCH_SIZE}/{NUM_EPOCHS * len(train_dataset)}], "
                  f"Loss: {loss.item():.8f}.")

        # Save the model checkpoint
        torch.save(model, MODEL_PATH + MODEL_NAME)
    print(f"Model save to {MODEL_PATH + MODEL_NAME}.")


if __name__ == '__main__':
    main()
