"""
[M-Medic ML Step 1] 해양사고 학습용 데이터 생성기
------------------------------------------------------
목적:
  - 실제 marine_accidents_sample.csv는 4행(시연용 샘플)에 불과
  - 실제 패턴(한국 해양안전심판원 통계 기반)을 반영한 1,500건의 합성 데이터 생성
  - 생성된 데이터는 ML 학습/평가에 사용

출력:
  - 01_data/processed/marine_accidents_augmented.csv
  - 01_data/processed/data_profile_report.txt
"""

import pandas as pd
import numpy as np
import os

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # M_MEDIC_v2/
RAW_DIR    = os.path.join(BASE_DIR, "01_data", "raw")
PROC_DIR   = os.path.join(BASE_DIR, "01_data", "processed")
os.makedirs(RAW_DIR,  exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

# ─── 도메인 지식 기반 확률 분포 정의 ─────────────────────────────────────────
# 한국 해양안전심판원 2019-2024 통계 패턴 반영
SHIP_TYPES    = ['어선', '화물선', '여객선', '유조선', '예인선', '어업지도선']
SHIP_WEIGHTS  = [0.48, 0.22, 0.10, 0.06, 0.08, 0.06]   # 어선 압도적 비중

ACC_TYPES     = ['충돌', '좌초', '화재', '침몰', '기관손상', '인명사고']
ACC_WEIGHTS   = [0.30, 0.18, 0.15, 0.12, 0.17, 0.08]

SEA_AREAS     = ['남해', '서해', '동해', '제주', '원양']
SEA_WEIGHTS   = [0.35, 0.28, 0.22, 0.10, 0.05]

CAUSES        = ['운항과실', '기계결함', '기상악화', '적재불량', '정비불량', '음주운항']
CAUSE_WEIGHTS = [0.38, 0.22, 0.18, 0.10, 0.08, 0.04]

# ─── 사상자 수 결정 로직 (현실적 도메인 규칙 반영) ────────────────────────────
CASUALTY_RISK = {
    # (사고유형, 선박종류) → 사상자 발생 확률
    ('화재',   '어선')  : 0.65,
    ('화재',   '여객선'): 0.70,
    ('침몰',   '어선')  : 0.75,
    ('침몰',   '여객선'): 0.80,
    ('인명사고','어선') : 0.90,
    ('충돌',   '어선')  : 0.35,
    ('기관손상','어선') : 0.10,
}

def get_casualties(acc_type, ship_type, rng):
    prob = CASUALTY_RISK.get((acc_type, ship_type), 0.15)
    if rng.random() < prob:
        # 사상자 발생 시: 1~5명 (포아송 분포)
        return int(rng.poisson(1.5)) + 1
    return 0

# ─── 부상 유형 매핑 (사고유형 → 주요 외상) ────────────────────────────────────
WOUND_MAP = {
    '화재':    '화상(Burns)',
    '충돌':    '열상(Lacerations)',
    '좌초':    '골절/타박상(Fracture)',
    '침몰':    '저체온증/익수(Hypothermia)',
    '기관손상':'화상(Burns)',
    '인명사고':'복합외상(Multiple Trauma)',
}

# ─── 데이터 생성 ─────────────────────────────────────────────────────────────
def generate_dataset(n_records: int = 1500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    years     = rng.integers(2019, 2025, size=n_records)
    ships     = rng.choice(SHIP_TYPES,  size=n_records, p=SHIP_WEIGHTS)
    acc_types = rng.choice(ACC_TYPES,   size=n_records, p=ACC_WEIGHTS)
    sea_areas = rng.choice(SEA_AREAS,   size=n_records, p=SEA_WEIGHTS)
    causes    = rng.choice(CAUSES,      size=n_records, p=CAUSE_WEIGHTS)
    casualties = np.array([
        get_casualties(a, s, rng)
        for a, s in zip(acc_types, ships)
    ])

    df = pd.DataFrame({
        '연도':       years,
        '사고유형':   acc_types,
        '선박종류':   ships,
        '사고원인':   causes,
        '발생해역':   sea_areas,
        '사상자수':   casualties,
        '사상자발생': (casualties > 0).astype(int),       # 이진 분류 타깃
        '위험등급':   pd.cut(                               # 다중 분류 타깃
            casualties,
            bins=[-1, 0, 1, 3, 100],
            labels=['GREEN', 'YELLOW', 'ORANGE', 'RED']
        ),
        '주요외상':   [WOUND_MAP.get(a, '기타') for a in acc_types],
    })

    # 기존 샘플 CSV도 병합 (호환성)
    raw_csv = os.path.join(
        BASE_DIR, "..", "data", "Marine_Accidents", "marine_accidents_sample.csv"
    )
    if os.path.exists(raw_csv):
        orig = pd.read_csv(raw_csv)
        orig.columns = ['연도','사고유형','선박종류','사고원인','발생해역','사상자수']
        orig['사상자발생'] = (orig['사상자수'] > 0).astype(int)
        orig['위험등급'] = pd.cut(
            orig['사상자수'], bins=[-1,0,1,3,100],
            labels=['GREEN','YELLOW','ORANGE','RED']
        )
        orig['주요외상'] = orig['사고유형'].map(WOUND_MAP).fillna('기타')
        df = pd.concat([df, orig], ignore_index=True)

    return df


def create_profile_report(df: pd.DataFrame) -> str:
    lines = [
        "=" * 60,
        "해양사고 데이터 프로파일 리포트",
        "=" * 60,
        f"\n총 레코드 수: {len(df):,}건",
        f"연도 범위: {df['연도'].min()} ~ {df['연도'].max()}",
        f"\n사상자 발생 비율: {df['사상자발생'].mean():.1%}",
        f"평균 사상자 수: {df['사상자수'].mean():.2f}명\n",
        "─ 사고유형 분포 ─",
        df['사고유형'].value_counts().to_string(),
        "\n─ 선박종류 분포 ─",
        df['선박종류'].value_counts().to_string(),
        "\n─ 위험등급 분포 ─",
        df['위험등급'].value_counts().to_string(),
        "\n─ 사고원인 × 사상자발생 교차표 ─",
        pd.crosstab(df['사고원인'], df['사상자발생']).to_string(),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print("[1/3] 데이터 생성 중...")
    df = generate_dataset(n_records=1500, seed=42)

    out_csv = os.path.join(PROC_DIR, "marine_accidents_augmented.csv")
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"  -> 저장 완료: {out_csv}  ({len(df):,}건)")

    print("[2/3] 프로파일 리포트 생성 중...")
    report = create_profile_report(df)
    report_path = os.path.join(PROC_DIR, "data_profile_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  -> 저장 완료: {report_path}")

    print("[3/3] 완료")
    print(report)
