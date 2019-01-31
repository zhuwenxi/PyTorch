import os

import torch
import torchvision
from torch import utils, optim, nn
from torchvision import transforms
from torchvision.utils import save_image

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

WORK_DIR = '../../../../../data/PASCAL/P2005'
NUM_EPOCHS = 50
BATCH_SIZE = 16
LEARNING_RATE = 2e-4
OPTIM_BETAS = (0.5, 0.999)

NOISE = 100

MODEL_PATH = '../../../../models/pytorch/PASCAL/P2005/'
MODEL_D = 'D.pth'
MODEL_G = 'G.pth'

# Create model
if not os.path.exists(MODEL_PATH):
    os.makedirs(MODEL_PATH)

if not os.path.exists(WORK_DIR + '/' + 'gen'):
    os.makedirs(WORK_DIR + '/' + 'gen')

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.ToTensor(),
])

to_pil_image = transforms.ToPILImage()

# pascal voc 2005 train_dataset
train_dataset = torchvision.datasets.ImageFolder(root=WORK_DIR + '/' + 'train',
                                                 transform=transform)

# Data loader
train_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                           batch_size=BATCH_SIZE,
                                           shuffle=True)


class Generator(nn.Module):
    def __init__(self, noise=NOISE):
        super(Generator, self).__init__()
        self.layer1 = nn.Sequential(
            nn.ConvTranspose2d(noise, 64 * 32, kernel_size=4, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(64 * 32),
            nn.ReLU(True)
        )
        self.layer2 = nn.Sequential(
            nn.ConvTranspose2d(64 * 32, 64 * 16, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 16),
            nn.ReLU(True)
        )
        self.layer3 = nn.Sequential(
            nn.ConvTranspose2d(64 * 16, 64 * 8, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 8),
            nn.ReLU(True)
        )
        self.layer4 = nn.Sequential(
            nn.ConvTranspose2d(64 * 8, 64 * 4, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 4),
            nn.ReLU(True)
        )
        self.layer5 = nn.Sequential(
            nn.ConvTranspose2d(64 * 4, 64 * 2, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 2),
            nn.ReLU(True)
        )
        self.layer6 = nn.Sequential(
            nn.ConvTranspose2d(64 * 2, 64, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(True)
        )
        self.classifier = nn.Sequential(
            nn.ConvTranspose2d(64, 3, kernel_size=4, stride=2, padding=1, bias=False),
            nn.Tanh()
        )

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.layer5(x)
        x = self.layer6(x)
        x = self.classifier(x)
        return x


class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, True)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 64 * 2, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 2),
            nn.LeakyReLU(0.2, True)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(64 * 2, 64 * 4, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 4),
            nn.LeakyReLU(0.2, True)
        )
        self.layer4 = nn.Sequential(
            nn.Conv2d(64 * 4, 64 * 8, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 8),
            nn.LeakyReLU(0.2, True)
        )
        self.layer5 = nn.Sequential(
            nn.Conv2d(64 * 8, 64 * 16, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 16),
            nn.LeakyReLU(0.2, True)
        )
        self.layer6 = nn.Sequential(
            nn.Conv2d(64 * 16, 64 * 32, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64 * 32),
            nn.LeakyReLU(0.2, True)
        )
        self.classifier = nn.Sequential(
            nn.Conv2d(64 * 32, 1, kernel_size=4, stride=1, padding=0, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.layer5(x)
        x = self.layer6(x)
        x = self.classifier(x)
        out = x.view(-1, 1).squeeze(1)
        return out


# first train run this line
D = Discriminator().to(device)
G = Generator().to(device)
# load model
# if torch.cuda.is_available():
#     D = torch.load(MODEL_PATH + 'D.pth').to(device)
#     G = torch.load(MODEL_PATH + 'G.pth').to(device)
# else:
#     D = torch.load(MODEL_PATH + 'D.pth', map_location='cpu')
#     G = torch.load(MODEL_PATH + 'G.pth', map_location='cpu')

# Binary cross entropy loss and optimizer
criterion = nn.BCELoss().to(device)
d_optimizer = optim.Adam(D.parameters(), lr=LEARNING_RATE, betas=OPTIM_BETAS)
g_optimizer = optim.Adam(G.parameters(), lr=LEARNING_RATE, betas=OPTIM_BETAS)


# Start training
def main():
    step = 0
    for epoch in range(1, NUM_EPOCHS + 1):
        for images, _ in train_loader:
            D.zero_grad()

            # Create the labels which are later used as input for the BCE loss
            real_labels = torch.ones(images.size(0),).to(device)
            fake_labels = torch.zeros(images.size(0),).to(device)

            # ================================================================== #
            #                      Train the discriminator                       #
            # ================================================================== #

            # Compute BCE_Loss using real images where BCE_Loss(x, y): - y * log(D(x)) - (1-y) * log(1 - D(x))
            # Second term of the loss is always zero since real_labels == 1
            outputs = D(images)
            d_loss_real = criterion(outputs, real_labels)
            d_loss_real.backward()
            real_score = outputs.mean().item()

            # Compute BCELoss using fake images
            # First term of the loss is always zero since fake_labels == 0
            noise = torch.randn(images.size(0), NOISE, 1, 1).to(device)
            fake = G(noise)
            outputs = D(fake.detach())
            d_loss_fake = criterion(outputs, fake_labels)
            d_loss_fake.backward()
            fake_score_z1 = outputs.mean().item()

            # Backprop and optimize
            d_loss = d_loss_real + d_loss_fake
            d_optimizer.step()

            # ================================================================== #
            #                        Train the generator                         #
            # ================================================================== #

            # Compute loss with fake images
            G.zero_grad()
            outputs = D(fake)
            g_loss = criterion(outputs, real_labels)
            g_loss.backward()
            fake_score_z2 = outputs.mean().item()
            g_optimizer.step()

            step += 1

            # func (item): Tensor turns into an int
            print(f"Step [{step * BATCH_SIZE}/{NUM_EPOCHS * len(train_dataset)}], "
                  f"d_loss: {d_loss.item():.4f}, "
                  f"g_loss: {g_loss.item():.4f}, "
                  f"D(x): {real_score:.4f}, "
                  f"D(G(z)): {fake_score_z1:.4f} / {fake_score_z2:.4f}.")

            images = images.reshape(images.size(0), 3, 256, 256)
            save_image(images, WORK_DIR + '/' + 'gen' + '/' + 'real' + '.jpg')
            fake_images = fake.reshape(images.size(0), 3, 256, 256)
            save_image(fake_images, WORK_DIR + '/' + 'gen' + '/' + str(step) + '.jpg')

        # Save the model checkpoint
        torch.save(D, MODEL_PATH + MODEL_D)
        torch.save(G, MODEL_PATH + MODEL_G)
    print(f"Model save to '{MODEL_PATH}'!")


if __name__ == '__main__':
    main()