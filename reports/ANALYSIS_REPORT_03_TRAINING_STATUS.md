# 🤖 Project Maritime-Medic (M-Medic) 학습 진행 보고서 #03

**작성일:** 2026-04-10  
**담당자:** Gemini CLI  
**주제:** WOUND_DATA 전체 데이터셋(10,015장) 10 Epoch 학습 진행 현황

---

## 1. 현재 학습 설정 (Training Config)
- **Model:** ResNet50 (Pre-trained on ImageNet)
- **Epochs:** 10
- **Batch Size:** 32
- **Data Augmentation:** Horizontal/Vertical Flip, Rotation(20), Color Jitter
- **Loss Function:** Weighted CrossEntropy (클래스 불균형 해소)
- **Optimizer:** Adam (LR: 0.0001)

---

## 2. 진행 상태 (Current Status)
- [x] 데이터 전처리 및 클래스 가중치 계산 완료
- [x] Train(80%) / Val(20%) 데이터 분리 완료
- [>] 전체 에폭 학습 진행 중 (백그라운드 실행)
- [ ] 최적 모델(`best_m_medic_model.pth`) 저장 대기
- [ ] 최종 성능 지표(F1-Score, Confusion Matrix) 도출 대기

---

## 3. 향후 계획
- 학습 완료 후 **Wound Image Dataset(외상 분류)**으로 학습 파이프라인을 확장.
- 저장된 모델을 활용한 **실시간 이미지 추론(Inference) 시스템** 구축.
- 선원법 가이드라인과 연계된 **지능형 응급처치 추천 로직** 통합.

---

## 4. 관리자 메모
- 대용량 이미지 학습 특성상 장시간 소요됨에 따라 프로세스를 안정적으로 유지 중.
- 최종 학습 결과는 본 문서에 업데이트되거나 별도의 `RESULTS.md`로 발행 예정.
