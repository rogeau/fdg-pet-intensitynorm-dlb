#!/usr/bin/env python3
import sys
import nibabel as nib
import numpy as np
from scipy.ndimage import binary_erosion, generate_binary_structure

def erode_nifti(input_file, output_file):
    img = nib.load(input_file)
    data = img.get_fdata()
    binary_data = data > 0
    struct = generate_binary_structure(3, 1)
    eroded = binary_erosion(binary_data, structure=struct)
    eroded = eroded.astype(data.dtype)
    eroded_img = nib.Nifti1Image(eroded, img.affine, img.header)
    nib.save(eroded_img, output_file)
    print(f"Eroded file saved as: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python erode_nifti.py input.nii.gz output.nii.gz")
        sys.exit(1)
    erode_nifti(sys.argv[1], sys.argv[2])
