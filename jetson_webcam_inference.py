import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from PIL import Image
import os
import json
import time

# 1. 설정
MODEL_PATH = "mobilenet_v3_wound_best.pth"
MAPPING_PATH = "wound_class_mapping.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_class_mapping(json_path):
    if not os.path.exists(json_path):
        return ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
    with open(json_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    return [mapping[str(i)] for i in range(len(mapping))]

def main():
    # 클래스 매핑 로드
    CLASS_NAMES = load_class_mapping(MAPPING_PATH)
    num_classes = len(CLASS_NAMES)

    # 2. 모델 로드
    print(f"[*] Loading model on {DEVICE}...")
    try:
        model = models.mobilenet_v3_large(weights=None)
    except TypeError:
        model = models.mobilenet_v3_large(pretrained=False)
        
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        print("[+] Model weights loaded successfully.")
    else:
        print(f"[!] Error: {MODEL_PATH} not found.")
        return

    model = model.to(DEVICE)
    model.eval()

    # 3. 전처리 설정
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 4. 웹캠 설정 (Jetson Nano의 경우 /dev/video0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Error: Could not open webcam.")
        return

    print("[*] Starting real-time inference. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 추론을 위해 프레임 복사 및 변환
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_t = preprocess(img_pil)
        batch_t = torch.unsqueeze(img_t, 0).to(DEVICE)

        # 5. 추론 실행
        with torch.no_grad():
            outputs = model(batch_t)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)

        label = CLASS_NAMES[index]
        conf_score = confidence.item() * 100

        # 6. 화면 결과 오버레이 (OpenCV)
        # 결과 텍스트 배경
        cv2.rectangle(frame, (0, 0), (300, 80), (0, 0, 0), -1)
        
        # 텍스트 색상 결정 (신뢰도에 따라)
        color = (0, 255, 0) if conf_score > 70 else (0, 255, 255)
        
        cv2.putText(frame, f"Result: {label}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"Conf: {conf_score:.2f}%", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # FPS 표시
        cv2.putText(frame, "M-Medic Real-time AI", (frame.shape[1]-200, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 7. 출력
        cv2.imshow("M-Medic Real-time Wound Analysis", frame)

        # 'q' 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
