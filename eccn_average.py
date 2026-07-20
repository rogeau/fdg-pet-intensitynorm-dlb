import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator

file_path = "shoot/normalizing_factors.xlsx"
df = pd.read_excel(file_path)

# --- Define groups based on 'cluster' column ---
dlb_group = df[df['cluster'].notna()]
hc_group  = df[df['cluster'].isna()]

def plot_histograms_and_qq(column_name, bins=20, save_dir="shoot/eccn_averages"):
    os.makedirs(save_dir, exist_ok=True)

    # --- Select DLB / reference (HC/PS/HN) depending on prefix ---
    if column_name.startswith("ips"):
        # DLB values from ips_* column, HC values from ps column but only HC rows
        data_dlb = dlb_group.get(column_name, pd.Series(dtype=float)).dropna()
        data_hc  = hc_group.get("ps", pd.Series(dtype=float)).dropna()

    elif column_name.startswith("ihn"):
        # DLB values from ihn_* column, HC values from hn column but only HC rows
        data_dlb = dlb_group.get(column_name, pd.Series(dtype=float)).dropna()
        data_hc  = hc_group.get("hn", pd.Series(dtype=float)).dropna()

    else:
        # Default: compare same column for DLB vs HC
        data_dlb = dlb_group.get(column_name, pd.Series(dtype=float)).dropna()
        data_hc  = hc_group.get(column_name, pd.Series(dtype=float)).dropna()


    # Guard against empty groups
    if data_dlb.empty or data_hc.empty:
        print(f"⚠️ Skipping {column_name}: len(dlb)={len(data_dlb)}, len({hc_label})={len(data_hc)}")
        return

    mean_dlb = data_dlb.mean()
    mean_hc  = data_hc.mean()

    # Use shared bin edges for fair comparison
    combined = np.concatenate([data_dlb.values, data_hc.values])
    bin_edges = np.histogram_bin_edges(combined, bins=bins)

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    color_dlb = "#4d65a7"
    color_hc  = "#e0af0d"

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=20)
    ax.xaxis.set_major_locator(MaxNLocator(7))
    ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.minorticks_off()

    # weights so each group's bars sum to 100%
    weights_dlb = np.ones(len(data_dlb)) / len(data_dlb) * 100
    weights_hc  = np.ones(len(data_hc))  / len(data_hc)  * 100

    ax.hist(data_dlb, bins=bin_edges, alpha=0.6,
                 weights=weights_dlb,
                 label=f'DLB (mean={mean_dlb:.2f})', color=color_dlb)
    ax.hist(data_hc, bins=bin_edges, alpha=0.6,
                 weights=weights_hc,
                 label=f'HC (mean={mean_hc:.2f})', color=color_hc)

    # mean lines
    ax.axvline(mean_dlb, color=color_dlb, linestyle='--', linewidth=2)
    ax.axvline(mean_hc,  color=color_hc,  linestyle='--', linewidth=2)

    # xlabel choice
    # if column_name.startswith(("ihn", "hn")):
    #     axes[0].set_xlabel("SUVR")
    # else:
    #     axes[0].set_xlabel("SUV")

    # axes[0].set_ylabel("Percentage (%)")
    # axes[0].set_title(f"Histogram: {column_name}")

    outpath = os.path.join(save_dir, f"{column_name}.png")
    fig.subplots_adjust(
    left=0.08,
    right=0.98,
    bottom=0.08,
    top=0.98,
    wspace=0.08)

    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"Saved: {outpath}")

# --- Example usage ---
print(df.columns)
for factor in df.columns[2:-2]:
    plot_histograms_and_qq(factor)