import os
import random
import glob
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

# 설정
DATA_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification"
MODEL_PATH = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results\mobilenet_v3_wound_best.pth"
CLASSES = ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 모델 로드
def load_model():
    model = models.mobilenet_v3_large(weights=None)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, len(CLASSES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

# 전처리
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def run_test_round(round_num):
    print(f"\n=== [검토 {round_num}회차] 분석 시작 ===")
    model = load_model()
    correct_count = 0
    
    for cls in CLASSES:
        cls_dir = os.path.join(DATA_DIR, cls)
        all_files = glob.glob(os.path.join(cls_dir, "*.*"))
        test_file = random.choice(all_files)
        
        # 이미지 로드 및 예측
        img = Image.open(test_file).convert('RGB')
        input_tensor = preprocess(img).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probs = torch.softmax(outputs, dim=1).squeeze().cpu().numpy()
            pred_idx = np.argmax(probs)
            confidence = probs[pred_idx]
            pred_class = CLASSES[pred_idx]
            
        is_correct = (pred_class == cls)
        if is_correct: correct_count += 1
        
        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"{status} 실제: {cls:<12} | 예측: {pred_class:<12} | 신뢰도: {confidence:.2%}")
        
    print(f"--- {round_num}회차 결과: {correct_count}/{len(CLASSES)} 적중 ---")

if __name__ == "__main__":
    for i in range(1, 6):
        run_test_round(i)
