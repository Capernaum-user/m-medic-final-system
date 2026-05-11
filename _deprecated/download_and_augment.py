import os
import kagglehub
import shutil
import glob
from PIL import Image, ImageEnhance
import random

def augment_image(image_path, output_dir, prefix, count=10):
    """이미지 하나를 여러 방식으로 증강하여 저장"""
    try:
        with Image.open(image_path) as img:
            for i in range(count):
                # 랜덤 회전
                rotated = img.rotate(random.randint(0, 360), expand=True)
                # 랜덤 좌우 반전
                if random.choice([True, False]):
                    rotated = rotated.transpose(Image.FLIP_LEFT_RIGHT)
                # 랜덤 밝기 조절
                enhancer = ImageEnhance.Brightness(rotated)
                rotated = enhancer.enhance(random.uniform(0.7, 1.3))
                
                # 저장
                save_name = f"{prefix}_aug_{i}_{os.path.basename(image_path)}"
                rotated.convert("RGB").save(os.path.join(output_dir, save_name))
    except Exception as e:
        print(f"Error augmenting {image_path}: {e}")

def download_and_integrate():
    target_base = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\M_MEDIC_v2\01_data\raw\wound_classification"
    classes = ["Abrasions", "Bruises", "Burns", "Cut", "Laceration", "Stab_wound"]
    
    # 1. Kaggle 데이터 다운로드
    print("Kaggle 데이터 다운로드 시작...")
    datasets = ["yasinpratomo/wound-dataset"]
    
    for ds in datasets:
        path = kagglehub.dataset_download(ds)
        print(f"Downloaded {ds} to {path}")
        
        # 다운로드된 폴더 구조 탐색 및 병합
        for root, dirs, files in os.walk(path):
            folder_name = os.path.basename(root)
            # 프로젝트 클래스명과 유사한 폴더가 있으면 복사
            for cls in classes:
                if cls.lower() in folder_name.lower():
                    target_dir = os.path.join(target_base, cls)
                    os.makedirs(target_dir, exist_ok=True)
                    for f in files:
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                            shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))
    
    # 2. 부족한 데이터 증강 (특히 Stab_wound)
    print("데이터 증강 시작...")
    stab_dir = os.path.join(target_base, "Stab_wound")
    stab_files = glob.glob(os.path.join(stab_dir, "*"))
    
    if len(stab_files) < 100:
        print(f"Stab_wound 데이터가 {len(stab_files)}개로 부족합니다. 증강을 실시합니다.")
        for f in stab_files:
            if "aug" not in f: # 이미 증강된 파일 제외
                augment_image(f, stab_dir, "stab", count=15) # 15배 증강
                
    # 다른 클래스들도 최소 500장을 맞추기 위해 증강 (선택적)
    for cls in classes:
        cls_dir = os.path.join(target_base, cls)
        files = [f for f in glob.glob(os.path.join(cls_dir, "*")) if "aug" not in f]
        current_count = len(glob.glob(os.path.join(cls_dir, "*")))
        if current_count < 500:
            needed = 500 - current_count
            factor = (needed // len(files)) + 1 if len(files) > 0 else 0
            print(f"{cls}: {current_count}개 -> 500개를 향해 {factor}배 증강 중...")
            for f in files:
                augment_image(f, cls_dir, cls.lower(), count=factor)

    print("모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    download_and_integrate()
