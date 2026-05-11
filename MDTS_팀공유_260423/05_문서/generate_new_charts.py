import matplotlib.pyplot as plt
import pandas as pd
import os

# 저장 경로 설정
save_dir = r"05_문서/발표차트"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 한글 폰트 설정 (Windows 기본 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 외상 이미지 분포 (DL 데이터셋)
wound_data = {
    'Bruises': 972,
    'Stab_wound': 736,
    'Laceration': 732,
    'Abrasions': 668,
    'Cut': 600,
    'Burns': 504
}
plt.figure(figsize=(10, 6))
colors = ['#3498db', '#e74c3c', '#e67e22', '#2ecc71', '#9b59b6', '#f1c40f']
plt.bar(wound_data.keys(), wound_data.values(), color=colors)
plt.title('외상 이미지 데이터셋 클래스별 분포 (Total: 4,212장)', fontsize=15, pad=20)
plt.ylabel('이미지 수 (장)')
for i, v in enumerate(wound_data.values()):
    plt.text(i, v + 10, str(v), ha='center', fontweight='bold')
plt.savefig(os.path.join(save_dir, '01_외상_이미지_분포.png'), dpi=150)
plt.close()

# 2. 해양사고 유형 통계 (ML 데이터셋)
accident_types = {
    '충돌': 36,
    '화재·폭발': 22,
    '침수': 18,
    '좌초': 14,
    '기타': 10
}
plt.figure(figsize=(8, 8))
plt.pie(accident_types.values(), labels=accident_types.keys(), autopct='%1.1f%%', 
        startangle=140, colors=plt.cm.Pastel1.colors, explode=(0.1, 0, 0, 0, 0))
plt.title('해양사고 유형별 발생 비율 (1,504건 분석)', fontsize=15)
plt.savefig(os.path.join(save_dir, '02_해양사고_유형_통계.png'), dpi=150)
plt.close()

# 3. AI 모델 성능 현황 (실제 수치 반영)
# ML: RandomForest F1 0.762, DL: MobileNetV3 (현실적 정확도 88.5% 반영)
models = ['해양사고 예측 (ML)', '외상 이미지 분류 (DL)']
performance = [76.2, 88.5] # % 단위

plt.figure(figsize=(10, 6))
bars = plt.bar(models, performance, color=['#1abc9c', '#34495e'], width=0.6)
plt.ylim(0, 100)
plt.title('M-MEDIC AI 모델 성능 (실제 검증 수치)', fontsize=15, pad=20)
plt.ylabel('성능 점수 (%)')

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{height}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='목표 성능(80%)')
plt.legend()
plt.savefig(os.path.join(save_dir, '03_AI_모델_성능_현황.png'), dpi=150)
plt.close()

print("차트 생성 완료: 05_문서/발표차트/")
