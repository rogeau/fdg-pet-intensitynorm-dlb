# """
# Example subjects drawn from each of the three disease scenarios.
# ================================================================

# Row 1  normal pattern, and the ground-truth diseased pattern for each ROI
#        (no global uptake, no noise) -- what the disease actually does.

# Row 2  ONE PATIENT per scenario, exactly as `sample_subjects` returns them:
#        normal * (1 - max_red*lambda*ROI) * g + noise.
#        The same lambda and the same g are used across the three columns so the
#        only thing changing is the ROI and its nominal depth.

# Row 3  the same patient after dividing by a PERFECT scaling factor (sf = g).
#        This is the best any normalization could do, and is what the recovery
#        step in pipeline.py is trying to approximate.

# Row 4  three DIFFERENT patients from the bilat_TP scenario with varying g,
#        to show the confound: global uptake shifts whole-brain brightness by
#        more than the lesion does, so raw scans are not comparable.

# Usage:
#     python show_subjects.py           # writes example_subjects.png
# """
# import numpy as np
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt

# from pattern import make_normal, make_diseased, default_reduction, SCENARIOS
# from sampling import sample_subjects, unflatten

# SEED = 3
# G_SIGMA = 0.3
# NOISE_SD = 0.03


# def mid_slice(vol, mask):
#     """Axial slice through the centre of the mask."""
#     zs = np.where(mask.any(axis=(0, 1)))[0]
#     z = int(round(zs.mean()))
#     return np.rot90(np.where(mask[:, :, z], vol[:, :, z], np.nan))


# def main():
#     scen = list(SCENARIOS)
#     normal, mask = make_normal()

#     # one shared subject: same severity, same global uptake, across scenarios
#     rng = np.random.default_rng(SEED)
#     lam = float(np.clip(rng.normal(1.0, 0.25), 0.0, None))
#     g = float(rng.lognormal(0.0, G_SIGMA))

#     fig, axes = plt.subplots(4, 3, figsize=(10.5, 13.5))

#     # ---- row 1: ground truth diseased pattern (no g, no noise) -------------
#     for j, sc in enumerate(scen):
#         red = default_reduction(sc)
#         img, truth, _ = make_diseased(sc)
#         ax = axes[0, j]
#         im = ax.imshow(mid_slice(img, mask), cmap="magma", vmin=0, vmax=1.3)
#         ax.set_title(f"{sc}\nground truth, {red:.0%} reduction", fontsize=9)
#         ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
#     axes[0, 0].set_ylabel("clean pattern", fontsize=10)
#     fig.colorbar(im, ax=axes[0, :], fraction=.03, pad=.02, label="uptake")

#     # ---- row 2: one sampled patient, same lambda and g throughout ----------
#     for j, sc in enumerate(scen):
#         imgs, _, _, _ = sample_subjects(1, sc, group="disease",
#                                         lams=np.array([lam]),
#                                         gains=np.array([g]),
#                                         noise_sd=NOISE_SD,
#                                         rng=np.random.default_rng(SEED))
#         vol = unflatten(imgs[0].astype(float), mask)
#         ax = axes[1, j]
#         im = ax.imshow(mid_slice(vol, mask), cmap="magma", vmin=0, vmax=1.3)
#         ax.set_title(f"$\\lambda$={lam:.2f}  g={g:.2f}", fontsize=9)
#         ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
#     axes[1, 0].set_ylabel("sampled patient\n(raw)", fontsize=10)
#     fig.colorbar(im, ax=axes[1, :], fraction=.03, pad=.02, label="uptake")

#     # ---- row 3: the same patient, normalized by a PERFECT sf = g -----------
#     for j, sc in enumerate(scen):
#         red = default_reduction(sc)
#         imgs, _, _, _ = sample_subjects(1, sc, group="disease",
#                                         lams=np.array([lam]),
#                                         gains=np.array([g]),
#                                         noise_sd=NOISE_SD,
#                                         rng=np.random.default_rng(SEED))
#         vol = unflatten(imgs[0].astype(float) / g, mask)
#         ratio = np.full(mask.shape, np.nan)
#         ratio[mask] = vol[mask] / normal[mask]      # vs the normal pattern
#         ax = axes[2, j]
#         im = ax.imshow(mid_slice(ratio, mask), cmap="RdBu_r", vmin=0.3, vmax=1.15)
#         expected = 1.0 - red * lam
#         ax.set_title(f"expected ratio in ROI = {max(expected,0):.2f}", fontsize=9)
#         ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
#     axes[2, 0].set_ylabel("normalized by g\n(ratio to normal)", fontsize=10)
#     fig.colorbar(im, ax=axes[2, :], fraction=.03, pad=.02, label="ratio")

#     # ---- row 4: the CONFOUND -- three patients, same ROI, different g ------
#     sc = "bilat_TP"
#     red = default_reduction(sc)
#     rng2 = np.random.default_rng(11)
#     lams = np.array([1.30, 1.00, 0.60])          # severe -> mild
#     gains = np.array([0.60, 1.00, 1.70])         # low -> high global uptake
#     imgs, _, _, _ = sample_subjects(3, sc, group="disease",
#                                     lams=lams, gains=gains,
#                                     noise_sd=NOISE_SD, rng=rng2)
#     for j in range(3):
#         vol = unflatten(imgs[j].astype(float), mask)
#         ax = axes[3, j]
#         im = ax.imshow(mid_slice(vol, mask), cmap="magma", vmin=0, vmax=1.3)
#         whole = float(np.nanmean(vol[mask]))
#         ax.set_title(f"$\\lambda$={lams[j]:.2f}  g={gains[j]:.2f}\n"
#                      f"mean uptake = {whole:.2f}", fontsize=9)
#         ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
#     axes[3, 0].set_ylabel(f"{sc}: the confound\n(raw, varying g)", fontsize=10)
#     fig.colorbar(im, ax=axes[3, :], fraction=.03, pad=.02, label="uptake")

#     fig.suptitle("Example subjects from the three disease scenarios", fontsize=13)
#     plt.savefig("example_subjects.png", dpi=140, bbox_inches="tight")
#     print("figure written: example_subjects.png")

#     # ---- the point of row 4, in numbers ------------------------------------
#     print(f"\n{sc}: raw whole-brain mean uptake, three patients")
#     print(f"{'lambda':>8}{'g':>8}{'mean':>10}")
#     for j in range(3):
#         vol = unflatten(imgs[j].astype(float), mask)
#         print(f"{lams[j]:>8.2f}{gains[j]:>8.2f}{float(vol[mask].mean()):>10.3f}")
#     print("-> the SICKEST patient has the LOWEST mean only because g is low;\n"
#           "   ordering by raw uptake recovers g, not disease.")


# if __name__ == "__main__":
#     main()


"""
Two random normal subjects and two random diseased subjects.
============================================================

Row 1  two random NORMAL subjects (group="normal"): normal * g + noise,
       no disease effect.

Row 2  two random DISEASED subjects (group="disease"):
       normal * (1 - max_red*lambda*ROI) * g + noise.

Each subject is drawn independently, so lambda (severity) and g (global
uptake) vary freely between panels.

Usage:
    python show_subjects.py           # writes example_subjects.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from pattern import make_normal, SCENARIOS
from sampling import sample_subjects, unflatten

SEED = 3
NOISE_FRAC = 0.03
SCENARIO = "bilat_TP"      # ROI used for the diseased row


# # Get original colormap
# base_cmap = plt.cm.get_cmap('gist_ncar')

# # Sample it
# colors = base_cmap(np.linspace(0, 1, 256))

# # 🔧 Modify low intensities (first ~11%)
# n_low = int(0.11 * 256)

# for i in range(n_low):
#     t = i / (n_low - 1)  # 0 → 1

#     # Take original color at boundary and scale it down
#     ref_color = colors[n_low].copy()

#     colors[i, :3] = t * ref_color[:3]   # scale RGB only
#     colors[i, 3] = 1.0                  # keep alpha

# # 🔧 Make the top ~5% white
# n_high = int(0.05 * 256)

# for i in range(256 - n_high, 256):
#     colors[i, :3] = 1.0                 # white RGB
#     colors[i, 3] = 1.0                  # keep alpha

# custom_cmap = ListedColormap(colors)

# Get original colormap
base_cmap = plt.cm.get_cmap('gist_ncar')

# Sample it
colors = base_cmap(np.linspace(0, 1, 256))

# 🔧 Modify low intensities (first ~11%): fade down to black
n_low = int(0.11 * 256)

for i in range(n_low):
    t = i / (n_low - 1)  # 0 → 1

    # Take original color at boundary and scale it down
    ref_color = colors[n_low].copy()

    colors[i, :3] = t * ref_color[:3]   # scale RGB only
    colors[i, 3] = 1.0                  # keep alpha

# 🔧 Modify high intensities (top ~20%): fade from magenta up to white
n_high = int(0.20 * 256)
start = 256 - n_high

# magenta reference = the color just below the top band
ref_high = colors[start - 1].copy()

for k in range(n_high):
    i = start + k
    t = k / (n_high - 1)  # 0 → 1
    colors[i, :3] = (1 - t) * ref_high[:3] + t * 1.0   # magenta → white
    colors[i, 3] = 1.0

custom_cmap = ListedColormap(colors)

def mid_slice(vol, mask):
    """Axial slice through the centre of the mask."""
    zs = np.where(mask.any(axis=(0, 1)))[0]
    z = int(round(zs.mean()))
    return np.rot90(np.where(mask[:, :, z], vol[:, :, z], np.nan))

def low_to_nan(sl, thresh=10000, center_frac=0.35):
    """Set voxels < thresh to NaN, except within a central region."""
    h, w = sl.shape
    cy, cx = h / 2, w / 2
    ry, rx = h * center_frac, w * center_frac      # half-size of protected box

    yy, xx = np.ogrid[:h, :w]
    # circular protected region:
    protect = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0
    # (for a rectangle instead: protect = (np.abs(yy-cy) <= ry) & (np.abs(xx-cx) <= rx))

    sl = sl.copy()
    sl[(sl < thresh) & ~protect] = np.nan
    return sl


def main():
    normal, mask = make_normal()
    rng = np.random.default_rng(SEED)

    # fixed global uptake: g=1.2 for the first subject, g=0.8 for the second
    gains = np.array([1.2, 0.9])

    normal_imgs, n_lams, n_gains, _ = sample_subjects(
        2, SCENARIO, group="normal", gains=gains,
        noise_frac=NOISE_FRAC, rng=rng)
    dis_imgs, d_lams, d_gains, _ = sample_subjects(
        2, SCENARIO, group="disease", gains=gains,
        noise_frac=NOISE_FRAC, rng=rng)

    # shared color scale across all four panels
    all_vals = np.concatenate([
        normal_imgs.astype(float).ravel(),
        dis_imgs.astype(float).ravel(),
    ])
    vmin, vmax = all_vals.min(), all_vals.max()
    print(f"color scale: vmin={vmin:.3f}, vmax={vmax:.3f}")

    fig, axes = plt.subplots(2, 2, figsize=(7.5, 7.5))
    fig.subplots_adjust(wspace=0, hspace=0)

    # ---- row 1: normal subjects -------------------------------------------
    for j in range(2):
        vol = unflatten(normal_imgs[j].astype(float), mask)
        sl = low_to_nan(mid_slice(vol, mask))
        ax = axes[0, j]
        im = ax.imshow(sl, cmap=custom_cmap,
                       vmin=vmin, vmax=vmax, interpolation="bilinear")
        ax.set_title(f"$\\lambda$={n_lams[j]:.2f}  g={n_gains[j]:.2f}",
                     fontsize=11, y=0.93)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
    axes[0, 0].set_ylabel("normal", fontsize=11)

    # ---- row 2: diseased subjects -----------------------------------------
    for j in range(2):
        vol = unflatten(dis_imgs[j].astype(float), mask)
        sl = low_to_nan(mid_slice(vol, mask))
        ax = axes[1, j]
        im = ax.imshow(sl, cmap=custom_cmap,
                       vmin=vmin, vmax=vmax, interpolation="bilinear")
        ax.set_title(f"$\\lambda$={d_lams[j]:.2f}  g={d_gains[j]:.2f}",
                     fontsize=11, y=0.93)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
    axes[1, 0].set_ylabel("diseased", fontsize=11)

    fig.colorbar(im, ax=axes, fraction=.03, pad=.02, label="counts")
    plt.savefig("example_subjects.png", dpi=140, bbox_inches="tight")
    print("figure written: example_subjects.png")


if __name__ == "__main__":
    main()