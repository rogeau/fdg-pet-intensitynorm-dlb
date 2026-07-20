# """
# Overlay three binary ROIs on a base image, one ROI per row, as CASCADED panels.

# Base image : hoffman_nii/final.nii   -- displayed in inverted grayscale
# Row 1 ROI  : hoffman_nii/ROI_L_parietal.nii            -- blue
# Row 2 ROI  : hoffman_nii/ROI_bilat_temporoparietal.nii -- green
# Row 3 ROI  : hoffman_nii/ROI_bilat_PFC_PTO.nii         -- red

# Within each row every slice is drawn as its own panel, offset horizontally
# from the previous one so successive panels partly cover the one before it
# (a fanned look). Panels are stacked so the LEFT side of each panel stays
# visible (radiological convention). The SAME slice indices (SLICES) are used
# for all three rows. Base voxels below THRESH are made transparent (NaN).

# Usage:
#     python show_overlay.py                # writes overlay.png
# """
# import numpy as np
# import nibabel as nib
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# from matplotlib.colors import ListedColormap

# BASE = "hoffman_nii/final.nii"

# # (ROI file, overlay color) for each row, top to bottom
# ROWS = [
#     ("hoffman_nii/ROI_L_parietal.nii",            (0, 0, 1, 1)),   # blue
#     ("hoffman_nii/ROI_bilat_temporoparietal.nii", (0, 1, 0, 1)),   # green
#     ("hoffman_nii/ROI_bilat_PFC_PTO.nii",         (1, 0, 0, 1)),   # red
# ]

# AXIS = 2                   # slicing axis: 0=sagittal, 1=coronal, 2=axial
# SLICES = [33, 40, 47, 54, 62]  # explicit slice indices to show (same for all rows)
# OUT = "overlay.png"

# THRESH = 500      # base voxels below this become transparent
# PANEL_W = 0.42    # each panel width as a fraction of the figure (0-1)
# PANEL_H = 0.28    # each panel height as a fraction of the figure (0-1)
# DX = 0.06         # horizontal offset between successive panels (smaller = closer)
# ROW_GAP = 0.02    # vertical gap between rows (figure fraction)


# def take_slice(vol, axis, idx):
#     """Extract a 2D slice along `axis`, oriented for display."""
#     sl = np.take(vol, idx, axis=axis)
#     return np.rot90(sl)


# def main():
#     base = nib.load(BASE).get_fdata()

#     # load and binarize all ROIs, check grids match the base
#     rois = []
#     for path, _ in ROWS:
#         r = nib.load(path).get_fdata() > 0.5
#         if r.shape != base.shape:
#             raise ValueError(f"shape mismatch: base {base.shape} vs "
#                              f"{path} {r.shape} -- reslice onto the base grid")
#         rois.append(r)

#     slices = np.array(SLICES)
#     n_slices = len(slices)

#     vmin, vmax = np.percentile(base[base >= THRESH], [1, 99])

#     n_rows = len(ROWS)
#     fig = plt.figure(figsize=(4 * n_slices, 4.0 * n_rows))
#     fig.patch.set_alpha(0)   # transparent figure background

#     # vertical band for each row, top row highest
#     total_h = n_rows * PANEL_H + (n_rows - 1) * ROW_GAP
#     top = (1.0 + total_h) / 2   # centre the block vertically

#     # draw RIGHT-most panel first, LEFT-most last -> left side stays on top
#     order = list(range(n_slices))[::-1]

#     for row, (roi, (_, color)) in enumerate(zip(rois, ROWS)):
#         overlay_cmap = ListedColormap([color])
#         bottom = top - (row + 1) * PANEL_H - row * ROW_GAP
#         for k in order:
#             idx = slices[k]
#             left = 0.03 + k * DX
#             ax = fig.add_axes([left, bottom, PANEL_W, PANEL_H])

#             b = take_slice(base, AXIS, idx).astype(float)
#             r = take_slice(roi, AXIS, idx)

#             b[b < THRESH] = np.nan   # low base voxels -> transparent

#             ax.imshow(b, cmap="gray_r", vmin=vmin, vmax=vmax,
#                       interpolation="bilinear")
#             r_masked = np.where(r, 1.0, np.nan)   # only 1-voxels paint
#             ax.imshow(r_masked, cmap=overlay_cmap, vmin=0, vmax=1,
#                       interpolation="bilinear", alpha=0.6)

#             ax.set_xticks([]); ax.set_yticks([])
#             ax.patch.set_alpha(0)                 # transparent panel background
#             for spine in ax.spines.values():      # no frames
#                 spine.set_visible(False)

#     plt.savefig(OUT, dpi=300, transparent=True)
#     print(f"figure written: {OUT}")


# if __name__ == "__main__":
#     main()


# """
# Four axial panels on one row, all showing the same slice:
#   1) Hoffman phantom alone
#   2) phantom + L parietal ROI            (blue)
#   3) phantom + bilat temporoparietal ROI (green)
#   4) phantom + bilat PFC/PTO ROI         (red)
# Inverted-grayscale colorbar underneath.
# ROI voxels falling where the phantom is transparent (NaN) are hidden.
# """
# import numpy as np
# import nibabel as nib
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# from matplotlib.colors import ListedColormap, Normalize
# from matplotlib.cm import ScalarMappable

# BASE = "hoffman_nii/final.nii"
# ROIS = [
#     ("hoffman_nii/ROI_L_parietal.nii",            (0, 0, 1, 1)),
#     ("hoffman_nii/ROI_bilat_temporoparietal.nii", (0, 1, 0, 1)),
#     ("hoffman_nii/ROI_bilat_PFC_PTO.nii",         (1, 0, 0, 1)),
# ]

# AXIS = 2
# SLICE = 50
# THRESH = 500
# OUT = "overlay.png"
# CBAR_MIN, CBAR_MAX = 0, 45000


# def take_slice(vol, axis, idx):
#     return np.rot90(np.take(vol, idx, axis=axis))


# def main():
#     base = nib.load(BASE).get_fdata()
#     vmin, vmax = np.percentile(base[base >= THRESH], [1, 99])

#     b = take_slice(base, AXIS, SLICE).astype(float)
#     valid = b >= THRESH          # where the phantom is actually drawn
#     b[~valid] = np.nan           # low base voxels -> transparent

#     fig, axes = plt.subplots(1, 4, figsize=(16, 6))
#     fig.patch.set_alpha(0)

#     titles = ["Hoffman phantom", r"$\bf{S1}$: $r$ = 0.2", r"$\bf{S2}$: $r$ = 0.4", r"$\bf{S3}$: $r$ = 0.6"]

#     for j, ax in enumerate(axes):
#         ax.imshow(b, cmap="gray_r", vmin=CBAR_MIN, vmax=CBAR_MAX, interpolation="bilinear")
#         if j > 0:
#             path, color = ROIS[j - 1]
#             r = nib.load(path).get_fdata() > 0.5
#             if r.shape != base.shape:
#                 raise ValueError(f"shape mismatch: base {base.shape} vs {path} {r.shape}")
#             r = take_slice(r, AXIS, SLICE) & valid   # drop ROI voxels over NaN base
#             ax.imshow(np.where(r, 1.0, np.nan), cmap=ListedColormap([color]),
#                       vmin=0, vmax=1, interpolation="nearest", alpha=0.6)
#         ax.text(0.5, 0.08, titles[j], transform=ax.transAxes,
#                 ha="center", va="top", fontsize=14)
#         ax.set_xticks([]); ax.set_yticks([])
#         ax.patch.set_alpha(0)
#         for s in ax.spines.values():
#             s.set_visible(False)

#     fig.subplots_adjust(bottom=0.16, wspace=-0.2)
#     cax = fig.add_axes([0.2, 0.1, 0.6, 0.03])
#     cb = fig.colorbar(ScalarMappable(norm=Normalize(vmin, vmax), cmap="gray_r"),
#                   cax=cax, orientation="horizontal")
#     cb.set_label("counts", fontsize=14)
#     cb.ax.tick_params(labelsize=14)

#     plt.savefig(OUT, dpi=300, transparent=True)
#     print(f"figure written: {OUT}")


# if __name__ == "__main__":
#     main()


# """
# Hoffman phantom on the left, S1/S2/S3 overlays stacked in a column on the right.
# Inverted-grayscale colorbar underneath.
# ROI voxels falling where the phantom is transparent (NaN) are hidden.
# """
# import numpy as np
# import nibabel as nib
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# from matplotlib.colors import ListedColormap, Normalize
# from matplotlib.cm import ScalarMappable
# from matplotlib.gridspec import GridSpec

# BASE = "hoffman_nii/final.nii"
# ROIS = [
#     ("hoffman_nii/ROI_L_parietal.nii",            (0, 0, 1, 1)),
#     ("hoffman_nii/ROI_bilat_temporoparietal.nii", (0, 1, 0, 1)),
#     ("hoffman_nii/ROI_bilat_PFC_PTO.nii",         (1, 0, 0, 1)),
# ]

# AXIS = 2
# SLICE = 50
# THRESH = 500
# OUT = "overlay.png"
# CBAR_MIN, CBAR_MAX = 0, 45000


# def take_slice(vol, axis, idx):
#     return np.rot90(np.take(vol, idx, axis=axis))


# def main():
#     base = nib.load(BASE).get_fdata()

#     b = take_slice(base, AXIS, SLICE).astype(float)
#     valid = b >= THRESH          # where the phantom is actually drawn
#     b[~valid] = np.nan           # low base voxels -> transparent

#     fig = plt.figure(figsize=(10, 10))
#     fig.patch.set_alpha(0)

#     gs = GridSpec(3, 2, figure=fig, width_ratios=[1, 2],
#               left=0.02, right=0.98,
#               bottom=0.12, top=0.98, wspace=-0.05, hspace=0.02)

#     ax_big = fig.add_subplot(gs[:, 0])            # phantom spans all 3 rows
#     axes = [ax_big] + [fig.add_subplot(gs[i, 1]) for i in range(3)]

#     titles = ["Hoffman phantom", r"$\bf{S1}$: $r$ = 0.2",
#               r"$\bf{S2}$: $r$ = 0.4", r"$\bf{S3}$: $r$ = 0.6"]

#     for j, ax in enumerate(axes):
#         ax.imshow(b, cmap="gray_r", vmin=CBAR_MIN, vmax=CBAR_MAX,
#                   interpolation="bilinear")
#         if j > 0:
#             path, color = ROIS[j - 1]
#             r = nib.load(path).get_fdata() > 0.5
#             if r.shape != base.shape:
#                 raise ValueError(f"shape mismatch: base {base.shape} vs {path} {r.shape}")
#             r = take_slice(r, AXIS, SLICE) & valid   # drop ROI voxels over NaN base
#             ax.imshow(np.where(r, 1.0, np.nan), cmap=ListedColormap([color]),
#                       vmin=0, vmax=1, interpolation="nearest", alpha=0.6)
#         ax.text(0.5, 0.08, titles[j], transform=ax.transAxes,
#                 ha="center", va="top", fontsize=14)
#         ax.set_xticks([]); ax.set_yticks([])
#         ax.patch.set_alpha(0)
#         for s in ax.spines.values():
#             s.set_visible(False)

#     cax = fig.add_axes([0.2, 0.06, 0.6, 0.025])
#     cb = fig.colorbar(ScalarMappable(norm=Normalize(CBAR_MIN, CBAR_MAX), cmap="gray_r"),
#                       cax=cax, orientation="horizontal")
#     cb.set_label("counts", fontsize=14)
#     cb.ax.tick_params(labelsize=14)

#     plt.savefig(OUT, dpi=300, transparent=True)
#     print(f"figure written: {OUT}")


# if __name__ == "__main__":
#     main()


"""
Hoffman phantom on the left, S1/S2/S3 overlays stacked in a column on the right,
with arrows from the phantom to each overlay.
Vertical inverted-grayscale colorbar on the left.
ROI voxels falling where the phantom is transparent (NaN) are hidden.
"""
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.gridspec import GridSpec
from matplotlib.patches import ConnectionPatch

BASE = "hoffman_nii/final.nii"
ROIS = [
    ("hoffman_nii/ROI_L_parietal.nii",            (0, 0, 1, 1)),
    ("hoffman_nii/ROI_bilat_temporoparietal.nii", (0, 1, 0, 1)),
    ("hoffman_nii/ROI_bilat_PFC_PTO.nii",         (1, 0, 0, 1)),
]

AXIS = 2
SLICE = 50
THRESH = 500
OUT = "overlay.png"
CBAR_MIN, CBAR_MAX = 0, 51600


def take_slice(vol, axis, idx):
    return np.rot90(np.take(vol, idx, axis=axis))


def main():
    base = nib.load(BASE).get_fdata()

    b = take_slice(base, AXIS, SLICE).astype(float)
    valid = b >= THRESH          # where the phantom is actually drawn
    b[~valid] = np.nan           # low base voxels -> transparent

    fig = plt.figure(figsize=(10, 10))
    fig.patch.set_alpha(0)

    gs = GridSpec(3, 2, figure=fig, width_ratios=[1, 1.5],
                  left=0.14, right=0.98,
                  bottom=0.02, top=0.94, wspace=0, hspace=-0.15)

    ax_big = fig.add_subplot(gs[:, 0])            # phantom spans all 3 rows
    axes = [ax_big] + [fig.add_subplot(gs[i, 1]) for i in range(3)]

    titles = ["Hoffman phantom", r"$\bf{S1}$: $r$ = 0.2",
              r"$\bf{S2}$: $r$ = 0.4", r"$\bf{S3}$: $r$ = 0.6"]

    for j, ax in enumerate(axes):
        ax.imshow(b, cmap="gray_r", vmin=CBAR_MIN, vmax=CBAR_MAX,
                  interpolation="bilinear")
        if j > 0:
            path, color = ROIS[j - 1]
            r = nib.load(path).get_fdata() > 0.5
            if r.shape != base.shape:
                raise ValueError(f"shape mismatch: base {base.shape} vs {path} {r.shape}")
            r = take_slice(r, AXIS, SLICE) & valid   # drop ROI voxels over NaN base
            ax.imshow(np.where(r, 1.0, np.nan), cmap=ListedColormap([color]),
                      vmin=0, vmax=1, interpolation="nearest", alpha=0.6)
        ax.text(0.5, 0.89, titles[j], transform=ax.transAxes,
                ha="center", va="bottom", fontsize=18)
        ax.set_xticks([]); ax.set_yticks([])
        ax.patch.set_alpha(0)
        for s in ax.spines.values():
            s.set_visible(False)

    # arrows: phantom -> S1 / S2 / S3
    # for i, ax in enumerate(axes[1:]):
    #     con = ConnectionPatch(
    #         xyA=(1.0, 0.5), coordsA=ax_big.transAxes,
    #         xyB=(0.0, 0.5), coordsB=ax.transAxes,
    #         arrowstyle="-|>", mutation_scale=22,
    #         linewidth=1.8, color="0.25",
    #         connectionstyle="arc3,rad=0.0" if i == 1 else
    #                         ("arc3,rad=-0.25" if i == 0 else "arc3,rad=0.25"),
    #         shrinkA=6, shrinkB=6, zorder=10,
    #     )
    #     fig.add_artist(con)

    ny, nx = b.shape

    for i, ax in enumerate(axes[1:]):
        con = ConnectionPatch(
            xyA=(nx * 0.9, ny * 0.5), coordsA=ax_big.transData,   # right edge of phantom
            xyB=(nx * 0.1, ny * 0.5), coordsB=ax.transData,       # left edge of target brain
            arrowstyle="-|>", mutation_scale=22,
            linewidth=1.8, color="0.25",
            connectionstyle=["arc3,rad=-0.1", "arc3,rad=0.0", "arc3,rad=0.1"][i],
            shrinkA=8, shrinkB=8, zorder=10,
        )
        fig.add_artist(con)

    cax = fig.add_axes([0.12, 0.2, 0.025, 0.6])
    cb = fig.colorbar(ScalarMappable(norm=Normalize(CBAR_MIN, CBAR_MAX), cmap="gray_r"),
                      cax=cax, orientation="vertical")
    cb.set_label("counts", fontsize=18)
    cb.ax.tick_params(labelsize=18)
    cb.set_ticks([10000, 20000, 30000, 40000, 50000])
    cax.yaxis.set_ticks_position("left")
    cax.yaxis.set_label_position("left")

    plt.savefig(OUT, dpi=300, transparent=True)
    print(f"figure written: {OUT}")


if __name__ == "__main__":
    main()