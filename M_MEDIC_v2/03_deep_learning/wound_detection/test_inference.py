import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# 1. 설정
MODEL_PATH = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\03_deep_learning\wound_detection\results\mobilenet_v3_wound_best.pth"
# 테스트할 이미지가 있다면 경로를 수정하세요. 없으면 데이터셋 중 하나를 골라 테스트합니다.
TEST_IMAGE = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification\Burns\wcs_burns (1).jpg"
CLASSES = ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']

def simple_test():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 2. 모델 구조 생성 및 가중치 로드
    model = models.mobilenet_v3_small()
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, len(CLASSES))
    
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    
    # 3. 이미지 전처리
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    if not os.path.exists(TEST_IMAGE):
        print(f"테스트할 이미지가 없습니다: {TEST_IMAGE}")
        return

    img = Image.open(TEST_IMAGE).convert("RGB")
    img_t = transform(img).unsqueeze(0).to(device)
    
    # 4. 추론 (Inference)
    with torch.no_grad():
        outputs = model(img_t)
        _, preds = torch.max(outputs, 1)
        prob = torch.softmax(outputs, dim=1)[0][preds[0]].item()
        
    print("\n" + "="*30)
    print(f"분석 결과: {CLASSES[preds[0]]}")
    print(f"확신도: {prob*100:.2f}%")
    print("="*30)

if __name__ == "__main__":
    simple_test()
