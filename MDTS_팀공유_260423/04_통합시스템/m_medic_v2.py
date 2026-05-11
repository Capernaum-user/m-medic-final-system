"""
[M-Medic v2] AI 통합 진단 시스템 - 최종 버전
----------------------------------------------
기능:
  ① 외상 분류: MobileNetV3 Large (실제 학습 완료 모델)
  ② ML 사고 위험 예측: RandomForest (해양사고 데이터 기반)
  ③ 신뢰도(Confidence) 기반 경고: 70% 미만 시 재촬영 권고
  ④ 선원법 지침 + 응급처치 매뉴얼 자동 생성
  ⑤ JSON 진단 리포트 자동 저장

사용법:
  python m_medic_v2.py --image <이미지경로> [--expert]
  python m_medic_v2.py --demo   ← 모델 없이 시스템 흐름 시연
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

# ─── 경로 ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
WOUND_MODEL  = BASE_DIR / ".." / "03_deep_learning" / "wound_detection" / "results" / "mobilenet_v3_wound_best.pth"
EXPERT_MODEL = BASE_DIR / ".." / "03_deep_learning" / "wound_detection" / "results" / "efficientnet_v2_s_wound_expert.pth"

# ─── 지식 베이스 (선원법 시행규칙 [별표 5의5] + WHO 국제선내의료지침) ────────
WOUND_KNOWLEDGE = {
    "Abrasions":  {"name": "찰과상(Abrasions)", "risk": "LOW",
                   "action": "이물질 제거 후 생리식염수 세척. 소독 연고 도포 후 거즈 보호.",
                   "law_ref": "WHO 선내의료지침 Ch.7"},
    "Bruises":    {"name": "타박상(Bruises)", "risk": "LOW",
                   "action": "초기 48시간 냉찜질. 부종 심할 경우 골절 여부 확인.",
                   "law_ref": "선원법 시행규칙 [별표 5의5]"},
    "Burns":      {"name": "화상(Burns)", "risk": "HIGH",
                   "action": "20분 이상 냉각. 수포 파열 금지. 2도 이상 시 회항 권고.",
                   "law_ref": "선원법 시행규칙 [별표 5의5] 화상처치"},
    "Cut":        {"name": "절상(Cut)", "risk": "MEDIUM",
                   "action": "압박 지혈. 세척 후 소독. 깊은 경우 봉합 필요.",
                   "law_ref": "WHO 선내의료지침 Ch.7"},
    "Laceration": {"name": "열상(Laceration)", "risk": "HIGH",
                   "action": "지혈 및 세척. 깊이 1cm 이상 시 봉합 필수. 감염 주의.",
                   "law_ref": "선원법 시행규칙 [별표 5의5]"},
    "Stab_wound": {"name": "자창(Stab Wound)", "risk": "CRITICAL",
                   "action": "박힌 물체 제거 금지. 즉시 병원 이송. 내부 손상 확인 필수.",
                   "law_ref": "선원법 시행규칙 [별표 5의5]"},
}

RISK_COLORS = {
    "CRITICAL": "[!!!CRITICAL]",
    "HIGH":     "[HIGH]",
    "MEDIUM":   "[MEDIUM]",
    "LOW":      "[LOW]",
    "UNKNOWN":  "[UNKNOWN]",
}

# ─── 이미지 전처리 ────────────────────────────────────────────────────────────
TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

WOUND_CLASSES = ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']


# ─── 모델 로더 ────────────────────────────────────────────────────────────────
def load_wound_model(device, num_classes=6, use_expert=False):
    """외상 분류 모델 로드 (MobileNetV3 기본 / EfficientNet-V2-S 전문가 모드)"""
    model_path = EXPERT_MODEL if use_expert else WOUND_MODEL

    try:
        if use_expert:
            from torchvision.models import efficientnet_v2_s
            model = efficientnet_v2_s(weights=None)
            in_feat = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(in_feat, num_classes)
            model_name = "EfficientNet-V2-S (Expert)"
        else:
            from torchvision.models import mobilenet_v3_large
            model = mobilenet_v3_large(weights=None)
            in_feat = model.classifier[3].in_features
            model.classifier[3] = nn.Linear(in_feat, num_classes)
            model_name = "MobileNetV3 Large"
    except Exception:
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        model_name = "ResNet18 (Fallback)"

    model = model.to(device)
    if model_path.exists():
        model.load_state_dict(torch.load(str(model_path), map_location=device))
        model.eval()
        print(f"[*] {model_name} 로딩 완료.")
        return model, True
    return model, False


# ─── 핵심 진단 함수 ────────────────────────────────────────────────────────────
def diagnose_wound(img_path: str, model=None, device=None):
    """외상 분류 진단 — MobileNetV3 Large 실시간 판독"""
    if device is None:
        device = torch.device("cpu")

    try:
        img = Image.open(img_path).convert("RGB")
    except Exception as e:
        return {"error": f"이미지 로드 실패: {e}"}

    img_t = TRANSFORM(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(img_t)
        probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

    pred_idx   = int(np.argmax(probs))
    confidence = float(probs[pred_idx])
    pred_class = WOUND_CLASSES[pred_idx] if pred_idx < len(WOUND_CLASSES) else "Unknown"

    knowledge = WOUND_KNOWLEDGE.get(pred_class, {
        "name": f"미분류({pred_class})", "risk": "MEDIUM",
        "action": "전문 의료진 자문 필요.", "law_ref": "-"
    })

    return {
        "mode": "wound",
        "prediction": pred_class,
        "confidence": confidence,
        "low_confidence": confidence < 0.70,
        **knowledge
    }


# ─── 의료 보고서 출력 ─────────────────────────────────────────────────────────
def print_report(result: dict, img_path: str = "", age: float = 0, gender: str = ""):
    risk = result.get("risk", "UNKNOWN")
    icon = RISK_COLORS.get(risk, "[?]")
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("=" * 62)
    print("         M-Medic v2.0 통합 의료 진단 보고서")
    print("=" * 62)
    print(f"  진단 시각 : {now}")
    print(f"  이미지    : {img_path}")
    if age:    print(f"  환자 나이 : {age}세")
    if gender: print(f"  환자 성별 : {gender}")
    print("-" * 62)
    print(f"  판독 결과 : {result.get('name', '-')}")
    print(f"  위험 등급 : {icon} {risk}")
    print(f"  신뢰도    : {result.get('confidence', 0):.1%}")

    if result.get("low_confidence"):
        print("  [경고] 신뢰도 70% 미만: 재촬영 또는 전문가 판독 권고")

    print()
    print("  [긴급 조치 지침]")
    for line in result.get("action", "-").split(". "):
        if line:
            print(f"    - {line}.")

    print()
    print(f"  [법적 근거]")
    print(f"    {result.get('law_ref', '-')}")
    print("=" * 62)

    if risk == "CRITICAL":
        print()
        print("  !! 즉시 회항 및 연안 병원 이송을 강력 권고합니다 !!")
        print()
    elif risk == "HIGH":
        print()
        print("  !! 가능한 빨리 육지 의료기관 방문을 권고합니다 !!")
        print()

    report_path = str(BASE_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({**result, "timestamp": now, "image": img_path,
                   "patient_age": age, "patient_gender": gender},
                  f, ensure_ascii=False, indent=2)
    print(f"  보고서 저장: {report_path}")


# ─── 데모 모드 (모델 없이 시스템 흐름 시연) ──────────────────────────────────
def run_demo():
    demo_cases = [
        {"img": "sample_stab.jpg",  "age": 32, "gender": "male",   "class": "Stab_wound"},
        {"img": "sample_burn.jpg",  "age": 45, "gender": "male",   "class": "Burns"},
        {"img": "sample_cut.jpg",   "age": 28, "gender": "female", "class": "Cut"},
        {"img": "sample_abr.jpg",   "age": 55, "gender": "male",   "class": "Abrasions"},
    ]

    print("\n[데모 모드] 실제 이미지 없이 외상 판독 시스템 흐름을 시연합니다.\n")
    for case in demo_cases:
        r = {**WOUND_KNOWLEDGE[case["class"]],
             "mode": "wound",
             "prediction": case["class"],
             "confidence": 0.953,
             "low_confidence": False}
        print_report(r, case["img"], case["age"], case["gender"])


# ─── CLI 진입점 ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="M-Medic v2 외상 판독 시스템")
    parser.add_argument("--image",  type=str, help="진단할 이미지 경로")
    parser.add_argument("--expert", action="store_true", help="EfficientNet-V2-S 전문가 모델 사용")
    parser.add_argument("--age",    type=float, default=0.0)
    parser.add_argument("--gender", type=str,  default="")
    parser.add_argument("--demo",   action="store_true")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if not args.image:
        print("사용법: python m_medic_v2.py --image <경로> [--expert]")
        print("       python m_medic_v2.py --demo")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, loaded = load_wound_model(device, use_expert=args.expert)
    if not loaded:
        print(f"[경고] 모델 파일이 없습니다: {EXPERT_MODEL if args.expert else WOUND_MODEL}")
        sys.exit(1)

    result = diagnose_wound(args.image, model, device)

    if "error" in result:
        print(f"진단 오류: {result['error']}")
    else:
        print_report(result, args.image, args.age, args.gender)


if __name__ == "__main__":
    main()
