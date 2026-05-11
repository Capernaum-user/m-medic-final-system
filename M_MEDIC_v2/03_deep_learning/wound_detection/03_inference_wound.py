import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# 1. 설정
MODEL_PATH = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results\mobilenet_v3_wound_best.pth"
# 테스트하고 싶은 이미지 경로를 아래에 입력하세요.
TEST_IMAGE_PATH = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification\abrasion\1.jpg" # 예시 경로
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 클래스 이름 (학습 시와 동일한 순서여야 합니다)
# ImageFolder를 사용했으므로 폴더 알파벳 순서입니다.
# 실제 클래스 이름을 확인하기 위해 학습 시 출력되었던 리스트를 참고하세요.
CLASS_NAMES = ['abrasion', 'burn', 'cut', 'laceration', 'puncture'] # 예시 클래스명 (자동 확인 권장)

def predict(image_path):
    # 2. 모델 구조 정의 (학습 시와 동일하게)
    model = models.mobilenet_v3_small(pretrained=False)
    num_classes = len(CLASS_NAMES)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    
    # 3. 가중치 로드
    if not os.path.exists(MODEL_PATH):
        print(f"Error: 모델 파일이 없습니다. {MODEL_PATH}")
        return
        
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval() # 추론 모드 설정

    # 4. 이미지 전처리
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    try:
        img = Image.open(image_path).convert('RGB')
        img_t = preprocess(img)
        batch_t = torch.unsqueeze(img_t, 0).to(DEVICE)
        
        # 5. 예측
        with torch.no_grad():
            outputs = model(batch_t)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)
            
        result = CLASS_NAMES[index]
        print(f"\n[ 분석 결과 ]")
        print(f"이미지: {os.path.basename(image_path)}")
        print(f"진단명: {result}")
        print(f"신뢰도: {confidence.item()*100:.2f}%")
        
    except Exception as e:
        print(f"Error: 이미지를 처리할 수 없습니다. {e}")

if __name__ == "__main__":
    predict(TEST_IMAGE_PATH)
