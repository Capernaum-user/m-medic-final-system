# 🚢 테이블 명세서 (Table Specification)

**프로젝트 명:** Maritime-Medic (M-Medic)  
**과제명:** AI 기반 선상 통합 진단 및 응급처치 가이드 시스템  
**작성일:** 2026-04-10  
**작성자:** Gemini CLI (Data Architect)

---

## I. 테이블 목록

| 테이블명 | 테이블_ID | 비고 |
| :--- | :--- | :--- |
| 피부 질환 메타데이터 | HAM_METADATA | WOUND_DATA 기반 |
| 해양사고 이력 통계 | ACCIDENT_HISTORY | 공공데이터 기반 |
| 외상 조치 지침 DB | WOUND_GUIDE | 선원법/WHO 지침 기반 |
| 의료관리자 교육과정 | TRAINING_INFO | 선원법 시행규칙 기반 |

---

## II. 테이블 정의서

### 1. 피부 질환 메타데이터
| 작성일자 | 2026-04-10 | 작성자 | Gemini CLI |
| :--- | :--- | :--- | :--- |
| **테이블명** | 피부 질환 메타데이터 | **테이블 ID** | HAM_METADATA |
| **테이블설명** | 10,015장의 피부 병변 이미지 분석 정보 및 환자 데이터 | | |

| 컬럼명 | 컬럼 ID | 타입(길이) | NN | PK | FK | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 병변 고유 ID | lesion_id | VARCHAR(50) | X | O | | |
| 이미지 ID | image_id | VARCHAR(50) | X | | | 파일명 매칭 |
| 질병 코드 | dx | VARCHAR(20) | X | | | mel, nv 등 7종 |
| 진단 방법 | dx_type | VARCHAR(30) | X | | | histo, consensus |
| 환자 나이 | age | FLOAT | | | | |
| 환자 성별 | sex | VARCHAR(10) | | | | male, female |
| 발생 부위 | localization | VARCHAR(50) | | | | face, back 등 |

#### [Table 생성 스크립트]
```sql
CREATE TABLE HAM_METADATA (
    lesion_id VARCHAR(50) PRIMARY KEY,
    image_id VARCHAR(50) NOT NULL,
    dx VARCHAR(20) NOT NULL,
    dx_type VARCHAR(30) NOT NULL,
    age FLOAT,
    sex VARCHAR(10),
    localization VARCHAR(50)
);
```

---

### 2. 해양사고 이력 통계
| 작성일자 | 2026-04-10 | 작성자 | Gemini CLI |
| :--- | :--- | :--- | :--- |
| **테이블명** | 해양사고 이력 통계 | **테이블 ID** | ACCIDENT_HISTORY |
| **테이블설명** | 최근 발생한 해상 사고의 원인, 선종 및 사상자 통계 데이터 | | |

| 컬럼명 | 컬럼 ID | 타입(길이) | NN | PK | FK | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 사고 ID | ACCIDENT_ID | INT | X | O | | 자동 증가 |
| 사고 연도 | YEAR | INT | X | | | |
| 사고 유형 | ACC_TYPE | VARCHAR(50) | X | | | 충돌, 화재 등 |
| 선박 종류 | SHIP_TYPE | VARCHAR(50) | X | | | 어선, 화물선 등 |
| 사고 원인 | CAUSE | VARCHAR(100) | X | | | 운항과실 등 |
| 사상자 수 | CASUALTIES | INT | X | | | |

#### [Table 생성 스크립트]
```sql
CREATE TABLE ACCIDENT_HISTORY (
    ACCIDENT_ID INT AUTO_INCREMENT PRIMARY KEY,
    YEAR INT NOT NULL,
    ACC_TYPE VARCHAR(50) NOT NULL,
    SHIP_TYPE VARCHAR(50) NOT NULL,
    CAUSE VARCHAR(100) NOT NULL,
    CASUALTIES INT DEFAULT 0
);
```

---

### 3. 외상 조치 지침 DB
| 작성일자 | 2026-04-10 | 작성자 | Gemini CLI |
| :--- | :--- | :--- | :--- |
| **테이블명** | 외상 조치 지침 DB | **테이블 ID** | WOUND_GUIDE |
| **테이블설명** | AI 판독 결과에 따른 선원법 기반 응급처치 지침 매칭 데이터 | | |

| 컬럼명 | 컬럼 ID | 타입(길이) | NN | PK | FK | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 카테고리 ID | CAT_ID | VARCHAR(20) | X | O | | Burns, Cuts 등 |
| 관리 번호 | GUIDE_CODE | VARCHAR(20) | X | | | BURN-01 등 |
| 질환명 | DX_NAME | VARCHAR(50) | X | | | 화상, 열상 등 |
| 위험 등급 | RISK_LEVEL | VARCHAR(10) | X | | | HIGH, LOW 등 |
| 조치 내용 | TREATMENT | TEXT | X | | | 상세 처치 방법 |

#### [Table 생성 스크립트]
```sql
CREATE TABLE WOUND_GUIDE (
    CAT_ID VARCHAR(20) PRIMARY KEY,
    GUIDE_CODE VARCHAR(20) NOT NULL,
    DX_NAME VARCHAR(50) NOT NULL,
    RISK_LEVEL VARCHAR(10) NOT NULL,
    TREATMENT TEXT NOT NULL
);
```
