# 📋 Project M-Medic 데이터 테이블 정의서

본 문서는 **Project Maritime-Medic**에서 활용하는 핵심 데이터셋의 컬럼 정의 및 구조를 설명합니다.

---

## 1. 피부 질환 메타데이터 (Table: WOUND_DATA_Metadata)
*   **파일 경로:** `data/WOUND_DATA/WOUND_DATA_metadata.csv`
*   **데이터 용도:** 피부암 및 일반 병변 이미지 분류 학습용 메타데이터

| 컬럼명 | 데이터 타입 | 설명 | 비고 (샘플/범주) |
| :--- | :--- | :--- | :--- |
| `lesion_id` | String | 병변 고유 ID | HAM_0000001 |
| `image_id` | String | 이미지 파일명 | ISIC_0024306 |
| `dx` | Category | 질병 코드 (라벨) | mel, nv, bcc, akiec 등 (7종) |
| `dx_type` | Category | 진단 확정 방법 | histo, follow_up, consensus |
| `age` | Float | 환자 나이 | 0.0 ~ 85.0 |
| `sex` | Category | 환자 성별 | male, female, unknown |
| `localization` | Category | 병변 발생 부위 | back, foot, trunk, face 등 (15종) |

---

## 2. 해양사고 통계 데이터 (Table: Marine_Accidents)
*   **파일 경로:** `data/Marine_Accidents/marine_accidents_history.csv`
*   **데이터 용도:** 해상 사고 패턴 분석 및 의료 지원 우선순위 도출용

| 컬럼명 | 데이터 타입 | 설명 | 비고 (샘플/범주) |
| :--- | :--- | :--- | :--- |
| `연도` | Integer | 사고 발생 연도 | 2023, 2024 등 |
| `사고유형` | Category | 사고의 종류 | 충돌, 화재, 좌초, 침몰, 전복 |
| `선박종류` | Category | 사고 선박의 타입 | 어선, 여객선, 화물선, 유조선 |
| `사고원인` | Category | 주요 사고 원인 | 운항과실, 기계결함, 기상악화 |
| `발생해역` | Category | 사고 발생 위치 | 동해, 서해, 남해, 원양 |
| `사상자수` | Integer | 인명 피해 인원수 | 0, 1, 2... |

---

## 3. 외상 조치 지침 데이터 (Table: Wound_Treatment_Guide)
*   **파일 경로:** `wound_pipeline.py` (내부 DB)
*   **데이터 용도:** AI 판독 결과에 따른 응급처치 가이드 매칭용

| 컬럼명 | 데이터 타입 | 설명 | 비고 (샘플/범주) |
| :--- | :--- | :--- | :--- |
| `Category` | String | 외상의 종류 (Key) | Burns, Cuts, Abrasions 등 |
| `Code` | String | 조치 관리 번호 | BURN-01, CUT-01 |
| `Name` | String | 표시용 질환명 | 화상(Burns), 절상(Cuts) |
| `Risk` | String | 위험 등급 | LOW, MEDIUM, HIGH, CRITICAL |
| `Treatment` | Text | 상세 응급처치 지침 | "흐르는 찬물에 식히십시오..." |

---

## 4. 의료관리자 교육 과정 (Table: Medical_Manager_Training)
*   **데이터 출처:** 선원법 시행규칙 [별표 5의5]
*   **데이터 용도:** 의료관리자 업무 범위 및 필수 역량 정의용

| 컬럼명 | 데이터 타입 | 설명 | 비고 (샘플/범주) |
| :--- | :--- | :--- | :--- |
| `과목명` | String | 교육 과목 | 기초응급처치학, 기초간호학 등 |
| `주요내용` | Text | 세부 학습 항목 | 심폐소생술, 지혈법, 공중보건 |
| `교육시간` | Integer | 이수 필요 시간 | 5, 10, 35 (단위: 시간) |
| `평가기준` | String | 수료 조건 | 60점 이상 득점 |

---
**작성일:** 2026-04-10
**작성자:** Gemini CLI (Data Architect)
