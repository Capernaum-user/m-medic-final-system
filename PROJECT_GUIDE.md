# 🚢 Project Maritime-Medic (M-Medic) 통합 가이드 및 최종 보고서

본 문서는 **Project Maritime-Medic**의 전체 여정, 시스템 구조, 사용법 및 분석 결과를 초보자도 쉽게 이해할 수 있도록 정리한 통합 가이드입니다.

---

## 1. 프로젝트 개요 (What is M-Medic?)
*   **목적:** 의사가 없는 선박 내에서 발생하는 피부 질환 및 외상을 AI가 판독하고, 선원법에 근거한 응급처치 지침을 제공하여 인명 피해를 최소화함.
*   **핵심 데이터:** 
    - **WOUND_DATA:** 10,015장의 피부 병변 이미지.
    - **Wound Dataset:** 화상, 절상 등 사고 외상 이미지.
    - **해양사고 통계:** 최근 해상 사고 패턴 데이터.
    - **의료지침:** 선원법 시행규칙 및 WHO 국제선내의료지침.

---

## 2. 폴더 및 파일 구조 (Folder Map)

```text
📁 maritime-medic/ (루트 폴더)
│
├── 📁 data/ (수집된 원본 데이터)
│   ├── 📁 WOUND_DATA/           # 10,015장의 피부 질환 이미지 및 정보
│   ├── 📁 Wound_Image_Dataset/ # 화상, 절상 등 외상 분류 이미지
│   ├── 📁 Marine_Accidents/    # 해양사고 통계 데이터 (CSV)
│   └── 📁 Medical_Guidelines/ # 선원법 및 WHO 의료 지침 문서
│
├── 📁 reports/ (분석 및 학습 결과 보고서)
│   ├── ANALYSIS_REPORT_01_EDA.md        # 데이터 기초 분석 결과
│   ├── ANALYSIS_REPORT_04_WOUND_EDA.md  # 외상 데이터 분석 결과
│   ├── training_history.csv             # AI 학습 기록 (Loss, Accuracy)
│   └── skin_disease_distribution.png    # 질병 분포 시각화 차트
│
├── 📄 eda_analysis.py            # [실행파일 1] 데이터를 분석하고 차트 생성
├── 📄 train_model.py             # [실행파일 2] AI 모델(ResNet50) 학습 시작
├── 📄 wound_pipeline.py          # [실행파일 3] 외상 데이터 전처리 및 지침 매칭
├── 📄 m_medic_integrated_system.py # [최종실행] AI 통합 진단기 실행 (메인 시스템)
└── 📄 best_m_medic_model.pth     # [핵심파일] 학습이 완료된 AI의 '두뇌' (가중치)
```

---

## 3. 주요 기능 및 실행 방법 (How to Use)

### ① 데이터 분석 결과 확인 (EDA)
*   **명령어:** `python eda_analysis.py`
*   **무엇을 하나요?** 수집된 1만 장의 사진 정보를 분석하여 어떤 질병이 많은지, 환자 나이대는 어떤지 시각화 차트를 만듭니다.
*   **결과물:** `reports` 폴더 안의 이미지와 마크다운 보고서.

### ② AI 모델 학습 (Training)
*   **명령어:** `python train_model.py`
*   **무엇을 하나요?** AI 모델(ResNet50)에게 사진을 보여주며 질병을 구별하는 방법을 가르칩니다.
*   **결과물:** 학습된 지능이 담긴 `best_m_medic_model.pth` 파일.

### ③ 통합 진단기 실행 (Final System)
*   **명령어:** `python m_medic_integrated_system.py`
*   **무엇을 하나요?** 사진 한 장으로 병명 판독 + 위험도 진단 + 응급처치 방법 안내를 동시에 수행합니다.
*   **핵심:** AI 판독 결과와 **선원법 가이드라인**을 자동으로 연결합니다.

---

## 4. 분석을 통해 알아낸 핵심 인사이트 (Key Insights)

1.  **클래스 불균형 발견:** 피부 질환 중 '점'이 가장 많지만, 치명적인 '흑색종'은 데이터가 적어 AI 학습 시 별도의 가중치 처리가 필수적임을 밝혀냈습니다.
2.  **사고-외상 매칭:** 해양사고 통계 분석을 통해 어선 사고 시 '화상'과 '열상'에 대한 대비가 가장 시급함을 도출했습니다.
3.  **지능형 가이드의 가치:** 단순히 병명을 아는 것보다, 선상에서 즉시 실행 가능한 **'법적 근거가 있는 조치 사항'**을 함께 제공하는 것이 의료 사고 예방에 핵심입니다.

---

## 5. 관리자 메모 (Future Work)
- 현재 시스템은 CPU/GPU 환경에서 모두 작동하도록 설계되었습니다.
- 향후 스마트폰 앱 형태로 배포한다면 선원들이 현장에서 즉시 부상 부위를 촬영하여 진단받는 '포켓 의료 관리자'가 될 수 있습니다.

---
**작성자:** Gemini CLI (Project M-Medic System Architect)
