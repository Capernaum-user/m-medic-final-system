import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, random_split
import matplotlib.pyplot as plt
import os
import time
import copy
import json

# 설정
DATA_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification"
SAVE_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results"
BATCH_SIZE = 32
NUM_EPOCHS = 40  # 학습 횟수 대폭 증가
LEARNING_RATE = 0.0005 # 더 세밀한 학습을 위해 학습률 조정
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_model():
    # 정밀도 향상을 위한 데이터 증강 전략 수정
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(30),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    full_dataset = datasets.ImageFolder(DATA_DIR)
    class_names = full_dataset.classes
    num_classes = len(class_names)
    
    with open(os.path.join(SAVE_DIR, 'wound_class_mapping.json'), 'w', encoding='utf-8') as f:
        json.dump({i: name for i, name in enumerate(class_names)}, f, ensure_ascii=False, indent=2)

    train_size = int(0.85 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_data, val_data = random_split(full_dataset, [train_size, val_size])

    train_data.dataset.transform = data_transforms['train']
    val_data.dataset.transform = data_transforms['val']

    dataloaders = {
        'train': DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True, num_workers=0),
        'val': DataLoader(val_data, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    }
    
    dataset_sizes = {'train': train_size, 'val': val_size}
    print(f"6종 정밀 학습 모드: {class_names}")

    # 성능 향상을 위해 MobileNetV3 Large 사용
    model = models.mobilenet_v3_large(pretrained=True)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1) # 일반화 성능 향상
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    history = {'train_acc': [], 'val_acc': []}

    for epoch in range(NUM_EPOCHS):
        print(f'Epoch {epoch}/{NUM_EPOCHS - 1}')
        for phase in ['train', 'val']:
            if phase == 'train': model.train()
            else: model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            if phase == 'train': scheduler.step()

            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            print(f'{phase} Acc: {epoch_acc:.4f}')
            
            if phase == 'val': history['val_acc'].append(epoch_acc.item())
            else: history['train_acc'].append(epoch_acc.item())

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    print(f'정밀 학습 완료! 최고 정확도: {best_acc:4f}')
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), os.path.join(SAVE_DIR, 'mobilenet_v3_wound_best.pth'))

if __name__ == '__main__':
    train_model()
