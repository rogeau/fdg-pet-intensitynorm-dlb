#!/bin/bash

ROI=./wfu_pons.nii
SUBDIR=./results_assembly

for ref in "$SUBDIR"/native_structures_*.nii.gz; do
    fname=$(basename "$ref")
    id=${fname#native_structures_}
    id=${id%.nii.gz}

    transform="$SUBDIR/matrix_affine_native_to_mni_${id}.txt"
    out="$SUBDIR/wfu_pons_native_${id}.nii.gz"

    echo "Processing $id ..."

    # Step 1: Warp ROI into native
    antsApplyTransforms -d 3 \
        -i "$ROI" \
        -r "$ref" \
        -t ["$transform",1] \
        -o "$out"

    # Step 2: Extract label 35 from ref
    fslmaths "$ref" -thr 35 -uthr 35 -bin "$SUBDIR/tmp_mask35_${id}.nii.gz"

    # Step 3: Intersect with warped ROI
    fslmaths "$out" -mas "$SUBDIR/tmp_mask35_${id}.nii.gz" "$out"

    # Step 4: clean up mask
    rm "$SUBDIR/tmp_mask35_${id}.nii.gz"
    
done
