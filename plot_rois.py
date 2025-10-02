import matplotlib.pyplot as plt
import pandas as pd
import os

def extract_region_values(excel_path, region):
    file = pd.ExcelFile(excel_path)
    fallback_region = "rGM" if region.startswith("rindividual_mask") else None

    # First try to find the exact region in any sheet
    for sheet_name in file.sheet_names:
        df = file.parse(sheet_name)
        if region in df.columns:
            return df[region].dropna()

    # If not found, try fallback if applicable
    if fallback_region:
        for sheet_name in file.sheet_names:
            df = file.parse(sheet_name)
            if fallback_region in df.columns:
                print(f"⚠️ '{region}' not found in '{excel_path}'. Falling back to '{fallback_region}' in sheet '{sheet_name}'.")
                return df[fallback_region].dropna()

    print(f"❌ Neither '{region}' nor fallback found in any sheet of '{excel_path}'.")
    return pd.Series(dtype=float)

def plot_region_histogram(excel_files, region, unit, save_path):
    plt.figure(figsize=(10, 6))

    for excel_path in excel_files:
        values = extract_region_values(excel_path, region)
        if values.empty:
            continue

        label = excel_path.split("/")[-1].split(".")[0]  # Filename as label
        mean_value = values.mean()

        _, _, patches = plt.hist(values, bins=25, alpha=0.5, label=f"{label} (mean={mean_value:.2f})")
        color = patches[0].get_facecolor()
        plt.axvline(mean_value, linestyle='dashed', linewidth=1.5, color=color)

    plt.title(f"{region}", fontweight='bold')
    plt.xlabel(f"{unit}")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.savefig(save_path, dpi=300)
    plt.show()

def main():
    # === USER SETTINGS ===
    region_to_plot = "Right_putamen"   # Enter region name here
    unit_label = "SUVR"                # Y-axis units or ROI units

    # Input files
    excel_file_1 = "coreg_center_mass_reorient/results_roi/pons_r_petsuv_DLB.xlsx"
    excel_file_2 = "coreg_center_mass_reorient/results_roi/pons_r_petsuv_HC.xlsx"

    # Output filename auto-generated from region name
    region_clean = region_to_plot.replace(" ", "").lower()
    save_path = os.path.join(
        "coreg_center_mass_reorient/results_roi",
        f"pons_r_petsuv_{region_clean}.png"
    )

    # Call plotting function
    plot_region_histogram([excel_file_1, excel_file_2], region_to_plot, unit_label, save_path)

if __name__ == "__main__":
    main()