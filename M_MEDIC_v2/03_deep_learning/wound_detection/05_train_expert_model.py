import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, random_split
import os
import time
import copy
import json

# 베테랑 설정
DATA_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\all_labeled_data"
SAVE_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results"
BATCH_SIZE = 16 # V2-S는 메모리를 더 사용하므로 배치 사이즈 조정
NUM_EPOCHS = 50 # 더 깊은 학습
LEARNING_RATE = 0.0001 # 정밀한 수렴을 위해 낮은 학습률
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_expert_model():
    # 고도화된 데이터 증강 (RandAugment 유사 구현)
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(0.4, 0.4, 0.4),
            transforms.RandomAffine(degrees=30, translate=(0.1, 0.1)),
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
    
    print(f"Expert Model 학습 시작 (클래스: {class_names})")

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

    # EfficientNet-V2-S 모델 로드
    model = models.efficientnet_v2_s(pretrained=True)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, num_classes)
    
    model = model.to(DEVICE)

    # Label Smoothing 적용된 Loss
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    # AdamW Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-2)
    # Cosine Annealing Scheduler
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(NUM_EPOCHS):
        print(f'Epoch {epoch}/{NUM_EPOCHS - 1}')
        for phase in ['train', 'val']:
            if phase == 'train': model.train()
            else: model.eval()

            running_loss, running_corrects = 0.0, 0

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

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    print(f'Expert 학습 완료! 최고 정확도: {best_acc:4f}')
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), os.path.join(SAVE_DIR, 'efficientnet_v2_s_wound_expert.pth'))

if __name__ == '__main__':
    train_expert_model()
