import os
import zipfile
import shutil
from kaggle.api.kaggle_api_extended import KaggleApi

# 1. 인증 파일 복사 및 환경 변수 설정
# 제공해주신 키는 kaggle.json 형식이 아니므로 인증 파일 대신 환경 변수로 강제 세팅
os.environ['KAGGLE_USERNAME'] = "KwonTaeHyang"
os.environ['KAGGLE_KEY'] = "KGAT_c4c685ec6f65ce80d482645486eb8532"

api = KaggleApi()
api.authenticate()

def clean_and_download(dataset, path):
    print(f"[{dataset}] 처리 중...")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    
    # 다운로드 (zip 상태로 받음)
    api.dataset_download_files(dataset, path=path, quiet=False)
    
    # 압축 풀기
    for item in os.listdir(path):
        if item.endswith('.zip'):
            zip_file = os.path.join(path, item)
            print(f"[{dataset}] 압축 해제 중: {zip_file}")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(path)
            os.remove(zip_file)
            print(f"[{dataset}] 완료!")

# 2. 실행
try:
    clean_and_download("kmader/skin-cancer-mnist-WOUND_DATA", r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\WOUND_DATA")
    clean_and_download("vuppalaadithyasairam/wound-dataset", r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data\Wound_Image_Dataset")
    print("모든 데이터 수집 및 압축 해제가 완수되었습니다.")
except Exception as e:
    print(f"오류 발생: {e}")
