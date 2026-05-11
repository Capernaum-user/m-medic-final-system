import os
import urllib.request
import json
import csv

BASE_DIR = r"D:\GeminiUniverse\vscode-workspace\maritime-medic\data"

# 폴더 구조 정의
folders = {
    "WOUND_DATA": os.path.join(BASE_DIR, "WOUND_DATA"),
    "Wound": os.path.join(BASE_DIR, "Wound_Image_Dataset"),
    "Stats": os.path.join(BASE_DIR, "Marine_Accidents"),
    "Guide": os.path.join(BASE_DIR, "Medical_Guidelines")
}

for folder in folders.values():
    os.makedirs(folder, exist_ok=True)

# 1. 샘플 이미지 다운로드 (분석 및 모델 설계 테스트용)
print("샘플 데이터를 구성하고 있습니다...")
try:
    urllib.request.urlretrieve("https://upload.wikimedia.org/wikipedia/commons/4/44/Melanoma.jpg", os.path.join(folders["WOUND_DATA"], "sample_melanoma.jpg"))
    urllib.request.urlretrieve("https://upload.wikimedia.org/wikipedia/commons/3/3b/Abrasion_on_the_knee.jpg", os.path.join(folders["Wound"], "sample_abrasion.jpg"))
except Exception as e:
    print(f"샘플 이미지 다운로드 실패: {e}")

# 2. 해양사고 통계 데이터 더미/초기 파일 생성 (EDA용 구조화)
stats_file = os.path.join(folders["Stats"], "marine_accidents_sample.csv")
with open(stats_file, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["연도", "사고유형", "선박종류", "사고원인", "발생해역", "사상자수"])
    writer.writerow(["2023", "충돌", "어선", "운항과실", "남해", "2"])
    writer.writerow(["2023", "화재", "여객선", "기계결함", "서해", "0"])
    writer.writerow(["2024", "좌초", "화물선", "기상악화", "동해", "0"])
    writer.writerow(["2024", "침몰", "어선", "적재불량", "남해", "1"])

# 3. 의료관리자 가이드라인 요약 생성
guide_file = os.path.join(folders["Guide"], "Medical_Manager_Guidelines_Summary.txt")
with open(guide_file, "w", encoding="utf-8") as f:
    f.write("선원법 의료관리자 가이드라인 (요약본)\n")
    f.write("======================================\n")
    f.write("1. 적용대상: 원양구역 5,000톤 이상 일반선박, 300톤 이상 어선\n")
    f.write("2. 필수자격: 의사, 간호사 면허소지자 또는 한국해양수산연수원 의료관리자 교육 이수자\n")
    f.write("3. 주요업무: 선원 건강관리, 선내 보건위생 관리, 의료용품 및 구급약 비치 관리\n")
    f.write("4. 기록유지: 환자 발생 시 표준의료보고서 작성 및 비밀 유지 의무\n")

# 4. 전체 데이터 다운로더 스크립트(Kaggle) 생성
downloader_script = os.path.join(BASE_DIR, "download_full_datasets.bat")
with open(downloader_script, "w", encoding="utf-8") as f:
    f.write("@echo off\n")
    f.write("echo [데이터 전체 다운로드 스크립트]\n")
    f.write("echo Kaggle API 인증을 위해 사용자 홈 디렉토리(.kaggle)에 kaggle.json 파일이 필요합니다.\n")
    f.write("pip install kaggle\n")
    f.write("kaggle datasets download -d kmader/skin-cancer-mnist-WOUND_DATA -p \"%~dp0WOUND_DATA\" --unzip\n")
    f.write("kaggle datasets download -d vuppalaadithyasairam/wound-dataset -p \"%~dp0Wound_Image_Dataset\" --unzip\n")
    f.write("echo 다운로드가 완료되었습니다.\n")
    f.write("pause\n")

print("초기 데이터 셋업 및 자동화 스크립트 생성이 완료되었습니다.")
