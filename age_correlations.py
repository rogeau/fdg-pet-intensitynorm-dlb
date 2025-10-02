#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy import stats

def main(input_excel, output_prefix="results"):
    # Load Excel
    df = pd.read_excel(input_excel)
    df = df.drop(df.columns[[0, 1]], axis=1)
    df = df[df['cluster'].isna()]

    predictors = [col for col in df.columns if not col.startswith(("ips", "ihn", "cluster", "age"))]
    target = "age"

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
        plt.ylabel(f"{target}")
        plt.title(f"{col} vs {target}, R² = {r2:.3f}")
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_{col}_vs_{target}.png", dpi=300)
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
