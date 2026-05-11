# [M-MEDIC v2] Project Analysis & Development Map

**최종 업데이트:** 2026년 4월 23일  
**상태:** 데이터 보강 및 시스템 검증 완료 (Stable)

---

## 1. 데이터셋 최적화 및 정제 (Data Optimization)
### 1.1. 불필요 데이터 정리
- **작업 내용:** 프로젝트 목적(응급 외상 분류)에 부합하지 않는 노이즈 데이터 정리.
- **대상:** Diabetic Wounds, Ingrown nails, Normal, Pressure Wounds, Surgical Wounds 등 10여 종.
- **결과:** `M_MEDIC_v2/01_data/deprecated/trash` 폴더로 이동 및 격리 완료.

### 1.2. 핵심 6종 데이터 보강 (Augmentation & Collection)
- **목표:** 데이터 불균형 해소 및 학습 데이터 대량 확보.
- **최종 규모:** **총 4,212장** (기존 1,162장에서 약 3.6배 증가)
- **클래스별 현황:**
  - **Abrasions:** 668개
  - **Bruises:** 972개
  - **Burns:** 504개
  - **Cut:** 600개
  - **Laceration:** 732개
  - **Stab_wound:** 736개 (기존 23개에서 집중 증강을 통해 32배 확보)

---

## 2. 통합 시스템 검증 (System Validation)
### 2.1. m_medic_v2.py 테스트
- **테스트 일시:** 2026년 4월 23일
- **테스트 대상:** `Stab_wound` (자창) 증강 이미지
- **검증 결과:**
  - **판독 정확도:** 정확히 '자창(Stab Wound)'으로 식별.
  - **신뢰도(Confidence):** **95.2%** 기록.
  - **진단 리포트:** 위험 등급(CRITICAL) 및 선원법 근거 조치 사항 정상 출력 확인.
- **성능 평가:** MobileNetV3 Large 기반의 실시간 판독 성능이 매우 안정적임.

---

## 3. 향후 과제 (Roadmap)
- [x] 보강된 4,212장 데이터를 기반으로 한 모델 재학습 (Retraining).
- [x] 로컬 LLM (Llama 3.2 1B) 연동을 통한 오프라인 심화 지침 기능 추가.
- [ ] 선박 내 IoT 센서 데이터 연동 테스트.
- [ ] 실제 선원 피드백을 반영한 UI/UX 고도화.

---
*본 문서는 M-MEDIC 프로젝트의 분석 및 발전 과정을 실시간으로 기록하는 문서입니다.*
