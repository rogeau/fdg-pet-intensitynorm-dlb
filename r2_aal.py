# #!/usr/bin/env python3
# import pandas as pd
# import statsmodels.api as sm
# import matplotlib.pyplot as plt
# import numpy as np


# def plot_r2(aal, normalizing_factors, output_prefix="results"):
#     df = pd.read_excel(aal).dropna()
#     df = df.drop(df.columns[0], axis=1)  # drop first column (ID column)
    

#     df_norm = pd.read_excel(normalizing_factors).dropna()
#     df_norm = df_norm.drop(df_norm.columns[:2], axis=1)  # drop first 2 cols (ID + cluster?)

#     target = "cluster"
#     predictors = [col for col in df.columns if not col.startswith(("cluster", "age"))]
    

#     # Original R²
#     r2_values = {}
#     for col in predictors:
#         x = df[col]
#         y = df[target]
#         X = sm.add_constant(x)
#         model = sm.OLS(y, X).fit()
#         r2_values[col] = model.rsquared

#     r2_df = pd.DataFrame(list(r2_values.items()), columns=["Region", "R²"])
#     r2_df = r2_df.sort_values("R²", ascending=True)

#     # Normalized R² (only for regions present in both)
#     r2_values_norm = {}
#     for col in df_norm.columns:
#         if col != target and col in df_norm.columns:  # ensure names align
#             x = df_norm[col]
#             y = df[target]
#             X = sm.add_constant(x)
#             model = sm.OLS(y, X).fit()
#             r2_values_norm[col] = model.rsquared

#     r2_norm_df = pd.DataFrame(list(r2_values_norm.items()), columns=["Region", "R²_norm"])
#     merged_df = pd.merge(r2_df, r2_norm_df, on="Region", how="outer")
#     print(merged_df)
#     merged_df = merged_df.assign(
#     sort_key = merged_df[["R²", "R²_norm"]].min(axis=1, skipna=True)
#     )
#     merged_df = merged_df.sort_values("sort_key", ascending=True).drop(columns="sort_key")

    
#     # Plot both sets side by side
#     plt.figure(figsize=(20, 6))
#     x = np.arange(len(merged_df))
#     width = 0.65
#     plt.bar(x, merged_df["R²"], width=width, label="Original", color="#94bedb")
#     plt.bar(x, merged_df["R²_norm"], width=width, label="Normalized", color="#034296")

#     # Set x-ticks (no global bold)
#     ax = plt.gca()
#     ax.set_xticks(x)
#     ax.set_xticklabels(merged_df["Region"], rotation=90)

#     # Bold only those tick labels corresponding to regions that have a normalized R²
#     has_norm = merged_df["R²_norm"].notna().values
#     for lbl, bold in zip(ax.get_xticklabels(), has_norm):
#         lbl.set_fontweight("bold" if bold else "normal")

#     # Axis formatting
#     plt.xlim(-1, len(merged_df))
#     plt.ylabel("R²")
#     plt.title("R² values of each AAL region or normalizing approach vs. cluster")
#     ax.spines['top'].set_visible(False)
#     ax.spines['right'].set_visible(False)

#     plt.tight_layout()
#     plt.savefig(f"{output_prefix}_r2_comparison_barplot.png", dpi=300)
#     plt.close()

#     print(f"✅ Done. Comparison bar chart saved to {output_prefix}_r2_comparison_barplot.png")
#     return merged_df

# # Example usage:
# r2_df = plot_r2("shoot/correlations/ROI_correlations/aal_values.xlsx",
#                 "shoot/normalizing_factors.xlsx",
#                   "shoot/correlations/ROI_correlations/aal")


#!/usr/bin/env python3
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np


def plot_r2(aal, normalizing_factors, output_prefix="results"):
    target = "cluster"

    # --- AAL regions: drop rows with missing data, drop the scan_path id col ---
    df = pd.read_excel(aal).dropna().reset_index(drop=True)
    df = df.drop(columns=[df.columns[0]])  # scan_path

    # --- Normalizing factors: take the first N rows so they line up
    #     positionally with the cleaned AAL rows, then drop id/meta cols ---
    n = len(df)
    df_norm = pd.read_excel(normalizing_factors).head(n).reset_index(drop=True)
    df_norm = df_norm.drop(columns=list(df_norm.columns[:2]))  # IPP + Date

    # target comes from the AAL file for both sets of regressions
    y = pd.to_numeric(df[target], errors="coerce")

    predictors = [c for c in df.columns if not c.startswith(("cluster", "age"))]
    norm_cols = [c for c in df_norm.columns if not c.startswith(("cluster", "age"))]

    def r2_for(series):
        x = pd.to_numeric(series, errors="coerce")
        mask = x.notna() & y.notna()
        if mask.sum() < 3:
            return None
        X = sm.add_constant(x[mask])
        return sm.OLS(y[mask], X).fit().rsquared

    # --- Original R2 (per AAL region) ---
    r2_values = {c: r for c in predictors if (r := r2_for(df[c])) is not None}
    r2_df = pd.DataFrame(r2_values.items(), columns=["Region", "R²"])

    # --- Normalized R2 (per normalizing approach) ---
    r2_values_norm = {c: r for c in norm_cols if (r := r2_for(df_norm[c])) is not None}
    r2_norm_df = pd.DataFrame(r2_values_norm.items(), columns=["Region", "R²_norm"])

    # --- Combine + sort ---
    merged_df = pd.merge(r2_df, r2_norm_df, on="Region", how="outer")
    print(merged_df)
    merged_df = merged_df.assign(
        sort_key=merged_df[["R²", "R²_norm"]].min(axis=1, skipna=True)
    ).sort_values("sort_key", ascending=True).drop(columns="sort_key")

    # --- 15 regions with the lowest R² (across AAL and normalizing factors) ---
    lowest15 = merged_df.head(15).reset_index(drop=True)
    print("\n15 lowest-R² regions (Original AAL R² and Normalized R²):")
    print(lowest15.to_string(index=False))

    # --- Plot ---
    plt.figure(figsize=(20, 6))
    x = np.arange(len(merged_df))
    width = 0.65
    plt.bar(x, merged_df["R²"], width=width, label="Original", color="#94bedb")
    plt.bar(x, merged_df["R²_norm"], width=width, label="Normalized", color="#034296")

    ax = plt.gca()
    ax.set_xticks(x)
    ax.set_xticklabels(merged_df["Region"], rotation=90)

    has_norm = merged_df["R²_norm"].notna().values
    for lbl, bold in zip(ax.get_xticklabels(), has_norm):
        lbl.set_fontweight("bold" if bold else "normal")

    plt.xlim(-1, len(merged_df))
    plt.ylabel("R²")
    plt.title("R² values of each AAL region or normalizing approach vs. cluster")
    plt.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_r2_comparison_barplot.png", dpi=300)
    plt.close()

    print(f"Done. Comparison bar chart saved to {output_prefix}_r2_comparison_barplot.png")
    return merged_df


# Example usage:
r2_df = plot_r2("shoot/correlations/ROI_correlations/aal_values.xlsx",
                "shoot/normalizing_factors.xlsx",
                "shoot/correlations/ROI_correlations/aal")