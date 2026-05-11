import os
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torchvision import transforms

# 1. 외상 분류 및 응급처치 매칭 DB (샘플)
WOUND_GUIDE_DB = {
    'Burns': {'Code': 'BURN-01', 'Treatment': '흐르는 찬물에 15분 이상 화상 부위를 식히십시오. 수포는 터뜨리지 마십시오.'},
    'Abrasions': {'Code': 'ABR-01', 'Treatment': '상처 부위를 식염수로 세척하고 오염물을 제거한 뒤 거즈로 보호하십시오.'},
    'Cuts': {'Code': 'CUT-01', 'Treatment': '직접 압박법으로 지혈하고, 상처 부위를 심장보다 높게 유지하십시오.'},
    'Lacerations': {'Code': 'LAC-01', 'Treatment': '출혈이 심할 경우 압박 지혈하고 즉시 봉합이 가능한 항구로 이동을 준비하십시오.'}
}

class WoundProcessor:
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size
        self.transform = transforms.Compose([
            transforms.Resize(self.target_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def preprocess_image(self, img_path):
        """이미지를 읽고 학습 가능한 텐서로 변환"""
        try:
            image = Image.open(img_path).convert('RGB')
            tensor = self.transform(image).unsqueeze(0) # 배치 차원 추가
            return tensor
        except Exception as e:
            print(f"이미지 전처리 오류 ({img_path}): {e}")
            return None

    def get_emergency_guide(self, predicted_class):
        """AI 판독 결과에 따른 응급처치 지침 반환"""
        return WOUND_GUIDE_DB.get(predicted_class, {"Treatment": "지침 없음. 원격 의료 지원을 요청하십시오."})

# 2. 파이프라인 엔진 가동 시나리오
if __name__ == "__main__":
    processor = WoundProcessor()
    
    # 예시: AI가 'Burns'로 판독했다고 가정할 때의 가이드 도출
    test_prediction = 'Burns'
    guide = processor.get_emergency_guide(test_prediction)
    
    print(f"--- [M-Medic] 실시간 응급처치 가이드 ---")
    print(f"판독 결과: {test_prediction}")
    print(f"관리 번호: {guide.get('Code', 'N/A')}")
    print(f"조치 사항: {guide['Treatment']}")
    
    # 파이프라인 스크립트 위치 저장
    PROJECT_ROOT = r"D:\GeminiUniverse\vscode-workspace\maritime-medic"
    print(f"\n파이프라인 엔진이 {PROJECT_ROOT}\wound_pipeline.py에 저장되었습니다.")
