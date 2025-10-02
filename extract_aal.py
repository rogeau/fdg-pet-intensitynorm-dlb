import os
import json
import nibabel as nib
import numpy as np
import pandas as pd

def compute_averages(root_dir, aal_json_path, output_xlsx="aal_pet_values.xlsx"):
    # Load AAL region labels
    with open(aal_json_path, "r") as f:
        aal_dict = json.load(f)

    region_names = list(aal_dict.values())
    results = []
    aal_path = "r_aal.nii"
    aal_img = nib.load(aal_path).get_fdata().astype(int)

    # Precompute indices for new meta-regions
    cerebellum_indices = [int(k) for k, v in aal_dict.items() if v.startswith("Cerebellum")]
    vermis_indices = [int(k) for k, v in aal_dict.items() if v.startswith("Vermis")]
    whole_cereb_indices = cerebellum_indices + vermis_indices

    # Walk through all nested directories for wr_petsuv.nii
    for dirpath, _, filenames in os.walk(root_dir):
        if "wr_petsuv.nii" in filenames:
            pet_path = os.path.join(dirpath, "wr_petsuv.nii")
            gm_path = os.path.join(dirpath, "mri", "wp1mri.nii")
            wm_path = os.path.join(dirpath, "mri", "wp2mri.nii")

            if not (os.path.exists(aal_path) and os.path.exists(gm_path) and os.path.exists(wm_path)):
                print(f"Skipping {pet_path}, missing one of AAL/GM/WM files")
                continue

            pet_img = nib.load(pet_path).get_fdata()
            gm_img = nib.load(gm_path).get_fdata()
            wm_img = nib.load(wm_path).get_fdata()

            gm_mask = gm_img > 0.7
            wm_mask = wm_img > 0.7

            scan_result = {"scan_path": pet_path}

            # Iterate over each AAL region
            for idx, region_name in aal_dict.items():
                idx = int(idx)
                region_mask = aal_img == idx

                if region_name.startswith("Vermis") or region_name.startswith("Cerebellum"):
                    mask = region_mask & (gm_mask | wm_mask)
                else:
                    mask = region_mask & gm_mask

                values = pet_img[mask]
                scan_result[region_name] = float(values.mean()) if values.size > 0 else np.nan

            # ---- Add composite regions ----
            # Cerebellum
            cereb_mask = np.isin(aal_img, cerebellum_indices) & (gm_mask | wm_mask)
            values = pet_img[cereb_mask]
            scan_result["Cerebellum"] = float(values.mean()) if values.size > 0 else np.nan

            # Vermis
            vermis_mask = np.isin(aal_img, vermis_indices) & (gm_mask | wm_mask)
            values = pet_img[vermis_mask]
            scan_result["Vermis"] = float(values.mean()) if values.size > 0 else np.nan

            # Whole cerebellum (Cerebellum + Vermis)
            whole_cereb_mask = np.isin(aal_img, whole_cereb_indices) & (gm_mask | wm_mask)
            values = pet_img[whole_cereb_mask]
            scan_result["Whole_Cerebellum"] = float(values.mean()) if values.size > 0 else np.nan

            results.append(scan_result)
            print(f"Processed {pet_path}")

    # Add new composite region names to columns
    df = pd.DataFrame(results, columns=["scan_path"] + region_names + ["Cerebellum", "Vermis", "Whole_Cerebellum"])

    # Save Excel
    df.to_excel(output_xlsx, index=False)
    print(f"Saved results to {output_xlsx}")

    return df


if __name__ == "__main__":
    compute_averages('shoot/', 'aal116.json', 'shoot/correlations/ROI_correlations/aal_values.xlsx')
