# MDTS / M-MEDIC 작업 기준 메모

## TL;DR

- 이 문서는 `D:\GeminiUniverse\vscode-workspace\wip-maritime-medic` 작업 시 우선 참조할 프로젝트 기준 문서다.
- 기준 검토일: 2026-05-12
- 검토 대상: 프로젝트 내 Markdown 40개
- 제외 대상: `.git`, `node_modules`, `.venv`, `venv`, `env`, `dist`, `build`, `.next`, `.cache`, `__pycache__`
- 폴더 최신 업데이트일은 해당 폴더 안의 Markdown 파일 중 가장 최근 `LastWriteTime` 기준이다.
- 현재 프로젝트 핵심 방향은 선박용 엣지 AI 의료 지원 시스템(MDTS/M-MEDIC)이다.

## 1. 프로젝트 핵심 정의

MDTS/M-MEDIC은 의사가 없는 선박 환경에서 러기드 태블릿 또는 선내 웹 대시보드로 환자 상태, 외상 이미지, 바이탈 데이터, 과거 진료 이력을 통합해 응급처치 의사결정을 지원하는 오프라인 우선 Edge AI 의료 지원 시스템이다.

핵심 구성은 다음과 같다.

- Jetson Nano: AI 추론, Ollama LLM, MobileNetV3 외상 분류, FastAPI 백엔드, Vite/React 대시보드 호스팅
- Raspberry Pi: MariaDB, Flask 센서 서버, USB 기반 Vector DB 저장소, NFS export
- AI 지식 구조: RAG용 ChromaDB, MariaDB 기반 환자 이력 MCP Bridge, 실시간 바이탈 컨텍스트
- UI: PyQt5 GUI, React/Vite 웹 대시보드
- 데이터: 외상 이미지, 피부 병변 이미지, 해양사고 통계, 선원법/WHO 의료 지침

## 2. 우선 참고 문서 순서

작업 전 다음 문서를 우선순위대로 참고한다.

1. `PROJECT_WORKING_MEMORY.md`: 폴더 기능과 현재 작업 기준
2. `HANDOVER_AI.md`: 최신 AI 시스템 인수인계 문서, v2.2
3. `PROJECT_STATE_LOG.md`: 하드웨어, 네트워크, DB, Vector DB, 최근 수정 이력
4. `emergency_protocol_v2.md`: 응급 상황 AI 행동 지침, Red Flag Protocol
5. `M_MEDIC_v2\HANDOFF.md`: Jetson/RPi 배포, 센서, PyQt GUI, 남은 작업
6. `frontend_integration\EMERGENCY_REVIEW.md`: 응급처치 UI/프로토콜 버그와 개선 우선순위

## 3. 폴더별 기능 및 최신 업데이트

| 폴더 | 기능 요약 | Markdown 수 | 최신 업데이트 | 최신 기준 파일 |
|---|---:|---:|---:|---|
| `.` | 루트 프로젝트 기준 문서, 전체 시스템 인수인계, DB 명세, 응급 AI 프로토콜, 프로젝트 맵 | 7 | 2026-05-12 09:20:19 +09:00 | `emergency_protocol_v2.md` |
| `frontend_integration` | React/Vite 웹 대시보드, 응급처치 UI 검토, 프론트엔드 인수인계, AI 시스템 상태 문서 | 5 | 2026-05-11 14:32:35 +09:00 | `frontend_integration\HANDOVER_AI.md` |
| `hancom_docs\documentation` | 한컴 제출/문서화용 프로젝트 가이드, 테이블 정의서, 테이블 명세서 복제본 | 3 | 2026-04-17 10:29:00 +09:00 | `hancom_docs\documentation\PROJECT_GUIDE.md` |
| `M_MEDIC_v2` | v2 핵심 구현 디렉터리, 실행 순서, 배포/센서/GUI 핸드오프 | 2 | 2026-05-11 09:51:28 +09:00 | `M_MEDIC_v2\HANDOFF.md` |
| `M_MEDIC_v2\01_data` | 데이터 폴더 구조, wound classification 클래스 정의, 데이터셋 출처 | 1 | 2026-04-17 10:29:00 +09:00 | `M_MEDIC_v2\01_data\README.md` |
| `M_MEDIC_v2\01_data\deprecated` | 현재 사용하지 않는 데이터와 제외된 wound class 정리 | 1 | 2026-04-17 10:29:00 +09:00 | `M_MEDIC_v2\01_data\deprecated\README.md` |
| `M_MEDIC_v2\04_integrated_system` | 통합 진단 시스템 실행 결과 보고, AI 판독 성능, 법적 근거, 팀 공유 기술 메모 | 1 | 2026-04-23 17:39:45 +09:00 | `M_MEDIC_v2\04_integrated_system\report_20260423_084007_REPORT.md` |
| `M_MEDIC_v2\05_presentation` | 발표용 분석 인사이트, Kaggle 추가 데이터 요구사항, 모델 한계와 개선 로드맵 | 2 | 2026-04-17 10:29:01 +09:00 | `M_MEDIC_v2\05_presentation\KAGGLE_REQUIREMENTS.md` |
| `M_MEDIC_v2\db_design\analysis` | 빅데이터 분석 목표, 분석용 컬럼 사전, 파생 변수, 조인 관계, 분석 정의서 | 3 | 2026-04-22 17:53:27 +09:00 | `M_MEDIC_v2\db_design\analysis\05_빅데이터분석정의서.md` |
| `MDTS_팀공유_260423` | 팀 공유 패키지 루트, 통합 시스템 실행 방법, ML/DL 재학습 방법, 핵심 결과 | 1 | 2026-04-23 17:48:25 +09:00 | `MDTS_팀공유_260423\README.md` |
| `MDTS_팀공유_260423\04_통합시스템` | MDTS 통합 진단 앱 사용 안내, 모델 3종, OOD 판정, 리포트 저장, 트러블슈팅 | 1 | 2026-04-29 09:33:25 +09:00 | `MDTS_팀공유_260423\04_통합시스템\MDTS_통합진단앱_사용안내.md` |
| `MDTS_팀공유_260423\05_문서\분석리포트` | 팀 공유용 EDA, 학습 전략, 학습 완료, 외상 분석, 통합 시스템 보고서 | 5 | 2026-04-23 17:48:40 +09:00 | `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_05_INTEGRATION.md` |
| `my_maritime_medic` | Gemini 작업공간 지시 문서만 존재, 실제 기능 문서는 미확인 | 1 | 2026-04-23 15:09:23 +09:00 | `my_maritime_medic\GEMINI.md` |
| `reports` | 루트 분석 보고서, EDA, 학습 계획, 학습 진행, 외상 분석, 통합 시스템 설계 | 5 | 2026-04-23 17:33:21 +09:00 | `reports\ANALYSIS_REPORT_01_EDA.md` |
| `shared_maritime_medic` | React/Vite 템플릿 문서와 Gemini 작업공간 지시 문서, 공유 프론트엔드 사본 성격 | 2 | 2026-04-23 12:39:21 +09:00 | `shared_maritime_medic\GEMINI.md` |

## 4. 문서별 핵심 내용 요약

### 루트 문서

- `emergency_protocol_v2.md`: HR, SpO2, SBP, 체온 기반 Critical 판정과 ABC 우선 조치 지침을 정의한다.
- `HANDOVER_AI.md`: v2.2 기준 최신 시스템 인수인계다. Jetson Nano, Raspberry Pi, RAG, MCP Bridge, MariaDB 이중 구조, Ollama 모델 지정, CORS, 엔트리포인트를 포함한다.
- `PROJECT_STATE_LOG.md`: 2026-05-11 기준 하드웨어 IP, 계정, AI 엔진, DB, NFS 기반 ChromaDB 저장 구조, 최근 핵심 수정사항을 기록한다.
- `M_MEDIC_PROJECT_MAP.md`: 데이터셋 정제, 핵심 6종 데이터 보강, 통합 시스템 검증, 향후 과제를 정리한다.
- `PROJECT_GUIDE.md`: 프로젝트 개요, 데이터, reports, 실행 스크립트, 통합 진단기 사용법, 인사이트를 정리한다.
- `TABLE_DEFINITION.md`: WOUND_DATA 메타데이터, 해양사고 통계, 외상 조치 지침, 의료관리자 교육 과정의 컬럼 정의서다.
- `TABLE_SPECIFICATION_FINAL.md`: HAM_METADATA, ACCIDENT_HISTORY, WOUND_GUIDE 테이블 명세와 SQL 생성 스크립트를 포함한다.

### 프론트엔드 문서

- `frontend_integration\HANDOVER_AI.md`: v2.1 기준 프론트 통합 시스템 인수인계다. 루트 `HANDOVER_AI.md`가 더 최신이다.
- `frontend_integration\PROJECT_STATE_LOG.md`: 루트 `PROJECT_STATE_LOG.md`와 같은 내용의 상태 로그다.
- `frontend_integration\EMERGENCY_REVIEW.md`: 응급 UI 관련 즉시 수정 버그와 의료 프로토콜 불일치를 정리한다.
- `frontend_integration\README.md`: React + Vite 기본 템플릿 설명이다.
- `frontend_integration\GEMINI.md`: UI 수정 후 lint/build 검증을 요구하는 작업 지시가 있다.

### M_MEDIC_v2 문서

- `M_MEDIC_v2\HANDOFF.md`: 센서 연동, 선원관리 화면, 모니터링 화면, Jetson/RPi 배포 방법, MAX30100 이슈, 남은 작업을 기록한다.
- `M_MEDIC_v2\README.md`: ML 데이터 생성, ML 학습, 딥러닝 학습, 평가, 발표 차트, 통합 시스템 데모 실행 순서를 제공한다.
- `M_MEDIC_v2\01_data\README.md`: 데이터 구조와 wound classification 클래스 정의를 제공한다.
- `M_MEDIC_v2\01_data\deprecated\README.md`: 사용하지 않는 데이터와 현재 사용 중인 데이터 기준을 구분한다.
- `M_MEDIC_v2\04_integrated_system\report_20260423_084007_REPORT.md`: 통합 진단 결과, AI 성능, 의학적 조치, 법적 근거를 팀 공유용으로 정리한다.
- `M_MEDIC_v2\05_presentation\ANALYSIS_INSIGHTS.md`: ML, 딥러닝, 외상 분류 인사이트와 현재 한계를 발표 관점으로 정리한다.
- `M_MEDIC_v2\05_presentation\KAGGLE_REQUIREMENTS.md`: 외상 데이터셋, 흑색종 데이터셋, 해양사고 데이터셋, 도메인 적응 데이터셋의 필요성을 정리한다.
- `M_MEDIC_v2\db_design\analysis\01_분석목표서.md`: 위험 등급 예측, 바이탈 임계값, 승조원 특성, 처치 시간, 동기화 장애 분석 목표를 정의한다.
- `M_MEDIC_v2\db_design\analysis\02_분석용_컬럼_사전.md`: `tb_crew`, `tb_vital`, `tb_analysis`, `tb_firstaid`, `tb_logs` 컬럼과 파생 변수를 정의한다.
- `M_MEDIC_v2\db_design\analysis\05_빅데이터분석정의서.md`: Wound Image Dataset 구성, 전처리, 모델링 전략을 정의한다.

### 팀 공유 및 보고서 문서

- `MDTS_팀공유_260423\README.md`: 팀 공유 패키지 구성, 통합 시스템 실행, ML/DL 재학습, 핵심 결과를 정리한다.
- `MDTS_팀공유_260423\04_통합시스템\MDTS_통합진단앱_사용안내.md`: 앱 실행, 화면 구성, 모델 3종, OOD 판정, 자동 리포트, 필수 파일/패키지, 트러블슈팅을 정리한다.
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_01_EDA.md`: 팀 공유용 데이터 수집과 EDA 결과다.
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_02_TRAINING_PLAN.md`: 외상 분류 DL과 해양사고 예측 ML 학습 전략이다.
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_03_TRAINING_STATUS.md`: 학습 완료 보고와 성능 결과다.
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_04_WOUND_ANALYSIS.md`: 해양사고와 외상 상관관계, 데이터 증강, 시스템 설계다.
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_05_INTEGRATION.md`: 외상 자동 식별, 위험등급, 응급처치 매뉴얼, 법적 근거, JSON 리포트 저장을 정리한다.
- `reports\ANALYSIS_REPORT_01_EDA.md`: 루트 보고서 기준 최신 EDA 결과다.
- `reports\ANALYSIS_REPORT_02_TRAINING_PLAN.md`: 초기 피부 질환 및 외상 분류 학습 전략이다.
- `reports\ANALYSIS_REPORT_03_TRAINING_STATUS.md`: WOUND_DATA 학습 진행 상태다.
- `reports\ANALYSIS_REPORT_04_WOUND_ANALYSIS.md`: 해양사고 기반 외상 패턴 분석과 시스템 설계다.
- `reports\ANALYSIS_REPORT_05_INTEGRATION.md`: 초기 통합 진단 시스템 설계 및 구현 결과다.

## 5. 현재 시스템 상태

### 하드웨어 및 네트워크

| 장치 | 내부 IP | 외부/Gateway IP | 역할 |
|---|---:|---:|---|
| Jetson Nano | `192.168.10.2` | `192.168.219.110` | AI 추론, FastAPI, Vite Dashboard, PyQt5 GUI |
| Raspberry Pi | `192.168.10.1` | `192.168.219.64` | MariaDB, Flask Sensor Server, USB Storage, NFS |

### AI 및 데이터 계층

- LLM: Ollama `llama3.2:1b`, API 요청 시 `"model": "llama3.2:1b"` 필수
- Vision: MobileNetV3 Large 기반 wound classification
- Backend: FastAPI `m_medic_server.py`, port `8000`
- Sensor: Raspberry Pi Flask server, port `5000`
- Web Dashboard: Vite/React, port `5173` 또는 `5174`
- Vector DB: Raspberry Pi USB 저장소를 Jetson Nano의 `~/remote_vector_db`로 NFS mount
- Relational DB: MariaDB `MDTS`, 주요 환자 이력 테이블 `tb_patient_history`

## 6. 응급 의료 AI 판단 기준

`emergency_protocol_v2.md`를 따른다.

- HR `0` 또는 `40` 미만: 심정지 또는 심각한 서맥으로 보고 CPR/AED 준비 지시
- HR `140` 이상: 심각한 빈맥으로 보고 절대 안정 및 산소 공급
- SpO2 `90%` 미만: 저산소증으로 보고 기도 확보 및 산소 마스크
- SBP `90` 미만: 저혈량 쇼크 의심, 다리 거상 및 수액 확보
- 체온 `35도` 미만: 저체온증, 가온 조치
- 체온 `40도` 이상: 열사병 또는 중증 감염, 냉각 조치
- 자창 후 혈압 하락 등 시간 변화가 있으면 진행성 쇼크로 판단하고 지혈대 재점검과 쇼크 포지션을 우선 지시

## 7. 알려진 위험 항목 및 우선 작업

### 즉시 수정 우선순위

- `frontend_integration\EMERGENCY_REVIEW.md` 기준 화상 냉각 타이머가 프로토콜 전환 시 초기화되지 않는다.
- 골든타임 타이머가 정적 텍스트로 하드코딩되어 있다.
- CPR 압박 속도가 `Emergency.jsx` 110 bpm, `AnalysisEmergency.jsx` 120 bpm으로 불일치한다.
- 화상 냉각 시간이 `Emergency.jsx` 20분, `AnalysisEmergency.jsx` 15분으로 불일치한다.
- 트리아지 문항 중 언어 반응 있음이 골절/탈구로 연결되는 매핑 오류가 있다.

### 단기 개선 항목

- 환자 알레르기 경고를 응급처치 화면에 표시한다.
- 응급 처치 세션 로그를 `localStorage` 또는 서버 동기화로 지속 저장한다.
- AI 후속 지침을 고정 텍스트가 아니라 `activeAction`과 수행 단계 기반으로 생성한다.
- 완료한 단계의 취소 토글을 추가한다.
- `patient` prop 기반 실측 바이탈을 `AnalysisEmergency.jsx`에 연동한다.

### 중장기 개선 항목

- Obsidian MCP를 RAG 파이프라인과 연결한다.
- MAX30100 IR threshold 불안정 문제를 보정한다.
- `tb_patient_history` 기반 Temporal Graph를 대시보드에 추가한다.
- 프로토콜 데이터와 바이탈 임계값을 공통 유틸로 중앙화한다.
- 해양 특수 프로토콜을 추가한다. 예: 아나필락시스, 열사병, 중독, 안구 화학손상, 잠수병, 전기 감전

## 8. 데이터 및 DB 기준

주요 분석 테이블은 다음 흐름을 기준으로 한다.

- `tb_crew`: 승조원 정보
- `tb_vital`: 생체 신호 데이터
- `tb_analysis`: AI 분석 결과
- `tb_firstaid`: 응급 처치 기록
- `tb_logs`: 육상 서버 동기화 로그
- `tb_patient_history`: 시간 축 기반 환자 이력과 바이탈 트렌드

초기 명세 문서의 핵심 테이블은 다음과 같다.

- `HAM_METADATA`: 피부 병변 이미지 분석 메타데이터
- `ACCIDENT_HISTORY`: 해양사고 이력 통계
- `WOUND_GUIDE`: 외상 조치 지침 DB
- `TRAINING_INFO`: 의료관리자 교육 과정

## 9. 작업 시 기준

- 이 폴더에서 작업할 때는 이 문서를 프로젝트 맵으로 우선 사용한다.
- 최신 시스템 상태는 루트 `HANDOVER_AI.md`와 `PROJECT_STATE_LOG.md`를 기준으로 한다.
- `frontend_integration\HANDOVER_AI.md`는 v2.1이고 루트 `HANDOVER_AI.md`는 v2.2이므로 충돌 시 루트 문서를 우선한다.
- 응급 판단 로직은 `emergency_protocol_v2.md`를 우선한다.
- 의료 관련 수치, 프로토콜, 약물/처치 권고는 추측으로 확정하지 않고 근거 문서와 코드 구현을 분리한다.
- UI 변경 시 `frontend_integration\GEMINI.md`는 lint/build 검증을 요구하지만, 실제 검증 실행은 사용자의 명시 요청 또는 승인 후 수행한다.
- 기존 문서 중 `PROJECT_GUIDE.md`, `TABLE_DEFINITION.md`, `TABLE_SPECIFICATION_FINAL.md`는 루트와 `hancom_docs\documentation`에 중복 존재한다.
- `my_maritime_medic`, `shared_maritime_medic`는 현재 Markdown 기준으로는 작업공간 지시와 React/Vite 템플릿 성격이 강하며 핵심 구현 기준 문서는 아니다.

## 10. Markdown 검토 목록

- `emergency_protocol_v2.md`
- `HANDOVER_AI.md`
- `M_MEDIC_PROJECT_MAP.md`
- `PROJECT_GUIDE.md`
- `PROJECT_STATE_LOG.md`
- `TABLE_DEFINITION.md`
- `TABLE_SPECIFICATION_FINAL.md`
- `frontend_integration\EMERGENCY_REVIEW.md`
- `frontend_integration\GEMINI.md`
- `frontend_integration\HANDOVER_AI.md`
- `frontend_integration\PROJECT_STATE_LOG.md`
- `frontend_integration\README.md`
- `hancom_docs\documentation\PROJECT_GUIDE.md`
- `hancom_docs\documentation\TABLE_DEFINITION.md`
- `hancom_docs\documentation\TABLE_SPECIFICATION_FINAL.md`
- `MDTS_팀공유_260423\README.md`
- `MDTS_팀공유_260423\04_통합시스템\MDTS_통합진단앱_사용안내.md`
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_01_EDA.md`
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_02_TRAINING_PLAN.md`
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_03_TRAINING_STATUS.md`
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_04_WOUND_ANALYSIS.md`
- `MDTS_팀공유_260423\05_문서\분석리포트\ANALYSIS_REPORT_05_INTEGRATION.md`
- `my_maritime_medic\GEMINI.md`
- `M_MEDIC_v2\HANDOFF.md`
- `M_MEDIC_v2\README.md`
- `M_MEDIC_v2\01_data\README.md`
- `M_MEDIC_v2\01_data\deprecated\README.md`
- `M_MEDIC_v2\04_integrated_system\report_20260423_084007_REPORT.md`
- `M_MEDIC_v2\05_presentation\ANALYSIS_INSIGHTS.md`
- `M_MEDIC_v2\05_presentation\KAGGLE_REQUIREMENTS.md`
- `M_MEDIC_v2\db_design\analysis\01_분석목표서.md`
- `M_MEDIC_v2\db_design\analysis\02_분석용_컬럼_사전.md`
- `M_MEDIC_v2\db_design\analysis\05_빅데이터분석정의서.md`
- `reports\ANALYSIS_REPORT_01_EDA.md`
- `reports\ANALYSIS_REPORT_02_TRAINING_PLAN.md`
- `reports\ANALYSIS_REPORT_03_TRAINING_STATUS.md`
- `reports\ANALYSIS_REPORT_04_WOUND_ANALYSIS.md`
- `reports\ANALYSIS_REPORT_05_INTEGRATION.md`
- `shared_maritime_medic\GEMINI.md`
- `shared_maritime_medic\README.md`
