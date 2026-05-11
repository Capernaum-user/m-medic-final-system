import os
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

def profile_trauma_data():
    base_path = "01_data/raw/wound_classification"
    burn_extra_path = "01_data/raw/kaggle_trauma/burns_extra"
    
    report = []
    report.append("="*50)
    report.append(" M-Medic v2 Trauma Data Profiling Report")
    report.append("="*50)
    
    # 1. 외상 유형별 분포 분석
    report.append("\n[1. Wound Type Distribution]")
    classes = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    total_images = 0
    
    dist_data = []
    for cls in classes:
        count = len(os.listdir(os.path.join(base_path, cls)))
        total_images += count
        dist_data.append({"Class": cls, "Count": count})
    
    df_dist = pd.DataFrame(dist_data)
    report.append(df_dist.to_string(index=False))
    report.append(f"\nTotal Primary Images: {total_images}")

    # 2. 화상 특화 데이터 분석
    if os.path.exists(burn_extra_path):
        burn_extra_count = len([f for f in os.listdir(burn_extra_path) if f.endswith('.jpg')])
        report.append(f"\n[2. Extra Burn Data]")
        report.append(f"Additional Burn Images: {burn_extra_count}")

    # 3. 이미지 해상도 및 특성 분석 (샘플링)
    report.append("\n[3. Image Properties (Sampling)]")
    sample_images = []
    for cls in classes[:3]:
        cls_dir = os.path.join(base_path, cls)
        files = os.listdir(cls_dir)[:5]
        for f in files:
            img_path = os.path.join(cls_dir, f)
            with Image.open(img_path) as img:
                sample_images.append({
                    "Class": cls,
                    "Size": img.size,
                    "Format": img.format,
                    "Mode": img.mode
                })
    
    df_sample = pd.DataFrame(sample_images)
    report.append(df_sample.to_string(index=False))

    # 리포트 저장
    report_content = "\n".join(report)
    with open("01_data/processed/trauma_data_profile.txt", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Profiling Complete: 01_data/processed/trauma_data_profile.txt")

if __name__ == "__main__":
    profile_trauma_data()
