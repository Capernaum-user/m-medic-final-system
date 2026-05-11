# -*- coding: utf-8 -*-
"""
공유 폴더용 발표차트 재생성
HAM10000 / WOUND_DATA / 피부질환 내용을 완전 제거하고
실제 프로젝트(외상 6종 + 해양사고 ML) 기반으로 재작성
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

CHART_DIR = r"D:\GeminiUniverse\vscode-workspace\wip-maritime-medic\MDTS_팀공유_260423\05_문서\발표차트"
os.makedirs(CHART_DIR, exist_ok=True)

# ── 차트 02: ML vs DL 역할 구분 ─────────────────────────────────────────────
def chart_ml_vs_dl():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("M-MEDIC v2 — ML과 DL의 역할 분담", fontsize=15, fontweight='bold', y=1.01)

    # ML 파이
    ax1 = axes[0]
    ml_labels = ['충돌·전복', '화재·폭발', '침수·좌초', '기상악화', '기타']
    ml_sizes  = [36, 22, 18, 14, 10]
    colors1   = ['#2196F3', '#FF5722', '#4CAF50', '#FF9800', '#9C27B0']
    wedges, texts, autotexts = ax1.pie(
        ml_sizes, labels=ml_labels, autopct='%1.0f%%',
        colors=colors1, startangle=90, pctdistance=0.75
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax1.set_title("ML — 해양사고 유형 분포\n(학습 데이터: 합성 1,504건)", fontsize=11)

    # DL 바차트
    ax2 = axes[1]
    dl_classes = ['Abrasions\n(찰과상)', 'Bruises\n(타박상)', 'Burns\n(화상)',
                  'Cut\n(절창)', 'Laceration\n(열창)', 'Stab_wound\n(자창)']
    dl_counts  = [668, 972, 504, 600, 732, 736]
    risk_colors = ['#4CAF50', '#4CAF50', '#F44336', '#FF9800', '#F44336', '#B71C1C']
    bars = ax2.bar(dl_classes, dl_counts, color=risk_colors, edgecolor='white', linewidth=0.5)
    for bar, cnt in zip(bars, dl_counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                 str(cnt), ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax2.set_title("DL — 외상 클래스별 이미지 수\n(학습 데이터: 4,212장)", fontsize=11)
    ax2.set_ylabel("이미지 수 (장)")
    ax2.set_ylim(0, 1100)

    legend = [
        mpatches.Patch(color='#B71C1C', label='CRITICAL'),
        mpatches.Patch(color='#F44336', label='HIGH'),
        mpatches.Patch(color='#FF9800', label='MEDIUM'),
        mpatches.Patch(color='#4CAF50', label='LOW'),
    ]
    ax2.legend(handles=legend, loc='upper right', fontsize=8)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "02_ml_vs_dl_scope.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [생성] 02_ml_vs_dl_scope.png")


# ── 차트 03: 모델 성능 달성 현황 ────────────────────────────────────────────
def chart_model_performance():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("M-MEDIC v2 — 모델 성능 목표 대비 달성 결과", fontsize=15, fontweight='bold')

    # DL 성능 (클래스별 F1)
    ax1 = axes[0]
    classes  = ['Abrasions', 'Bruises', 'Burns', 'Cut', 'Laceration', 'Stab_wound']
    f1_scores = [1.00, 1.00, 0.99, 1.00, 1.00, 1.00]
    bar_colors = ['#4CAF50' if f == 1.0 else '#FF9800' for f in f1_scores]
    bars = ax1.barh(classes, f1_scores, color=bar_colors, edgecolor='white')
    ax1.axvline(x=0.95, color='red', linestyle='--', linewidth=1.5, label='목표 95%')
    for bar, f in zip(bars, f1_scores):
        ax1.text(bar.get_width() - 0.005, bar.get_y() + bar.get_height()/2,
                 f'{f:.2f}', ha='right', va='center', fontsize=10, fontweight='bold', color='white')
    ax1.set_xlim(0.90, 1.01)
    ax1.set_title("DL 외상 분류 — 클래스별 F1 Score\n(MobileNetV3 Large, 검증셋 843장)", fontsize=11)
    ax1.set_xlabel("F1 Score")
    ax1.legend(fontsize=9)

    # ML 성능 (이진/다중)
    ax2 = axes[1]
    models_ml  = ['RandomForest\n(이진분류)', 'GradientBoosting\n(이진분류)',
                  'RandomForest\n(다중분류)', 'GradientBoosting\n(다중분류)']
    f1_ml      = [0.762, 0.754, 0.626, 0.632]
    colors_ml  = ['#2196F3', '#1565C0', '#4CAF50', '#2E7D32']
    bars2 = ax2.bar(models_ml, f1_ml, color=colors_ml, edgecolor='white')
    ax2.axhline(y=0.70, color='red', linestyle='--', linewidth=1.5, label='목표 F1=0.70')
    for bar, f in zip(bars2, f1_ml):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f'{f:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 0.85)
    ax2.set_title("ML 해양사고 예측 — 모델별 F1 Score\n(5-Fold CV, 합성 데이터 1,504건)", fontsize=11)
    ax2.set_ylabel("F1 Score (macro)")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "03_model_performance_targets.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [생성] 03_model_performance_targets.png")


# ── 실행 ─────────────────────────────────────────────────────────────────────
print("발표차트 재생성 시작 (HAM10000 제거 버전)")
chart_ml_vs_dl()
chart_model_performance()
print("완료: 02, 03번 차트 재생성")
