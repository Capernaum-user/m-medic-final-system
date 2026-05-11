"""
변경 요약:
- 현재 공유 폴더 구조 기준으로 MobileNetV3 Large 외상 분류 모델을 로드하는 로컬 웹 테스트 페이지 추가
- 이미지 업로드 후 상처 분류명, 신뢰도, Top-3 후보, 위험도, 응급처치 지침을 JSON API와 화면으로 제공
- 업로드 이미지는 저장하지 않고 메모리에서만 검증 및 추론
- 추론 전처리를 학습 검증 파이프라인과 동일하게 Resize(256) + CenterCrop(224)로 정렬
- 학습 데이터 feature centroid와 비교해 유사도가 낮은 입력은 확인불가 이미지로 판정
- 팀 웹페이지 연동을 위해 CORS 응답과 /api/predict 별칭 추가
- /api/predict를 브라우저에서 직접 열었을 때 POST 전용 API 안내 응답 추가

실행:
    python 04_통합시스템/wound_test_page.py
    브라우저: http://127.0.0.1:8008

필요 패키지:
    torch, torchvision, Pillow
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import torch
import torch.nn as nn
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms


ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "03_딥러닝" / "결과물" / "mobilenet_v3_wound_best.pth"
CLASS_MAPPING_PATH = ROOT_DIR / "03_딥러닝" / "결과물" / "wound_class_mapping.json"
OOD_REFERENCE_PATH = Path(__file__).resolve().parent / "wound_ood_reference.json"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000
LOW_CONFIDENCE_THRESHOLD = 0.70
AMBIGUOUS_MARGIN_THRESHOLD = 0.20
DEFAULT_OOD_SIMILARITY_THRESHOLD = 0.50
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8008

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


@dataclass(frozen=True)
class WoundInfo:
    """상처 클래스별 표시명, 위험도, 처치 지침."""

    display_name: str
    risk: str
    action: str
    law_ref: str


WOUND_KNOWLEDGE: dict[str, WoundInfo] = {
    "Abrasions": WoundInfo(
        display_name="찰과상(Abrasions)",
        risk="LOW",
        action="이물질 제거 후 생리식염수로 세척. 소독 연고 도포 후 거즈로 보호.",
        law_ref="WHO 선내의료지침 Ch.7",
    ),
    "Bruises": WoundInfo(
        display_name="타박상(Bruises)",
        risk="LOW",
        action="초기 48시간 냉찜질. 부종과 통증이 심하면 골절 여부 확인.",
        law_ref="선원법 시행규칙 [별표 5의5]",
    ),
    "Burns": WoundInfo(
        display_name="화상(Burns)",
        risk="HIGH",
        action="20분 이상 냉각. 수포 파열 금지. 2도 이상이 의심되면 의료기관 이송.",
        law_ref="선원법 시행규칙 [별표 5의5] 화상처치",
    ),
    "Cut": WoundInfo(
        display_name="절상(Cut)",
        risk="MEDIUM",
        action="압박 지혈. 세척 후 소독. 깊거나 벌어진 상처는 봉합 필요.",
        law_ref="WHO 선내의료지침 Ch.7",
    ),
    "Laceration": WoundInfo(
        display_name="열상(Laceration)",
        risk="HIGH",
        action="지혈 및 세척. 깊이 1cm 이상이면 봉합 필요. 감염 징후 관찰.",
        law_ref="선원법 시행규칙 [별표 5의5]",
    ),
    "Stab_wound": WoundInfo(
        display_name="자창(Stab Wound)",
        risk="CRITICAL",
        action="박힌 물체 제거 금지. 압박 지혈. 쇼크 방지 후 즉시 병원 이송.",
        law_ref="선원법 시행규칙 [별표 5의5]",
    ),
}


HTML_PAGE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MDTS 상처 분류 테스트</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #667085;
      --line: #d9e1e7;
      --primary: #1f6feb;
      --primary-dark: #174ea6;
      --ok: #157347;
      --warning: #b45309;
      --danger: #b42318;
      --critical: #7f1d1d;
      --shadow: 0 14px 35px rgba(31, 41, 51, 0.08);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Malgun Gothic", "Segoe UI", Arial, sans-serif;
      line-height: 1.5;
    }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    header {
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }

    .header-inner {
      max-width: 1180px;
      margin: 0 auto;
      padding: 18px 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }

    h1 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }

    .model-state {
      color: var(--muted);
      font-size: 13px;
      text-align: right;
      word-break: keep-all;
    }

    main {
      max-width: 1180px;
      width: 100%;
      margin: 0 auto;
      padding: 28px 22px 40px;
      display: grid;
      grid-template-columns: minmax(320px, 0.95fr) minmax(340px, 1.05fr);
      gap: 22px;
    }

    section {
      min-width: 0;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .upload-panel {
      padding: 20px;
    }

    .drop-zone {
      position: relative;
      min-height: 360px;
      border: 2px dashed #a8b8c7;
      border-radius: 8px;
      display: grid;
      place-items: center;
      padding: 20px;
      background: #fbfcfd;
      transition: border-color 0.15s ease, background 0.15s ease;
      overflow: hidden;
    }

    .drop-zone.dragging {
      border-color: var(--primary);
      background: #eef5ff;
    }

    .drop-content {
      display: grid;
      gap: 12px;
      justify-items: center;
      text-align: center;
      color: var(--muted);
    }

    .drop-title {
      color: var(--text);
      font-weight: 700;
      font-size: 18px;
    }

    .file-input {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    .preview {
      width: 100%;
      max-height: 420px;
      object-fit: contain;
      display: none;
    }

    .upload-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    .file-name {
      min-width: 0;
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    button {
      border: 0;
      border-radius: 6px;
      background: var(--primary);
      color: #ffffff;
      min-height: 42px;
      padding: 0 18px;
      font-weight: 700;
      cursor: pointer;
    }

    button:hover {
      background: var(--primary-dark);
    }

    button:disabled {
      background: #9aa8b5;
      cursor: not-allowed;
    }

    .result-panel {
      padding: 22px;
      min-height: 480px;
    }

    .empty {
      min-height: 430px;
      display: grid;
      place-items: center;
      color: var(--muted);
      text-align: center;
      border: 1px dashed var(--line);
      border-radius: 8px;
    }

    .result {
      display: none;
    }

    .result-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 18px;
    }

    .prediction {
      margin: 0;
      font-size: 28px;
      line-height: 1.25;
      letter-spacing: 0;
      overflow-wrap: anywhere;
    }

    .risk {
      flex: 0 0 auto;
      border-radius: 999px;
      padding: 6px 11px;
      font-size: 12px;
      font-weight: 800;
      color: #ffffff;
      background: var(--muted);
    }

    .risk.LOW {
      background: var(--ok);
    }

    .risk.MEDIUM {
      background: var(--warning);
    }

    .risk.HIGH {
      background: var(--danger);
    }

    .risk.CRITICAL {
      background: var(--critical);
    }

    .confidence {
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }

    .confidence-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 14px;
    }

    .bar {
      height: 12px;
      border-radius: 999px;
      background: #e8eef3;
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      width: 0;
      background: var(--primary);
      transition: width 0.2s ease;
    }

    .warning-box {
      display: none;
      border: 1px solid #f2b8b5;
      background: #fff4f2;
      color: #8a1c13;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 18px;
      font-size: 14px;
    }

    .info-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 18px;
    }

    .info-box {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 78px;
      background: #fbfcfd;
    }

    .label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 5px;
    }

    .value {
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .action {
      border-top: 1px solid var(--line);
      padding-top: 18px;
      margin-top: 18px;
    }

    .action h2,
    .top3 h2 {
      margin: 0 0 10px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .action p {
      margin: 0;
      color: #344054;
    }

    .top3 {
      margin-top: 18px;
    }

    .candidate {
      display: grid;
      grid-template-columns: minmax(120px, 1fr) 84px;
      gap: 10px;
      align-items: center;
      padding: 9px 0;
      border-bottom: 1px solid #edf1f4;
    }

    .candidate:last-child {
      border-bottom: 0;
    }

    .candidate-name {
      overflow-wrap: anywhere;
    }

    .candidate-score {
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--muted);
    }

    .error {
      display: none;
      border: 1px solid #f2b8b5;
      background: #fff4f2;
      color: #8a1c13;
      border-radius: 8px;
      padding: 12px;
      margin-top: 14px;
      font-size: 14px;
      overflow-wrap: anywhere;
    }

    @media (max-width: 860px) {
      .header-inner {
        align-items: flex-start;
        flex-direction: column;
      }

      .model-state {
        text-align: left;
      }

      main {
        grid-template-columns: 1fr;
      }

      .drop-zone {
        min-height: 280px;
      }

      .info-grid {
        grid-template-columns: 1fr;
      }

      .result-head {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="header-inner">
        <h1>MDTS 상처 분류 테스트</h1>
        <div class="model-state" id="modelState">모델 상태 확인 중</div>
      </div>
    </header>
    <main>
      <section class="panel upload-panel">
        <form id="uploadForm">
          <div class="drop-zone" id="dropZone">
            <img class="preview" id="preview" alt="업로드 이미지 미리보기">
            <div class="drop-content" id="dropContent">
              <div class="drop-title">이미지 선택</div>
              <div>JPG, PNG, BMP, WEBP / 최대 10MB</div>
            </div>
            <input class="file-input" id="imageInput" name="image" type="file" accept="image/*">
          </div>
          <div class="upload-actions">
            <div class="file-name" id="fileName">선택된 파일 없음</div>
            <button id="predictButton" type="submit" disabled>분석 실행</button>
          </div>
          <div class="error" id="errorBox"></div>
        </form>
      </section>
      <section class="panel result-panel">
        <div class="empty" id="emptyState">이미지를 업로드하면 분류 결과가 표시됩니다.</div>
        <div class="result" id="resultState">
          <div class="result-head">
            <div>
              <div class="label">판독 결과</div>
              <h2 class="prediction" id="predictionName">-</h2>
            </div>
            <div class="risk" id="riskBadge">UNKNOWN</div>
          </div>
          <div class="confidence">
            <div class="confidence-row">
              <span>신뢰도</span>
              <strong id="confidenceText">0.00%</strong>
            </div>
            <div class="bar">
              <div class="bar-fill" id="confidenceBar"></div>
            </div>
          </div>
          <div class="warning-box" id="warningBox">신뢰도 70% 미만입니다. 같은 부위를 더 밝고 선명하게 재촬영한 뒤 다시 테스트하십시오.</div>
          <div class="info-grid">
            <div class="info-box">
              <div class="label">모델 클래스</div>
              <div class="value" id="rawClass">-</div>
            </div>
            <div class="info-box">
              <div class="label">법적 근거</div>
              <div class="value" id="lawRef">-</div>
            </div>
          </div>
          <div class="action">
            <h2>응급처치 지침</h2>
            <p id="actionText">-</p>
          </div>
          <div class="top3">
            <h2>Top-3 후보</h2>
            <div id="top3List"></div>
          </div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const form = document.getElementById("uploadForm");
    const input = document.getElementById("imageInput");
    const button = document.getElementById("predictButton");
    const fileName = document.getElementById("fileName");
    const preview = document.getElementById("preview");
    const dropZone = document.getElementById("dropZone");
    const dropContent = document.getElementById("dropContent");
    const errorBox = document.getElementById("errorBox");
    const emptyState = document.getElementById("emptyState");
    const resultState = document.getElementById("resultState");

    function showError(message) {
      errorBox.textContent = message;
      errorBox.style.display = "block";
    }

    function clearError() {
      errorBox.textContent = "";
      errorBox.style.display = "none";
    }

    function setBusy(isBusy) {
      button.disabled = isBusy || input.files.length === 0;
      button.textContent = isBusy ? "분석 중" : "분석 실행";
    }

    function updatePreview() {
      clearError();
      const file = input.files[0];
      if (!file) {
        fileName.textContent = "선택된 파일 없음";
        button.disabled = true;
        preview.style.display = "none";
        dropContent.style.display = "grid";
        return;
      }
      fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`;
      button.disabled = false;
      const reader = new FileReader();
      reader.onload = () => {
        preview.src = reader.result;
        preview.style.display = "block";
        dropContent.style.display = "none";
      };
      reader.readAsDataURL(file);
    }

    function renderResult(data) {
      emptyState.style.display = "none";
      resultState.style.display = "block";
      document.getElementById("predictionName").textContent = data.display_name;
      document.getElementById("rawClass").textContent = data.is_unknown
        ? `모델 추정: ${data.model_prediction} / 유사도: ${data.in_distribution_similarity_percent.toFixed(2)}%`
        : data.prediction;
      document.getElementById("lawRef").textContent = data.law_ref;
      document.getElementById("actionText").textContent = data.action;
      document.getElementById("confidenceText").textContent = `${data.confidence_percent.toFixed(2)}%`;
      document.getElementById("confidenceBar").style.width = `${Math.max(0, Math.min(100, data.confidence_percent))}%`;

      const riskBadge = document.getElementById("riskBadge");
      riskBadge.textContent = data.risk;
      riskBadge.className = `risk ${data.risk}`;

      const warningBox = document.getElementById("warningBox");
      warningBox.textContent = data.warning_message || "신뢰도 70% 미만입니다. 같은 부위를 더 밝고 선명하게 재촬영한 뒤 다시 테스트하십시오.";
      warningBox.style.display = data.is_unknown || data.low_confidence ? "block" : "none";

      const top3List = document.getElementById("top3List");
      top3List.replaceChildren();
      data.top3.forEach((item) => {
        const row = document.createElement("div");
        row.className = "candidate";
        const name = document.createElement("div");
        name.className = "candidate-name";
        name.textContent = item.display_name;
        const score = document.createElement("div");
        score.className = "candidate-score";
        score.textContent = `${item.confidence_percent.toFixed(2)}%`;
        row.append(name, score);
        top3List.appendChild(row);
      });
    }

    input.addEventListener("change", updatePreview);

    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("dragging");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("dragging");
      });
    });

    dropZone.addEventListener("drop", (event) => {
      const file = event.dataTransfer.files[0];
      if (!file) {
        return;
      }
      const transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      updatePreview();
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearError();
      if (!input.files[0]) {
        showError("이미지를 선택하십시오.");
        return;
      }
      const formData = new FormData();
      formData.append("image", input.files[0]);
      setBusy(true);
      try {
        const response = await fetch("/predict", {
          method: "POST",
          body: formData
        });
        const data = await response.json();
        if (!response.ok) {
          showError(data.error || "분석 요청 실패");
          return;
        }
        renderResult(data);
      } catch (error) {
        showError(`요청 오류: ${error.message}`);
      } finally {
        setBusy(false);
      }
    });

    fetch("/health")
      .then((response) => response.json())
      .then((data) => {
        const state = data.model_loaded ? "로드 완료" : "로드 대기";
        document.getElementById("modelState").textContent = `모델: ${state} / ${data.model_path}`;
      })
      .catch(() => {
        document.getElementById("modelState").textContent = "모델 상태 확인 실패";
      });
  </script>
</body>
</html>
"""


def load_class_names(mapping_path: Path) -> list[str]:
    """클래스 매핑 JSON을 숫자 키 순서로 읽는다."""
    default_classes = ["Abrasions", "Bruises", "Burns", "Cut", "Laceration", "Stab_wound"]
    if not mapping_path.exists():
        return default_classes

    try:
        raw_data = json.loads(mapping_path.read_text(encoding="utf-8"))
        indexed = sorted(((int(key), str(value)) for key, value in raw_data.items()), key=lambda item: item[0])
        class_names = [name for _, name in indexed]
        return class_names if class_names else default_classes
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return default_classes


def load_ood_reference(reference_path: Path, class_names: list[str], device: torch.device) -> tuple[torch.Tensor, float] | None:
    """학습 데이터 feature centroid 기준을 로드한다."""
    if not reference_path.exists():
        return None

    try:
        raw_data = json.loads(reference_path.read_text(encoding="utf-8"))
        centroids_by_class = raw_data["centroids"]
        centroids = [centroids_by_class[class_name] for class_name in class_names]
        threshold = float(raw_data.get("similarity_threshold", DEFAULT_OOD_SIMILARITY_THRESHOLD))
        tensor = torch.tensor(centroids, dtype=torch.float32, device=device)
        tensor = torch.nn.functional.normalize(tensor, dim=1)
        return tensor, threshold
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def open_valid_image(image_bytes: bytes) -> Image.Image:
    """업로드 바이트를 PIL 이미지로 검증하고 RGB 이미지로 반환한다."""
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


class WoundPredictor:
    """MobileNetV3 Large 외상 분류 모델 래퍼."""

    def __init__(self, model_path: Path, mapping_path: Path, ood_reference_path: Path) -> None:
        self.model_path = model_path
        self.mapping_path = mapping_path
        self.ood_reference_path = ood_reference_path
        self.class_names = load_class_names(mapping_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module | None = None
        self.ood_centroids: torch.Tensor | None = None
        self.ood_similarity_threshold = DEFAULT_OOD_SIMILARITY_THRESHOLD
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    def load(self) -> None:
        """모델을 한 번만 메모리에 로드한다."""
        if self.model is not None:
            return
        if not self.model_path.exists():
            raise FileNotFoundError(f"모델 파일이 없습니다: {self.model_path}")

        model = models.mobilenet_v3_large(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, len(self.class_names))

        try:
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
        except TypeError:
            state_dict = torch.load(self.model_path, map_location=self.device)

        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model
        reference = load_ood_reference(self.ood_reference_path, self.class_names, self.device)
        if reference is not None:
            self.ood_centroids, self.ood_similarity_threshold = reference

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        """이미지 바이트를 입력받아 외상 분류 결과를 반환한다."""
        self.load()
        if self.model is None:
            raise RuntimeError("모델 로드 실패")

        image = open_valid_image(image_bytes)
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        # O(C + D): 클래스 수 C softmax와 D차원 embedding 유사도 계산
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
        ood_reference_loaded = self.ood_centroids is not None
        if self.ood_centroids is not None:
            similarity_scores = torch.mv(self.ood_centroids, embedding.squeeze(0))
            similarity = float(torch.max(similarity_scores).item())
            predicted_similarity = float(similarity_scores[prediction_index].item())

        wound_info = WOUND_KNOWLEDGE.get(
            prediction,
            WoundInfo(
                display_name=f"미분류({prediction})",
                risk="UNKNOWN",
                action="전문 의료진 자문 필요.",
                law_ref="-",
            ),
        )

        top3 = []
        for value, index in zip(values.tolist(), indices.tolist()):
            class_name = self.class_names[int(index)]
            info = WOUND_KNOWLEDGE.get(
                class_name,
                WoundInfo(
                    display_name=f"미분류({class_name})",
                    risk="UNKNOWN",
                    action="-",
                    law_ref="-",
                ),
            )
            top3.append(
                {
                    "class_name": class_name,
                    "display_name": info.display_name,
                    "confidence": float(value),
                    "confidence_percent": float(value) * 100.0,
                }
            )

        low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD
        ambiguous_prediction = top2_margin < AMBIGUOUS_MARGIN_THRESHOLD
        out_of_distribution = ood_reference_loaded and similarity < self.ood_similarity_threshold
        is_unknown = low_confidence or ambiguous_prediction or out_of_distribution

        warning_reasons = []
        if out_of_distribution:
            warning_reasons.append(
                f"학습 데이터 feature 유사도 {similarity * 100.0:.2f}%가 기준 {self.ood_similarity_threshold * 100.0:.0f}%보다 낮습니다."
            )
        if low_confidence:
            warning_reasons.append(f"모델 confidence {confidence * 100.0:.2f}%가 기준 70%보다 낮습니다.")
        if ambiguous_prediction:
            warning_reasons.append(f"1위와 2위 후보 차이 {top2_margin * 100.0:.2f}%가 기준 20%보다 작습니다.")

        if is_unknown:
            display_name = "확인불가 이미지"
            risk = "UNKNOWN"
            action = "학습된 6종 상처 이미지와 충분히 유사하지 않습니다. 상처 부위를 중심으로 더 밝고 선명하게 재촬영하거나 전문가 확인이 필요합니다."
            law_ref = "-"
            warning_message = " ".join(warning_reasons) if warning_reasons else "확인불가 이미지입니다."
        else:
            display_name = wound_info.display_name
            risk = wound_info.risk
            action = wound_info.action
            law_ref = wound_info.law_ref
            warning_message = ""

        return {
            "prediction": "UNKNOWN" if is_unknown else prediction,
            "display_name": display_name,
            "model_prediction": prediction,
            "model_display_name": wound_info.display_name,
            "confidence": confidence,
            "confidence_percent": confidence * 100.0,
            "top2_margin": top2_margin,
            "top2_margin_percent": top2_margin * 100.0,
            "low_confidence": low_confidence,
            "ambiguous_prediction": ambiguous_prediction,
            "out_of_distribution": out_of_distribution,
            "is_unknown": is_unknown,
            "in_distribution_similarity": similarity,
            "in_distribution_similarity_percent": similarity * 100.0,
            "predicted_class_similarity": predicted_similarity,
            "predicted_class_similarity_percent": predicted_similarity * 100.0,
            "ood_reference_loaded": ood_reference_loaded,
            "ood_similarity_threshold": self.ood_similarity_threshold,
            "risk": risk,
            "action": action,
            "law_ref": law_ref,
            "warning_message": warning_message,
            "top3": top3,
            "model_path": str(self.model_path),
            "device": str(self.device),
        }


def parse_multipart_image(content_type: str, body: bytes) -> tuple[bytes, str]:
    """multipart/form-data에서 image 필드를 추출한다."""
    if "multipart/form-data" not in content_type:
        raise ValueError("Content-Type은 multipart/form-data여야 합니다.")

    message_bytes = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    message = BytesParser(policy=policy.default).parsebytes(message_bytes)
    if not message.is_multipart():
        raise ValueError("multipart 요청 형식이 올바르지 않습니다.")

    for part in message.iter_parts():
        field_name = part.get_param("name", header="content-disposition")
        if field_name != "image":
            continue
        payload = part.get_payload(decode=True)
        filename = part.get_filename() or "uploaded-image"
        if not payload:
            raise ValueError("업로드된 이미지가 비어 있습니다.")
        return payload, filename

    raise ValueError("image 필드가 없습니다.")


class WoundTestHandler(BaseHTTPRequestHandler):
    """단일 페이지와 예측 API를 제공하는 HTTP 핸들러."""

    predictor = WoundPredictor(MODEL_PATH, CLASS_MAPPING_PATH, OOD_REFERENCE_PATH)
    server_version = "MDTSWoundTest/1.0"

    def log_message(self, format_string: str, *args: Any) -> None:
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format_string % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(HTML_PAGE)
            return
        if parsed.path == "/health":
            self.send_json(
                {
                    "ok": True,
                    "model_path": str(MODEL_PATH),
                    "model_exists": MODEL_PATH.exists(),
                    "model_loaded": self.predictor.model is not None,
                    "class_mapping_path": str(CLASS_MAPPING_PATH),
                    "ood_reference_path": str(OOD_REFERENCE_PATH),
                    "ood_reference_exists": OOD_REFERENCE_PATH.exists(),
                    "ood_reference_loaded": self.predictor.ood_centroids is not None,
                    "ood_similarity_threshold": self.predictor.ood_similarity_threshold,
                    "classes": self.predictor.class_names,
                    "device": str(self.predictor.device),
                }
            )
            return
        if parsed.path in {"/predict", "/api/predict"}:
            self.send_json(
                {
                    "ok": True,
                    "message": "이 주소는 이미지 업로드 POST 전용 API입니다. 브라우저에서는 웹페이지 주소를 여십시오.",
                    "web_page_url": "http://127.0.0.1:5174",
                    "model_test_page_url": "http://127.0.0.1:8008",
                    "method": "POST",
                    "form_field": "image",
                }
            )
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "요청 경로가 없습니다.")

    def do_OPTIONS(self) -> None:
        """브라우저 CORS preflight 요청에 응답한다."""
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
            image_bytes, filename = parse_multipart_image(self.headers.get("Content-Type", ""), body)
            if len(image_bytes) > MAX_UPLOAD_BYTES:
                raise ValueError("이미지 파일은 최대 10MB까지 허용합니다.")
            result = self.predictor.predict(image_bytes)
            result["filename"] = html.escape(filename)
            self.send_json(result)
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
        """로컬 팀 웹페이지에서 모델 API를 호출할 수 있도록 CORS를 허용한다."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(host: str, port: int) -> None:
    """웹 테스트 서버를 실행한다."""
    server = ThreadingHTTPServer((host, port), WoundTestHandler)
    url = f"http://{host}:{server.server_address[1]}"
    print(f"MDTS 상처 분류 테스트 페이지 실행: {url}")
    print(f"모델 파일: {MODEL_PATH}")
    print("종료: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
    finally:
        server.server_close()


def main() -> None:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="MDTS 상처 분류 웹 테스트 페이지")
    parser.add_argument("--host", default=DEFAULT_HOST, help="바인딩 호스트")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="바인딩 포트")
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
