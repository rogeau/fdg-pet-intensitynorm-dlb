#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from pathlib import Path


def main(input_excel, output_prefix="results"):
    # Load Excel
    df = pd.read_excel(input_excel)


    input_path = Path(input_excel)
    out_dir = input_path.parent / "correlations2"
    out_dir.mkdir(parents=True, exist_ok=True)
    df = df.drop(df.columns[[0, 1]], axis=1)
    df = df.drop(columns=["age"])
    df = df.dropna()
    df = df.rename(columns={"cluster": "meta-ROI",
                            "pons": "Pons",
                            "cerebellum": "Cerebellum",
                            "wm": "WM",
                            "ps": "PS",
                            "ips_001": "iPS",
                            "hn": "HN",
                            "ihn_001": "iHN"})
    ordered_cols = [
        "Pons",
        "Cerebellum",
        "WM",
        "PS",
        "iPS",
        "HN",
        "iHN",
        "meta-ROI",
        # add the rest in desired order
    ]
    df = df[[c for c in ordered_cols if c in df.columns]]
    # === 1. Correlation Heatmap ===
    corr = df.corr() ** 2

    plt.figure(figsize=(10, 8))
    plt.rcParams.update({
            "font.size": 14,
            "axes.titlesize": 14,
            "axes.labelsize": 14,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14
        })

    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True, cbar=True)
    # plt.title("R² Heatmap")
    plt.tight_layout()
    plt.savefig(out_dir / f"{output_prefix}_heatmap.png", dpi=300)
    plt.close()

    # === 2. Regression plots (first 7 variables vs cluster) ===
    predictors = [col for col in df.columns if not col.startswith(("cluster", "age"))]
    target = "cluster"

    for col in predictors:
        x = df[col]
        y = df[target]

        # Fit linear regression with statsmodels
        X = sm.add_constant(x)  # add intercept
        model = sm.OLS(y, X).fit()

        r2 = model.rsquared
        pval = model.pvalues[1]  # p-value for slope

        # Scatter + regression line
        plt.figure(figsize=(6, 5))
        sns.regplot(x=x, y=y, ci=95, line_kws={"color": "red"})
        plt.xlabel(f"{col} (SUVR)" if col in ["hn", "ihn"] else f"{col} (SUV)")
        plt.ylabel(f"{target} (SUV)")
        plt.title(f"{col} vs {target}, R² = {r2:.3f}")
        plt.tight_layout()
        plt.savefig(out_dir / f"{output_prefix}_{col}_vs_{target}.png", dpi=300)
        plt.close()

    print("✅ Done. Heatmap and regression plots saved.")

if __name__ == "__main__":
    # Example usage
    # python analysis.py table.xlsx results
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analysis.py <input_excel> [output_prefix]")
        sys.exit(1)

    input_excel = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "results"
    main(input_excel, output_prefix)
