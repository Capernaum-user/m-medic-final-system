"""
MDTS (M-MEDIC v2) 통합 진단 앱
================================
이미지 1장으로 DL/ML/종합 모델 3가지를 동시에 호출해 결과를 출력하는 단일 실행 프로그램.

기능:
  ① 이미지 업로드 → DL(MobileNetV3 Large) 외상 6종 분류 + 신뢰도/Top-3
  ② 사고 정보 입력 → ML(RandomForest) 사상자 발생 확률 예측
  ③ DL + ML 결과 결합 → 종합 위험등급 + 응급처치 매뉴얼
  ④ 신뢰도/유사도 기준 미달 시 "확인불가 이미지"로 표시 (OOD 검증)
  ⑤ JSON 진단 리포트 자동 저장

실행:
  더블클릭: MDTS_실행.bat
  CLI    : python MDTS_통합진단앱.py [--port 8009] [--no-browser]
  접속   : http://127.0.0.1:8009
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import pickle
import sys
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from sklearn.preprocessing import LabelEncoder
from torchvision import models, transforms


ROOT_DIR = Path(__file__).resolve().parents[1]
DL_MODEL_PATH = ROOT_DIR / "03_딥러닝" / "결과물" / "mobilenet_v3_wound_best.pth"
DL_CLASS_MAPPING = ROOT_DIR / "03_딥러닝" / "결과물" / "wound_class_mapping.json"
ML_MODEL_PATH = ROOT_DIR / "02_머신러닝" / "결과물" / "model_randomforest_binary.pkl"
ML_DATA_PATH = ROOT_DIR / "01_데이터셋" / "ML_해양사고데이터" / "marine_accidents_augmented_1504건(합성학습용).csv"
OOD_REFERENCE_PATH = Path(__file__).resolve().parent / "wound_ood_reference.json"
REPORT_DIR = Path(__file__).resolve().parent / "진단결과_샘플JSON"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000
LOW_CONFIDENCE_THRESHOLD = 0.70
AMBIGUOUS_MARGIN_THRESHOLD = 0.20
DEFAULT_OOD_SIMILARITY_THRESHOLD = 0.50
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8009

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

ML_FEATURE_COLS = ["연도", "사고유형", "선박종류", "사고원인", "발생해역"]
ML_CATEGORICAL_COLS = ["사고유형", "선박종류", "사고원인", "발생해역"]


@dataclass(frozen=True)
class WoundInfo:
    """상처 클래스별 표시명, 위험도, 처치 지침."""

    display_name: str
    risk: str
    risk_score: int  # LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4
    description: str
    action: str
    law_ref: str
    expected_accidents: tuple[str, ...]


WOUND_KNOWLEDGE: dict[str, WoundInfo] = {
    "Abrasions": WoundInfo(
        display_name="찰과상(Abrasions)",
        risk="LOW",
        risk_score=1,
        description="피부가 거친 표면에 마찰되어 표피만 벗겨진 얕은 상처. 출혈은 적으나 이물질·박테리아가 묻기 쉽고 따끔한 통증을 동반한다.",
        action="① 흐르는 생리식염수(또는 깨끗한 물)로 이물질 세척  ② 소독 연고 도포  ③ 통기성 거즈로 보호  ④ 24시간마다 드레싱 교체, 발적·고름 시 재평가",
        law_ref="WHO 선내의료지침 Ch.7",
        expected_accidents=("좌초", "충돌"),
    ),
    "Bruises": WoundInfo(
        display_name="타박상(Bruises)",
        risk="LOW",
        risk_score=1,
        description="외부 충격으로 피부는 찢어지지 않았으나 피하 모세혈관이 터져 멍·부종·통증이 발생한 상태. 골절·내부 출혈이 동반될 수 있다.",
        action="① 초기 48시간 냉찜질(20분 적용/20분 휴식 반복)  ② 환부 거상  ③ 48시간 이후 온찜질로 회복 촉진  ④ 통증·부종 악화 또는 변형 시 골절 의심, 부목 고정",
        law_ref="선원법 시행규칙 [별표 5의5]",
        expected_accidents=("충돌", "좌초"),
    ),
    "Burns": WoundInfo(
        display_name="화상(Burns)",
        risk="HIGH",
        risk_score=3,
        description="열·화학물질·전기·복사로 인한 피부·조직 손상. 1도(홍반), 2도(수포), 3도(괴사)로 구분되며 면적·깊이가 클수록 쇼크 위험이 커진다.",
        action="① 즉시 흐르는 찬물로 20분 이상 냉각  ② 수포 절대 터뜨리지 말고 거즈로 덮기  ③ 옷·반지 등 압박 요소 제거  ④ 2도 이상 또는 손바닥 이상 면적이면 회항·이송, 연고·기름 도포 금지",
        law_ref="선원법 시행규칙 [별표 5의5] 화상처치",
        expected_accidents=("화재", "기관손상"),
    ),
    "Cut": WoundInfo(
        display_name="절상(Cut)",
        risk="MEDIUM",
        risk_score=2,
        description="칼·유리 등 날카로운 물체에 베여 가장자리가 비교적 깨끗한 상처. 깊이에 따라 혈관·신경·힘줄 손상이 동반될 수 있다.",
        action="① 멸균 거즈로 직접 압박 지혈(5~10분 유지)  ② 지혈 후 생리식염수 세척·소독  ③ 깊이 1cm 미만은 스테리스트립으로 접합  ④ 벌어지거나 깊으면 봉합 필요, 6시간 내 처치 권고",
        law_ref="WHO 선내의료지침 Ch.7",
        expected_accidents=("충돌", "기관손상"),
    ),
    "Laceration": WoundInfo(
        display_name="열상(Laceration)",
        risk="HIGH",
        risk_score=3,
        description="둔기 충격으로 피부가 불규칙하게 찢어진 상처. 가장자리가 들쭉날쭉하고 조직 손상·오염이 심해 감염·흉터 위험이 높다.",
        action="① 강한 직접 압박으로 지혈, 동맥성 출혈은 근위부 압박  ② 다량 생리식염수로 세척하여 오염 제거  ③ 깊이 1cm 이상이면 봉합 필수  ④ 파상풍 예방 확인, 항생제 고려, 24~48시간 감염 징후 관찰",
        law_ref="선원법 시행규칙 [별표 5의5]",
        expected_accidents=("충돌", "전복"),
    ),
    "Stab_wound": WoundInfo(
        display_name="자창(Stab Wound)",
        risk="CRITICAL",
        risk_score=4,
        description="뾰족한 물체가 깊이 찔러 생긴 상처. 외부 출혈은 적어 보여도 장기·혈관·신경 손상과 내부 출혈로 쇼크에 빠질 수 있는 가장 위험한 외상.",
        action="① 박힌 물체는 절대 제거 금지(고정만 한다)  ② 주변을 거즈로 둘러 압박 지혈, 흉부면 폐쇄식 드레싱  ③ 환자 보온·하지 거상으로 쇼크 방지, 금식  ④ 즉시 회항 결정, 의료진에 무선 보고하며 최단 경로로 병원 이송",
        law_ref="선원법 시행규칙 [별표 5의5]",
        expected_accidents=("충돌", "기관손상"),
    ),
}

RISK_LABEL_TO_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 0}
RISK_SCORE_TO_LABEL = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}


# ─── 유틸 ─────────────────────────────────────────────────────────────────────

def load_class_names(mapping_path: Path) -> list[str]:
    """클래스 매핑 JSON을 숫자 키 순서로 읽는다."""
    default_classes = ["Abrasions", "Bruises", "Burns", "Cut", "Laceration", "Stab_wound"]
    if not mapping_path.exists():
        return default_classes
    try:
        raw_data = json.loads(mapping_path.read_text(encoding="utf-8"))
        indexed = sorted(((int(k), str(v)) for k, v in raw_data.items()), key=lambda x: x[0])
        names = [name for _, name in indexed]
        return names if names else default_classes
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return default_classes


def load_ood_reference(reference_path: Path, class_names: list[str], device: torch.device):
    """학습 데이터 feature centroid 기준을 로드한다."""
    if not reference_path.exists():
        return None
    try:
        raw_data = json.loads(reference_path.read_text(encoding="utf-8"))
        centroids_by_class = raw_data["centroids"]
        centroids = [centroids_by_class[name] for name in class_names]
        threshold = float(raw_data.get("similarity_threshold", DEFAULT_OOD_SIMILARITY_THRESHOLD))
        tensor = torch.tensor(centroids, dtype=torch.float32, device=device)
        tensor = torch.nn.functional.normalize(tensor, dim=1)
        return tensor, threshold
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def open_valid_image(image_bytes: bytes) -> Image.Image:
    """업로드 바이트를 PIL 이미지로 검증하고 RGB로 반환한다."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError(f"유효한 이미지 파일이 아닙니다: {exc}") from exc

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("이미지 크기가 올바르지 않습니다.")
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError(f"이미지 해상도가 너무 큽니다. 최대 {MAX_IMAGE_PIXELS:,}픽셀까지 허용합니다.")
    return image


# ─── DL 엔진: MobileNetV3 외상 분류 ──────────────────────────────────────────

class WoundClassifier:
    """MobileNetV3 Large 외상 분류 모델 + OOD 검출."""

    def __init__(self) -> None:
        self.class_names = load_class_names(DL_CLASS_MAPPING)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module | None = None
        self.ood_centroids: torch.Tensor | None = None
        self.ood_similarity_threshold = DEFAULT_OOD_SIMILARITY_THRESHOLD
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def load(self) -> None:
        if self.model is not None:
            return
        if not DL_MODEL_PATH.exists():
            raise FileNotFoundError(f"DL 모델 파일이 없습니다: {DL_MODEL_PATH}")

        model = models.mobilenet_v3_large(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, len(self.class_names))

        try:
            state_dict = torch.load(DL_MODEL_PATH, map_location=self.device, weights_only=True)
        except TypeError:
            state_dict = torch.load(DL_MODEL_PATH, map_location=self.device)

        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model

        reference = load_ood_reference(OOD_REFERENCE_PATH, self.class_names, self.device)
        if reference is not None:
            self.ood_centroids, self.ood_similarity_threshold = reference

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        self.load()
        if self.model is None:
            raise RuntimeError("DL 모델 로드 실패")

        image = open_valid_image(image_bytes)
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.features(tensor)
            pooled = self.model.avgpool(features).flatten(1)
            embedding = torch.nn.functional.normalize(pooled, dim=1)
            logits = self.model.classifier(pooled)
            probabilities = torch.softmax(logits, dim=1).squeeze(0).cpu()

        top_count = min(3, len(self.class_names))
        values, indices = torch.topk(probabilities, k=top_count)
        prediction_index = int(indices[0].item())
        prediction = self.class_names[prediction_index]
        confidence = float(values[0].item())
        top2_margin = float((values[0] - values[1]).item()) if top_count > 1 else confidence

        similarity = 1.0
        predicted_similarity = 1.0
        ood_loaded = self.ood_centroids is not None
        if self.ood_centroids is not None:
            sim_scores = torch.mv(self.ood_centroids, embedding.squeeze(0))
            similarity = float(torch.max(sim_scores).item())
            predicted_similarity = float(sim_scores[prediction_index].item())

        info = WOUND_KNOWLEDGE.get(prediction)
        top3 = []
        for value, index in zip(values.tolist(), indices.tolist()):
            cn = self.class_names[int(index)]
            cinfo = WOUND_KNOWLEDGE.get(cn)
            top3.append({
                "class_name": cn,
                "display_name": cinfo.display_name if cinfo else f"미분류({cn})",
                "confidence": float(value),
                "confidence_percent": float(value) * 100.0,
            })

        low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD
        ambiguous = top2_margin < AMBIGUOUS_MARGIN_THRESHOLD
        out_of_distribution = ood_loaded and similarity < self.ood_similarity_threshold
        is_unknown = low_confidence or ambiguous or out_of_distribution

        warning_reasons = []
        if out_of_distribution:
            warning_reasons.append(
                f"학습 데이터 feature 유사도 {similarity * 100.0:.2f}%가 기준 {self.ood_similarity_threshold * 100.0:.0f}%보다 낮습니다."
            )
        if low_confidence:
            warning_reasons.append(f"모델 confidence {confidence * 100.0:.2f}%가 기준 70%보다 낮습니다.")
        if ambiguous:
            warning_reasons.append(f"1위와 2위 후보 차이 {top2_margin * 100.0:.2f}%가 기준 20%보다 작습니다.")

        return {
            "prediction": "UNKNOWN" if is_unknown else prediction,
            "model_prediction": prediction,
            "display_name": "확인불가 이미지" if is_unknown else (info.display_name if info else f"미분류({prediction})"),
            "model_display_name": info.display_name if info else f"미분류({prediction})",
            "confidence": confidence,
            "confidence_percent": confidence * 100.0,
            "top2_margin": top2_margin,
            "top2_margin_percent": top2_margin * 100.0,
            "low_confidence": low_confidence,
            "ambiguous_prediction": ambiguous,
            "out_of_distribution": out_of_distribution,
            "is_unknown": is_unknown,
            "in_distribution_similarity": similarity,
            "in_distribution_similarity_percent": similarity * 100.0,
            "predicted_class_similarity": predicted_similarity,
            "predicted_class_similarity_percent": predicted_similarity * 100.0,
            "ood_reference_loaded": ood_loaded,
            "ood_similarity_threshold": self.ood_similarity_threshold,
            "warning_reasons": warning_reasons,
            "warning_message": " ".join(warning_reasons) if warning_reasons else "",
            "risk": "UNKNOWN" if is_unknown else (info.risk if info else "UNKNOWN"),
            "risk_score": 0 if is_unknown else (info.risk_score if info else 0),
            "action": (
                "학습된 6종 상처 이미지와 충분히 유사하지 않습니다. 상처 부위를 중심으로 더 밝고 선명하게 재촬영하거나 전문가 확인이 필요합니다."
                if is_unknown
                else (info.action if info else "전문 의료진 자문 필요.")
            ),
            "law_ref": "-" if is_unknown else (info.law_ref if info else "-"),
            "expected_accidents": list(info.expected_accidents) if info else [],
            "model_description": info.description if info else "",
            "model_action": info.action if info else "",
            "top3": top3,
            "device": str(self.device),
        }


# ─── ML 엔진: RandomForest 사상자 발생 예측 ──────────────────────────────────

class AccidentRiskPredictor:
    """RandomForest 모델 + 학습 CSV 기반 LabelEncoder 재구성."""

    def __init__(self) -> None:
        self.model = None
        self.encoders: dict[str, LabelEncoder] = {}
        self.unique_values: dict[str, list[str]] = {}
        self.year_range: tuple[int, int] = (2014, 2024)
        self.feature_importance: dict[str, float] = {}
        self.loaded = False

    def load(self) -> None:
        if self.loaded:
            return
        if not ML_MODEL_PATH.exists():
            raise FileNotFoundError(f"ML 모델 파일이 없습니다: {ML_MODEL_PATH}")
        if not ML_DATA_PATH.exists():
            raise FileNotFoundError(
                f"ML 학습 CSV가 없습니다(인코더 재구성 필요): {ML_DATA_PATH}"
            )

        with open(ML_MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)

        # CSV에서 LabelEncoder 재구성 (학습 시점과 동일 순서를 위해 LabelEncoder fit만 수행)
        rows: list[dict[str, str]] = []
        with open(ML_DATA_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        if not rows:
            raise RuntimeError("ML 학습 CSV가 비어 있습니다.")

        for col in ML_CATEGORICAL_COLS:
            values = sorted({str(r[col]) for r in rows if r.get(col)})
            le = LabelEncoder()
            le.fit(values)
            self.encoders[col] = le
            self.unique_values[col] = [str(c) for c in le.classes_]

        years = [int(r["연도"]) for r in rows if r.get("연도", "").isdigit()]
        if years:
            self.year_range = (min(years), max(years))

        if hasattr(self.model, "feature_importances_"):
            for name, imp in zip(ML_FEATURE_COLS, self.model.feature_importances_):
                self.feature_importance[name] = float(imp)

        self.loaded = True

    def encode_input(self, data: dict[str, Any]) -> tuple[np.ndarray, dict[str, str]]:
        """사용자 입력을 모델 입력 벡터로 변환."""
        if not self.loaded:
            self.load()

        normalized: dict[str, str] = {}
        encoded: list[float] = []

        try:
            year = int(data.get("연도", self.year_range[1]))
        except (TypeError, ValueError):
            year = self.year_range[1]
        encoded.append(float(year))
        normalized["연도"] = str(year)

        for col in ML_CATEGORICAL_COLS:
            raw = str(data.get(col, "")).strip()
            le = self.encoders[col]
            classes = list(le.classes_)
            if raw not in classes:
                raw = classes[0]
            encoded.append(float(le.transform([raw])[0]))
            normalized[col] = raw

        return np.array(encoded, dtype=float).reshape(1, -1), normalized

    def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self.loaded:
            self.load()
        if self.model is None:
            raise RuntimeError("ML 모델 로드 실패")

        x, normalized = self.encode_input(data)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(x)[0]
            classes = list(getattr(self.model, "classes_", [0, 1]))
            casualty_index = classes.index(1) if 1 in classes else len(classes) - 1
            casualty_prob = float(probs[casualty_index])
        else:
            casualty_prob = float(self.model.predict(x)[0])

        predicted_label = int(self.model.predict(x)[0])

        if casualty_prob >= 0.75:
            risk = "HIGH"
        elif casualty_prob >= 0.50:
            risk = "MEDIUM"
        elif casualty_prob >= 0.25:
            risk = "LOW"
        else:
            risk = "LOW"

        return {
            "input": normalized,
            "casualty_probability": casualty_prob,
            "casualty_probability_percent": casualty_prob * 100.0,
            "predicted_casualty": bool(predicted_label),
            "risk": risk,
            "risk_score": RISK_LABEL_TO_SCORE.get(risk, 0),
            "feature_importance": self.feature_importance,
            "year_range": list(self.year_range),
        }

    def options(self) -> dict[str, Any]:
        if not self.loaded:
            self.load()
        return {
            "year_range": list(self.year_range),
            "categories": {col: list(self.unique_values[col]) for col in ML_CATEGORICAL_COLS},
            "feature_importance": self.feature_importance,
        }


# ─── 종합 모델: DL + ML 결합 ─────────────────────────────────────────────────

def integrate_results(dl_result: dict[str, Any], ml_result: dict[str, Any]) -> dict[str, Any]:
    """DL의 외상 위험과 ML의 사상자 확률을 가중 결합해 최종 등급을 산출."""
    if dl_result.get("is_unknown"):
        return {
            "is_unknown": True,
            "risk": "UNKNOWN",
            "risk_score": 0.0,
            "final_score": 0.0,
            "dl_weight": 0.6,
            "ml_weight": 0.4,
            "dl_score_norm": 0.0,
            "ml_score_norm": 0.0,
            "summary": "확인불가 이미지로 판정되어 종합 진단을 보류합니다. 재촬영 후 다시 시도하십시오.",
            "action": "이미지를 더 밝고 선명하게 재촬영하거나 전문 의료진의 직접 판독을 받으십시오.",
            "law_ref": "-",
        }

    dl_score = float(dl_result.get("risk_score", 0))            # 1~4
    ml_prob = float(ml_result.get("casualty_probability", 0.0))  # 0~1

    dl_norm = dl_score / 4.0          # 0~1
    ml_norm = ml_prob                 # 0~1
    weight_dl = 0.6
    weight_ml = 0.4

    final_norm = dl_norm * weight_dl + ml_norm * weight_ml      # 0~1
    final_score = final_norm * 4.0                              # 0~4

    if final_score >= 3.5:
        final_risk = "CRITICAL"
    elif final_score >= 2.5:
        final_risk = "HIGH"
    elif final_score >= 1.5:
        final_risk = "MEDIUM"
    else:
        final_risk = "LOW"

    dl_class = dl_result.get("model_prediction", "")
    info = WOUND_KNOWLEDGE.get(dl_class)

    summary_lines = [
        f"DL 외상 분류: {dl_result.get('model_display_name', '-')} (위험도 {dl_result.get('risk', '-')})",
        f"ML 사상자 발생 확률: {ml_prob * 100.0:.2f}% (위험도 {ml_result.get('risk', '-')})",
        f"종합 위험등급: {final_risk} (가중 점수 {final_score:.2f}/4.00)",
    ]

    action_priority = {
        "CRITICAL": "즉시 회항 및 연안 병원 이송. 지혈·쇼크 방지·기도 확보 우선.",
        "HIGH": "가능한 빨리 육지 의료기관 방문. 항행 중 응급처치 + 2차 감염 방지.",
        "MEDIUM": "선내에서 1차 처치 후 24시간 내 의료진 자문 권고. 감염·통증 관찰.",
        "LOW": "현장 처치 후 경과 관찰. 악화 시 즉시 재평가.",
    }

    return {
        "is_unknown": False,
        "risk": final_risk,
        "risk_score": final_score,
        "final_score": final_score,
        "final_score_percent": final_norm * 100.0,
        "dl_weight": weight_dl,
        "ml_weight": weight_ml,
        "dl_score_norm": dl_norm,
        "ml_score_norm": ml_norm,
        "dl_risk": dl_result.get("risk"),
        "ml_risk": ml_result.get("risk"),
        "summary": " / ".join(summary_lines),
        "summary_lines": summary_lines,
        "action": action_priority.get(final_risk, "전문 의료진 자문 필요."),
        "law_ref": info.law_ref if info else "-",
        "wound_action": info.action if info else "-",
    }


# ─── HTTP 서버 ────────────────────────────────────────────────────────────────

def parse_multipart(content_type: str, body: bytes) -> tuple[bytes, str, dict[str, str]]:
    """multipart/form-data에서 image 필드와 텍스트 필드를 추출."""
    if "multipart/form-data" not in content_type:
        raise ValueError("Content-Type은 multipart/form-data여야 합니다.")

    message_bytes = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    message = BytesParser(policy=policy.default).parsebytes(message_bytes)
    if not message.is_multipart():
        raise ValueError("multipart 요청 형식이 올바르지 않습니다.")

    image_bytes = b""
    image_filename = ""
    fields: dict[str, str] = {}

    for part in message.iter_parts():
        field_name = part.get_param("name", header="content-disposition")
        if field_name == "image":
            payload = part.get_payload(decode=True) or b""
            if not payload:
                raise ValueError("업로드된 이미지가 비어 있습니다.")
            image_bytes = payload
            image_filename = part.get_filename() or "uploaded-image"
        elif field_name:
            payload = part.get_payload(decode=True) or b""
            try:
                fields[field_name] = payload.decode("utf-8")
            except UnicodeDecodeError:
                fields[field_name] = payload.decode("utf-8", errors="ignore")

    if not image_bytes:
        raise ValueError("image 필드가 없습니다.")

    return image_bytes, image_filename, fields


HTML_PAGE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MDTS 통합 진단 시스템</title>
<style>
  :root {
    color-scheme: light;
    --bg: #f4f6f8; --panel: #fff; --text: #1f2933; --muted: #667085;
    --line: #d9e1e7; --primary: #1f6feb; --primary-dark: #174ea6;
    --ok: #157347; --warning: #b45309; --danger: #b42318; --critical: #7f1d1d;
    --shadow: 0 14px 35px rgba(31,41,51,.08);
  }
  * { box-sizing: border-box; }
  body { margin:0; background: var(--bg); color: var(--text);
    font-family: "Malgun Gothic","Segoe UI",Arial,sans-serif; line-height:1.5; }
  header { border-bottom:1px solid var(--line); background:#fff; }
  .header-inner { max-width:1280px; margin:0 auto; padding:18px 22px;
    display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap; }
  h1 { margin:0; font-size:22px; }
  .subtitle { color:var(--muted); font-size:13px; }
  main { max-width:1280px; margin:0 auto; padding:24px 22px 40px;
    display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
  .full { grid-column: 1 / -1; }
  .panel { background:var(--panel); border:1px solid var(--line);
    border-radius:10px; box-shadow: var(--shadow); padding:20px; min-width:0; }
  .panel h2 { margin:0 0 14px; font-size:16px; }
  .drop-zone { position:relative; min-height:300px; border:2px dashed #a8b8c7;
    border-radius:8px; display:grid; place-items:center; padding:18px;
    background:#fbfcfd; transition:.15s; overflow:hidden; }
  .drop-zone.dragging { border-color:var(--primary); background:#eef5ff; }
  .drop-content { display:grid; gap:10px; justify-items:center; text-align:center; color:var(--muted); }
  .drop-title { color:var(--text); font-weight:700; font-size:18px; }
  .file-input { position:absolute; inset:0; opacity:0; cursor:pointer; }
  .preview { width:100%; max-height:340px; object-fit:contain; display:none; }
  .file-name { color:var(--muted); font-size:13px; margin-top:10px; overflow-wrap:anywhere; }
  .form-grid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
  .field { display:grid; gap:5px; }
  .field label { font-size:12px; color:var(--muted); }
  select, input[type=number] { width:100%; padding:8px 10px; border:1px solid var(--line);
    border-radius:6px; background:#fff; font:inherit; }
  .actions { display:flex; gap:10px; align-items:center; margin-top:14px; flex-wrap:wrap; }
  button { border:0; border-radius:6px; background:var(--primary); color:#fff;
    min-height:44px; padding:0 22px; font-weight:700; cursor:pointer; }
  button:hover { background:var(--primary-dark); }
  button:disabled { background:#9aa8b5; cursor:not-allowed; }
  .empty { min-height:240px; display:grid; place-items:center; color:var(--muted);
    text-align:center; border:1px dashed var(--line); border-radius:8px; padding:18px; }
  .result-grid { display:grid; grid-template-columns: 1fr 1fr 1fr; gap:14px; }
  @media (max-width: 1100px){ main { grid-template-columns:1fr; } .result-grid { grid-template-columns:1fr; } }
  .card { border:1px solid var(--line); border-radius:8px; padding:14px; background:#fbfcfd; min-width:0; }
  .card h3 { margin:0 0 10px; font-size:14px; color:var(--muted); letter-spacing:.5px; text-transform:uppercase; }
  .card .big { font-size:22px; font-weight:800; margin:4px 0; overflow-wrap:anywhere; }
  .risk-badge { display:inline-block; padding:4px 10px; border-radius:999px; color:#fff;
    font-size:12px; font-weight:800; background:var(--muted); letter-spacing:.5px; }
  .risk-badge.LOW { background: var(--ok); }
  .risk-badge.MEDIUM { background: var(--warning); }
  .risk-badge.HIGH { background: var(--danger); }
  .risk-badge.CRITICAL { background: var(--critical); }
  .bar { height:10px; border-radius:999px; background:#e8eef3; overflow:hidden; margin-top:8px; }
  .bar-fill { height:100%; width:0; background:var(--primary); transition: width .25s ease; }
  .row { display:flex; justify-content:space-between; gap:8px; color:var(--muted); font-size:13px; margin-top:6px; }
  .warn { display:none; border:1px solid #f2b8b5; background:#fff4f2; color:#8a1c13;
    border-radius:8px; padding:12px; margin-top:12px; font-size:14px; overflow-wrap:anywhere; }
  .top3 .candidate { display:grid; grid-template-columns: 1fr 80px; gap:8px; padding:7px 0;
    border-bottom:1px solid #edf1f4; align-items:center; font-size:13px; }
  .top3 .candidate:last-child { border-bottom:0; }
  .candidate-score { text-align:right; font-variant-numeric: tabular-nums; color:var(--muted); }
  .summary-list { margin:0; padding-left:18px; }
  .summary-list li { margin:4px 0; color:#344054; font-size:14px; }
  .error { display:none; border:1px solid #f2b8b5; background:#fff4f2; color:#8a1c13;
    border-radius:8px; padding:12px; margin-top:12px; font-size:14px; overflow-wrap:anywhere; }
  .info-line { color:var(--muted); font-size:13px; margin-top:8px; overflow-wrap:anywhere; }
  .feature-importance { display:grid; gap:6px; margin-top:10px; }
  .fi-row { display:grid; grid-template-columns: 90px 1fr 60px; gap:8px; align-items:center; font-size:12px; color:var(--muted); }
  .fi-bar { height:8px; background:#e8eef3; border-radius:999px; overflow:hidden; }
  .fi-fill { height:100%; background:#1f6feb; }
  .desc-block { margin-top:10px; padding:10px; background:#fff; border:1px solid var(--line);
    border-radius:6px; font-size:13px; color:#344054; }
  .desc-block .desc-label { color:var(--muted); font-size:11px; text-transform:uppercase;
    letter-spacing:.5px; margin-bottom:4px; }
  .ood-explainer { font-size:12px; color:var(--muted); margin-top:8px; line-height:1.5; }
  .guide-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; }
  @media (max-width: 1100px) { .guide-grid { grid-template-columns:1fr 1fr; } }
  @media (max-width: 720px)  { .guide-grid { grid-template-columns:1fr; } }
  .guide-card { border:1px solid var(--line); border-radius:8px; padding:14px; background:#fbfcfd; }
  .guide-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:8px; flex-wrap:wrap; }
  .guide-head .name { font-weight:800; font-size:15px; }
  .guide-section { margin-top:10px; }
  .guide-section .label { color:var(--muted); font-size:11px; text-transform:uppercase;
    letter-spacing:.5px; margin-bottom:4px; }
  .guide-section .body { font-size:13px; color:#344054; line-height:1.55; }
  .guide-section .body.action { white-space:pre-line; }
</style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <h1>MDTS 통합 진단 시스템</h1>
        <div class="subtitle">DL 외상 분류 + ML 사고 예측 + 종합 위험등급</div>
      </div>
      <div class="subtitle" id="modelState">모델 상태 확인 중...</div>
    </div>
  </header>
  <main>
    <section class="panel">
      <h2>1. 외상 이미지 업로드</h2>
      <div class="drop-zone" id="dropZone">
        <img class="preview" id="preview" alt="업로드 이미지 미리보기">
        <div class="drop-content" id="dropContent">
          <div class="drop-title">이미지 선택 또는 드래그</div>
          <div>JPG, PNG, BMP, WEBP / 최대 10MB</div>
        </div>
        <input class="file-input" id="imageInput" type="file" accept="image/*">
      </div>
      <div class="file-name" id="fileName">선택된 파일 없음</div>
    </section>

    <section class="panel">
      <h2>2. 사고 정보 입력 (ML 모델용)</h2>
      <div class="form-grid">
        <div class="field">
          <label for="year">연도</label>
          <input type="number" id="year" min="2000" max="2099" step="1">
        </div>
        <div class="field">
          <label for="accidentType">사고유형</label>
          <select id="accidentType"></select>
        </div>
        <div class="field">
          <label for="vesselType">선박종류</label>
          <select id="vesselType"></select>
        </div>
        <div class="field">
          <label for="cause">사고원인</label>
          <select id="cause"></select>
        </div>
        <div class="field" style="grid-column: 1 / -1;">
          <label for="region">발생해역</label>
          <select id="region"></select>
        </div>
      </div>
      <div class="actions">
        <button type="button" id="runButton" disabled>분석 실행</button>
        <span class="info-line" id="hintLine">이미지를 업로드하면 활성화됩니다.</span>
      </div>
      <div class="error" id="errorBox"></div>
    </section>

    <section class="panel full">
      <h2>3. 분석 결과</h2>
      <div class="empty" id="emptyState">이미지를 업로드하고 [분석 실행]을 누르면 DL/ML/종합 결과가 여기에 표시됩니다.</div>
      <div id="resultArea" style="display:none;">
        <div class="warn" id="warningBox"></div>
        <div class="result-grid">
          <div class="card">
            <h3>① 딥러닝 (외상 분류)</h3>
            <div class="big" id="dlName">-</div>
            <span class="risk-badge" id="dlRisk">UNKNOWN</span>
            <div class="row"><span>신뢰도</span><strong id="dlConf">0.00%</strong></div>
            <div class="bar"><div class="bar-fill" id="dlBar"></div></div>
            <div class="row"><span>학습 데이터 유사도</span><strong id="dlSim">-</strong></div>
            <div class="row"><span>1·2위 차이</span><strong id="dlMargin">-</strong></div>
            <div class="info-line" id="dlNote"></div>
            <div class="ood-explainer" id="dlOodExplainer" style="display:none;">
              ※ 신뢰도(softmax)는 6종 중 하나로 분류한 결과의 확신도이고, 학습 데이터 유사도는 입력 이미지가 학습된 외상 사진과 얼마나 비슷한지를 별도로 측정합니다. 신뢰도가 높아도 유사도가 기준 미만이면 학습 범위 밖 이미지로 보고 확인불가로 표시합니다.
            </div>
            <div class="desc-block" id="dlDescBlock" style="display:none;">
              <div class="desc-label">상처 설명</div>
              <div id="dlDesc">-</div>
            </div>
            <div class="desc-block" id="dlActionBlock" style="display:none;">
              <div class="desc-label">응급 조치</div>
              <div id="dlAction">-</div>
            </div>
            <div class="top3" id="top3List" style="margin-top:10px;"></div>
          </div>
          <div class="card">
            <h3>② 머신러닝 (해양사고 예측)</h3>
            <div class="big" id="mlProb">0.00%</div>
            <span class="risk-badge" id="mlRisk">UNKNOWN</span>
            <div class="row"><span>예측</span><strong id="mlPred">-</strong></div>
            <div class="row"><span>입력 사고유형</span><strong id="mlAccident">-</strong></div>
            <div class="row"><span>입력 선박종류</span><strong id="mlVessel">-</strong></div>
            <div class="row"><span>입력 발생해역</span><strong id="mlRegion">-</strong></div>
            <div class="feature-importance" id="featureImportance"></div>
          </div>
          <div class="card">
            <h3>③ 종합 모델 (최종 위험등급)</h3>
            <div class="big" id="finalRisk">-</div>
            <span class="risk-badge" id="finalRiskBadge">UNKNOWN</span>
            <div class="row"><span>가중 점수</span><strong id="finalScore">0.00 / 4.00</strong></div>
            <div class="bar"><div class="bar-fill" id="finalBar"></div></div>
            <div class="row"><span>DL 가중치</span><strong>60%</strong></div>
            <div class="row"><span>ML 가중치</span><strong>40%</strong></div>
            <div class="info-line" style="margin-top:10px;"><strong>응급 조치:</strong> <span id="finalAction">-</span></div>
            <div class="info-line"><strong>법적 근거:</strong> <span id="finalLaw">-</span></div>
          </div>
        </div>
        <div style="margin-top:18px;">
          <h3 style="margin:0 0 8px; font-size:14px; color:var(--muted); letter-spacing:.5px; text-transform:uppercase;">진단 요약</h3>
          <ul class="summary-list" id="summaryList"></ul>
          <div class="info-line" id="reportPath"></div>
        </div>
      </div>
    </section>

    <section class="panel full">
      <h2>4. 외상 6종 가이드 — 모델이 학습한 클래스별 설명·응급조치</h2>
      <div class="guide-grid" id="woundGuide"></div>
    </section>
  </main>
<script>
const $ = (id) => document.getElementById(id);
const fileInput = $("imageInput"), preview = $("preview"), dropZone = $("dropZone");
const dropContent = $("dropContent"), fileName = $("fileName"), runButton = $("runButton");
const errorBox = $("errorBox"), warnBox = $("warningBox");
const emptyState = $("emptyState"), resultArea = $("resultArea");
let categoriesCache = null;

function showError(msg){ errorBox.textContent = msg; errorBox.style.display = "block"; }
function clearError(){ errorBox.textContent = ""; errorBox.style.display = "none"; }
function setBusy(b){ runButton.disabled = b || !fileInput.files[0];
  runButton.textContent = b ? "분석 중..." : "분석 실행"; }

function fillSelect(id, values, fallback){
  const sel = $(id);
  sel.replaceChildren();
  (values && values.length ? values : [fallback]).forEach(v => {
    const opt = document.createElement("option");
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  });
}

function updatePreview(){
  clearError();
  const f = fileInput.files[0];
  if(!f){ fileName.textContent = "선택된 파일 없음"; preview.style.display = "none";
    dropContent.style.display = "grid"; runButton.disabled = true;
    $("hintLine").textContent = "이미지를 업로드하면 활성화됩니다."; return; }
  fileName.textContent = `${f.name} (${(f.size/1024/1024).toFixed(2)}MB)`;
  runButton.disabled = false;
  $("hintLine").textContent = "[분석 실행]을 눌러 DL/ML/종합 진단을 시작하세요.";
  const r = new FileReader();
  r.onload = () => { preview.src = r.result; preview.style.display = "block"; dropContent.style.display = "none"; };
  r.readAsDataURL(f);
}
fileInput.addEventListener("change", updatePreview);
["dragenter","dragover"].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add("dragging"); }));
["dragleave","drop"].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove("dragging"); }));
dropZone.addEventListener("drop", (ev) => {
  const f = ev.dataTransfer.files[0]; if(!f) return;
  const dt = new DataTransfer(); dt.items.add(f); fileInput.files = dt.files; updatePreview();
});

function renderTop3(list){
  const root = $("top3List"); root.replaceChildren();
  list.forEach(item => {
    const row = document.createElement("div");
    row.className = "candidate";
    const name = document.createElement("div"); name.textContent = item.display_name;
    const score = document.createElement("div"); score.className = "candidate-score";
    score.textContent = `${item.confidence_percent.toFixed(2)}%`;
    row.append(name, score); root.appendChild(row);
  });
}

function renderFeatureImportance(fi){
  const root = $("featureImportance"); root.replaceChildren();
  if(!fi || Object.keys(fi).length === 0) return;
  const entries = Object.entries(fi).sort((a,b)=>b[1]-a[1]);
  const max = Math.max(...entries.map(e=>e[1])) || 1;
  entries.forEach(([k,v]) => {
    const wrap = document.createElement("div"); wrap.className = "fi-row";
    const name = document.createElement("div"); name.textContent = k;
    const bar = document.createElement("div"); bar.className = "fi-bar";
    const fill = document.createElement("div"); fill.className = "fi-fill";
    fill.style.width = `${(v/max*100).toFixed(0)}%`; bar.appendChild(fill);
    const pct = document.createElement("div"); pct.textContent = `${(v*100).toFixed(1)}%`;
    pct.style.textAlign = "right";
    wrap.append(name, bar, pct); root.appendChild(wrap);
  });
}

function setRiskBadge(el, risk){ el.textContent = risk; el.className = `risk-badge ${risk}`; }

function renderResult(d){
  emptyState.style.display = "none";
  resultArea.style.display = "block";

  const dl = d.dl, ml = d.ml, fin = d.final;

  $("dlName").textContent = dl.display_name || "-";
  setRiskBadge($("dlRisk"), dl.risk || "UNKNOWN");
  $("dlConf").textContent = `${dl.confidence_percent.toFixed(2)}%`;
  $("dlBar").style.width = `${Math.max(0, Math.min(100, dl.confidence_percent))}%`;
  $("dlSim").textContent = dl.ood_reference_loaded
    ? `${dl.in_distribution_similarity_percent.toFixed(2)}% (기준 ${(dl.ood_similarity_threshold*100).toFixed(0)}%)`
    : "기준 미로딩";
  $("dlMargin").textContent = `${dl.top2_margin_percent.toFixed(2)}%`;
  $("dlNote").textContent = dl.is_unknown
    ? `모델 추정값: ${dl.model_display_name}`
    : `모델 클래스: ${dl.model_prediction}`;
  $("dlOodExplainer").style.display = dl.is_unknown ? "block" : "none";

  if (dl.model_description) {
    $("dlDesc").textContent = dl.model_description;
    $("dlDescBlock").style.display = "block";
  } else { $("dlDescBlock").style.display = "none"; }
  if (dl.model_action) {
    $("dlAction").textContent = dl.model_action;
    $("dlActionBlock").style.display = "block";
  } else { $("dlActionBlock").style.display = "none"; }

  renderTop3(dl.top3 || []);

  if(ml && !ml.error){
    $("mlProb").textContent = `${ml.casualty_probability_percent.toFixed(2)}%`;
    setRiskBadge($("mlRisk"), ml.risk || "UNKNOWN");
    $("mlPred").textContent = ml.predicted_casualty ? "사상자 발생 예측" : "사상자 미발생 예측";
    $("mlAccident").textContent = ml.input ? ml.input["사고유형"] : "-";
    $("mlVessel").textContent = ml.input ? ml.input["선박종류"] : "-";
    $("mlRegion").textContent = ml.input ? ml.input["발생해역"] : "-";
    renderFeatureImportance(ml.feature_importance || {});
  } else {
    $("mlProb").textContent = "-";
    setRiskBadge($("mlRisk"), "UNKNOWN");
    $("mlPred").textContent = (ml && ml.error) ? ml.error : "-";
    $("mlAccident").textContent = "-"; $("mlVessel").textContent = "-"; $("mlRegion").textContent = "-";
  }

  if(fin.is_unknown){
    $("finalRisk").textContent = "확인불가";
    setRiskBadge($("finalRiskBadge"), "UNKNOWN");
    $("finalScore").textContent = "- / 4.00";
    $("finalBar").style.width = "0%";
  } else {
    $("finalRisk").textContent = fin.risk;
    setRiskBadge($("finalRiskBadge"), fin.risk);
    $("finalScore").textContent = `${fin.final_score.toFixed(2)} / 4.00`;
    $("finalBar").style.width = `${Math.max(0, Math.min(100, fin.final_score_percent || (fin.final_score/4*100)))}%`;
  }
  $("finalAction").textContent = fin.action || "-";
  $("finalLaw").textContent = fin.law_ref || "-";

  const summaryList = $("summaryList"); summaryList.replaceChildren();
  (fin.summary_lines || [fin.summary || ""]).forEach(line => {
    if(!line) return;
    const li = document.createElement("li"); li.textContent = line; summaryList.appendChild(li);
  });

  const warnings = [];
  if(dl.is_unknown){ warnings.push("⚠ 확인불가: " + (dl.warning_message || "이미지 신뢰도 미달")); }
  else if(dl.low_confidence){ warnings.push("⚠ DL 신뢰도 70% 미만 - 재촬영 권장"); }
  if(warnings.length){ warnBox.textContent = warnings.join(" / "); warnBox.style.display = "block"; }
  else { warnBox.style.display = "none"; }

  $("reportPath").textContent = d.report_path ? `진단 리포트 저장: ${d.report_path}` : "";
}

runButton.addEventListener("click", async () => {
  if(!fileInput.files[0]){ showError("이미지를 선택하세요."); return; }
  clearError(); setBusy(true);
  const fd = new FormData();
  fd.append("image", fileInput.files[0]);
  fd.append("연도", $("year").value);
  fd.append("사고유형", $("accidentType").value);
  fd.append("선박종류", $("vesselType").value);
  fd.append("사고원인", $("cause").value);
  fd.append("발생해역", $("region").value);
  try {
    const res = await fetch("/predict", { method: "POST", body: fd });
    const data = await res.json();
    if(!res.ok){ showError(data.error || "분석 요청 실패"); return; }
    renderResult(data);
  } catch (e) { showError(`요청 오류: ${e.message}`); }
  finally { setBusy(false); }
});

function renderWoundGuide(items){
  const root = $("woundGuide"); root.replaceChildren();
  (items || []).forEach(item => {
    const card = document.createElement("div"); card.className = "guide-card";
    const head = document.createElement("div"); head.className = "guide-head";
    const name = document.createElement("div"); name.className = "name"; name.textContent = item.display_name;
    const badge = document.createElement("span"); badge.className = `risk-badge ${item.risk}`;
    badge.textContent = item.risk;
    head.append(name, badge); card.appendChild(head);

    const mkSection = (label, text, extraClass) => {
      const sec = document.createElement("div"); sec.className = "guide-section";
      const lab = document.createElement("div"); lab.className = "label"; lab.textContent = label;
      const body = document.createElement("div"); body.className = "body" + (extraClass ? " " + extraClass : "");
      body.textContent = text;
      sec.append(lab, body); return sec;
    };
    card.appendChild(mkSection("상처 설명", item.description));
    card.appendChild(mkSection("응급 조치", item.action, "action"));
    card.appendChild(mkSection("법적 근거", item.law_ref));
    root.appendChild(card);
  });
}

fetch("/health").then(r => r.json()).then(data => {
  const dl = data.dl_loaded ? "DL 로드" : "DL 미로드";
  const ml = data.ml_loaded ? "ML 로드" : "ML 미로드";
  $("modelState").textContent = `${dl} / ${ml} / device: ${data.device}`;
  if(data.categories){
    categoriesCache = data.categories;
    fillSelect("accidentType", data.categories["사고유형"], "충돌");
    fillSelect("vesselType", data.categories["선박종류"], "어선");
    fillSelect("cause", data.categories["사고원인"], "운항과실");
    fillSelect("region", data.categories["발생해역"], "남해");
  }
  if(data.year_range){
    $("year").min = data.year_range[0]; $("year").max = data.year_range[1] + 5;
    $("year").value = new Date().getFullYear();
  }
  renderWoundGuide(data.wound_guide);
}).catch(()=>{ $("modelState").textContent = "모델 상태 확인 실패"; });
</script>
</body>
</html>
"""


# ─── 진단 리포트 저장 ────────────────────────────────────────────────────────

def save_report(payload: dict[str, Any]) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = REPORT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(path)


# ─── HTTP 핸들러 ─────────────────────────────────────────────────────────────

class IntegratedHandler(BaseHTTPRequestHandler):
    """단일 페이지 + /health + /predict API."""

    dl_engine = WoundClassifier()
    ml_engine = AccidentRiskPredictor()
    server_version = "MDTS-Integrated/1.0"

    def log_message(self, format_string: str, *args: Any) -> None:
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format_string % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(HTML_PAGE); return
        if parsed.path == "/health":
            ml_options: dict[str, Any] = {}
            ml_loaded = False
            try:
                ml_options = self.ml_engine.options()
                ml_loaded = self.ml_engine.loaded
            except Exception as exc:
                ml_options = {"error": str(exc)}

            wound_guide = []
            for class_name in self.dl_engine.class_names:
                info = WOUND_KNOWLEDGE.get(class_name)
                if info is None:
                    continue
                wound_guide.append({
                    "class_name": class_name,
                    "display_name": info.display_name,
                    "risk": info.risk,
                    "risk_score": info.risk_score,
                    "description": info.description,
                    "action": info.action,
                    "law_ref": info.law_ref,
                    "expected_accidents": list(info.expected_accidents),
                })

            self.send_json({
                "ok": True,
                "dl_model_path": str(DL_MODEL_PATH),
                "dl_model_exists": DL_MODEL_PATH.exists(),
                "dl_loaded": self.dl_engine.model is not None,
                "ml_model_path": str(ML_MODEL_PATH),
                "ml_model_exists": ML_MODEL_PATH.exists(),
                "ml_loaded": ml_loaded,
                "ood_reference_loaded": self.dl_engine.ood_centroids is not None,
                "device": str(self.dl_engine.device),
                "classes": self.dl_engine.class_names,
                "wound_guide": wound_guide,
                "categories": ml_options.get("categories", {}),
                "year_range": ml_options.get("year_range", [2014, 2024]),
                "feature_importance": ml_options.get("feature_importance", {}),
            })
            return
        if parsed.path in {"/predict", "/api/predict"}:
            self.send_json({
                "ok": True,
                "message": "이 주소는 이미지 업로드 POST 전용 API입니다. 브라우저에서는 메인 페이지를 여십시오.",
                "main_page": f"http://{DEFAULT_HOST}:{DEFAULT_PORT}",
                "method": "POST",
                "form_fields": ["image", "연도", "사고유형", "선박종류", "사고원인", "발생해역"],
            })
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "요청 경로가 없습니다.")

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/predict", "/api/predict"}:
            self.send_error_json(HTTPStatus.NOT_FOUND, "요청 경로가 없습니다.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Content-Length가 올바르지 않습니다.")
            return

        if content_length <= 0:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "업로드 본문이 비어 있습니다.")
            return
        if content_length > MAX_UPLOAD_BYTES:
            self.send_error_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "이미지 파일은 최대 10MB까지 허용합니다.")
            return

        try:
            body = self.rfile.read(content_length)
            image_bytes, filename, fields = parse_multipart(self.headers.get("Content-Type", ""), body)
            if len(image_bytes) > MAX_UPLOAD_BYTES:
                raise ValueError("이미지 파일은 최대 10MB까지 허용합니다.")

            dl_result = self.dl_engine.predict(image_bytes)

            ml_input = {
                "연도": fields.get("연도", "").strip() or datetime.now().year,
                "사고유형": fields.get("사고유형", "").strip(),
                "선박종류": fields.get("선박종류", "").strip(),
                "사고원인": fields.get("사고원인", "").strip(),
                "발생해역": fields.get("발생해역", "").strip(),
            }
            try:
                ml_result = self.ml_engine.predict(ml_input)
                ml_result["error"] = None
            except FileNotFoundError as exc:
                ml_result = {"error": f"ML 모델/CSV 누락: {exc}",
                             "casualty_probability": 0.0, "casualty_probability_percent": 0.0,
                             "predicted_casualty": False, "risk": "UNKNOWN", "risk_score": 0,
                             "input": ml_input, "feature_importance": {}}
            except Exception as exc:
                ml_result = {"error": f"ML 추론 오류: {exc}",
                             "casualty_probability": 0.0, "casualty_probability_percent": 0.0,
                             "predicted_casualty": False, "risk": "UNKNOWN", "risk_score": 0,
                             "input": ml_input, "feature_importance": {}}

            final = integrate_results(dl_result, ml_result)

            payload = {
                "ok": True,
                "filename": html.escape(filename),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dl": dl_result,
                "ml": ml_result,
                "final": final,
            }
            payload["report_path"] = save_report(payload)
            self.send_json(payload)
        except FileNotFoundError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
        except RuntimeError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"모델 실행 오류: {exc}")
        except Exception as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"예상하지 못한 오류: {exc}")

    def send_html(self, text: str) -> None:
        payload = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"ok": False, "error": message}, status=status)

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


# ─── 서버 실행 ────────────────────────────────────────────────────────────────

def open_browser_later(url: str, delay: float = 1.2) -> None:
    def _open():
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Timer(delay, _open).start()


def warmup_models() -> None:
    """서버 시작 시 모델을 백그라운드에서 미리 로드한다."""
    def _warm():
        try:
            IntegratedHandler.dl_engine.load()
            print("[*] DL 모델 로드 완료")
        except Exception as exc:
            print(f"[!] DL 모델 로드 실패: {exc}")
        try:
            IntegratedHandler.ml_engine.load()
            print("[*] ML 모델 로드 완료")
        except Exception as exc:
            print(f"[!] ML 모델 로드 실패: {exc}")
    threading.Thread(target=_warm, daemon=True).start()


def run_server(host: str, port: int, open_browser: bool) -> None:
    server = ThreadingHTTPServer((host, port), IntegratedHandler)
    actual_port = server.server_address[1]
    url = f"http://{host}:{actual_port}"
    print("=" * 64)
    print("  MDTS 통합 진단 시스템 (M-MEDIC v2)")
    print("=" * 64)
    print(f"  접속 주소 : {url}")
    print(f"  DL 모델   : {DL_MODEL_PATH}")
    print(f"  ML 모델   : {ML_MODEL_PATH}")
    print(f"  ML CSV    : {ML_DATA_PATH}")
    print(f"  종료      : Ctrl+C")
    print("=" * 64)

    warmup_models()
    if open_browser:
        open_browser_later(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 서버 종료")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="MDTS 통합 진단 앱 (DL + ML + 종합)")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true", help="자동 브라우저 오픈 비활성화")
    args = parser.parse_args()
    run_server(args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
