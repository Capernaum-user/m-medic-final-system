import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

# 1. 인증 설정
os.environ['KAGGLE_API_TOKEN'] = 'KGAT_c4c685ec6f65ce80d482645486eb8532'

api = KaggleApi()
api.authenticate()

def robust_download_and_extract(dataset, path):
    print(f"[{dataset}] 다운로드 시작...")
    os.makedirs(path, exist_ok=True)
    
    # zip 파일만 먼저 다운로드
    api.dataset_download_files(dataset, path=path)
    
    # 다운로드된 파일 찾기
    zip_files = [f for f in os.listdir(path) if f.endswith('.zip')]
    if not zip_files:
        print(f"[{dataset}] zip 파일을 찾을 수 없습니다.")
        return

    zip_path = os.path.join(path, zip_files[0])
    print(f"[{dataset}] 압축 해제 중: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(path)
    
    # 사용 완료한 zip 파일 삭제
    os.remove(zip_path)
    print(f"[{dataset}] 완료!")

# 실행
robust_download_and_extract("kmader/skin-cancer-mnist-WOUND_DATA", r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\WOUND_DATA")
robust_download_and_extract("vuppalaadithyasairam/wound-dataset", r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\Wound_Image_Dataset")

print("모든 작업이 성공적으로 마무리되었습니다.")
