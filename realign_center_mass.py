import os
import sys
import nibabel as nib
import numpy as np
from scipy.ndimage import center_of_mass

def realign_nii_files(root_dir, overwrite=False):
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith((".nii", ".nii.gz")):
                fpath = os.path.join(dirpath, fname)
                print(f"Processing: {fpath}")

                img = nib.load(fpath)
                data = img.get_fdata()

                # Compute center of mass in voxel coordinates
                com_vox = np.array(center_of_mass(data))
                # Convert voxel coordinates to world coordinates
                com_world = nib.affines.apply_affine(img.affine, com_vox)

                # Shift affine so that CoM is at (0,0,0)
                new_affine = img.affine.copy()
                new_affine[:3, 3] -= com_world

                # Save result
                if overwrite:
                    out_path = fpath
                else:
                    if fpath.endswith(".nii.gz"):
                        out_path = fpath[:-7] + "_realigned.nii.gz"
                    elif fpath.endswith(".nii"):
                        out_path = fpath[:-4] + "_realigned.nii"
                    else:
                        out_path = fpath + "_realigned"

                nib.save(nib.Nifti1Image(data, new_affine, img.header), out_path)
                print(f"Saved: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python realign_nii.py /path/to/directory [--overwrite]")
        sys.exit(1)

    directory = sys.argv[1]
    overwrite_flag = "--overwrite" in sys.argv

    realign_nii_files(directory, overwrite=overwrite_flag)
