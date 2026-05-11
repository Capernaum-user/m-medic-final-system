@echo off
echo [데이터 전체 다운로드 스크립트]
echo Kaggle API 인증을 위해 사용자 홈 디렉토리(.kaggle)에 kaggle.json 파일이 필요합니다.
pip install kaggle
kaggle datasets download -d kmader/skin-cancer-mnist-WOUND_DATA -p "%~dp0WOUND_DATA" --unzip
kaggle datasets download -d vuppalaadithyasairam/wound-dataset -p "%~dp0Wound_Image_Dataset" --unzip
echo 다운로드가 완료되었습니다.
pause
