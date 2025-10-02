#!/usr/bin/env python3
import sys
import nibabel as nib
import numpy as np

def binarize_first_two_volumes(input_file, output_file, threshold=0.1):
    # Load NIfTI
    img = nib.load(input_file)
    data = img.get_fdata()

    # Sanity check: must be 4D
    if data.ndim != 4 or data.shape[3] < 2:
        raise ValueError("Input must be a 4D file with at least 2 volumes")

    # Extract first 2 volumes
    vol1 = data[..., 0]
    vol2 = data[..., 1]

    # Create binary mask (union of both conditions)
    mask = (vol1 > threshold) | (vol2 > threshold)

    # Convert to int (0/1)
    mask = mask.astype(np.uint8)

    # Save as 3D NIfTI
    mask_img = nib.Nifti1Image(mask, img.affine, img.header)
    nib.save(mask_img, output_file)
    print(f"Binary mask saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python binarize_template.py <Template_4.nii> <output_mask.nii>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    binarize_first_two_volumes(input_file, output_file)
