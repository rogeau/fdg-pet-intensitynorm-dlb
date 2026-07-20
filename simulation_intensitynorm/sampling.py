"""
Sample subjects from the real PET normal pattern + binary-ROI disease.
======================================================================

    image = normal * (1 - max_reduction * lambda * effect_map) * g + noise

  normal     : hoffman_nii/wpet_brain_only.nii, rescaled to mean 1 in brain.
  effect_map : BINARY ROI (1.0 inside, 0.0 outside). No gradient.
  lambda     : PER-SUBJECT disease severity. HC -> 0. Patients -> ~N(1, sd).
  g          : PER-SUBJECT GLOBAL UPTAKE. Lognormal, multiplicative. THIS is
               what normalization must remove.
  noise      : additive measurement noise, inside the brain mask only.

REPRESENTATION
--------------
Images are stored FLAT: shape (n_subjects, n_brain_voxels), holding only the
voxels inside the brain mask. Nothing downstream ever needs the 3D volume --
rmse, depth and progression are all computed as `x[mask]`. Flattening cuts the
array from 91*109*91 = 902,629 to ~318,169 elements and removes the background
zeros entirely. Use `unflatten(vec, mask)` to rebuild a volume for display.

Because effect_map is BINARY, the diseased image is just `normal` scaled by the
scalar (1 - max_reduction*lambda) inside the ROI and left alone outside it. No
per-voxel multiply is needed, so each subject costs one scalar scale on a
sub-vector plus one noise draw.
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from pattern import (make_normal, get_effect_map, default_reduction,
                     SCENARIOS)


def unflatten(vec, mask, fill=0.0):
    """Rebuild a 3D volume from a flat in-mask vector."""
    vol = np.full(mask.shape, fill, dtype=float)
    vol[mask] = vec
    return vol


def sample_subjects(n_subjects,
                    scenario,
                    group="disease",
                    max_reduction=None,
                    lam_mean=1.0, lam_sd=0.25,   # severity centred on lambda=1
                    g_sigma=0.3,                # global uptake variability
                    noise_frac=0.03,               # measurement noise
                    lams=None, gains=None,       # supply to re-scan same subjects
                    dtype=np.float32,
                    rng=None):
    """
    Returns imgs (n, n_brain_vox), lams, gains, mask.
    `imgs` is FLAT: only in-brain voxels. See `unflatten`.
    If `lams` / `gains` are given they are used verbatim (longitudinal re-scan).
    """
    if rng is None:
        rng = np.random.default_rng()
    if max_reduction is None:
        max_reduction = default_reduction(scenario)

    normal, mask = make_normal()
    effect_map, _ = get_effect_map(scenario)

    base = normal[mask].astype(dtype)          # flat normal pattern
    roi = effect_map[mask] > 0.5               # flat boolean ROI
    nvox = base.size

    if lams is None:
        if group == "normal":
            lams = np.zeros(n_subjects)
        else:
            lams = np.clip(rng.normal(lam_mean, lam_sd, n_subjects), 0.0, None)
    if gains is None:
        gains = rng.lognormal(mean=0.0, sigma=g_sigma, size=n_subjects)

    lams = np.asarray(lams, float)
    gains = np.asarray(gains, float)

    # scalar disease factor per subject: applies inside the ROI only
    factor = np.clip(1.0 - max_reduction * lams, 0.0, None)

    # Build the clean signal first, then add noise -- this ORDER is part of the
    # experiment (it fixes how the RNG stream is consumed), so do not reorder
    # it for speed. Only the ROI sub-vector differs between subjects, so the
    # per-voxel multiply is a scalar scale on a slice.
    g = gains.astype(dtype)
    f = factor.astype(dtype)

    imgs = np.empty((n_subjects, nvox), dtype=dtype)
    imgs[:] = base
    imgs[:, roi] *= f[:, None]                        # uniform ROI reduction
    imgs *= g[:, None]                                # global uptake

    if noise_frac > 0:
        sigma = noise_frac * base.mean()
        imgs += rng.normal(0.0, sigma, imgs.shape).astype(dtype)
        np.clip(imgs, 0.0, None, out=imgs)


    coords = np.argwhere(mask)
    lo = coords.min(0)
    hi = coords.max(0) + 1
    sl = tuple(slice(lo[d], hi[d]) for d in range(mask.ndim))
    sub_mask = mask[sl]

    smoothed = np.empty_like(imgs)
    vol = np.zeros(sub_mask.shape, dtype=dtype)
    for s in range(n_subjects):
        vol[sub_mask] = imgs[s]
        vol = gaussian_filter(vol, sigma=0.8, truncate=2.0)
        smoothed[s] = vol[sub_mask]
    imgs = smoothed


    return imgs, lams, gains, mask


def sample_followup(lams_baseline, scenario, progression,
                    g_sigma=0.3, max_reduction=None, noise_frac=0.03,
                    dtype=np.float32, rng=None, **kw):
    """
    Re-scan the SAME patients at follow-up.
      progression : fractional increase in lambda per timepoint
                    (0.30 -> 30% more severe than baseline)
    A fresh global uptake factor is drawn: g is a scan-level nuisance
    (glycaemia on the day), not a subject constant.
    """
    if rng is None:
        rng = np.random.default_rng()
    lams_baseline = np.asarray(lams_baseline, float)
    lams_fu = lams_baseline * (1.0 + progression)
    gains_fu = rng.lognormal(0.0, g_sigma, len(lams_baseline))
    return sample_subjects(len(lams_baseline), scenario, group="disease",
                           lams=lams_fu, gains=gains_fu,
                           max_reduction=max_reduction,
                           noise_frac=noise_frac, dtype=dtype, rng=rng, **kw)


if __name__ == "__main__":
    for sc in SCENARIOS:
        rng = np.random.default_rng(1)
        red = default_reduction(sc)
        hc,  lam_hc,  g_hc,  mask = sample_subjects(500, sc, group="normal",  rng=rng)
        dlb, lam_dlb, g_dlb, _    = sample_subjects(500, sc, group="disease", rng=rng)

        raw_hc = hc.mean(axis=1)
        raw_dlb = dlb.mean(axis=1)

        print(f"\n=== {sc}  (reduction {red:.0%}) ===")
        print(f"images shape {dlb.shape} ({dlb.nbytes/1e6:.0f} MB)")
        print(f"HC      lambda mean {lam_hc.mean():.3f} (should be 0)")
        print(f"Disease lambda mean {lam_dlb.mean():.3f} sd {lam_dlb.std():.3f}")
        print(f"global uptake g range {g_dlb.min():.2f}-{g_dlb.max():.2f}")
        print(f"raw mean uptake  HC {raw_hc.mean():.3f} +/- {raw_hc.std():.3f}")
        print(f"raw mean uptake DLB {raw_dlb.mean():.3f} +/- {raw_dlb.std():.3f}")
        print("-> group difference swamped by global-uptake variability")

        fu, lam_fu, g_fu, _ = sample_followup(lam_dlb, sc, progression=0.30, rng=rng)
        print(f"follow-up lambda mean {lam_fu.mean():.3f} "
              f"(baseline {lam_dlb.mean():.3f}, +30%)")
# Get original colormap
# base_cmap = plt.cm.get_cmap('gist_ncar')

# # Sample it
# colors = base_cmap(np.linspace(0, 1, 256))

# # 🔧 Modify low intensities (first ~15%)
# n_low = int(0.11 * 256)

# for i in range(n_low):
#     t = i / (n_low - 1)  # 0 → 1

#     # Take original color at boundary and scale it down
#     ref_color = colors[n_low].copy()

#     colors[i, :3] = t * ref_color[:3]   # scale RGB only
#     colors[i, 3] = 1.0                  # keep alpha

# custom_cmap = ListedColormap(colors)