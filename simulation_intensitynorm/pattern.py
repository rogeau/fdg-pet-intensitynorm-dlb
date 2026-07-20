"""
Real-PET pattern definition (replaces the 2D elliptical phantom).
=================================================================

The normal pattern is no longer synthesised: it is the Hoffman phantom PET
volume itself, `hoffman_nii/wpet_brain_only.nii`. Its GM/WM contrast is real,
so `normal` is NOT uniform.

Disease is a UNIFORM multiplicative reduction inside a binary ROI:

    truth = 1 - max_reduction * effect_map          effect_map in {0, 1}
    diseased = normal * truth

Three scenarios, each with its own ROI and nominal depth:

    L_parietal        ROI_L_parietal.nii              20% reduction
    bilat_TP          ROI_bilat_temporoparietal.nii   40% reduction
    bilat_PFC_PTO     ROI_bilat_PFC_PTO.nii           60% reduction

Because effect_map is binary, `truth` takes exactly two values inside the
brain: 1.0 outside the ROI and (1 - max_reduction) inside it. There is no
gradient. `core` (used for depth scoring) is therefore the whole ROI, and
`true_depth` is exactly 1 - max_reduction.
"""
import os
import numpy as np
import nibabel as nib

NII_DIR = os.environ.get("HOFFMAN_DIR", "hoffman_nii")

PET_FILE = "final.nii"

GM_THRESH = 24000.0

# scenario -> (ROI filename, nominal fractional reduction)
SCENARIOS = {
    "L_parietal":    ("ROI_L_parietal.nii",            0.20),
    "bilat_TP":      ("ROI_bilat_temporoparietal.nii", 0.40),
    "bilat_PFC_PTO": ("ROI_bilat_PFC_PTO.nii",         0.60),
}

# brain mask threshold on the PET (background is 0 after skull-stripping)
BRAIN_THRESH = 0.0

_cache = {}


# ------------------------------------------------------------------ loading
def _path(fname):
    return os.path.join(NII_DIR, fname)

def load_pet():
    """
    Normal pattern = the raw PET volume. Extra-brain voxels are already 0 in
    the file, so no masking or rescaling is needed here; disease (severity),
    global uptake (g) and noise are applied on top of these values downstream.

    Returns (normal, mask, affine).
    """
    if "pet" in _cache:
        return _cache["pet"]

    img = nib.load(_path(PET_FILE))
    normal = np.asarray(img.dataobj, dtype=float)
    mask = normal > BRAIN_THRESH

    _cache["pet"] = (normal, mask, img.affine)
    return _cache["pet"]


def load_roi(scenario):
    """Binary ROI mask, intersected with the brain mask. Returns (roi, mask)."""
    if scenario not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario!r}; "
                       f"choose from {list(SCENARIOS)}")
    key = ("roi", scenario)
    if key in _cache:
        return _cache[key]

    _, mask, _ = load_pet()
    fname, _ = SCENARIOS[scenario]
    roi_img = nib.load(_path(fname))
    roi = np.asarray(roi_img.dataobj) > 0

    if roi.shape != mask.shape:
        raise ValueError(f"{fname} shape {roi.shape} != PET shape {mask.shape}; "
                         "reslice the ROI onto the PET grid first")

    roi = roi & mask
    if not roi.any():
        raise ValueError(f"{fname}: empty after intersection with brain mask")

    _cache[key] = (roi, mask)
    return _cache[key]


# ------------------------------------------------------------------ patterns
def make_normal():
    """Uniform-scale normal pattern. Returns (img, mask)."""
    normal, mask, _ = load_pet()
    return normal.copy(), mask


def get_effect_map(scenario, max_reduction=None):
    """
    Binary effect map: 1.0 inside the ROI, 0.0 elsewhere.
    `max_reduction` is accepted and ignored (kept for signature compatibility);
    the effect map does not depend on it.

    Returns (effect_map, mask).
    """
    roi, mask = load_roi(scenario)
    effect_map = roi.astype(float)
    return effect_map, mask


def default_reduction(scenario):
    """The nominal reduction attached to this scenario (0.20 / 0.40 / 0.60)."""
    return SCENARIOS[scenario][1]


def make_diseased(scenario, max_reduction=None):
    """
    Ground-truth diseased pattern for one scenario.

    Returns (img, truth, mask) where
        truth = 1 - max_reduction inside the ROI, 1.0 elsewhere in the brain
        img   = normal * truth
    """
    if max_reduction is None:
        max_reduction = default_reduction(scenario)

    normal, mask = make_normal()
    effect_map, _ = get_effect_map(scenario)

    truth = np.zeros_like(normal)
    truth[mask] = 1.0 - max_reduction * effect_map[mask]

    img = normal * truth
    return img, truth, mask


def save_like(data, fname, ref_affine=None):
    """Write a volume on the PET grid."""
    if ref_affine is None:
        _, _, ref_affine = load_pet()
    nib.save(nib.Nifti1Image(np.asarray(data, dtype=np.float32), ref_affine),
             fname)
    

def load_gm(scenario=None):
    """Grey-matter mask: final.nii > GM_THRESH, intersected with the brain mask."""
    if "gm" in _cache:
        return _cache["gm"]
    gm_img = nib.load(_path(PET_FILE))
    gm = np.asarray(gm_img.dataobj, dtype=float) > GM_THRESH
    _cache["gm"] = gm
    return _cache["gm"]


if __name__ == "__main__":
    normal, mask = make_normal()
    print(f"PET grid {normal.shape}   brain voxels {mask.sum()}")
    print(f"normal uptake in brain: {normal[mask].min():.3f} - "
          f"{normal[mask].max():.3f}  (mean {normal[mask].mean():.3f})")

    for sc in SCENARIOS:
        red = default_reduction(sc)
        _, truth, _ = make_diseased(sc)
        roi, _ = load_roi(sc)
        gm = load_gm()
        frac = roi.sum() / gm.sum()
        print(f"\n{sc:<15} reduction {red:.0%}   "
              f"ROI {roi.sum():>7} vox ({frac:.1%} of GM)")
        print(f"{'':15} truth in GM: {truth[mask].min():.3f} - "
              f"{truth[mask].max():.3f}")
        print(f"{'':15} truth inside ROI: {truth[roi].mean():.3f} "
              f"(expected {1-red:.3f})")