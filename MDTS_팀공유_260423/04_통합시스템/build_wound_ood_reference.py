"""
변경 요약:
- MobileNetV3 Large 학습 모델의 feature centroid를 클래스별로 계산하는 OOD 기준 생성 스크립트 추가
- 생성 결과는 wound_ood_reference.json으로 저장되며, 테스트 페이지에서 확인불가 이미지 판정에 사용

실행:
    python 04_통합시스템/build_wound_ood_reference.py

필요 패키지:
    torch, torchvision, Pillow
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "01_데이터셋" / "DL_외상이미지_4212장"
MODEL_PATH = ROOT_DIR / "03_딥러닝" / "결과물" / "mobilenet_v3_wound_best.pth"
CLASS_MAPPING_PATH = ROOT_DIR / "03_딥러닝" / "결과물" / "wound_class_mapping.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "wound_ood_reference.json"

SAMPLES_PER_CLASS = 120
RANDOM_SEED = 42
SIMILARITY_THRESHOLD = 0.50


def load_class_names(mapping_path: Path) -> list[str]:
    """클래스 매핑 JSON을 숫자 키 순서로 읽는다."""
    raw_data = json.loads(mapping_path.read_text(encoding="utf-8"))
    indexed = sorted(((int(key), str(value)) for key, value in raw_data.items()), key=lambda item: item[0])
    return [name for _, name in indexed]


def build_model(class_count: int, model_path: Path, device: torch.device) -> nn.Module:
    """저장된 MobileNetV3 Large 모델을 로드한다."""
    if not model_path.exists():
        raise FileNotFoundError(f"모델 파일이 없습니다: {model_path}")

    model = models.mobilenet_v3_large(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, class_count)
    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def build_transform() -> transforms.Compose:
    """학습 검증 파이프라인과 동일한 전처리를 반환한다."""
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


def extract_embedding(model: nn.Module, image: Image.Image, transform: transforms.Compose, device: torch.device) -> torch.Tensor:
    """MobileNetV3 classifier 직전 feature embedding을 추출한다."""
    tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    # O(D): D차원 feature를 L2 정규화해 cosine similarity 기준으로 비교
    with torch.no_grad():
        features = model.features(tensor)
        pooled = model.avgpool(features).flatten(1)
        normalized = torch.nn.functional.normalize(pooled, dim=1)
    return normalized.squeeze(0).cpu()


def collect_class_files(class_dir: Path, sample_count: int, rng: random.Random) -> list[Path]:
    """클래스 폴더에서 기준 생성용 이미지를 안정적으로 샘플링한다."""
    files = sorted(
        path
        for path in class_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    )
    if not files:
        raise FileNotFoundError(f"이미지 파일이 없습니다: {class_dir}")
    if len(files) <= sample_count:
        return files
    return rng.sample(files, sample_count)


def build_reference() -> dict[str, Any]:
    """클래스별 centroid와 분포 요약을 생성한다."""
    rng = random.Random(RANDOM_SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    class_names = load_class_names(CLASS_MAPPING_PATH)
    model = build_model(len(class_names), MODEL_PATH, device)
    transform = build_transform()

    centroids: dict[str, list[float]] = {}
    similarity_summary: dict[str, dict[str, float | int]] = {}

    for class_name in class_names:
        class_dir = DATA_DIR / class_name
        image_paths = collect_class_files(class_dir, SAMPLES_PER_CLASS, rng)
        embeddings = []
        for image_path in image_paths:
            with Image.open(image_path) as image:
                embeddings.append(extract_embedding(model, image, transform, device))

        stacked = torch.stack(embeddings)
        centroid = torch.nn.functional.normalize(stacked.mean(dim=0), dim=0)
        similarities = torch.mv(stacked, centroid).tolist()
        sorted_similarities = sorted(float(value) for value in similarities)
        centroids[class_name] = [round(float(value), 8) for value in centroid.tolist()]
        similarity_summary[class_name] = {
            "samples": len(image_paths),
            "min": round(sorted_similarities[0], 6),
            "p05": round(sorted_similarities[int(len(sorted_similarities) * 0.05)], 6),
            "median": round(sorted_similarities[len(sorted_similarities) // 2], 6),
            "max": round(sorted_similarities[-1], 6),
        }
        print(
            f"{class_name}: samples={len(image_paths)}, "
            f"min={similarity_summary[class_name]['min']}, "
            f"p05={similarity_summary[class_name]['p05']}, "
            f"median={similarity_summary[class_name]['median']}"
        )

    return {
        "version": 1,
        "model": "MobileNetV3 Large",
        "model_path": str(MODEL_PATH),
        "data_dir": str(DATA_DIR),
        "classes": class_names,
        "samples_per_class": SAMPLES_PER_CLASS,
        "random_seed": RANDOM_SEED,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "centroids": centroids,
        "similarity_summary": similarity_summary,
    }


def main() -> None:
    """OOD reference JSON을 저장한다."""
    reference = build_reference()
    OUTPUT_PATH.write_text(json.dumps(reference, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
