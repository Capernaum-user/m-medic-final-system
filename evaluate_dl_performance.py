import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import json
import os

# 설정
MODEL_PATH = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results\mobilenet_v3_wound_best.pth"
DATA_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def evaluate_dl():
    # 1. 데이터 로드 및 전처리
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
    # 실제 검증 환경을 위해 20%를 테스트용으로 분리 (시드 고정으로 일관성 유지)
    _, val_set = torch.utils.data.random_split(dataset, [int(0.8*len(dataset)), len(dataset)-int(0.8*len(dataset))], 
                                              generator=torch.Generator().manual_seed(42))
    loader = DataLoader(val_set, batch_size=32, shuffle=False)
    
    class_names = dataset.classes
    num_classes = len(class_names)

    # 2. 모델 로드
    model = models.mobilenet_v3_large()
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    # 3. 예측 및 분석
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 4. 리포트 생성
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    
    print("\n[딥러닝: 상처 분류 모델 정밀 검증 결과]")
    print(f"전체 정확도(Accuracy): {report['accuracy']:.4f}")
    print(f"가중 평균 F1-Score: {report['weighted avg']['f1-score']:.4f}")
    
    # 오차가 큰 클래스 확인
    low_perf_classes = [c for c in class_names if report[c]['f1-score'] < 0.90]
    if low_perf_classes:
        print(f"⚠ 성능 보강 필요 클래스 (F1 < 0.9): {low_perf_classes}")
    else:
        print("✅ 모든 클래스에서 90% 이상의 안정적인 성능을 보입니다.")

    return report

if __name__ == "__main__":
    evaluate_dl()
