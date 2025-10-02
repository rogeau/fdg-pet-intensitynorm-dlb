import os
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.ndimage import mean as nd_mean
from concurrent.futures import ProcessPoolExecutor, as_completed
import matplotlib.pyplot as plt

def find_files(root_folder, target_name):
    """Recursively find all files with a given name."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename == target_name:
                matches.append(os.path.join(dirpath, filename))
    return matches

def save_qc_overlay(volume, pons, subject_id, root):
    parent = os.path.dirname(root)
    qc_dir = os.path.join(parent, 'QC')
    os.makedirs(qc_dir, exist_ok=True)

    # find z indices where pons > 0
    z_indices = np.where(np.any(pons > 0, axis=(0, 1)))[0]
    if len(z_indices) == 0:
        print(f"[QC] No pons voxels found for {subject_id}")
        return
    z_mid = int(np.median(z_indices))  # middle slice of pons region

    # plot overlay
    plt.figure(figsize=(6, 6))
    plt.imshow(volume[:, :, z_mid].T, cmap="gray", origin="lower")
    plt.imshow(np.ma.masked_where(pons[:, :, z_mid].T == 0, pons[:, :, z_mid].T),
               cmap="autumn", alpha=0.5, origin="lower")
    plt.title(f"{subject_id} (z={z_mid})")
    plt.axis("off")

    # save
    outpath = os.path.join(qc_dir, f"{subject_id}_qc.png")
    plt.savefig(outpath, bbox_inches="tight")
    plt.close()

def calculate_roi_single(file, labels, names, atlas_folder, root='forROIanalyses/DLB'):
    """Calculate ROI values for a single file."""
    path = Path(file)
    date = path.parent.name
    ipp = path.parent.parent.name
    group = path.parent.parent.parent.name
    subject_id = f"{group}_{ipp}_{date}"

    # Atlas path
    atlas_basename = f"native_structures_{group}_{ipp}_{date}.nii.gz"
    atlas_path = Path(atlas_folder) / atlas_basename

    pons_basename = f"wfu_pons_native_{group}_{ipp}_{date}.nii.gz"
    pons_path = Path(atlas_folder) / pons_basename

    # Load NIfTI volumes
    volume = nib.load(file).get_fdata(dtype=np.float32)
    atlas = nib.load(atlas_path).get_fdata(dtype=np.float32).astype(np.int32)
    pons = nib.load(pons_path).get_fdata(dtype=np.float32).astype(np.int32)

    save_qc_overlay(volume, pons, subject_id, root)

    # ROI means from atlas
    means = nd_mean(volume, labels=atlas, index=labels)

    row = {"subject_id": subject_id, "file": str(file)}
    for name, val in zip(names, means):
        row[name] = float(val) if not np.isnan(val) else np.nan

    # Pons mean (mask > 0)
    if np.any(pons > 0):
        pons_mean = volume[pons > 0].mean()
    else:
        pons_mean = np.nan
    row["Pons"] = float(pons_mean)

    return row

def calculate_rois_parallel(list_files, json_file, atlas_folder="results_assembly", output_excel="roi_results.xlsx", root='forROIanalyses/DLB', n_workers=4):
    """Parallel ROI calculation."""
    # Load atlas definition
    with open(json_file, "r") as f:
        atlas_def = json.load(f)["structures"]

    labels = [s["label"] for s in atlas_def]
    names = [s["name"] for s in atlas_def]

    results = []

    # Parallel processing
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(calculate_roi_single, f, labels, names, atlas_folder): f for f in list_files}
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            print(row)

    # Save results
    df = pd.DataFrame(results)
    df.to_excel(output_excel, index=False)
    print(f"Saved ROI results to {output_excel}")
    return df

def main():
    root_folder = "coreg_center_mass_reorient/HC"
    target_filename = "pons_r_petsuv.nii.gz"
    atlas_json = "results_assembly/structures.json"
    atlas_folder = "results_assembly"
    output_excel = "coreg_center_mass_reorient/results_roi/pons_r_petsuv_HC.xlsx"

    list_files = find_files(root_folder, target_filename)
    df_results = calculate_rois_parallel(list_files, atlas_json, atlas_folder, output_excel, root_folder, n_workers=8)

if __name__ == "__main__":
    main()
