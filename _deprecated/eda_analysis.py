import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. 경로 설정
BASE_DIR = r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data"
HAM_METADATA = os.path.join(BASE_DIR, "WOUND_DATA", "WOUND_DATA_metadata.csv")
ACCIDENT_STATS = os.path.join(BASE_DIR, "Marine_Accidents", "marine_accidents_sample.csv")
REPORT_DIR = os.path.join(r"D:\GeminiUniverse\vscode-workspace\maritime-medic", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# 한글 폰트 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def analyze_WOUND_DATA():
    print("--- WOUND_DATA 메타데이터 분석 시작 ---")
    df = pd.read_csv(HAM_METADATA)
    
    # 질병 코드 매핑 (이해하기 쉽게 변환)
    dx_map = {
        'akiec': '광선각화증(암전단계)',
        'bcc': '기저세포암(피부암)',
        'bkl': '양성각화증',
        'df': '피부섬유종',
        'mel': '흑색종(악성피부암)',
        'nv': '멜라닌세포모반(점)',
        'vasc': '혈관병변'
    }
    df['질병명'] = df['dx'].map(dx_map)

    # 1. 질병별 분포 시각화
    plt.figure(figsize=(12, 6))
    sns.countplot(data=df, x='질병명', order=df['질병명'].value_counts().index, palette='viridis')
    plt.title('WOUND_DATA 피부 질환별 데이터 분포')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, "skin_disease_distribution.png"))
    plt.close()

    # 2. 나이대별 분포
    plt.figure(figsize=(10, 5))
    sns.histplot(df['age'].dropna(), bins=20, kde=True, color='skyblue')
    plt.title('피부 질환 환자 연령대 분포')
    plt.xlabel('나이')
    plt.ylabel('빈도')
    plt.savefig(os.path.join(REPORT_DIR, "age_distribution.png"))
    plt.close()

    # 3. 성별 및 위치 분석 요약
    print(df[['질병명', 'sex', 'localization']].describe(include='all'))
    return df

def analyze_accidents():
    print("\n--- 해양사고 통계 분석 시작 ---")
    df = pd.read_csv(ACCIDENT_STATS)
    
    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x='사고유형', hue='선박종류', palette='magma')
    plt.title('해양사고 유형별 선박 분포')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, "marine_accident_analysis.png"))
    plt.close()
    
    print(df.head())

if __name__ == "__main__":
    ham_df = analyze_WOUND_DATA()
    analyze_accidents()
    print(f"\n분석 보고서(이미지)가 {REPORT_DIR} 폴더에 저장되었습니다.")
