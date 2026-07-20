#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_cv(normalizing_factors, output_prefix="results"):
    df = pd.read_excel(normalizing_factors)
    df = df.drop(['IPP', 'Date', 'age', 'cluster'], axis=1)
    df = df.dropna(axis=0)

    cv_values = {}
    for col in df.columns:
        cv_values[col] = df[col].std() / df[col].mean()

    cv_df = pd.DataFrame(list(cv_values.items()), columns=["Region", "CV"])

    rename_dict = {
            "ps": "PS",
            "pons": "Pons",
            "wm": "WM",
            "hn": "HN",
            "ips_001": "iPS",
            "ihn_001": "iHN",
            "cerebellum": "Cerebellum"
        }

    order = [
    "Pons",
    "Cerebellum",
    "WM",
    "PS",
    "iPS",
    "HN",
    "iHN"
    ]

    cv_df["Region"] = cv_df["Region"].replace(rename_dict)
    cv_df["Region"] = pd.Categorical(cv_df["Region"], categories=order, ordered=True)
    cv_df = cv_df.sort_values("Region")

    print(cv_df)

    # --- Plot ---
    plt.figure(figsize=(5, 6))
    x = np.arange(len(cv_df))
    width = 0.7

    # Colors: pale blue for normalized, deep blue for original
    plt.bar(x, cv_df["CV"], width=width, label="Original", color="#000000")   # deep blue
    
    # X ticks
    ax = plt.gca()
    ax.set_xticks(x)
    ax.set_xticklabels(
        cv_df["Region"],
        fontsize=16,
        rotation=45,
        ha="right",
        rotation_mode="anchor")

    # Formatting
    plt.xlim(-1, len(cv_df))
    plt.ylabel("Coefficient of Variation", fontsize = 16)
    plt.yticks(fontsize=16)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.title("CV of Scaling Factors", fontsize = 16)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_cv_comparison_barplot.png", dpi=300)
    plt.close()

    print(f"✅ Done. CV comparison bar chart saved to {output_prefix}_cv_comparison_barplot.png")
    return cv_df

# Example usage:
cv_df = plot_cv("shoot/normalizing_factors.xlsx", "shoot/correlations/ROI_correlations/eccn")