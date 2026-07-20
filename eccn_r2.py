#!/usr/bin/env python3
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

def plot_r2(normalizing_factors, output_prefix="results"):
    df_norm = pd.read_excel(normalizing_factors)
    df_norm = df_norm.drop(['IPP', 'Date', 'age'], axis=1)
    df_norm = df_norm.dropna(axis=0)

    target = "cluster"
    r2_values_norm = {}
    for col in df_norm.columns:
        if col != target and col in df_norm.columns:  # ensure names align
            x = df_norm[col]
            y = df_norm[target]
            X = sm.add_constant(x)
            model = sm.OLS(y, X).fit()
            r2_values_norm[col] = model.rsquared

    r2_norm_df = pd.DataFrame(list(r2_values_norm.items()), columns=["Region", "R²_norm"])

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

    r2_norm_df["Region"] = r2_norm_df["Region"].replace(rename_dict)
    r2_norm_df["Region"] = pd.Categorical(r2_norm_df["Region"], categories=order, ordered=True)
    r2_norm_df = r2_norm_df.sort_values("Region")
    

    print(r2_norm_df)

    # Plot both sets side by side
    plt.figure(figsize=(5, 6))
    width = 0.7
    plt.bar(r2_norm_df["Region"], r2_norm_df["R²_norm"], width=width, label="Normalized", color="#000000")

    # Set x-ticks (no global bold)
    ax = plt.gca()
    ax.set_xticklabels(r2_norm_df["Region"],
        fontsize=16,
        rotation=45,
        ha="right",
        rotation_mode="anchor")

    # Axis formatting
    plt.xlim(-1, len(r2_norm_df))
    plt.ylabel("R²", fontsize = 16)
    plt.yticks(fontsize=16)
    plt.title("R² values of Scaling Factors with DLB meta-ROI", fontsize = 16)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_r2_comparison_barplot.png", dpi=300)
    plt.close()

    print(f"✅ Done. Comparison bar chart saved to {output_prefix}_r2_comparison_barplot.png")
    return r2_norm_df

# Example usage:
r2_df = plot_r2("shoot/normalizing_factors.xlsx", "shoot/correlations/ROI_correlations/eccn")
