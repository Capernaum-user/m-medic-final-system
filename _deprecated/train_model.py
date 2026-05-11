import os
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

# 1. 설정 및 경로
BASE_DIR = r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\WOUND_DATA"
METADATA_PATH = os.path.join(BASE_DIR, "WOUND_DATA_metadata.csv")
# 이미지가 두 폴더에 나누어져 있을 수 있음 (WOUND_DATA_images_part_1, part_2 등)
IMAGE_DIRS = [os.path.join(BASE_DIR, d) for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]

# 2. 커스텀 데이터셋 정의
class HAMDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df
        self.transform = transform
        # 파일 경로 사전 매핑 (이미지 폴더가 여러 개일 수 있으므로)
        self.image_path_dict = {os.path.splitext(f)[0]: os.path.join(root, f) 
                                for d in IMAGE_DIRS for root, dirs, files in os.walk(d) for f in files}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        img_id = self.df.iloc[idx]['image_id']
        img_path = self.image_path_dict[img_id]
        image = Image.open(img_path).convert('RGB')
        label = self.df.iloc[idx]['label']
        
        if self.transform:
            image = self.transform(image)
        return image, label

# 3. 데이터 준비 및 전처리
def prepare_data():
    df = pd.read_csv(METADATA_PATH)
    # 라벨 인코딩 (dx -> int)
    dx_codes = {v: i for i, v in enumerate(df['dx'].unique())}
    df['label'] = df['dx'].map(dx_codes)
    
    train_df, val_df = train_test_split(df, test_size=0.2, stratify=df['label'], random_state=42)
    
    # 클래스 가중치 계산 (불균형 해소용)
    class_weights = compute_class_weight('balanced', classes=np.unique(df['label']), y=df['label'])
    
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    train_ds = HAMDataset(train_df, train_transform)
    val_ds = HAMDataset(val_df, val_transform)
    
    return train_ds, val_ds, len(dx_codes), class_weights

# 4. 모델 구축 및 학습 함수
def train_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {device}")
    
    train_ds, val_ds, num_classes, weights = prepare_data()
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    
    # ResNet50 전이 학습 모델 설정 (최신 라이브러리 방식)
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss(weight=torch.FloatTensor(weights).to(device))
    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    
    # 5. 전체 학습 루프
    num_epochs = 10
    best_val_loss = float('inf')
    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}

    print(f"{num_epochs} 에폭 동안 전체 학습을 시작합니다...")
    
    for epoch in range(num_epochs):
        # Training Phase
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)
        
        epoch_loss = running_loss / len(train_loader.dataset)
        history['train_loss'].append(epoch_loss)

        # Validation Phase
        model.eval()
        val_loss = 0.0
        correct = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                correct += torch.sum(preds == labels.data)
        
        epoch_val_loss = val_loss / len(val_loader.dataset)
        epoch_val_acc = correct.double() / len(val_loader.dataset)
        history['val_loss'].append(epoch_val_loss)
        history['val_acc'].append(epoch_val_acc.item())

        print(f"Epoch {epoch+1}/{num_epochs} | Train Loss: {epoch_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc:.4f}")

        # 최적 모델 저장
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            torch.save(model.state_dict(), os.path.join(r"D:\GeminiUniverse\vscode-workspace\maritime-medic", "best_m_medic_model.pth"))
            print("  --> 최적 모델 저장됨 (Best Val Loss 갱신)")

    print("\n모든 학습이 완료되었습니다.")
    # 최종 결과 리포트용 로그 저장
    log_df = pd.DataFrame(history)
    log_df.to_csv(os.path.join(r"D:\GeminiUniverse\vscode-workspace\maritime-medic\reports", "training_history.csv"), index=False)

if __name__ == "__main__":
    train_model()
