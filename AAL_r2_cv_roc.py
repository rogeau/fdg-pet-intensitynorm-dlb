#!/usr/bin/env python3
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

# --------------------
# Load data
# --------------------
df = pd.read_excel(
    "shoot/correlations/ROI_correlations/aal_values.xlsx"
).iloc[:, 1:].dropna()

df_norm = pd.read_excel(
    "shoot/normalizing_factors.xlsx"
).iloc[:, 2:-1].dropna()

target = "cluster"

# --------------------
# Metrics function
# --------------------
def metrics(data):
    rows = []
    for col in data.columns:
        X = sm.add_constant(data[col])
        y = data[target]
        r2 = sm.OLS(y, X).fit().rsquared
        cv = data[col].std() / data[col].mean()
        rows.append([col, r2, cv])
    return pd.DataFrame(rows, columns=["region", "R2", "CV"])

final_df = pd.concat(
    [metrics(df), metrics(df_norm)],
    ignore_index=True
)

df = pd.read_excel('shoot/normalizing_factors.xlsx', index_col=False)
df_aal = pd.read_excel('shoot/correlations/ROI_correlations/aal_values.xlsx', index_col=False)
df_aal[['IPP', 'Date']] = df_aal['scan_path'].str.split('/', expand=True).iloc[:, 2:4]
df_aal.drop(columns=['scan_path', 'cluster'], inplace=True)
df_aal['Date'] = df_aal['Date'].astype('int64')
df = pd.merge(df, df_aal, on=["IPP", "Date"], how="outer")
df.drop(["age"], axis=1, inplace=True)
df.dropna(inplace=True)
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

# Total number of scans from subjects with ≥2 scans
total_scans_multi = df[df['IPP'].isin(scan_counts[scan_counts >= 2].index)].shape[0]
avg_rate_per_patient = df.groupby('IPP').apply(patient_rate)
overall_avg_rate_per_factor = avg_rate_per_patient.mean(axis=0, skipna=True) * 365.25 * 100
sd_per_factor = avg_rate_per_patient.std(axis=0, skipna=True) * 365.25 * 100

avg_roc_df = overall_avg_rate_per_factor.rename('avg_roc').reset_index().rename(columns={'index': 'region'})
sd_roc_df = sd_per_factor.rename('sd_roc').reset_index().rename(columns={'index': 'region'})

# Merge into final_df
final_df = final_df.merge(avg_roc_df, on='region', how='left')
final_df = final_df.merge(sd_roc_df, on='region', how='left')

idx_to_remove = final_df[final_df["region"] == "cluster"].index[1]
final_df = final_df.drop(idx_to_remove)


final_df["region"] = final_df["region"].replace({
    "pons": "Pons",
    "Cerebellum": "Cerebellum_AAL",
    "cerebellum": "Cerebellum",
    "wm": "WM",
    "ps": "PS",
    "ips_001": "iPS",
    "hn": "HN",
    "ihn_001": "iHN",
    "cluster": "Meta-ROI"
})
print(final_df)

custom_order = {
    "Normalization": ["PS","iPS","HN","iHN","WM"],
    "Frontal": ["Precentral_L","Precentral_R","Frontal_Sup_L","Frontal_Sup_R",
                "Frontal_Sup_Orb_L","Frontal_Sup_Orb_R","Frontal_Mid_L","Frontal_Mid_R",
                "Frontal_Mid_Orb_L","Frontal_Mid_Orb_R","Frontal_Inf_Oper_L",
                "Frontal_Inf_Oper_R","Frontal_Inf_Tri_L","Frontal_Inf_Tri_R",
                "Frontal_Inf_Orb_L","Frontal_Inf_Orb_R","Rolandic_Oper_L",
                "Rolandic_Oper_R","Supp_Motor_Area_L","Supp_Motor_Area_R",
                "Olfactory_L","Olfactory_R","Frontal_Sup_Medial_L",
                "Frontal_Sup_Medial_R","Frontal_Med_Orb_L","Frontal_Med_Orb_R",
                "Rectus_L","Rectus_R"],
    "Parietal": ["Postcentral_L","Postcentral_R","Parietal_Sup_L","Parietal_Sup_R",
                 "Parietal_Inf_L","Parietal_Inf_R","SupraMarginal_L",
                 "SupraMarginal_R","Angular_L","Angular_R","Precuneus_L",
                 "Precuneus_R","Paracentral_Lobule_L","Paracentral_Lobule_R",
                 "Meta-ROI"],
    "Temporal": ["Heschl_L","Heschl_R","Temporal_Sup_L","Temporal_Sup_R",
                 "Temporal_Pole_Sup_L","Temporal_Pole_Sup_R","Temporal_Mid_L",
                 "Temporal_Mid_R","Temporal_Pole_Mid_L","Temporal_Pole_Mid_R",
                 "Temporal_Inf_L","Temporal_Inf_R","Fusiform_L","Fusiform_R"],
    "Limbic": ["Insula_L","Insula_R","Cingulum_Ant_L","Cingulum_Ant_R",
               "Cingulum_Mid_L","Cingulum_Mid_R","Cingulum_Post_L",
               "Cingulum_Post_R","Hippocampus_L","Hippocampus_R",
               "ParaHippocampal_L","ParaHippocampal_R","Amygdala_L", "Amygdala_R"],
    "Occipital": ["Calcarine_L","Calcarine_R","Cuneus_L",
                  "Cuneus_R","Lingual_L","Lingual_R"],
    "Basal ganglia": ["Caudate_L","Caudate_R","Putamen_L",
                                 "Putamen_R","Pallidum_L","Pallidum_R",
                                 "Thalamus_L","Thalamus_R"],
    "Pons, Cerebellum": ["Pons","Cerebellum"],
    "Infratentorial": ["Cerebellum_Crus1_L",
                        "Cerebellum_Crus1_R","Cerebellum_Crus2_L",
                        "Cerebellum_Crus2_R","Cerebellum_3_L",
                        "Cerebellum_3_R","Cerebellum_4_5_L",
                        "Cerebellum_4_5_R","Cerebellum_6_L",
                        "Cerebellum_6_R","Cerebellum_7b_L",
                        "Cerebellum_7b_R","Cerebellum_8_L",
                        "Cerebellum_8_R","Cerebellum_9_L",
                        "Cerebellum_9_R","Cerebellum_10_L",
                        "Cerebellum_10_R","Vermis_1_2","Vermis_3",
                        "Vermis_4_5","Vermis_6","Vermis_7","Vermis_8",
                        "Vermis_9","Vermis_10","Cerebellum_AAL","Vermis",
                        "Whole_Cerebellum"]
}

group_colors = {
    "Normalization": "#000000",
    "Frontal": "#fdc08b",
    "Parietal": "#80ad80",
    "Temporal": "#d68989",
    "Limbic": "#9f8bb3",
    "Occipital": "#93b2d6",
    "Basal ganglia": "#b39792",
    "Pons, Cerebellum": "#000000",
    "Infratentorial": "#e7bedb"
}

# --------------------
# Apply custom order
# --------------------
ordered_regions = [
    r for group in custom_order.values() for r in group
    if r in final_df["region"].values
]

final_df = (
    final_df
    .set_index("region")
    .loc[ordered_regions]
    .reset_index()
)

regions = final_df["region"].values
y = np.arange(len(regions))

# Map region → group → color
region_to_group = {
    r: g for g, regs in custom_order.items() for r in regs
}
colors = [
    group_colors.get(region_to_group.get(r, ""), "#cccccc")
    for r in regions
]

# --------------------
# Plot
# --------------------
fig, (ax_r2, ax_cv, ax_roc) = plt.subplots(
    ncols=3, sharey=True, figsize=(12, 17)
)

for ax in [ax_r2, ax_cv, ax_roc]:
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(False)
    ax.margins(y=0.01)
    ax.tick_params(axis='x', labelsize=11)
    ax.grid(axis='x', linestyle='--', linewidth=0.8, alpha=1)
    ax.tick_params(axis='x', top=True, labeltop=True)


ax_r2.set_xlim(left=0.1)
ax_cv.set_xlim(left=0.1, right=0.33)

ax_r2.tick_params(axis='y', labelsize=10)

bold_labels = ["Pons", "Cerebellum", "WM", "PS", "iPS", "HN", "iHN"]

# --- R² ---
for i, region in enumerate(regions):
    alpha = 1.0
    ax_r2.barh(y[i], final_df["R2"].iloc[i], color=colors[i], alpha=alpha)
    ax_cv.barh(y[i], final_df["CV"].iloc[i], color=colors[i], alpha=alpha)
    ax_roc.scatter(final_df["avg_roc"].iloc[i], y[i], color=colors[i], alpha=alpha)
    ax_roc.hlines(y[i], final_df["avg_roc"].iloc[i] - final_df["sd_roc"].iloc[i], final_df["avg_roc"].iloc[i] + final_df["sd_roc"].iloc[i], color=colors[i], linewidth=1.5, alpha=alpha)
    
ax_r2.set_xlabel("R²", fontsize=12)
ax_r2.set_yticks(y)
ax_r2.set_yticklabels(regions, ha='left')
ax_r2.tick_params(axis='y', pad=108)   # increase padding between labels and axis
ax_r2.invert_yaxis()

# Bold labels
for label in ax_r2.get_yticklabels():
    if label.get_text() in bold_labels:
        label.set_fontweight('bold')
    if label.get_text() == "Meta-ROI":
        label.set_color('blue')


ax_cv.set_xlabel("Coefficients of variation", fontsize=12)
ax_roc.set_xlabel("Annual rates of change (%)", fontsize=12)
ax_roc.axvline(x=0, color='gray', linestyle='--', linewidth=1)

handles = []
for group, color in group_colors.items():
    if group == "Pons, Cerebellum":
        continue  # skip this group
    alpha = 1.0
    patch = mpatches.Patch(color=color, label=group, alpha=alpha)
    handles.append(patch)

# Add legend to the CV plot
ax_cv.legend(
    handles=handles,
    loc='upper right',
    bbox_to_anchor=(1.15, 1),  # slightly outside the axes
    fontsize=12,
    frameon=True
)
fig.tight_layout(pad=1)
fig.savefig("shoot/figure4.png", dpi=500)