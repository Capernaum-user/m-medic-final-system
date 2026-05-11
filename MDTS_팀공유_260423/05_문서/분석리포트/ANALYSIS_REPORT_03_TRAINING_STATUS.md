# M-MEDIC v2 (MDTS) 학습 완료 보고서 #03

**작성일:** 2026-04-22  
**담당자:** 빅데이터 분석팀  
**주제:** MobileNetV3 Large 외상 분류 모델 학습 완료 및 성능 검증 결과

---

## 1. 최종 학습 설정 (Training Config)

| 항목 | 설정값 |
| :--- | :--- |
| 모델 | MobileNetV3 Large (ImageNet 사전학습) |
| 파라미터 수 | 4,209,718개 (~4.2M) |
| 학습 데이터 | 3,369장 (전체 4,212장의 80%) |
| 검증 데이터 | 843장 (전체 4,212장의 20%) |
| Epochs | 20 |
| Batch Size | 32 |
| Optimizer | AdamW (lr=1e-3, weight_decay=1e-4) |
| Scheduler | CosineAnnealingLR (T_max=20) |
| Loss | CrossEntropyLoss |
| 데이터 증강 | RandomHFlip, RandomVFlip, RandomRotation(±25°), ColorJitter, RandomAffine |

---

## 2. 학습 진행 상태

- [x] 데이터 전처리 및 증강 완료 (4,212장 구성)
- [x] Stratified Split Train/Val 분리 완료 (80:20)
- [x] WeightedRandomSampler 적용 (Stab_wound 소수 클래스 보정)
- [x] **모델 학습 완료** — `mobilenet_v3_wound_best.pth` 저장 (17MB)
- [x] **최종 성능 검증 완료**

---

## 3. 최종 성능 결과

| 지표 | 전체 | Abrasions | Bruises | Burns | Cut | Laceration | Stab_wound |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Precision | **88.50%** | 0.89 | 0.92 | 0.84 | 0.86 | 0.88 | 0.90 |
| Recall | **88.20%** | 0.87 | 0.93 | 0.82 | 0.85 | 0.89 | 0.91 |
| F1 Score | **88.35%** | 0.88 | 0.92 | 0.83 | 0.86 | 0.88 | 0.90 |

---

## 4. 향후 계획

- 저장된 모델(`mobilenet_v3_wound_best.pth`)을 통합 시스템(`m_medic_v2.py`)과 연동 완료
- 세그멘테이션 모델 추가 학습 예정 (v3)
- IoT 센서(활력징후) 데이터와 결합한 복합 진단 기능 확장 예정
