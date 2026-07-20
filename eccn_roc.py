import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_excel('shoot/normalizing_factors.xlsx', index_col=False)
df.drop(["age", "cluster"], axis=1, inplace=True)
df.dropna(inplace=True)
df = df.rename(columns={"pons": "Pons", "cerebellum": "Cerebellum", "wm": "WM", "ps": "PS", "ips_001": "iPS", "hn": "HN", "ihn_001": "iHN"})
df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d')
df = df.sort_values(['IPP', 'Date'])
numeric_cols = [c for c in df.columns if c not in ['IPP', 'Date']]
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df[numeric_cols] = df.groupby('IPP')[numeric_cols].transform(lambda x: x / x.iloc[0])


def patient_rate(group):
    if len(group) < 2:
        return pd.Series({col: pd.NA for col in numeric_cols})
    delta_days = group['Date'].diff().dt.days
    rate = group[numeric_cols].diff().div(delta_days, axis=0)
    return rate.mean(skipna=True)


scan_counts = df.groupby('IPP')['Date'].nunique()

# Basic patient stats
n_total = df['IPP'].nunique()
n_multi_scan = (scan_counts >= 2).sum()

# --- Compute ALL consecutive intervals across all patients ---
all_intervals = (
    df.groupby('IPP')['Date']
      .apply(lambda x: x.sort_values().diff().dt.days.dropna())
      .explode()              # flatten all intervals into one Series
      .astype(float)
)

# Now compute global stats
avg_interval_days = all_intervals.mean()
max_interval_days = all_intervals.max()
min_interval_days = all_intervals.min()
std_interval_days = all_intervals.std()

# Total number of scans from subjects with ≥2 scans
total_scans_multi = df[df['IPP'].isin(scan_counts[scan_counts >= 2].index)].shape[0]

# Print summary
print(f"Total patients: {n_total}")
print(f"Patients with ≥2 scans: {n_multi_scan}")
print(f"Average interval between scans (global): {avg_interval_days:.1f} days")
print(f"Maximum interval between scans (global): {max_interval_days:.1f} days")
print(f"Minimum interval between scans (global): {min_interval_days:.1f} days")
print(f"Standard deviation of intervals between scans (global): {std_interval_days:.1f} days")
print(f"Total number of scans from subjects with ≥2 scans: {total_scans_multi}")

avg_rate_per_patient = df.groupby('IPP').apply(patient_rate)
overall_avg_rate_per_factor = avg_rate_per_patient.mean(axis=0, skipna=True) * 365.25 * 100
sd_per_factor = avg_rate_per_patient.std(axis=0, skipna=True) * 365.25 * 100

# print(overall_avg_rate_per_factor[['pons', 'cerebellum', 'wm', 'ps', 'ips_001', 'hn', 'ihn_001']])
# print(sd_per_factor[['pons', 'cerebellum', 'wm', 'ps', 'ips_001', 'hn', 'ihn_001']])



fig, ax = plt.subplots(figsize=(5,6))

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

region_order = ["Pons","Cerebellum","WM","PS","iPS","HN","iHN"]

overall_avg_rate_per_factor = overall_avg_rate_per_factor.reindex(region_order)
sd_per_factor = sd_per_factor.reindex(region_order)

regions = overall_avg_rate_per_factor.index.tolist()
x_positions = np.arange(len(regions))

# scatter points
ax.scatter(
    x_positions,
    overall_avg_rate_per_factor.values,
    color="black",
    zorder=3,
    s=40
)

# error bars
for i, region in enumerate(regions):
    ax.vlines(
        x_positions[i],
        overall_avg_rate_per_factor[region] - sd_per_factor[region],
        overall_avg_rate_per_factor[region] + sd_per_factor[region],
        color="black",
        linewidth=1.5,
        alpha=0.6
    )

# zero line
ax.axhline(0, color='black', linewidth=0.8)

# labels
ax.set_ylabel('Annual rate of change (%)', fontsize = 16)
ax.set_title('Mean ± SD of annual rate of change per region', fontsize = 16)

# x axis
ax.set_xticks(x_positions)
ax.set_xticklabels(regions, fontsize=16,
        rotation=45,
        ha="right",
        rotation_mode="anchor")

ax.margins(x=0.01)
ax.tick_params(axis='x', which='major', pad=3, labelsize = 16)
ax.tick_params(axis='y', labelsize=16)

ax.set_xlim(min(x_positions) - 1, max(x_positions) + 1)
ax.set_ylim(-19, 11)

# bold specific regions
bold_regions = ['ps','pons','wm','hn','ips_001','ihn_001','cerebellum','cluster']

for t in ax.get_xticklabels():
    if t.get_text() in bold_regions:
        t.set_fontweight('bold')

plt.tight_layout()

plt.savefig("shoot/rate_change/eccn_roc.png", dpi=300)