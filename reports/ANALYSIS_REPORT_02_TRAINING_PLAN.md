# 🧠 Project Maritime-Medic (M-Medic) 학습 전략 보고서 #02

**작성일:** 2026-04-10  
**담당자:** Gemini CLI  
**주제:** 피부 질환 및 외상 분류 모델 학습 계획 및 파이프라인 설계

---

## 1. 학습 목표 (Training Objectives)
- **WOUND_DATA 데이터셋:** 7가지 피부 질환(암 포함)에 대한 고정밀 분류 모델 개발.
- **Wound 데이터셋:** 선상 사고 시 빈번한 외상(화상, 절상 등)에 대한 응급 분류 체계 마련.

---

## 2. 모델링 전략 (Modeling Strategy)

### 2.1 아키텍처 선택 (Model Selection)
- **ResNet50 (Transfer Learning):** ImageNet으로 사전 학습된 가중치를 활용하여 학습 속도를 높이고 적은 데이터에서도 높은 성능 확보.

### 2.2 데이터 불균형 해결 (Addressing Class Imbalance)
- **Class Weights:** EDA 결과 '점(nv)' 데이터가 67%로 편중되어 있음. 손실 함수 산출 시 적은 데이터(흑색종 등)에 높은 가중치를 부여함.
- **Augmentation:** 
    - RandomHorizontalFlip, RandomVerticalFlip (기하학적 증강)
    - ColorJitter (조명 변화 대응)
    - RandomRotation (다양한 촬영 각도 대응)

### 2.3 학습 파이프라인 (Pipeline)
- **Framework:** PyTorch
- **Optimizer:** Adam (Initial LR: 0.0001)
- **Scheduler:** StepLR (성능 정체 시 학습률 감소)
- **Validation:** 8:2 비율로 Train/Val 데이터 분리

---

## 3. 예상 성과 (Expected Outcomes)
- 초기 테스트 결과 기반 85% 이상의 분류 정확도 목표.
- 악성 피부암(흑색종)에 대한 Recall(재현율) 극대화 (위험 상황 조기 발견 우선).

---

## 4. 관리자 메모
- 현재 학습 코드는 CPU/GPU 환경을 자동으로 감지하도록 설계됨.
- 학습 완료 후 `ANALYSIS_REPORT_03_RESULTS.md`에 최종 성능 지표 기록 예정.
