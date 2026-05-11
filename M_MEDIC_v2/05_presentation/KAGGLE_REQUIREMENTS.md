# M-Medic 추가 필요 Kaggle 데이터셋 분석

**작성일:** 2026-04-15  
**분석 목적:** 현재 프로젝트의 데이터 공백을 채울 Kaggle 데이터셋 조사

---

## 1. 현재 데이터 현황 및 공백

| 데이터 영역 | 보유 현황 | 공백 / 문제점 |
|-------------|-----------|---------------|
| 피부 병변 (WOUND_DATA) | 10,015장 ✓ | nv(점) 67% 불균형, 악성 데이터 부족 |
| 외상 이미지 | **0장 (미확보)** | 화상·열상·절상 분류 불가 |
| 해양사고 통계 | 4행 샘플만 | 실제 1,000건 이상 필요 |
| 선박 환경 이미지 | 없음 | 실제 선박 조명/각도 도메인 편향 |
| 피부경 이미지 | 없음 | 전문 진단 정확도 향상 가능 |

---

## 2. 최우선 확보 필요 데이터셋 (Priority 1)

### A. 외상(Wound) 분류 데이터셋 — 즉시 필요

**1순위: Wound Image Dataset**
```
데이터셋명 : Wound Classification Dataset
Kaggle 경로: kaggle datasets download ibrahimfateen/wound-classification
포함 클래스: Burns, Cuts, Lacerations, Bruises (약 2,000장)
필요 이유  : 현재 외상 분류 모델이 전혀 학습되지 않은 상태
             실제 화상과 열상을 구분 못하면 처치 방향이 완전히 달라짐
활용 방안  : 03_deep_learning/wound_detection/ 의 학습 파이프라인에 바로 적용
다운로드   : kaggle datasets download -d ibrahimfateen/wound-classification
```

**2순위: Wound Segmentation Dataset**
```
데이터셋명 : Skin Wound Detection and Segmentation
Kaggle 경로: kaggle datasets download kushagra3204/wound-segmentation-dataset
특징       : 픽셀 단위 세그멘테이션 마스크 포함 (상처 범위 측정 가능)
추가 가치  : 화상 범위(%) 측정 → "체표면적 15% 이상 시 즉시 회항" 자동화 가능
```

**3순위: Burn Wound Images**
```
데이터셋명 : Burn Wound Images Dataset  
Kaggle 경로: kaggle datasets download rrafieighiasvand/burn-wound-images
특징       : 1도/2도/3도 화상 분류 레이블 포함
추가 가치  : 화상 심도 분류 → 처치 지침을 더 세분화 가능
```

---

## 3. 피부 병변 보완 데이터셋 (Priority 2)

### B. 흑색종 특화 데이터셋 — F1 Score 개선용

**1순위: ISIC 2020 Challenge Dataset**
```
데이터셋명 : SIIM-ISIC Melanoma Classification
Kaggle 경로: kaggle competitions download siim-isic-melanoma-classification
크기       : 33,126장 (WOUND_DATA의 3배 이상)
필요 이유  : WOUND_DATA에서 흑색종(mel) 데이터가 1,113장으로 부족
             이 데이터셋 병합 시 흑색종 F1 Score 0.05~0.10 향상 예상
주의       : 이미지 크기가 다양 (리사이징 전처리 필요)
```

**2순위: Skin Lesion Analysis Dataset (ISIC 2019)**
```
데이터셋명 : Skin Lesion Analysis Toward Melanoma Detection 2019
Kaggle 경로: kaggle datasets download andrewmvd/isic-2019
크기       : 25,331장, 9개 클래스 (WOUND_DATA 7클래스 + 2종 추가)
필요 이유  : 더 다양한 피부 병변 유형 학습 → 범용성 향상
```

---

## 4. 해양사고 통계 보완 (Priority 2)

### C. 국내외 해양사고 공공데이터

**국내 공공데이터 (Kaggle 아님)**
```
출처     : 해양안전종합정보시스템 (GICOMS)
URL      : https://www.gicoms.go.kr
다운로드 : 통계자료 > 해양사고 현황
기간     : 2014~2024 (10년치)
필요 이유: 현재 샘플 4행 → 실제 5,000건 이상 확보 가능
활용     : ML 모델 정확도를 현재 예상치(F1 0.81)에서 0.85 이상으로 향상
```

**국제 해양사고 데이터**
```
데이터셋명 : Maritime Accident Dataset
Kaggle 경로: kaggle datasets download eminbasturk/marine-accidents-1991-2023
크기       : 1991~2023 국제 해양사고 11,000건
필요 이유  : 국내 데이터만 학습 시 원양 항로 선박에는 일반화 어려움
```

---

## 5. 고급 활용 데이터셋 (Priority 3 - 향후 개선)

### D. 선박 환경 도메인 적응용

**선박 환경 이미지**
```
문제   : WOUND_DATA은 병원 피부과 촬영 이미지
        실제 선박은 형광등 조명, 스마트폰 촬영, 흔들림 있음
        → 도메인 갭(Domain Gap)으로 성능 20~30% 하락 예상
해결책 : 선박 환경에서 직접 촬영한 이미지로 Fine-tuning 필요
데이터 : 시범 사업 선박 5척 이상에서 실제 촬영 데이터 수집 권장
```

**피부경(Dermoscopy) 이미지**
```
데이터셋명 : ISIC Archive (피부경 촬영)
특징       : 전문 피부경으로 촬영 → 피부 아래 구조까지 보임
기대 효과  : 피부암 분류 정확도 추가 5~10% 향상
현실적 문제: 선박에 피부경 장비 없음 → 스마트폰 촬영 기준으로 유지 권장
```

---

## 6. 데이터 확보 우선순위 로드맵

```
즉시 (이번 발표 전):
  [1] Wound Classification Dataset 다운로드
      → 외상 분류 모델 학습 완료
  [2] GICOMS 해양사고 통계 다운로드
      → ML 모델 재학습

단기 (1개월 내):
  [3] SIIM-ISIC 2020 Melanoma Dataset
      → 흑색종 F1 Score 개선

중기 (시범 사업 후):
  [4] 실제 선박 환경 촬영 데이터 수집
      → 도메인 적응 Fine-tuning
```

---

## 7. 데이터 통합 후 예상 성능 향상

| 데이터 추가 전 | 데이터 추가 후 | 향상폭 |
|---------------|---------------|--------|
| 외상 분류: 불가 | Val Acc ≥ 0.85 | 핵심 기능 활성화 |
| 흑색종 F1: ~0.72 | F1 ≥ 0.80 | 안전성 크게 향상 |
| ML F1: ~0.81 | F1 ≥ 0.87 | 실제 통계 학습 효과 |
| 선박 환경 테스트: 미실시 | Acc 하락 폭 < 5% | 현장 적용 가능 수준 |

---

> **결론:** 현재 가장 시급한 것은 **외상 이미지 데이터 확보**입니다.  
> 피부 병변 AI는 이미 동작하지만, 선박에서 더 빈번한 화상·열상 분류 모델이  
> 현재 시뮬레이션 상태이므로 실제 가치 제공이 불가능합니다.
