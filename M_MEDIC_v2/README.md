# M-Medic v2 프로젝트 구조 가이드

## 폴더 구조

```
M_MEDIC_v2/
├── 01_data/                         ← 데이터 관리
│   ├── raw/                         (원본 데이터 참조 위치)
│   └── processed/                   (전처리 완료 데이터)
│       ├── marine_accidents_augmented.csv   ← ML 학습용 (생성 후)
│       └── data_profile_report.txt          ← 데이터 현황 요약
│
├── 02_machine_learning/             ← 머신러닝 (해양사고 정형 데이터)
│   ├── 01_generate_accident_data.py ← [1단계] 학습 데이터 생성
│   ├── 02_train_accident_ml.py      ← [2단계] RF+XGBoost 학습
│   └── results/                     (모델, 차트, 보고서 저장)
│
├── 03_deep_learning/                ← 딥러닝 (이미지 데이터)
│   ├── skin_disease/
│   │   ├── 01_train_skin_efficientnet.py  ← EfficientNet-B3 학습
│   │   ├── 02_evaluate_skin_model.py      ← 평가 + Grad-CAM
│   │   └── results/
│   └── wound_detection/
│       ├── 01_train_wound_cnn.py          ← MobileNetV3 외상 분류
│       └── results/
│
├── 04_integrated_system/            ← 통합 진단 시스템
│   └── m_medic_v2.py                ← 최종 실행 파일
│
└── 05_presentation/                 ← 발표/보고서 자료
    ├── generate_charts.py           ← 발표용 차트 자동 생성
    ├── charts/                      (생성된 차트 PNG)
    ├── ANALYSIS_INSIGHTS.md         ← AI 결과 해석 가이드
    └── KAGGLE_REQUIREMENTS.md       ← 추가 필요 데이터셋 목록
```

## 실행 순서

```bash
# Step 1: ML 데이터 생성
python 02_machine_learning/01_generate_accident_data.py

# Step 2: ML 학습
pip install xgboost scikit-learn pandas matplotlib seaborn
python 02_machine_learning/02_train_accident_ml.py

# Step 3: 딥러닝 피부 분류 학습 (WOUND_DATA 필요)
pip install torch torchvision pillow
python 03_deep_learning/skin_disease/01_train_skin_efficientnet.py

# Step 4: 딥러닝 평가 (Step 3 완료 후)
python 03_deep_learning/skin_disease/02_evaluate_skin_model.py

# Step 5: 외상 분류 학습 (Wound 데이터셋 다운로드 후)
python 03_deep_learning/wound_detection/01_train_wound_cnn.py

# Step 6: 발표 차트 생성
python 05_presentation/generate_charts.py

# Step 7: 통합 시스템 데모 실행
python 04_integrated_system/m_medic_v2.py --demo
python 04_integrated_system/m_medic_v2.py --image <이미지경로> --mode skin --age 45
```

## ML vs 딥러닝 선택 근거 요약

| 구분 | 적용 영역 | 이유 |
|------|-----------|------|
| 머신러닝 | 해양사고 통계 예측 | 정형 테이블 데이터 → RF/XGBoost 최적, 설명 가능성 필요 |
| 딥러닝 | 피부 병변 분류 | 이미지에서 공간 패턴 자동 학습 필수, 수만 장 데이터 |
| 딥러닝 | 외상 이미지 분류 | 동일한 이유, MobileNetV3(경량화)로 선박 엣지 AI 배포 |
