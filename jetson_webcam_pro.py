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
import threading
from queue import Queue
from collections import deque

# 1. 설정
MODEL_PATH = "mobilenet_v3_wound_best.pth"
MAPPING_PATH = "wound_class_mapping.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 라즈베리파이 MySQL DB 설정 (MDTS)
DB_CONFIG = {
    "host": "192.168.219.64",
    "user": "mdts",
    "password": "12345",
    "database": "MDTS"
}

# --- 비동기 DB 작업자 (Thread) ---
db_queue = Queue()

def db_worker():
    conn = None
    while True:
        # 큐에서 데이터가 올 때까지 대기
        item = db_queue.get()
        if item is None: break
        
        diagnosis, confidence = item
        try:
            if conn is None or not conn.is_connected():
                conn = mysql.connector.connect(**DB_CONFIG)
            
            cursor = conn.cursor()
            sql = "INSERT INTO WOUND_DETECTIONS (diagnosis, confidence, detected_at) VALUES (%s, %s, %s)"
            val = (diagnosis, confidence, datetime.now())
            cursor.execute(sql, val)
            conn.commit()
            # print(f"[DB ASYNC SAVED] {diagnosis}")
        except Exception as e:
            print(f"[!] DB Async Error: {e}")
        finally:
            db_queue.task_done()

    if conn: conn.close()

# 작업자 스레드 시작
t = threading.Thread(target=db_worker, daemon=True)
t.start()

# --- 메인 클래스 ---
def load_class_mapping(json_path):
    if not os.path.exists(json_path):
        return ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
    with open(json_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    return [mapping[str(i)] for i in range(len(mapping))]

def main():
    CLASS_NAMES = load_class_mapping(MAPPING_PATH)
    num_classes = len(CLASS_NAMES)

    # 모델 로드 (최적화)
    print(f"[*] Loading model on {DEVICE}...")
    model = models.mobilenet_v3_large(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        print("[+] Model loaded.")
    else:
        print("[!] Model not found.")
        return

    model = model.to(DEVICE).eval()

    preprocess = transforms.Compose([
        transforms.Resize(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 인식 안정화를 위한 버퍼 (최근 5프레임 저장)
    result_buffer = deque(maxlen=5)
    
    cap = cv2.VideoCapture(0)
    # 젯슨나노 오린의 경우 해상도 조절로 FPS 확보 가능
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[*] Professional Mode Started. Press 'q' to quit.")

    last_save_time = 0
    save_cooldown = 3.0 # 동일 상처 저장 쿨다운

    while True:
        ret, frame = cap.read()
        if not ret: break

        # ROI 크롭 (중앙 300x300)
        h, w, _ = frame.shape
        box_size = 300
        x1, y1 = (w - box_size) // 2, (h - box_size) // 2
        x2, y2 = x1 + box_size, y1 + box_size
        
        roi = frame[y1:y2, x1:x2]
        img_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_t = preprocess(img_pil).unsqueeze(0).to(DEVICE)

        # 1. 추론
        with torch.no_grad():
            outputs = model(img_t)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            conf, idx = torch.max(probs, 0)
        
        # 2. 이동 평균 필터 적용 (안정화)
        result_buffer.append((idx.item(), conf.item()))
        
        # 버퍼 내에서 가장 많이 등장한 클래스 찾기
        counts = {}
        for c_idx, _ in result_buffer:
            counts[c_idx] = counts.get(c_idx, 0) + 1
        final_idx = max(counts, key=counts.get)
        
        # 해당 클래스의 평균 신뢰도 계산
        avg_conf = sum([c[1] for c in result_buffer if c[0] == final_idx]) / counts[final_idx]
        
        final_label = CLASS_NAMES[final_idx]
        final_score = avg_conf * 100

        # 3. 비동기 DB 저장 (신뢰도 높고 쿨다운 지났을 때)
        if final_score > 85 and (time.time() - last_save_time) > save_cooldown:
            db_queue.put((final_label, final_score))
            last_save_time = time.time()
            print(f"[ASYNC QUEUE] {final_label} ({final_score:.1f}%)")

        # 4. UI 렌더링
        color = (0, 255, 0) if final_score > 80 else (0, 255, 255) if final_score > 50 else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{final_label} {final_score:.1f}%", (x1, y1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # 상태 표시
        cv2.putText(frame, "ASYNC DB MODE: ON", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(frame, f"BUFFER: {len(result_buffer)}/5", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("M-Medic Pro Inference", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    # 종료 시 큐 정리
    db_queue.put(None)
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
