import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from PIL import Image
import os
import json
import time
import mysql.connector
from datetime import datetime

# 1. 설정
MODEL_PATH = "mobilenet_v3_wound_best.pth"
MAPPING_PATH = "wound_class_mapping.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 라즈베리파이 MySQL DB 설정
DB_CONFIG = {
    "host": "192.168.219.64",
    "user": "root",
    "password": "1234",
    "database": "sensor"
}

def init_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[!] DB Connection Error: {e}")
        return None

def save_to_db(conn, diagnosis, confidence):
    if conn is None: return
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO wound_results (diagnosis, confidence, detected_at) VALUES (%s, %s, %s)"
        val = (diagnosis, confidence, datetime.now())
        cursor.execute(sql, val)
        conn.commit()
    except Exception as e:
        print(f"[!] DB Save Error: {e}")

def load_class_mapping(json_path):
    if not os.path.exists(json_path):
        return ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
    with open(json_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    return [mapping[str(i)] for i in range(len(mapping))]

def main():
    CLASS_NAMES = load_class_mapping(MAPPING_PATH)
    num_classes = len(CLASS_NAMES)

    # DB 초기화
    db_conn = init_db()
    if db_conn:
        print("[+] Connected to Raspberry Pi DB.")

    # 모델 로드
    print(f"[*] Loading model on {DEVICE}...")
    model = models.mobilenet_v3_large(weights=None)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, num_classes)
    
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        print("[+] Model weights loaded.")
    else:
        print("[!] Model not found.")
        return

    model = model.to(DEVICE)
    model.eval()

    preprocess = transforms.Compose([
        transforms.Resize(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    cap = cv2.VideoCapture(0)
    print("[*] Monitoring with Targeting Box... Press 'q' to quit.")

    last_save_time = 0
    save_interval = 3 

    while True:
        ret, frame = cap.read()
        if not ret: break

        # --- 타겟팅 박스(ROI) 설정 ---
        h, w, _ = frame.shape
        box_size = 300
        x1 = (w - box_size) // 2
        y1 = (h - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size

        # 박스 영역만 크롭하여 AI에게 전달 (정확도 향상)
        roi = frame[y1:y2, x1:x2]
        img_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_t = preprocess(img_pil)
        batch_t = torch.unsqueeze(img_t, 0).to(DEVICE)

        # AI 추론
        with torch.no_grad():
            outputs = model(batch_t)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)

        label = CLASS_NAMES[index]
        conf_score = confidence.item() * 100

        # DB 저장 (80% 이상일 때)
        if conf_score > 80 and (time.time() - last_save_time) > save_interval:
            if db_conn and db_conn.is_connected():
                save_to_db(db_conn, label, conf_score)
                print(f"[PI DB SAVED] {label} ({conf_score:.2f}%)")
            last_save_time = time.time()

        # --- UI 그리기 ---
        # 신뢰도에 따라 박스 색상 변경 (녹색: 높음, 노란색: 보통, 빨간색: 낮음)
        if conf_score > 85: box_color = (0, 255, 0) # Green
        elif conf_score > 60: box_color = (0, 255, 255) # Yellow
        else: box_color = (0, 0, 255) # Red

        # 타겟팅 박스 그리기
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
        # 모서리 강조 효과
        length = 30
        cv2.line(frame, (x1, y1), (x1 + length, y1), box_color, 6)
        cv2.line(frame, (x1, y1), (x1, y1 + length), box_color, 6)
        cv2.line(frame, (x2, y1), (x2 - length, y1), box_color, 6)
        cv2.line(frame, (x2, y1), (x2, y1 + length), box_color, 6)
        cv2.line(frame, (x1, y2), (x1 + length, y2), box_color, 6)
        cv2.line(frame, (x1, y2), (x1, y2 - length), box_color, 6)
        cv2.line(frame, (x2, y2), (x2 - length, y2), box_color, 6)
        cv2.line(frame, (x2, y2), (x2, y2 - length), box_color, 6)

        # 결과 텍스트 표시
        cv2.rectangle(frame, (x1, y1 - 40), (x1 + 250, y1), box_color, -1)
        cv2.putText(frame, f"{label} {conf_score:.1f}%", (x1 + 5, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.putText(frame, "Align wound inside the box", (10, h - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("M-Medic AI Targeting", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    if db_conn: db_conn.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
