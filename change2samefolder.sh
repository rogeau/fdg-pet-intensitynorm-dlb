#!/bin/bash

SRC_DIR="$1"
DST_DIR="$2"

# Check arguments
if [[ -z "$SRC_DIR" || -z "$DST_DIR" ]]; then
    echo "Usage: $0 <source_dir> <destination_dir>"
    exit 1
fi

# Create destination if it doesn't exist
mkdir -p "$DST_DIR"

# Find and process mri.nii files
find "$SRC_DIR" -type f -name "mri.nii" | while read -r file; do
    # Get the three parent directory names
    dir1=$(basename "$(dirname "$file")")                # immediate parent
    dir2=$(basename "$(dirname "$(dirname "$file")")")   # 2nd parent
    dir3=$(basename "$(dirname "$(dirname "$(dirname "$file")")")") # 3rd parent

    # New filename format: dir3_dir2_dir1.nii
    newname="${dir3}_${dir2}_${dir1}.nii"

    # Copy file with new name
    cp "$file" "$DST_DIR/$newname"

    echo "Copied: $file -> $DST_DIR/$newname"
done

