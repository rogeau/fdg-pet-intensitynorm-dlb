import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

# Print summary
print(f"Total patients: {n_total}")
print(f"Patients with ≥2 scans: {n_multi_scan}")
print(f"Average interval between scans (global): {avg_interval_days:.1f} days")
print(f"Maximum interval between scans (global): {max_interval_days:.1f} days")
print(f"Minimum interval between scans (global): {min_interval_days:.1f} days")
print(f"Total number of scans from subjects with ≥2 scans: {total_scans_multi}")



avg_rate_per_patient = df.groupby('IPP').apply(patient_rate)
overall_avg_rate_per_factor = avg_rate_per_patient.mean(axis=0, skipna=True) * 365.25 * 100
sd_per_factor = avg_rate_per_patient.std(axis=0, skipna=True) * 365.25 * 100

print(overall_avg_rate_per_factor[['pons', 'cerebellum', 'wm', 'ps', 'ips_001', 'hn', 'ihn_001', 'cluster', 'Cerebellum_10_L', 'Cerebellum_10_R']])
print(sd_per_factor[['pons', 'cerebellum', 'wm', 'ps', 'ips_001', 'hn', 'ihn_001', 'cluster','Cerebellum_10_L', 'Cerebellum_10_R']])

custom_order = {
    "Global": ["ps","ips_001","hn","ihn_001","wm"],
    "Frontal": ["Precentral_L","Precentral_R","Frontal_Sup_L","Frontal_Sup_R","Frontal_Sup_Orb_L","Frontal_Sup_Orb_R","Frontal_Mid_L","Frontal_Mid_R","Frontal_Mid_Orb_L","Frontal_Mid_Orb_R","Frontal_Inf_Oper_L","Frontal_Inf_Oper_R","Frontal_Inf_Tri_L","Frontal_Inf_Tri_R","Frontal_Inf_Orb_L","Frontal_Inf_Orb_R","Rolandic_Oper_L","Rolandic_Oper_R","Supp_Motor_Area_L","Supp_Motor_Area_R","Olfactory_L","Olfactory_R","Frontal_Sup_Medial_L","Frontal_Sup_Medial_R","Frontal_Med_Orb_L","Frontal_Med_Orb_R","Rectus_L","Rectus_R"],
    "Parietal": ["Postcentral_L","Postcentral_R","Parietal_Sup_L","Parietal_Sup_R","Parietal_Inf_L","Parietal_Inf_R","SupraMarginal_L","SupraMarginal_R","Angular_L","Angular_R","Precuneus_L","Precuneus_R","Paracentral_Lobule_L","Paracentral_Lobule_R","cluster"],
    "Temporal": ["Heschl_L","Heschl_R","Temporal_Sup_L","Temporal_Sup_R","Temporal_Pole_Sup_L","Temporal_Pole_Sup_R","Temporal_Mid_L","Temporal_Mid_R","Temporal_Pole_Mid_L","Temporal_Pole_Mid_R","Temporal_Inf_L","Temporal_Inf_R","Fusiform_L","Fusiform_R"],
    "Limbic": ["Insula_L","Insula_R","Cingulum_Ant_L","Cingulum_Ant_R","Cingulum_Mid_L","Cingulum_Mid_R","Cingulum_Post_L","Cingulum_Post_R","Hippocampus_L","Hippocampus_R","ParaHippocampal_L","ParaHippocampal_R","Amygdala_L","Amygdala_R","Calcarine_L","Calcarine_R","Cuneus_L","Cuneus_R","Lingual_L","Lingual_R"],
    "Subcortical_BasalGanglia": ["Caudate_L","Caudate_R","Putamen_L","Putamen_R","Pallidum_L","Pallidum_R","Thalamus_L","Thalamus_R"],
    "Infratentorial": ["pons","cerebellum","Cerebellum_Crus1_L","Cerebellum_Crus1_R","Cerebellum_Crus2_L","Cerebellum_Crus2_R","Cerebellum_3_L","Cerebellum_3_R","Cerebellum_4_5_L","Cerebellum_4_5_R","Cerebellum_6_L","Cerebellum_6_R","Cerebellum_7b_L","Cerebellum_7b_R","Cerebellum_8_L","Cerebellum_8_R","Cerebellum_9_L","Cerebellum_9_R","Cerebellum_10_L","Cerebellum_10_R","Vermis_1_2","Vermis_3","Vermis_4_5","Vermis_6","Vermis_7","Vermis_8","Vermis_9","Vermis_10","Cerebellum","Vermis","Whole_Cerebellum"]
}

group_colors = {
    "Global": "#1f77b4",
    "Frontal": "#ff7f0e",
    "Parietal": "#2ca02c",
    "Temporal": "#d62728",
    "Limbic": "#9467bd",
    "Subcortical_BasalGanglia": "#8c564b",
    "Infratentorial": "#e377c2"
}

fig, ax = plt.subplots(figsize=(20,6))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

x_positions, x_labels, current_x = [], [], 0

for group_name, regions in custom_order.items():
    regions = [r for r in regions if r in overall_avg_rate_per_factor.index]
    n = len(regions)
    x_group = np.arange(current_x, current_x + n)
    ax.scatter(x_group, overall_avg_rate_per_factor[regions], color=group_colors[group_name], zorder=3, s=40, label=group_name)
    for i, region in enumerate(regions):
        ax.vlines(x_group[i],
                  overall_avg_rate_per_factor[region] - sd_per_factor[region],
                  overall_avg_rate_per_factor[region] + sd_per_factor[region],
                  color=group_colors[group_name], linewidth=1.5, alpha=0.6)
    x_positions.extend(x_group)
    x_labels.extend(regions)
    current_x += n

ax.axhline(0, color='black', linewidth=0.8)
ax.set_ylabel('Annual rate of change (%)')
ax.set_title('Mean ± SD of annual rate of change per region (grouped by anatomical subgroup)')
ax.set_xticks(x_positions)
ax.set_xticklabels(x_labels, rotation=90, ha='center')

ax.margins(x=0.01)
ax.tick_params(axis='x', which='major', pad=3)
ax.set_xlim(min(x_positions) - 2, max(x_positions) + 2)
ax.set_ylim(-19, 11)

bold_regions = ['ps','pons','wm','hn','ips_001','ihn_001','cerebellum','cluster']
for t in ax.get_xticklabels():
    if t.get_text() in bold_regions:
        t.set_fontweight('bold')

handles, labels = ax.get_legend_handles_labels()

plt.tight_layout()
plt.savefig(f"shoot/rate_change/rate_change_barplot.png", dpi=300)