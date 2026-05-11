import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import pandas as pd

# 1. 의료 지침 데이터베이스 (M-Medic Knowledge Base)
SKIN_DISEASE_GUIDE = {
    'mel': {'Name': '흑색종(악성피부암)', 'Risk': 'CRITICAL', 'Action': '즉시 회항 및 전문가 진료가 필요함. 전이 위험이 매우 높음.'},
    'nv': {'Name': '멜라닌세포모반(점)', 'Risk': 'LOW', 'Action': '일반적인 점으로 판단되나, 크기나 모양이 변할 경우 재진단 권장.'},
    'bcc': {'Name': '기저세포암(피부암)', 'Risk': 'HIGH', 'Action': '상태 악화 전 육지 병원에서 절제 수술을 권고함.'},
    'akiec': {'Name': '광선각화증(암전단계)', 'Risk': 'MEDIUM', 'Action': '자외선 차단 및 피부 보호 연고 사용 권장.'}
}

WOUND_TREATMENT_GUIDE = {
    'Burns': {'Name': '화상(Burns)', 'Risk': 'HIGH', 'Action': '수포를 터뜨리지 말고 환부를 찬물로 식히십시오. 감염 방지용 거즈 부착.'},
    'Cuts': {'Name': '절상(Cuts)', 'Risk': 'MEDIUM', 'Action': '출혈 부위를 압박 지혈하고 식염수로 세척 후 연고 도포.'},
    'Lacerations': {'Name': '열상(Lacerations)', 'Risk': 'HIGH', 'Action': '깊은 상처는 지혈 후 가급적 빠른 봉합 처치가 필요함.'}
}

class MMedicSystem:
    def __init__(self, model_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path)
        self.classes = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc'] # WOUND_DATA 7종
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _load_model(self, model_path):
        model = models.resnet50()
        num_ftrs = model.fc.in_features
        model.fc = nn.Linear(num_ftrs, 7)
        if model_path and os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        return model

    def diagnose(self, img_path, is_wound=False):
        """이미지 진단 통합 함수"""
        print(f"\n[M-Medic] '{img_path}' 분석을 시작합니다...")
        
        # 외상(Wound) 로직 (현재는 간단한 시뮬레이션으로 구현)
        if is_wound:
            # 예시로 폴더명이나 파일명에서 외상 유추 (데모용)
            result_key = 'Burns'
            guide = WOUND_TREATMENT_GUIDE.get(result_key)
            return self._format_result(guide)

        # 피부 질환(Skin Disease) 판독
        try:
            image = Image.open(img_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                output = self.model(input_tensor)
                _, pred = torch.max(output, 1)
                dx_code = self.classes[pred.item()]
            
            guide = SKIN_DISEASE_GUIDE.get(dx_code, {'Name': '알 수 없는 병변', 'Risk': 'UNKNOWN', 'Action': '전문 의료진의 자문 필요.'})
            return self._format_result(guide)
        except Exception as e:
            return f"오류 발생: {e}"

    def _format_result(self, guide):
        report = f"""
==================================================
        🚢 M-Medic 통합 의료 진단 보고서 🚢
==================================================
● 판독 질환: {guide.get('Name', '분석 불가')}
● 위험 등급: {guide.get('Risk', '미확인')}
--------------------------------------------------
● 긴급 조치 지침 (선원법 기반):
   - {guide.get('Action', '조치 사항 없음')}
==================================================
"""
        return report

# 2. 실행 테스트
if __name__ == "__main__":
    # 학습된 모델 경로 지정
    model_file = r"D:\GeminiUniverse\vscode-workspace\maritime-medic\best_m_medic_model.pth"
    system = MMedicSystem(model_path=model_file)
    
    # 샘플 이미지 테스트 (실제 이미지가 있다면 경로 입력)
    sample_path = r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\WOUND_DATA\sample_melanoma.jpg"
    if os.path.exists(sample_path):
        result = system.diagnose(sample_path)
        print(result)
    else:
        print("테스트용 샘플 이미지가 없습니다. 실제 이미지 경로를 입력해 주세요.")
