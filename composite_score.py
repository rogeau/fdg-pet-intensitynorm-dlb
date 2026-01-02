import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

file_path = "shoot/normalizing_factors.xlsx"
df = pd.read_excel(file_path)
df = df.drop(["age"], axis=1)

file_path_aal = "shoot/correlations/ROI_correlations/aal_values.xlsx"
df_aal = pd.read_excel(file_path_aal)
df_aal[['IPP', 'Date']] = df_aal['scan_path'].str.split('/', expand=True).iloc[:, 2:4]
df_aal.drop(columns=['scan_path', 'cluster', 'Pallidum_L', 'Pallidum_R'], inplace=True)
df_aal['Date'] = df_aal['Date'].astype('int64')
df = pd.merge(df, df_aal, on=["IPP", "Date"], how="outer")

subset = df[df['ips_001'].isna() | df['ihn_001'].isna()]
non_subset = df.drop(subset.index)

cols = df.columns[2:]

diffs = {}
r2s = {}
cv = {}
roc = {}

for col in cols:
    mean_non_subset = non_subset[col].mean(skipna=True)
    
    # Use ps/hn for subset if column starts with ips/ihn
    if col.startswith('ips'):
        subset_col = 'ps'
    elif col.startswith('ihn'):
        subset_col = 'hn'
    else:
        subset_col = col

    # Safely compute mean for subset
    if subset_col not in df.columns:
        mean_subset = np.nan
    else:
        mean_subset = subset[subset_col].mean(skipna=True)

    # Percent difference
    if pd.notna(mean_subset) and mean_subset != 0:
        percent_diff = abs((mean_non_subset - mean_subset) / mean_subset * 100)
    else:
        percent_diff = np.nan

    diffs[col] = percent_diff


    r = df[[col, 'cluster']].dropna().corr().iloc[0, 1]
    r2 = r**2
    r2s[col] = r2
    col_values = non_subset[col].dropna()
    if col_values.mean() != 0:
        cv[col] = col_values.std() / col_values.mean()
    else:
        cv[col] = np.nan


df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d')
df = df.sort_values(['IPP', 'Date'])
numeric_cols = [c for c in df.columns if c not in ['IPP', 'Date', 'cluster']]
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

# --- Normalize by first scan per patient ---
df[numeric_cols] = df.groupby('IPP')[numeric_cols].transform(lambda x: x / x.iloc[0])

def patient_rate(group):
    if len(group) < 2:
        return pd.Series({col: pd.NA for col in numeric_cols})
    delta_days = group['Date'].diff().dt.days
    rate = group[numeric_cols].diff().div(delta_days, axis=0)
    return rate.mean(skipna=True)

avg_rate_per_patient = df.groupby('IPP').apply(patient_rate)
avg_rate_per_patient = avg_rate_per_patient.dropna(how='all')
overall_avg_rate_per_factor = abs(avg_rate_per_patient.mean(axis=0, skipna=True) * 365.25 * 100)
roc = overall_avg_rate_per_factor.to_dict()


# Convert to DataFrame
composc_df = pd.DataFrame({
    'average_diff': pd.Series(diffs),
    'R_squared': pd.Series(r2s),
    'cv': pd.Series(cv),
    'roc': pd.Series(roc)
})

composc_df = composc_df.dropna()
composc_df = composc_df.apply(lambda x: (x - x.mean()) / x.std())
composc_df = composc_df * -1
# Suppose you want to sum 'col1', 'col2', 'col3'
composc_df['compos_sc'] = composc_df[['average_diff', 'R_squared', 'cv', 'roc']].sum(axis=1)

composc_df = composc_df.sort_values(by=['compos_sc'], ascending=False)


# Show full table
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

print(composc_df)



# Define subset to show in legend
legend_rows = ['pons', 'cerebellum', 'wm', 'ps', 'ips_001', 'hn', 'ihn_001']

legend_label_map = {
    'pons': 'Pons',
    'cerebellum': 'Cerebellum',
    'wm': 'WM',
    'ps': 'PS',
    'ips_001': 'iPS',
    'hn': 'HN',
    'ihn_001': 'iHN'
}


# Define specific colors for each row
color_map = {
    'pons': "#e65400",
    'wm': "#ddce00",         
    'cerebellum': "#2dc000", 
    'ps': "#18d8c8",          
    'ips_001': "#525AD4",      
    'hn': "#db6edf",           
    'ihn_001': "#D4007C",     
}

# Extract subset for rotation reference
df_plot = composc_df.loc[legend_rows]

categories = composc_df.columns
N = len(categories)

# Mapping from short names to full names
label_map = {
    'cv': 'Interindividual stability',
    'compos_sc': 'Composite score',
    'roc': 'Temporal stability',
    'R_squared': 'Disease independence',
    'average_diff': 'Normative alignment',
}

categories_pretty = [label_map.get(c, c) for c in categories]

# Compute angles
angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
top_category = 'compos_sc'
top_index = list(categories).index(top_category)

# Rotate so top_category is vertical
angles = np.roll(angles, -top_index)
rotation_offset = np.pi / 2 - angles[0]
angles = (angles + rotation_offset) % (2 * np.pi)
angles_closed = np.concatenate((angles, [angles[0]]))

# Create radar plot
fig, ax = plt.subplots(figsize=(14, 10), subplot_kw=dict(polar=True))
plt.rcParams.update({
    "font.size": 14
})
ax.spines['polar'].set_visible(False)

# Plot every row
# First: plot background rows (not part of legend)
for i, row in composc_df.iterrows():
    if i not in legend_rows:
        values = np.roll(row.values, -top_index)
        values_closed = np.concatenate((values, [values[0]]))
        ax.plot(angles_closed, values_closed, color='gray', alpha=0.35, lw=1)

for i in legend_rows:
    row = composc_df.loc[i]
    values = np.roll(row.values, -top_index)
    values_closed = np.concatenate((values, [values[0]]))
    ax.plot(
        angles_closed,
        values_closed,
        lw=4,
        alpha=0.7,
        color=color_map[i],
        label=legend_label_map[i]
    )

# Axis labels
ax.set_xticks(angles)
ax.tick_params(pad=27)  # default is ~5
ax.set_xticklabels(np.roll(categories_pretty, -top_index), fontsize=14)
# ax.set_yticklabels([])
# ax.set_yticks([-1, 0, 1, 2])
# ax.set_yticklabels(['-1', '0', '1', '2'], fontsize=12)
# ax.tick_params(axis='y', labelsize=14)
# ax.set_rlabel_position(18)

# for label in ax.get_yticklabels():
#     label.set_fontweight('bold')

# # --- Radial scale ---
ax.set_ylim(-7.5, 8)
ax.set_yticks([-6, -3, 0, 3, 6])
# ax.set_yticklabels(['-6', '-3', '0', '3', '6'])

# # --- Grid (curvatures) ---
# ax.yaxis.grid(True)
# ax.xaxis.grid(True)

# # --- Label styling ---
# ax.tick_params(axis='y', labelsize=14)
# ax.set_rlabel_position(18)

# for label in ax.get_yticklabels():
#     label.set_fontweight('bold')
ax.set_yticklabels([])
ax.yaxis.grid(True)
r_ticks = [-6, -3, 0, 3, 6]

import matplotlib.transforms as transforms

theta = np.deg2rad(18)

# vertical shift in points (positive = upward on the screen)
dy = 8  # adjust to taste

for r in r_ticks:
    trans = transforms.offset_copy(
        ax.transData, fig=ax.figure, x=0, y=dy, units='points'
    )

    ax.text(
        theta, r, f"{r}",
        transform=trans,
        ha='center',
        va='center',
        fontsize=14,
        fontweight='bold',
        zorder=1_000_000,
        bbox=dict(facecolor='none', edgecolor='none', alpha=0.)
    )



# Legend only for selected subset
# ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
import matplotlib.lines as mlines

# Dummy entry for gray background lines
aal_patch = mlines.Line2D([], [], color='gray', alpha=0.35, lw=3, label='AAL regions')

# Add it to existing legend entries
handles, labels = ax.get_legend_handles_labels()
handles.append(aal_patch)
labels.append("AAL regions")

ax.legend(handles, labels, loc='upper right', bbox_to_anchor=(1.3, 1.1))

plt.savefig('shoot/composite_score2/radar_plot.png', bbox_inches='tight', dpi=300)
plt.show()
