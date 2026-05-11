import os
import zipfile

# 1. 인증 설정
os.environ['KAGGLE_API_TOKEN'] = 'KGAT_c4c685ec6f65ce80d482645486eb8532'

try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    print("Kaggle 라이브러리가 설치되지 않았습니다. 설치를 시도합니다.")
    os.system('pip install kaggle')
    from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

def download_and_extract(dataset, path):
    print(f"다운로드 중: {dataset} -> {path}")
    os.makedirs(path, exist_ok=True)
    # zip 파일로 다운로드
    api.dataset_download_files(dataset, path=path, unzip=True)
    print(f"완료: {dataset}")

# 2. 데이터셋 목록 및 경로
datasets = {
    "kmader/skin-cancer-mnist-WOUND_DATA": r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\WOUND_DATA",
    "vuppalaadithyasairam/wound-dataset": r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\Wound_Image_Dataset"
}

# 3. 실행
for ds, target_path in datasets.items():
    try:
        download_and_extract(ds, target_path)
    except Exception as e:
        print(f"에러 발생 ({ds}): {e}")

print("모든 데이터 다운로드 및 압축 해제가 완료되었습니다.")
