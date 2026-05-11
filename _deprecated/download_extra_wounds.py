import os
import kagglehub
import shutil

def download_and_move():
    # 1. Kaggle에서 데이터셋 다운로드
    print("Kaggle에서 데이터셋 다운로드 중...")
    
    # yasinpratomo/wound-dataset
    path1 = kagglehub.dataset_download("yasinpratomo/wound-dataset")
    print(f"Dataset 1 downloaded to: {path1}")
    
    # gauravsharma99/wound-dataset (대체 후보)
    try:
        path2 = kagglehub.dataset_download("gauravsharma99/wound-dataset")
        print(f"Dataset 2 downloaded to: {path2}")
    except:
        print("Dataset 2 다운로드 실패. 다른 데이터셋 탐색.")
        path2 = None

    target_base = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification"
    
    # 2. 다운로드된 파일들을 타겟 구조로 복사 (분류 로직은 폴더명 기반)
    # 실제 수동 분류가 필요할 수 있으나, 일단 다운로드 폴더 구조를 확인하여 최대한 자동화
    print("다운로드 완료. 파일 구조 확인 및 통합이 필요합니다.")

if __name__ == "__main__":
    download_and_move()
