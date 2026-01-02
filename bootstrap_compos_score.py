import numpy as np
import pandas as pd

def compute_composc(df):
    # Drop "age" if exists
    df = df.drop(["age"], axis=1, errors="ignore")

    # Merge AAL data
    file_path_aal = "shoot/correlations/ROI_correlations/aal_values.xlsx"
    df_aal = pd.read_excel(file_path_aal)
    df_aal[['IPP', 'Date']] = df_aal['scan_path'].str.split('/', expand=True).iloc[:, 2:4]
    df_aal.drop(columns=['scan_path', 'cluster', 'Pallidum_L', 'Pallidum_R'], inplace=True)
    df_aal['Date'] = df_aal['Date'].astype('int64')

    df = pd.merge(df, df_aal, on=["IPP", "Date"], how="outer")

    subset = df[df['ips_001'].isna() | df['ihn_001'].isna()]
    non_subset = df.drop(subset.index)
    cols = df.columns[2:]

    diffs, r2s, cv = {}, {}, {}

    for col in cols:
        mean_non_subset = non_subset[col].mean(skipna=True)
        subset_col = 'ps' if col.startswith('ips') else 'hn' if col.startswith('ihn') else col
        mean_subset = subset[subset_col].mean(skipna=True) if subset_col in df.columns else np.nan

        diffs[col] = abs((mean_non_subset - mean_subset) / mean_subset * 100) if pd.notna(mean_subset) and mean_subset != 0 else np.nan
        r = df[[col, 'cluster']].dropna().corr().iloc[0, 1]
        r2s[col] = r ** 2
        col_values = non_subset[col].dropna()
        cv[col] = col_values.std() / col_values.mean() if col_values.mean() != 0 else np.nan

    # Normalize by first scan per patient
    df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d', errors='coerce')
    df = df.sort_values(['IPP', 'Date'])
    numeric_cols = [c for c in df.columns if c not in ['IPP', 'Date', 'cluster']]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df[numeric_cols] = df.groupby('IPP')[numeric_cols].transform(lambda x: x / x.iloc[0])

    def patient_rate(group):
        if len(group) < 2:
            return pd.Series({col: pd.NA for col in numeric_cols})
        delta_days = group['Date'].diff().dt.days
        rate = group[numeric_cols].diff().div(delta_days, axis=0)
        return rate.mean(skipna=True)

    avg_rate_per_patient = df.groupby('IPP').apply(patient_rate).dropna(how='all')
    roc = (abs(avg_rate_per_patient.mean(axis=0, skipna=True)) * 365.25 * 100).to_dict()

    composc_df = pd.DataFrame({
        'average_diff': pd.Series(diffs),
        'R_squared': pd.Series(r2s),
        'cv': pd.Series(cv),
        'roc': pd.Series(roc)
    }).dropna()

    composc_df = composc_df.apply(lambda x: (x - x.mean()) / x.std())
    composc_df = composc_df * -1
    composc_df['compos_sc'] = composc_df[['average_diff', 'R_squared', 'cv', 'roc']].sum(axis=1)
    return composc_df


# # === BOOTSTRAP ===
# n_boot = 10
# boot_results = []

# file_path = "shoot/normalizing_factors.xlsx"
# df_full = pd.read_excel(file_path)

# ipps = df_full['IPP'].unique()

# for b in range(n_boot):
#     sampled_ipps = np.random.choice(ipps, size=len(ipps), replace=True)
#     df_boot = df_full[df_full['IPP'].isin(sampled_ipps)].copy()
#     res = compute_composc(df_boot)
#     boot_results.append(res['compos_sc'])

# # Combine into a single DataFrame
# boot_df = pd.concat(boot_results, axis=1)
# boot_df.columns = [f"boot_{i+1}" for i in range(n_boot)]

# # Compute summary statistics
# summary_df = pd.DataFrame({
#     "mean": boot_df.mean(axis=1),
#     "std": boot_df.std(axis=1),
#     "ci_lower": boot_df.quantile(0.025, axis=1),
#     "ci_upper": boot_df.quantile(0.975, axis=1),
# })
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
# print(summary_df.sort_values("mean", ascending=False))


# === BOOTSTRAP ===
n_boot = 1000
boot_results = []

file_path = "shoot/normalizing_factors.xlsx"
df_full = pd.read_excel(file_path)

# Separate subjects based on ips_001 availability
ipps_with_ips = df_full.loc[df_full['ips_001'].notna(), 'IPP'].unique()
ipps_without_ips = df_full.loc[df_full['ips_001'].isna(), 'IPP'].unique()

# Fixed subset: subjects without ips_001 (always kept as-is)
df_fixed = df_full[df_full['IPP'].isin(ipps_without_ips)].copy()

for b in range(n_boot):
    # Bootstrap only the IPPs with valid ips_001
    sampled_ipps = np.random.choice(ipps_with_ips, size=len(ipps_with_ips), replace=True)
    df_boot = df_full[df_full['IPP'].isin(sampled_ipps)].copy()
    
    # Combine bootstrapped patients with fixed patients
    df_boot = pd.concat([df_boot, df_fixed], ignore_index=True)
    
    # Optional: reset index to keep clean
    df_boot.reset_index(drop=True, inplace=True)
    
    # Compute composite metrics
    res = compute_composc(df_boot)
    boot_results.append(res['compos_sc'])

# Combine into a single DataFrame
boot_df = pd.concat(boot_results, axis=1)
boot_df.columns = [f"boot_{i+1}" for i in range(n_boot)]

# Compute summary statistics
summary_df = pd.DataFrame({
    "mean": boot_df.mean(axis=1),
    "std": boot_df.std(axis=1),
    "ci_lower": boot_df.quantile(0.025, axis=1),
    "ci_upper": boot_df.quantile(0.975, axis=1),
})

# Display full table
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(summary_df.sort_values("mean", ascending=False))
