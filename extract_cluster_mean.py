#!/usr/bin/env python3
import sys
import os
import glob
import numpy as np
import nibabel as nib
import pandas as pd

def extract_means(search_pattern, search_dir, output_excel):
    mask_img = nib.load("multreg_cluster.nii")
    mask = mask_img.get_fdata() > 0  # binary mask

    # Build search path
    search_path = os.path.join(search_dir, f"**/{search_pattern}.nii*")
    nii_files = glob.glob(search_path, recursive=True)

    if not nii_files:
        print(f"No files found in {search_dir} with pattern '{search_pattern}'")
        return

    results = []

    for f in nii_files:
        try:
            img = nib.load(f)
            data = img.get_fdata()

            # Check shape compatibility
            if data.shape != mask.shape:
                print(f"Warning: {f} has shape {data.shape}, mask has shape {mask.shape} → skipping")
                continue

            values = data[mask]
            mean_val = float(np.mean(values)) if values.size > 0 else np.nan

            results.append({"file": os.path.dirname(f), "mean": mean_val})
            print(f"Processed {f} → mean = {mean_val:.4f}")
        except Exception as e:
            print(f"Error with {f}: {e}")

    if not results:
        print("No valid results to save.")
        return

    # Convert to DataFrame
    df_new = pd.DataFrame(results)

    # If file exists → append
    if os.path.exists(output_excel):
        df_old = pd.read_excel(output_excel)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    # Save to Excel
    df.to_excel(output_excel, index=False)
    print(f"Results saved to {output_excel}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extract_means.py <search_name> <directory> <output.xlsx>")
        sys.exit(1)

    search_name = sys.argv[1]
    search_dir = sys.argv[2]
    output_excel = sys.argv[3]

    extract_means(search_name, search_dir, output_excel)
