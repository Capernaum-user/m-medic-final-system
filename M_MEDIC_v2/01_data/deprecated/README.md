# deprecated/ — 사용하지 않는 데이터

이 폴더는 프로젝트 방향과 맞지 않아 **학습 파이프라인에서 제외된 데이터**를 보관합니다.
삭제하지 않고 보존하여, 추후 방향 변경 시 재활용할 수 있습니다.

---

## WOUND_DATA  (01_data/WOUND_DATA/ — 물리 이동 안 함)

| 항목 | 내용 |
|------|------|
| 용량 | 약 2.7 GB (10,015장) |
| 클래스 | mel(흑색종) / nv(멜라닌세포 모반) / bcc(기저세포암) / akiec / bkl / df / vasc |
| 제외 이유 | **피부암·피부 병변 이미지** — 선박 사고 시 발생하는 외상(찰과상·화상·타박상)과 무관 |
| 원 경로 | `01_data/WOUND_DATA/` |
| 참조 출처 | Kaggle WOUND_DATA / ISIC Archive |

> 물리적으로 이동하지 않았습니다. 폴더가 크기 때문에 삭제 전 팀 확인 후 진행하세요.

---

## wound_classes_not_used/  (이 폴더 안)

선박 사고와 무관한 의료적 만성 상처 클래스입니다.
원본 출처: `wound-classification-system/Wound_dataset copy/`

| 폴더명 | 한글명 | 장수 | 제외 이유 |
|--------|--------|------|-----------|
| Diabetic_Wounds | 당뇨성 궤양 | 462장 | 만성 당뇨 합병증 — 사고 외상 아님 |
| Pressure_Wounds | 욕창 | 602장 | 장기 와상에 의한 만성 상처 — 사고 외상 아님 |
| Venous_Wounds | 정맥성 궤양 | 494장 | 혈관 질환 — 사고 외상 아님 |
| Normal | 정상 피부 | 200장 | 학습 데이터로 활용 가능하나 현재 파이프라인 미포함 |
| Surgical_Wounds | 수술 상처 | 420장 | 선박에서 수술 시행 불가 — 현재 범위 외 |
| Ingrown_nails | 내성 발톱 | 31장 | 외상 아님 |

---

## 현재 사용 중인 데이터

| 경로 | 설명 | 장수 |
|------|------|------|
| `raw/wound_classification/` | **통합 외상 분류 데이터 (주 학습용)** | 1,162장 |
| `raw/wound_segmentation/` | 외상 세그멘테이션 데이터 | 2,760장 |
| `raw/wound_dataset_yasin/` | yasin 원본 (참조용 보존) | 431장 |
| `raw/gicoms_marine_accidents_2014_2024.csv` | 해양사고 통계 (ML용) | 48건 |
| `processed/marine_accidents_augmented.csv` | 해양사고 합성 데이터 (ML용) | 1,500건 |
