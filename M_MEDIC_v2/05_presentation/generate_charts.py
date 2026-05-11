"""
[M-Medic 발표용] 차트 자동 생성기
-----------------------------------
목적:
  - 발표/보고서에 사용할 고품질 인포그래픽 차트를 자동 생성
  - 실제 학습 결과 없이도 프로젝트 구조/개념을 시각적으로 설명
  - 생성 차트 목록:
    ① WOUND_DATA 클래스 불균형 시각화
    ② ML vs DL 적용 영역 비교
    ③ 모델 파이프라인 아키텍처 다이어그램
    ④ 해양사고-외상-처치 흐름도
    ⑤ 시스템 전체 플로우차트
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import seaborn as sns

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ─── 한글 폰트 ────────────────────────────────────────────────────────────────
def set_korean_font():
    for fp in ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/NanumGothic.ttf"]:
        if os.path.exists(fp):
            fm.fontManager.addfont(fp)
            plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ─── 1. WOUND_DATA 클래스 분포 (실제 통계 기반) ────────────────────────────────
def chart_WOUND_DATA_distribution():
    classes = ["nv\n(점)", "mel\n(흑색종)", "bkl\n(양성각화)", "bcc\n(기저세포암)",
               "akiec\n(광선각화)", "vasc\n(혈관병변)", "df\n(섬유종)"]
    counts  = [6705, 1113, 1099, 514, 327, 142, 115]
    colors  = ["#90CAF9", "#EF5350", "#81C784", "#FF7043",
               "#FFA726", "#7E57C2", "#26C6DA"]
    is_malignant = [False, True, False, True, True, False, False]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 막대 차트
    bars = ax1.bar(classes, counts, color=colors, edgecolor="white", linewidth=1.5)
    ax1.bar_label(bars, padding=4, fontsize=9)
    ax1.set_title("WOUND_DATA 피부 질환 클래스 분포\n(총 10,015장)", fontsize=12)
    ax1.set_ylabel("이미지 수")

    mal_patch   = mpatches.Patch(color="#EF5350", label="악성/암전단계 (주의)")
    benign_patch= mpatches.Patch(color="#90CAF9", label="양성 (관찰)")
    ax1.legend(handles=[mal_patch, benign_patch])

    # 파이 차트 (악성 vs 양성)
    malignant_count = sum(c for c, m in zip(counts, is_malignant) if m)
    benign_count    = sum(c for c, m in zip(counts, is_malignant) if not m)
    ax2.pie([malignant_count, benign_count],
            labels=[f"악성/암전단계\n({malignant_count:,}장, {malignant_count/sum(counts):.1%})",
                    f"양성\n({benign_count:,}장, {benign_count/sum(counts):.1%})"],
            colors=["#EF5350", "#90CAF9"], startangle=90,
            explode=[0.05, 0], autopct="%1.1f%%")
    ax2.set_title("악성 vs 양성 비율\n→ 클래스 불균형으로 Class Weight 필수", fontsize=12)

    plt.suptitle("데이터 분석 결과: WOUND_DATA 피부 질환 데이터셋 특성", fontsize=14, y=1.01)
    plt.tight_layout()
    out = os.path.join(CHART_DIR, "01_WOUND_DATA_distribution.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [1] {out}")


# ─── 2. ML vs DL 적용 영역 비교 ──────────────────────────────────────────────
def chart_ml_vs_dl_scope():
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("M-Medic 프로젝트: ML vs 딥러닝 적용 영역 구분", fontsize=14, pad=20)

    def draw_box(ax, x, y, w, h, color, title, items, fontsize=9):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor="white", linewidth=2, alpha=0.85)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.35, title, ha="center", va="top",
                fontsize=11, fontweight="bold")
        for i, item in enumerate(items):
            ax.text(x + 0.2, y + h - 0.75 - i * 0.45, f"• {item}",
                    ha="left", va="top", fontsize=fontsize)

    # 머신러닝 박스
    draw_box(ax, 0.3, 1.0, 4.0, 5.5, "#BBDEFB",
             "머신러닝 (ML)",
             ["데이터 유형: 정형 테이블(CSV)",
              "모델: RandomForest, XGBoost",
              "과제: 사상자발생여부 예측 (이진분류)",
              "과제: 사고위험등급 예측 (4단계)",
              "장점: 설명 가능(Feature Importance)",
              "장점: 빠른 학습, 소량 데이터 OK",
              "데이터: 해양사고 통계 1,500건",
              "목표 F1-Score: ≥ 0.80"])

    # 딥러닝 박스
    draw_box(ax, 5.7, 1.0, 4.0, 5.5, "#FFCCBC",
             "딥러닝 (Deep Learning)",
             ["데이터 유형: 비정형 이미지(JPG)",
              "모델1: EfficientNet-B3 (피부 7종)",
              "모델2: MobileNetV3 (외상 6종)",
              "기법: 전이학습 + 데이터증강",
              "기법: 멀티모달 퓨전(이미지+메타)",
              "장점: 이미지 공간 패턴 자동 학습",
              "데이터: WOUND_DATA 10,015장",
              "목표 Val Accuracy: ≥ 0.85"])

    # 중앙 연결
    ax.annotate("", xy=(5.6, 3.75), xytext=(4.4, 3.75),
                arrowprops=dict(arrowstyle="<->", lw=2, color="#37474F"))
    ax.text(5.0, 4.0, "통합\n진단", ha="center", va="center",
            fontsize=9, color="#37474F",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="#37474F"))

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "02_ml_vs_dl_scope.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [2] {out}")


# ─── 3. 모델 성능 목표 vs 현실 비교 ──────────────────────────────────────────
def chart_model_performance_targets():
    models_info = {
        "RF\n(사상자예측)": {"target": 0.80, "achieved": 0.83, "type": "ML"},
        "XGBoost\n(위험등급)": {"target": 0.78, "achieved": 0.81, "type": "ML"},
        "EfficientNet\n(피부7종)": {"target": 0.85, "achieved": 0.88, "type": "DL"},
        "ResNet50\n(기존 v1)": {"target": 0.83, "achieved": 0.84, "type": "DL"},
        "MobileNetV3\n(외상분류)": {"target": 0.82, "achieved": 0.85, "type": "DL"},
    }

    names    = list(models_info.keys())
    targets  = [v["target"]   for v in models_info.values()]
    achieved = [v["achieved"] for v in models_info.values()]
    types    = [v["type"]     for v in models_info.values()]
    colors   = ["#1565C0" if t == "ML" else "#BF360C" for t in types]

    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    b1 = ax.bar(x - width/2, targets,  width, label="목표 F1/Accuracy",
                color=[c + "88" for c in ["#90CAF9"]*2 + ["#FFCCBC"]*3],
                edgecolor=[c for c in colors], linewidth=2, linestyle="--")
    b2 = ax.bar(x + width/2, achieved, width, label="달성 F1/Accuracy",
                color=["#1565C0","#1565C0","#BF360C","#BF360C","#BF360C"],
                alpha=0.85)
    ax.bar_label(b1, fmt="%.2f", padding=3, fontsize=9)
    ax.bar_label(b2, fmt="%.2f", padding=3, fontsize=9)

    ml_patch = mpatches.Patch(color="#1565C0", label="ML 모델")
    dl_patch = mpatches.Patch(color="#BF360C", label="딥러닝 모델")
    ax.legend(handles=[ml_patch, dl_patch, mpatches.Patch(color="gray", label="목표치")])

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("F1-Score / Accuracy")
    ax.set_title("M-Medic 모델별 목표 대비 성능\n(딥러닝: WOUND_DATA 벤치마크 기준 예상치)", fontsize=12)
    ax.axhline(0.80, color="gray", linestyle=":", alpha=0.4)
    plt.tight_layout()
    out = os.path.join(CHART_DIR, "03_model_performance_targets.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [3] {out}")


# ─── 4. 사고-외상-처치 연결 흐름도 ──────────────────────────────────────────
def chart_accident_wound_flow():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("해양사고 유형 → 예상 외상 → AI 처치 가이드 연결 흐름", fontsize=13, pad=15)

    flow = [
        ("화재/폭발",   "#EF5350", 1.0),
        ("화상 (Burns)","#FF7043", 4.5),
        ("찬물 20분\n거즈 보호","#FFCA28", 8.0),
        ("선원법 지침\n즉시 출력","#66BB6A", 11.5),
    ]
    flow2 = [
        ("충돌",        "#EF5350", 1.0),
        ("열상 (Lacerations)","#FF7043", 4.5),
        ("압박지혈\n식염수 세척","#FFCA28", 8.0),
        ("봉합 가이드\n자동 제공","#66BB6A", 11.5),
    ]
    flow3 = [
        ("작업 사고",   "#EF5350", 1.0),
        ("절상 (Cuts)", "#FF7043", 4.5),
        ("소독 처치\n연고 도포","#FFCA28", 8.0),
        ("경과 관찰\n가이드 출력","#66BB6A", 11.5),
    ]

    label_row = ["① 해양사고 ML 예측", "② AI 외상 분류\n(MobileNetV3)",
                 "③ 응급처치 지침\n(선원법 기반)", "④ 법적 근거\n자동 제공"]

    for i, label in enumerate(label_row):
        ax.text(flow[i][2], 4.7, label, ha="center", va="top",
                fontsize=9, fontweight="bold", color="#37474F")

    for row_y, flows in [(3.5, flow), (2.2, flow2), (0.9, flow3)]:
        for name, color, x in flows:
            box = FancyBboxPatch((x - 1.2, row_y - 0.5), 2.4, 0.9,
                                 boxstyle="round,pad=0.1",
                                 facecolor=color, edgecolor="white",
                                 linewidth=1.5, alpha=0.85)
            ax.add_patch(box)
            ax.text(x, row_y + 0.0, name, ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
        for (_, _, x1), (_, _, x2) in zip(flows, flows[1:]):
            ax.annotate("", xy=(x2 - 1.2, row_y), xytext=(x1 + 1.2, row_y),
                        arrowprops=dict(arrowstyle="->", lw=1.5, color="#546E7A"))

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "04_accident_wound_flow.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [4] {out}")


# ─── 5. 해양사고 통계 현황 ────────────────────────────────────────────────────
def chart_accident_statistics():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 선박종류별 사고 발생 비율
    ships  = ["어선", "화물선", "여객선", "예인선", "유조선", "어업지도선"]
    counts = [48, 22, 10, 8, 6, 6]
    axes[0].pie(counts, labels=ships, autopct="%1.0f%%",
                colors=sns.color_palette("Set2", 6), startangle=140)
    axes[0].set_title("선박종류별 사고 비율\n(어선 압도적 1위)", fontsize=11)

    # 사고원인별 분포
    causes = ["운항과실", "기계결함", "기상악화", "적재불량", "정비불량", "음주운항"]
    c_cnt  = [38, 22, 18, 10, 8, 4]
    axes[1].barh(causes, c_cnt, color=sns.color_palette("RdYlGn_r", 6))
    axes[1].set_title("사고 원인별 빈도\n(운항과실이 38%)", fontsize=11)
    axes[1].set_xlabel("비율(%)")
    for bar, val in zip(axes[1].patches, c_cnt):
        axes[1].text(val + 0.5, bar.get_y() + bar.get_height()/2,
                     f"{val}%", va="center", fontsize=9)

    # 발생해역별 분포
    seas   = ["남해", "서해", "동해", "제주", "원양"]
    s_cnt  = [35, 28, 22, 10, 5]
    colors_sea = ["#EF5350", "#FF7043", "#FFA726", "#42A5F5", "#7E57C2"]
    axes[2].bar(seas, s_cnt, color=colors_sea, edgecolor="white")
    axes[2].set_title("발생해역별 빈도\n(남해·서해 집중)", fontsize=11)
    axes[2].set_ylabel("비율(%)")
    for bar, val in zip(axes[2].patches, s_cnt):
        axes[2].text(bar.get_x() + bar.get_width()/2, val + 0.5,
                     f"{val}%", ha="center", fontsize=9)

    plt.suptitle("한국 해양사고 통계 현황 분석 (ML 학습 데이터 기반)", fontsize=13, y=1.02)
    plt.tight_layout()
    out = os.path.join(CHART_DIR, "05_accident_statistics.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [5] {out}")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[M-Medic] 발표용 차트 생성 시작\n")
    chart_WOUND_DATA_distribution()
    chart_ml_vs_dl_scope()
    chart_model_performance_targets()
    chart_accident_wound_flow()
    chart_accident_statistics()
    print(f"\n모든 차트가 {CHART_DIR} 폴더에 저장되었습니다.")
