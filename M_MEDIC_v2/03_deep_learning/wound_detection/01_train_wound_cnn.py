"""
[M-Medic DL Step 3] 외상 분류 CNN 학습 파이프라인
-------------------------------------------------
데이터셋: M_MEDIC_v2/01_data/raw/wound_classification/
         (총 1,162장, 6개 클래스)

클래스 현황 (선박 사고 외상 전용):
  Burns(193), Laceration(183), Cut(150), Abrasions(249), Bruises(364), Stab_wound(23)

데이터 출처:
  wcs_* prefix : wound-classification-system (Kaggle)
  yasin_* prefix: wound_dataset_yasin (Kaggle)

모델: MobileNetV3-Small
  - 파라미터 ~2.5M, 크기 ~10MB → 선박 엣지 디바이스 배포 최적화
  - 추론 속도 < 200ms (CPU 기준)

출력:
  - results/best_wound_mobilenet.pth
  - results/wound_training_history.csv
  - results/wound_class_distribution.png
  - results/wound_confusion_matrix.png
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from PIL import Image

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
# M_MEDIC_v2/01_data/raw/wound_classification/ (통합 데이터셋)
WOUND_DIR  = Path(__file__).parent.parent.parent / "01_data" / "raw" / "wound_classification"
RESULT_DIR = Path(__file__).parent / "results"
RESULT_DIR.mkdir(exist_ok=True)

# ─── 클래스 정의 ──────────────────────────────────────────────────────────────
# 선박 사고 외상 전용 6개 클래스 (통합 데이터셋 기준)
ALL_CLASSES = {
    "Abrasions"  : {"name": "찰과상", "risk": "LOW",    "maritime": True},
    "Bruises"    : {"name": "타박상", "risk": "LOW",    "maritime": True},
    "Burns"      : {"name": "화상",   "risk": "HIGH",   "maritime": True},
    "Cut"        : {"name": "절창",   "risk": "MEDIUM", "maritime": True},
    "Laceration" : {"name": "열창",   "risk": "HIGH",   "maritime": True},
    "Stab_wound" : {"name": "자창",   "risk": "HIGH",   "maritime": True},
}

# ─── 한글 폰트 ────────────────────────────────────────────────────────────────
def set_korean_font():
    for fp in ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/NanumGothic.ttf"]:
        if os.path.exists(fp):
            fm.fontManager.addfont(fp)
            plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ─── 데이터셋 스캔 ────────────────────────────────────────────────────────────
def scan_wound_dataset():
    """실제 폴더를 스캔하여 클래스별 이미지 경로 수집"""
    found = {}
    if not WOUND_DIR.exists():
        print(f"[오류] 데이터셋 경로를 찾을 수 없습니다: {WOUND_DIR}")
        return found

    for cls_name in ALL_CLASSES.keys():
        cls_dir = WOUND_DIR / cls_name
        if cls_dir.exists():
            imgs = (list(cls_dir.glob("*.jpg")) +
                    list(cls_dir.glob("*.jpeg")) +
                    list(cls_dir.glob("*.png")))
            if imgs:
                found[cls_name] = imgs

    return found

# ─── 커스텀 데이터셋 ───────────────────────────────────────────────────────────
class WoundDataset(Dataset):
    def __init__(self, samples: list, transform=None):
        self.samples   = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (128, 128, 128))
        if self.transform:
            image = self.transform(image)
        return image, label

# ─── MobileNetV3 모델 ─────────────────────────────────────────────────────────
def build_model(num_classes: int):
    try:
        model = models.mobilenet_v3_small(
            weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
        )
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
    except AttributeError:
        # 구버전 torchvision 폴백
        model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

# ─── 시각화: 클래스 분포 ──────────────────────────────────────────────────────
def plot_class_distribution(found: dict):
    names   = list(found.keys())
    counts  = [len(v) for v in found.values()]
    kr_names= [ALL_CLASSES[n]["name"] for n in names]
    colors  = []
    for n in names:
        risk = ALL_CLASSES[n]["risk"]
        if risk == "HIGH":   colors.append("#EF5350")
        elif risk == "MEDIUM": colors.append("#FF8F00")
        elif risk == "LOW":  colors.append("#42A5F5")
        else:                colors.append("#9E9E9E")

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(kr_names, counts, color=colors, edgecolor="white", linewidth=1.3)
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_title(f"외상 분류 데이터셋 클래스 분포 (총 {sum(counts):,}장)\n"
                 f"(빨강=HIGH위험, 주황=MEDIUM, 파랑=LOW)", fontsize=11)
    ax.set_ylabel("이미지 수")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    out = str(RESULT_DIR / "wound_class_distribution.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> 분포 차트: {out}")

# ─── 시각화: 혼동 행렬 ────────────────────────────────────────────────────────
def plot_confusion_matrix(y_true, y_pred, class_names):
    cm = confusion_matrix(y_true, y_pred)
    kr_names = [ALL_CLASSES.get(n, {}).get("name", n) for n in class_names]

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=kr_names, yticklabels=kr_names, ax=ax)
    ax.set_title("외상 분류 혼동 행렬", fontsize=12)
    ax.set_ylabel("실제 외상")
    ax.set_xlabel("AI 예측")
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    out = str(RESULT_DIR / "wound_confusion_matrix.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> 혼동 행렬: {out}")

# ─── 학습 함수 ────────────────────────────────────────────────────────────────
def train(found: dict):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[사용 장치] {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    class_names = sorted(found.keys())
    label_map   = {name: idx for idx, name in enumerate(class_names)}
    all_samples = []
    for cls_name, img_paths in found.items():
        lbl = label_map[cls_name]
        all_samples.extend([(str(p), lbl) for p in img_paths])

    # Stratified split
    labels_list = [s[1] for s in all_samples]
    train_s, val_s = train_test_split(
        all_samples, test_size=0.2, stratify=labels_list, random_state=42
    )

    # WeightedRandomSampler (소수 클래스 오버샘플링)
    train_labels = [s[1] for s in train_s]
    counts  = np.bincount(train_labels)
    weights = 1.0 / counts
    sample_weights = np.array([weights[lbl] for lbl in train_labels])
    sampler = WeightedRandomSampler(
        torch.from_numpy(sample_weights).double(),
        num_samples=len(train_s), replacement=True
    )

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(25),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_ds = WoundDataset(train_s, train_tf)
    val_ds   = WoundDataset(val_s,   val_tf)
    train_loader = DataLoader(train_ds, batch_size=32, sampler=sampler, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=32, shuffle=False,   num_workers=0)

    model     = build_model(len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20, eta_min=1e-6)

    history   = {"train_loss": [], "val_loss": [], "val_acc": []}
    best_acc  = 0.0
    best_path = str(RESULT_DIR / "best_wound_mobilenet.pth")
    last_preds, last_true = [], []

    print(f"\n{'='*55}")
    print(f"  MobileNetV3-Small 외상 분류 학습 시작")
    print(f"  클래스({len(class_names)}종): {class_names}")
    print(f"  훈련: {len(train_s)}장 | 검증: {len(val_s)}장")
    print(f"{'='*55}\n")

    for epoch in range(20):
        # Train
        model.train()
        running_loss = 0.0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * imgs.size(0)

        # Validate
        model.eval()
        val_loss, correct = 0.0, 0
        ep_preds, ep_true = [], []
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                out   = model(imgs)
                val_loss += criterion(out, labels).item() * imgs.size(0)
                preds = out.argmax(1)
                correct += (preds == labels).sum().item()
                ep_preds.extend(preds.cpu().numpy())
                ep_true.extend(labels.cpu().numpy())

        tl = running_loss / len(train_loader.dataset)
        vl = val_loss     / len(val_loader.dataset)
        va = correct      / len(val_loader.dataset)
        history["train_loss"].append(tl)
        history["val_loss"].append(vl)
        history["val_acc"].append(va)
        scheduler.step()

        star = ""
        if va > best_acc:
            best_acc = va
            torch.save(model.state_dict(), best_path)
            last_preds, last_true = ep_preds, ep_true
            star = " ★ BEST"
        print(f"Epoch {epoch+1:>2}/20 | Train: {tl:.4f} | Val: {vl:.4f} | Acc: {va:.4f}{star}")

    # 결과 저장
    pd.DataFrame(history).to_csv(
        str(RESULT_DIR / "wound_training_history.csv"), index=False
    )
    print(f"\n학습 완료! 최적 모델: {best_path}")
    print(f"  최고 Val Accuracy: {best_acc:.4f}")

    # 최종 Classification Report
    print("\n[최종 Classification Report]")
    kr_names_list = [ALL_CLASSES.get(class_names[i], {}).get("name", class_names[i])
                     for i in range(len(class_names))]
    print(classification_report(last_true, last_preds, target_names=kr_names_list))

    # 혼동 행렬 시각화
    plot_confusion_matrix(last_true, last_preds, class_names)

    # 클래스-인덱스 매핑 저장 (통합 시스템에서 사용)
    mapping = {str(idx): name for name, idx in label_map.items()}
    mapping_path = str(RESULT_DIR / "wound_class_mapping.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"  클래스 매핑 저장: {mapping_path}")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[M-Medic] 외상 분류 딥러닝 파이프라인 시작")
    print(f"  데이터셋 경로: {WOUND_DIR}\n")

    found = scan_wound_dataset()
    if not found:
        print("[오류] 이미지를 찾을 수 없습니다. 경로를 확인하세요.")
        sys.exit(1)

    print("발견된 클래스:")
    total = 0
    for cls, imgs in sorted(found.items()):
        info  = ALL_CLASSES.get(cls, {})
        risk  = info.get("risk", "?")
        kr    = info.get("name", cls)
        marine= "★ 선박 핵심" if info.get("maritime") else ""
        print(f"  {cls:<20} {len(imgs):>4}장  [{risk}]  {marine}")
        total += len(imgs)
    print(f"  {'합계':<20} {total:>4}장\n")

    plot_class_distribution(found)
    train(found)
