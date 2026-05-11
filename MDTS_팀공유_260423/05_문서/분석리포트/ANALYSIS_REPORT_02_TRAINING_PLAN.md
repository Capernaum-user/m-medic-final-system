# M-MEDIC v2 (MDTS) 학습 전략 보고서 #02

**작성일:** 2026-04-10  
**담당자:** 빅데이터 분석팀  
**주제:** 외상 분류 모델(DL) 및 해양사고 예측 모델(ML) 학습 계획 및 파이프라인 설계

---

## 1. 학습 목표

- **딥러닝 (DL):** MobileNetV3 Large로 선박 사고 외상 6종 자동 분류 모델 개발
- **머신러닝 (ML):** RandomForest / GradientBoosting으로 해양사고 사상자 발생 예측 모델 개발

---

## 2. 딥러닝 모델링 전략 (외상 분류)

### 2.1 아키텍처 선택

| 항목 | 내용 |
| :--- | :--- |
| 모델 | MobileNetV3 Large (torchvision 제공 사전학습 가중치) |
| 파라미터 수 | 약 4.2M (4,209,718개) — 엣지 디바이스 최적화 |
| 모델 크기 | 약 17MB |
| 추론 속도 | < 200ms (CPU 기준) |
| 분류기 교체 | 마지막 Linear 레이어 → 출력 6 (외상 클래스 수) |

### 2.2 데이터 불균형 해결

- **WeightedRandomSampler:** 소수 클래스(Stab_wound) 오버샘플링으로 클래스 불균형 보정
- **데이터 증강 (훈련셋 한정):**
  - RandomHorizontalFlip (p=0.5), RandomVerticalFlip (p=0.3)
  - RandomRotation (±25°), ColorJitter (밝기·대비·채도·색조)
  - RandomAffine (translate ±5%)
- **정규화:** ImageNet 기준 mean/std

### 2.3 학습 파이프라인

| 항목 | 설정값 |
| :--- | :--- |
| Framework | PyTorch |
| Batch Size | 32 |
| Epochs | 20 |
| Optimizer | AdamW (lr=1e-3, weight_decay=1e-4) |
| Scheduler | CosineAnnealingLR (T_max=20, eta_min=1e-6) |
| Loss | CrossEntropyLoss |
| 장치 | CUDA(GPU 우선) / CPU 폴백 |

---

## 3. 머신러닝 모델링 전략 (해양사고 예측)

### 3.1 아키텍처 선택

- **RandomForest** (이진분류 최고 성능) — 사상자 발생 여부 예측
- **GradientBoosting** (다중분류 최고 성능) — 위험등급 4단계 예측

### 3.2 학습 파이프라인

| 항목 | 설정값 |
| :--- | :--- |
| 입력 피처 | 연도, 사고유형, 선박종류, 사고원인, 발생해역 (범주형 5개) |
| 검증 전략 | 5-Fold Stratified Cross Validation |
| 평가 지표 | F1-Score (macro), Accuracy |

---

## 4. 예상 성과

- DL 외상 분류 목표 정확도: **95% 이상** (실제 달성: 99.76%)
- ML 사상자 예측 목표 F1: **0.70 이상** (실제 달성: RF F1=0.762)
