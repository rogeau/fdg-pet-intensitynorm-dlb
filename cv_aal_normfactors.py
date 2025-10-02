#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_cv(aal, normalizing_factors, output_prefix="results"):
    df = pd.read_excel(aal).dropna()
    df = df.drop(df.columns[0], axis=1)  # drop first column (ID column)

    df_norm = pd.read_excel(normalizing_factors).dropna()
    df_norm = df_norm.drop(df_norm.columns[:2], axis=1)  # drop first 2 cols (ID + cluster?)

    target = "cluster"
    predictors = [col for col in df.columns if col != target]

    # --- Original CV ---
    cv_values = {}
    for col in predictors:
        cv_values[col] = df[col].std() / df[col].mean()

    cv_df = pd.DataFrame(list(cv_values.items()), columns=["Region", "CV"])

    # --- Normalized CV (for all regions available in df_norm) ---
    cv_values_norm = {}
    for col in df_norm.columns:
        if col != target:
            cv_values_norm[col] = df_norm[col].std() / df_norm[col].mean()

    cv_norm_df = pd.DataFrame(list(cv_values_norm.items()), columns=["Region", "CV_norm"])

    # --- Merge both sets ---
    merged_df = pd.merge(cv_df, cv_norm_df, on="Region", how="outer")

    # Sort by whichever is available (min of CV or CV_norm)
    merged_df = merged_df.assign(
        sort_key=merged_df[["CV", "CV_norm"]].min(axis=1, skipna=True)
    )
    merged_df = merged_df.sort_values("sort_key", ascending=True).drop(columns="sort_key")

    # --- Plot ---
    plt.figure(figsize=(20, 6))
    x = np.arange(len(merged_df))
    width = 0.65

    # Colors: pale blue for normalized, deep blue for original
    plt.bar(x, merged_df["CV"], width=width, label="Original", color="#94bedb")   # deep blue
    plt.bar(x, merged_df["CV_norm"], width=width, label="Normalized", color="#034296")  # pale blue

    # X ticks
    ax = plt.gca()
    ax.set_xticks(x)
    ax.set_xticklabels(merged_df["Region"], rotation=90)

    # Bold ticks where normalized exists
    has_norm = merged_df["CV_norm"].notna().values
    for lbl, bold in zip(ax.get_xticklabels(), has_norm):
        lbl.set_fontweight("bold" if bold else "normal")

    # Formatting
    plt.xlim(-1, len(merged_df))
    plt.ylabel("Coefficient of Variation")
    plt.title("Coefficients of variation per AAL region and normalizing approach")
    plt.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_cv_comparison_barplot.png", dpi=300)
    plt.close()

    print(f"✅ Done. CV comparison bar chart saved to {output_prefix}_cv_comparison_barplot.png")
    return merged_df


# Example usage:
cv_df = plot_cv("shoot/correlations/ROI_correlations/aal_values.xlsx",
                "shoot/normalizing_factors.xlsx",
                "shoot/correlations/ROI_correlations/aal")