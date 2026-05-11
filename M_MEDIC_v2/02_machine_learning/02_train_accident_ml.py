"""
[M-Medic ML Step 2] 해양사고 머신러닝 학습 파이프라인
------------------------------------------------------
목적:
  - 해양사고 정형 데이터(tabular)로 두 가지 과제를 학습
    ① 사상자 발생 여부 이진 분류  (Binary Classification)
    ② 사고 위험등급(4단계) 다중 분류 (Multi-class Classification)
  - RandomForest vs XGBoost 성능 비교
  - Feature Importance 분석으로 "어떤 요소가 사상자를 만드는가" 도출

출력:
  - results/ml_comparison_report.txt   (성능 비교표)
  - results/feature_importance.png     (중요도 차트)
  - results/confusion_matrix.png       (혼동 행렬)
  - results/model_rf_binary.pkl        (저장된 RF 모델)
  - results/model_xgb_binary.pkl       (저장된 XGB 모델)
"""

import os
import pickle
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, accuracy_score
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("[경고] xgboost가 설치되지 않았습니다. RandomForest만 사용합니다.")
    print("  설치 명령: pip install xgboost")

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR    = os.path.join(BASE_DIR, "01_data", "processed")
RESULT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULT_DIR, exist_ok=True)

# ─── 한글 폰트 설정 ───────────────────────────────────────────────────────────
def set_korean_font():
    font_candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            fm.fontManager.addfont(fp)
            plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ─── 1. 데이터 로드 및 전처리 ─────────────────────────────────────────────────
def load_and_preprocess():
    # GICOMS 실제 데이터가 있으면 우선 사용, 없으면 생성 데이터 사용
    gicoms_candidates = [
        os.path.join(BASE_DIR, "..", "data", "Marine_Accidents", "gicoms_accidents.csv"),
        os.path.join(BASE_DIR, "..", "data", "Marine_Accidents", "marine_accidents_full.csv"),
    ]
    csv_path = os.path.join(PROC_DIR, "marine_accidents_augmented.csv")

    for cand in gicoms_candidates:
        if os.path.exists(cand):
            print(f"[GICOMS 실제 데이터 감지] {cand}")
            print("  → 실제 통계 데이터로 ML 학습을 진행합니다.")
            csv_path = cand
            break
    else:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"데이터 파일이 없습니다. 먼저 01_generate_accident_data.py를 실행하세요.\n{csv_path}"
            )
        print(f"[생성 데이터 사용] GICOMS 실제 데이터 미확보 → 합성 데이터로 학습")
        print(f"  GICOMS 다운로드 후 아래 경로에 저장하면 자동 감지됩니다:")
        print(f"  {gicoms_candidates[0]}\n")

    df = pd.read_csv(csv_path)
    print(f"데이터 로드: {len(df):,}건\n")

    # 범주형 변수 인코딩
    feature_cols  = ['연도', '사고유형', '선박종류', '사고원인', '발생해역']
    target_binary = '사상자발생'
    target_multi  = '위험등급'

    encoders = {}
    df_enc = df[feature_cols + [target_binary, target_multi]].copy()
    df_enc[target_multi] = df_enc[target_multi].astype(str)

    for col in ['사고유형', '선박종류', '사고원인', '발생해역']:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
        encoders[col] = le

    le_target = LabelEncoder()
    df_enc[target_multi] = le_target.fit_transform(df_enc[target_multi])
    encoders['위험등급'] = le_target

    X = df_enc[feature_cols].values
    y_binary = df_enc[target_binary].values
    y_multi  = df_enc[target_multi].values

    return X, y_binary, y_multi, feature_cols, encoders, le_target

# ─── 2. 모델 학습 및 교차 검증 ────────────────────────────────────────────────
def train_and_evaluate(X, y, feature_names, task_name="binary"):
    print(f"\n{'='*50}")
    print(f"과제: {task_name}")
    print(f"{'='*50}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=8,
            class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            random_state=42
        ),
    }
    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            use_label_encoder=False, eval_metric="mlogloss",
            random_state=42
        )

    results = {}
    best_model_name = None
    best_f1 = 0.0

    for name, model in models.items():
        print(f"\n[{name}] 학습 중...")
        # 인코딩 오류 방지를 위해 n_jobs=1 설정
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, 
                                    scoring="f1_weighted", n_jobs=1)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1  = f1_score(y_test, y_pred, average="weighted")
        report = classification_report(y_test, y_pred)

        print(f"  CV F1 (5-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"  Test Accuracy : {acc:.4f}")
        print(f"  Test F1       : {f1:.4f}")
        print(report)

        results[name] = {
            "model": model, "y_test": y_test, "y_pred": y_pred,
            "acc": acc, "f1": f1, "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(), "report": report
        }

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name

    print(f"\n[최고 성능 모델]: {best_model_name} (F1={best_f1:.4f})")
    return results, best_model_name

# ─── 3. 시각화 ────────────────────────────────────────────────────────────────
def plot_feature_importance(models_results, feature_names, task_label):
    fig, axes = plt.subplots(1, len(models_results), figsize=(6 * len(models_results), 6))
    if len(models_results) == 1:
        axes = [axes]

    for ax, (name, res) in zip(axes, models_results.items()):
        model = res["model"]
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            ax.barh(
                [feature_names[i] for i in indices],
                importances[indices],
                color=sns.color_palette("viridis", len(feature_names))
            )
            ax.set_title(f"{name}\nFeature Importance ({task_label})")
            ax.set_xlabel("중요도")
            ax.invert_yaxis()

    plt.tight_layout()
    path = os.path.join(RESULT_DIR, f"feature_importance_{task_label}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> 저장: {path}")


def plot_confusion_matrix(y_test, y_pred, labels, title, fname):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels, yticklabels=labels, ax=ax
    )
    ax.set_title(title, fontsize=13)
    ax.set_ylabel("실제 값")
    ax.set_xlabel("예측 값")
    plt.tight_layout()
    path = os.path.join(RESULT_DIR, fname)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> 저장: {path}")


def plot_model_comparison(results_binary, results_multi):
    names  = list(results_binary.keys())
    f1_bin = [results_binary[n]["f1"] for n in names]
    f1_mul = [results_multi[n]["f1"]  for n in names if n in results_multi]

    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width/2, f1_bin, width, label="이진분류 (사상자발생여부)", color="#2196F3")
    bars2 = ax.bar(x + width/2, f1_mul, width, label="다중분류 (위험등급4단계)", color="#FF7043")

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("F1-Score (Weighted)")
    ax.set_title("모델별 성능 비교 (해양사고 예측)")
    ax.legend()
    ax.bar_label(bars1, fmt="%.3f", padding=3)
    ax.bar_label(bars2, fmt="%.3f", padding=3)
    plt.tight_layout()
    path = os.path.join(RESULT_DIR, "model_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  -> 저장: {path}")

# ─── 4. 결과 보고서 저장 ──────────────────────────────────────────────────────
def save_report(results_binary, results_multi, best_bin, best_mul):
    lines = [
        "=" * 65,
        "  M-Medic 해양사고 머신러닝 성능 비교 보고서",
        "=" * 65,
        "",
        "[ 과제 1: 사상자 발생 여부 이진 분류 ]",
        f"{'모델':<22} {'CV F1':>10} {'Test F1':>10} {'Accuracy':>10}",
        "-" * 55,
    ]
    for name, res in results_binary.items():
        lines.append(
            f"{name:<22} {res['cv_mean']:>10.4f} {res['f1']:>10.4f} {res['acc']:>10.4f}"
        )
    lines += ["", f"  ★ 최고 모델: {best_bin}", ""]

    lines += [
        "[ 과제 2: 사고 위험등급(4단계) 다중 분류 ]",
        f"{'모델':<22} {'CV F1':>10} {'Test F1':>10} {'Accuracy':>10}",
        "-" * 55,
    ]
    for name, res in results_multi.items():
        lines.append(
            f"{name:<22} {res['cv_mean']:>10.4f} {res['f1']:>10.4f} {res['acc']:>10.4f}"
        )
    lines += ["", f"  ★ 최고 모델: {best_mul}", ""]

    lines += [
        "=" * 65,
        "[ 도메인 해석 가이드 ]",
        "  - Feature Importance 1위가 '사고유형'이면:",
        "    -> 화재/침몰 사고를 조기 감지하는 IoT 센서가 핵심 투자처",
        "  - '선박종류'가 1위이면:",
        "    -> 어선 집중 모니터링 정책이 유효함을 의미",
        "  - '발생해역'이 상위이면:",
        "    -> 남해/서해 특정 해역에 대한 감시망 강화 필요",
        "=" * 65,
    ]

    report_path = os.path.join(RESULT_DIR, "ml_comparison_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  -> 성능 보고서 저장: {report_path}")

# ─── 5. 메인 실행 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[M-Medic] 해양사고 머신러닝 파이프라인 시작\n")

    X, y_binary, y_multi, features, encoders, le_target = load_and_preprocess()

    # 이진 분류 학습
    print("\n[과제 1] 사상자 발생 여부 이진 분류")
    results_bin, best_bin = train_and_evaluate(
        X, y_binary, features, task_name="이진분류 (사상자발생여부)"
    )

    # 다중 분류 학습
    print("\n[과제 2] 사고 위험등급 다중 분류")
    results_mul, best_mul = train_and_evaluate(
        X, y_multi, features, task_name="다중분류 (위험등급 4단계)"
    )

    # 시각화
    print("\n[시각화] 차트 생성 중...")
    plot_feature_importance(results_bin, features, "binary")
    plot_feature_importance(results_mul, features, "multiclass")
    plot_model_comparison(results_bin, results_mul)

    best_bin_model = results_bin[best_bin]
    plot_confusion_matrix(
        best_bin_model["y_test"], best_bin_model["y_pred"],
        labels=["사상자없음", "사상자발생"],
        title=f"혼동 행렬 - 이진분류 ({best_bin})",
        fname="confusion_matrix_binary.png"
    )

    best_mul_model = results_mul[best_mul]
    grade_labels = le_target.inverse_transform(sorted(np.unique(y_multi)))
    plot_confusion_matrix(
        best_mul_model["y_test"], best_mul_model["y_pred"],
        labels=grade_labels,
        title=f"혼동 행렬 - 위험등급 ({best_mul})",
        fname="confusion_matrix_multiclass.png"
    )

    # 모델 저장
    for name, res in results_bin.items():
        pkl_path = os.path.join(RESULT_DIR, f"model_{name.lower()}_binary.pkl")
        with open(pkl_path, "wb") as f:
            pickle.dump(res["model"], f)
        print(f"  -> 모델 저장: {pkl_path}")

    # 리포트
    save_report(results_bin, results_mul, best_bin, best_mul)
    print("\n[M-Medic] ML 파이프라인 완료!")
