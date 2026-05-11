# -*- coding: utf-8 -*-
"""
팀 공유 폴더 생성 스크립트
MDTS_팀공유_260423/ 에 데이터셋 + ML/DL 프로그램 + 결과물 + 문서 일괄 복사
"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic"
OUT  = os.path.join(BASE, "MDTS_팀공유_260423")

def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [복사] {os.path.basename(dst)}")

def cp_tree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = sum(len(f) for _, _, f in os.walk(dst))
    print(f"  [폴더복사] {os.path.basename(dst)}/ — {n}개 파일")

def mdir(path):
    os.makedirs(path, exist_ok=True)

print("=" * 60)
print("MDTS 팀 공유 폴더 생성 시작")
print("=" * 60)

# 기존 폴더 초기화
if os.path.exists(OUT):
    shutil.rmtree(OUT)
    print("기존 폴더 제거 후 재생성\n")

# ── 01_데이터셋 ──────────────────────────────────────────
print("\n[1/5] 데이터셋 복사 중...")

# DL 외상 이미지 4,212장
cp_tree(
    os.path.join(BASE, "M_MEDIC_v2", "01_data", "all_labeled_data"),
    os.path.join(OUT, "01_데이터셋", "DL_외상이미지_4212장")
)

# ML 해양사고 CSV
ml_data_dst = os.path.join(OUT, "01_데이터셋", "ML_해양사고데이터")
mdir(ml_data_dst)
cp(
    os.path.join(BASE, "M_MEDIC_v2", "01_data", "processed", "marine_accidents_augmented.csv"),
    os.path.join(ml_data_dst, "marine_accidents_augmented_1504건(합성학습용).csv")
)
cp(
    os.path.join(BASE, "M_MEDIC_v2", "01_data", "raw", "gicoms_marine_accidents_2014_2024.csv"),
    os.path.join(ml_data_dst, "gicoms_marine_accidents_2014_2024_48건(원본통계).csv")
)

# 세그멘테이션 5,520개
seg_src = os.path.join(BASE, "M_MEDIC_v2", "01_data", "deprecated", "trash", "wound_segmentation", "data_wound_seg")
if os.path.exists(seg_src):
    cp_tree(
        seg_src,
        os.path.join(OUT, "01_데이터셋", "Seg_세그멘테이션_5520개(이미지+마스크)")
    )
else:
    print("  [경고] 세그멘테이션 폴더를 찾을 수 없음 — 건너뜀")

# ── 02_머신러닝 ──────────────────────────────────────────
print("\n[2/5] 머신러닝 파일 복사 중...")

ml_src = os.path.join(BASE, "M_MEDIC_v2", "02_machine_learning")
ml_dst = os.path.join(OUT, "02_머신러닝")
mdir(ml_dst)

cp(os.path.join(ml_src, "01_generate_accident_data.py"), os.path.join(ml_dst, "01_generate_accident_data.py"))
cp(os.path.join(ml_src, "02_train_accident_ml.py"),      os.path.join(ml_dst, "02_train_accident_ml.py"))

ml_res_src = os.path.join(ml_src, "results")
ml_res_dst = os.path.join(ml_dst, "결과물")
mdir(ml_res_dst)
for fname in os.listdir(ml_res_src):
    cp(os.path.join(ml_res_src, fname), os.path.join(ml_res_dst, fname))

# ── 03_딥러닝 ────────────────────────────────────────────
print("\n[3/5] 딥러닝 파일 복사 중...")

dl_src = os.path.join(BASE, "M_MEDIC_v2", "03_deep_learning", "wound_detection")
dl_dst = os.path.join(OUT, "03_딥러닝")
mdir(dl_dst)

# 핵심 학습/추론 스크립트만 포함
for fname in ["02_train_mobilenet_v3.py", "03_inference_wound.py", "05_train_expert_model.py", "test_inference.py"]:
    src_f = os.path.join(dl_src, fname)
    if os.path.exists(src_f):
        cp(src_f, os.path.join(dl_dst, fname))

dl_res_src = os.path.join(dl_src, "results")
dl_res_dst = os.path.join(dl_dst, "결과물")
mdir(dl_res_dst)
for fname in os.listdir(dl_res_src):
    cp(os.path.join(dl_res_src, fname), os.path.join(dl_res_dst, fname))

# ── 04_통합시스템 ────────────────────────────────────────
print("\n[4/5] 통합 시스템 복사 중...")

sys_src = os.path.join(BASE, "M_MEDIC_v2", "04_integrated_system")
sys_dst = os.path.join(OUT, "04_통합시스템")
mdir(sys_dst)

cp(os.path.join(sys_src, "m_medic_v2.py"), os.path.join(sys_dst, "m_medic_v2.py"))

# JSON 진단 결과 샘플
json_dst = os.path.join(sys_dst, "진단결과_샘플JSON")
mdir(json_dst)
for fname in os.listdir(sys_src):
    if fname.endswith(".json"):
        cp(os.path.join(sys_src, fname), os.path.join(json_dst, fname))

# ── 05_문서 ──────────────────────────────────────────────
print("\n[5/5] 문서 복사 중...")

doc_dst = os.path.join(OUT, "05_문서")
mdir(doc_dst)

# 완성된 빅데이터분석정의서 (핵심)
cp(
    os.path.join(BASE, "M_MEDIC_v2", "db_design", "analysis", "3-3._빅데이터분석정의서_MDTS 260422.docx"),
    os.path.join(doc_dst, "3-3._빅데이터분석정의서_MDTS 260422.docx")
)
# 프로젝트 분석 가이드
cp(
    os.path.join(BASE, "M_MEDIC_v2_프로젝트분석가이드_빅데이터담당자용.docx"),
    os.path.join(doc_dst, "M_MEDIC_v2_프로젝트분석가이드_빅데이터담당자용.docx")
)
# 분석 리포트들
reports_dst = os.path.join(doc_dst, "분석리포트")
mdir(reports_dst)
reports_src = os.path.join(BASE, "reports")
for fname in os.listdir(reports_src):
    if fname.endswith(".md") or fname.endswith(".png"):
        cp(os.path.join(reports_src, fname), os.path.join(reports_dst, fname))

# 발표 차트
charts_dst = os.path.join(doc_dst, "발표차트")
mdir(charts_dst)
charts_src = os.path.join(BASE, "M_MEDIC_v2", "05_presentation", "charts")
for fname in os.listdir(charts_src):
    cp(os.path.join(charts_src, fname), os.path.join(charts_dst, fname))

# ── README 작성 ──────────────────────────────────────────
readme = """# MDTS (M-MEDIC v2) — 팀 공유 패키지
생성일: 2026-04-23

## 폴더 구성

| 폴더 | 내용 | 파일 수 |
|------|------|---------|
| 01_데이터셋/DL_외상이미지_4212장 | 6종 외상 이미지 (증강 포함) | 4,212장 |
| 01_데이터셋/ML_해양사고데이터 | 합성 1,504건 + GICOMS 원본 48건 | 2개 CSV |
| 01_데이터셋/Seg_세그멘테이션_5520개 | 이미지+마스크 페어 | 5,520개 |
| 02_머신러닝 | 학습 스크립트 + pkl 모델 + 차트 | — |
| 03_딥러닝 | 학습 스크립트 + .pth 모델 + 차트 | — |
| 04_통합시스템 | m_medic_v2.py + 진단결과 JSON | — |
| 05_문서 | 빅데이터분석정의서 + 분석가이드 + 리포트 | — |

## 실행 방법

### 통합 시스템 실행
```
cd 04_통합시스템
python m_medic_v2.py
```
필요 패키지: torch, torchvision, scikit-learn, Pillow, pandas

### ML 모델 재학습
```
cd 02_머신러닝
python 02_train_accident_ml.py
```

### DL 모델 재학습
```
cd 03_딥러닝
python 02_train_mobilenet_v3.py
```
데이터 경로: ../01_데이터셋/DL_외상이미지_4212장/

## 핵심 결과
- MobileNetV3 Large 외상 분류: **Accuracy 99.76%** (검증셋 843장)
- RandomForest 해양사고 이진분류: **F1 0.762**
- 통합 시스템 실시간 판독 신뢰도: **95.2%+**
"""
with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)
print("  [생성] README.md")

# ── 완료 통계 ─────────────────────────────────────────────
print("\n" + "=" * 60)
total_files = sum(len(files) for _, _, files in os.walk(OUT))
total_size  = sum(
    os.path.getsize(os.path.join(r, f))
    for r, _, files in os.walk(OUT)
    for f in files
)
print(f"완료: {total_files:,}개 파일 / 총 {total_size / 1024 / 1024:.1f} MB")
print(f"폴더 위치: {OUT}")
print("=" * 60)
