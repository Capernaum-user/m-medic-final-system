# 01_data — 데이터 폴더 구조

MDTS 프로젝트에서 사용하는 모든 데이터의 현황과 경로를 정리합니다.

---

## 폴더 구조

```
01_data/
├── raw/
│   ├── wound_classification/       ← ★ 주 학습 데이터 (외상 분류)
│   │   ├── Abrasions/              찰과상  249장
│   │   ├── Bruises/                타박상  364장
│   │   ├── Burns/                  화상    193장
│   │   ├── Cut/                    절창    150장
│   │   ├── Laceration/             열창    183장
│   │   └── Stab_wound/             자창     23장
│   │                               합계  1,162장
│   │
│   ├── wound_segmentation/         ← 외상 세그멘테이션 (별도 모델용)
│   │   └── data_wound_seg/
│   │       ├── train_images/       2,208장
│   │       ├── train_masks/        2,208장
│   │       ├── test_images/          552장
│   │       └── test_masks/           552장
│   │
│   ├── wound_dataset_yasin/        ← yasin 원본 보존 (참조용)
│   │   └── Wound_dataset/          431장 (7클래스)
│   │
│   └── gicoms_marine_accidents_2014_2024.csv   ← 해양사고 통계 (ML용)
│                                                  48건, 2014~2024
│
├── processed/
│   └── marine_accidents_augmented.csv          ← 합성 해양사고 데이터
│                                                  1,500건
│
├── WOUND_DATA/                       ← [미사용] 피부암 이미지 — deprecated 참조
│   ├── WOUND_DATA_images_part_1/     5,000장
│   └── WOUND_DATA_images_part_2/     5,015장
│
└── deprecated/
    ├── README.md                   ← 미사용 데이터 설명
    └── wound_classes_not_used/     ← 선박 외상과 무관한 클래스
        ├── Diabetic_Wounds/        462장
        ├── Pressure_Wounds/        602장
        ├── Venous_Wounds/          494장
        ├── Normal/                 200장
        ├── Surgical_Wounds/        420장
        └── Ingrown_nails/           31장
```

---

## 데이터셋 출처

| 데이터셋 | 출처 | 용도 |
|----------|------|------|
| wound_classification | wound-classification-system (Kaggle) + yasin/wound-dataset (Kaggle) 병합 | 외상 분류 DL 학습 |
| wound_segmentation | leoscode/wound-segmentation-images (Kaggle) | 외상 세그멘테이션 |
| gicoms_marine_accidents | 중앙해양안전심판원 통계 기반 재구성 | 해양사고 ML 학습 |
| marine_accidents_augmented | 한국 해양안전심판원 통계 패턴 기반 합성 | 해양사고 ML 보조 |
| WOUND_DATA | ISIC Archive / Kaggle | [미사용] 피부암 — 제외됨 |

---

## wound_classification 클래스 정의

| 클래스 | 한글명 | 장수 | 선박 사고 관련성 |
|--------|--------|------|-----------------|
| Abrasions | 찰과상 | 249 | 갑판·구조물에 쓸린 상처 |
| Bruises | 타박상 | 364 | 충돌·낙하 시 타박 |
| Burns | 화상 | 193 | 엔진실 화재·증기 화상 |
| Cut | 절창 | 150 | 날카로운 도구에 의한 절상 |
| Laceration | 열창 | 183 | 거친 표면에 의한 찢김 |
| Stab_wound | 자창 | 23 | 날카로운 물체 관통 |

> 데이터 병합 출처: wcs_ 접두사 = wound-classification-system, yasin_ 접두사 = wound_dataset_yasin
