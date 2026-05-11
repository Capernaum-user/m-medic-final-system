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

# DB 설정 (라즈베리파이 또는 젯슨나노 로컬 DB 정보에 맞춰 수정 필요)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "yahboom", # 비밀번호 확인 필요
    "database": "m_medic_db"
}

def init_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # 데이터베이스 생성 (없을 경우)
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.database = DB_CONFIG['database']
        # 테이블 생성 (없을 경우)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wound_detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                diagnosis VARCHAR(100),
                confidence FLOAT,
                detected_at DATETIME,
                is_synced TINYINT DEFAULT 0
            )
        """)
        conn.commit()
        return conn
    except Exception as e:
        print(f"[!] DB Connection Error: {e}")
        return None

def save_to_db(conn, diagnosis, confidence):
    if conn is None: return
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO wound_detections (diagnosis, confidence, detected_at) VALUES (%s, %s, %s)"
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
        print("[+] DB Connected and Table Ready.")

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
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    cap = cv2.VideoCapture(0)
    print("[*] Monitoring... Press 'q' to quit.")

    last_save_time = 0
    save_interval = 3 # 3초마다 한 번씩 저장 (너무 자주 저장되지 않도록)

    while True:
        ret, frame = cap.read()
        if not ret: break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_t = preprocess(img_pil)
        batch_t = torch.unsqueeze(img_t, 0).to(DEVICE)

        with torch.no_grad():
            outputs = model(batch_t)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, index = torch.max(probabilities, 0)

        label = CLASS_NAMES[index]
        conf_score = confidence.item() * 100

        # 신뢰도가 80% 이상일 때만 DB 저장 시도
        if conf_score > 80 and (time.time() - last_save_time) > save_interval:
            save_to_db(db_conn, label, conf_score)
            last_save_time = time.time()
            print(f"[DB SAVED] {label} ({conf_score:.2f}%)")

        # 화면 출력
        color = (0, 255, 0) if conf_score > 70 else (0, 255, 255)
        cv2.putText(frame, f"Result: {label} ({conf_score:.2f}%)", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("M-Medic DB Sync Monitoring", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    if db_conn: db_conn.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
