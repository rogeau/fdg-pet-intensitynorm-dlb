"""
Outcome measures: N_SCEN scenarios with all four metrics drawn randomly.

Each scenario draws X1..X4 uniformly from their ranges, simulates the cohort,
normalises, and scores recovery against the known ground truth.

Because all four vary simultaneously, a plot of RMSE against one metric shows
its MARGINAL relationship (the other three appear as scatter). A multiple
regression across the scenarios recovers each metric's independent
contribution.

Run once per ROI scenario (L_parietal / bilat_TP / bilat_PFC_PTO), which are
three independent experiments with different ground truths.

Metric naming:
    mean_drop    -> Normative alignment       (Delta_mu, %)
    corr_lambda  -> Disease independence       (R^2 = corr_lambda**2)
    cv           -> Interindividual stability   (CV)
    long_decline -> Temporal stability          (ROC)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

from pipeline import run_scenario, _mid_slice
from pattern import SCENARIOS, default_reduction, load_gm

N_SCEN = 100
RANGES = {"mean_drop":   (0.00, 0.40),
          "cv":          (0.1, 0.35),
          "corr_lambda": (0, 1.00),
          "long_decline":(0.00, 0.30)}

ORDER = ["mean_drop", "corr_lambda", "cv", "long_decline"]
TITLES = {
    "mean_drop":    "Normative alignment",
    "corr_lambda":  "Disease independence",
    "cv":           "Interindividual stability",
    "long_decline": "Temporal stability",
}
COLORS = {
    "mean_drop":    "#c0392b",
    "corr_lambda":  "#2980b9",
    "cv":           "#27ae60",
    "long_decline": "#8e44ad",
}
XLABELS = {
    "mean_drop":    r"$\Delta_\mu$ (%)",
    "corr_lambda":  r"$R^2$",
    "cv":           "CV",
    "long_decline": "ROC",
}


def metric_value(k, raw):
    """Value of metric `k` as USED/DISPLAYED, from the raw drawn value(s).

    corr_lambda is drawn as Pearson's r; the metric considered is R^2 = r**2.
    mean_drop is shown as a percentage.
    """
    if k == "corr_lambda":
        return raw ** 2
    if k == "mean_drop":
        return raw * 100.0
    return raw

def _fixed_slice(img, mask, z, axis=2):
    """Slice `img` at index `z` along `axis`, masking to `mask`, oriented for display."""
    img_s = np.take(img, z, axis=axis)
    mask_s = np.take(mask, z, axis=axis)
    return np.rot90(np.where(mask_s, img_s, np.nan)), np.rot90(mask_s)

def caption(draws, i):
    """Metric values for scenario i, using the displayed metrics."""
    md   = draws["mean_drop"][i]              # fraction
    cv   = draws["cv"][i]
    r2   = draws["corr_lambda"][i] ** 2       # R^2
    roc  = -draws["long_decline"][i]          # signed: always a decrease
    return (f"$\\Delta_\\mu$ = {md:.1%}   CV = {cv:.2f}\n"
            f"$R^2$ = {r2:.2f}   ROC = {roc:.1%}")


def run_experiment(sc):
    red = default_reduction(sc)
    print(f"\n\n{'#'*78}")
    print(f"# {sc}   (uniform {red:.0%} reduction inside ROI)")
    print(f"{'#'*78}")

    rng = np.random.default_rng(2)
    draws = {k: rng.uniform(*v, N_SCEN) for k, v in RANGES.items()}

    rmse, depth, prog = [], [], []
    for i in range(N_SCEN):
        r = run_scenario(*[draws[k][i] for k in ORDER],
                         scenario=sc, pool_followup=True, n_seeds=1)
        rmse.append(r["rmse"]); depth.append(r["depth"]); prog.append(r["rec_prog"])
        print(f"\r  scenario {i+1}/{N_SCEN} done", end="", flush=True)

    rmse = np.array(rmse); depth = np.array(depth); prog = np.array(prog)
    TRUE_DEPTH, TRUE_PROG = r["true_depth"], r["true_prog"]

    print(f"\ntrue depth={TRUE_DEPTH:.3f}  true progression={TRUE_PROG:.3f}")
    print(f"RMSE  : {rmse.min():.4f} - {rmse.max():.4f}")
    print(f"depth : {depth.min():.3f} - {depth.max():.3f}")

    # ---- multiple regression: independent contribution of each metric ------
    # use the DISPLAYED metric values (corr_lambda -> R^2)
    X = np.column_stack([metric_value(k, draws[k]) for k in RANGES])
    Xs = (X - X.mean(0)) / X.std(0)               # standardised -> comparable betas
    A = np.column_stack([np.ones(N_SCEN), Xs])
    beta, *_ = np.linalg.lstsq(A, rmse, rcond=None)
    pred = A @ beta
    R2_fit = 1 - ((rmse-pred)**2).sum() / ((rmse-rmse.mean())**2).sum()

    print(f"\nStandardised regression of RMSE on the four metrics (R2={R2_fit:.3f}):")
    for k, b in zip(RANGES, beta[1:]):
        print(f"  {k:<13} beta = {b:+.4f}")

    print(f"\nPearson correlation between RMSE and each metric ({sc}):")
    for k in ORDER:
        x = metric_value(k, draws[k])
        rho, pval = pearsonr(x, rmse)
        star = "***" if pval < 1e-3 else "**" if pval < 1e-2 else "*" if pval < 0.05 else ""
        print(f"  {TITLES[k]:<26} ({k:<12}) r = {rho:+.3f}   p = {pval:.3g} {star}")

    # ---- marginal scatter: RMSE vs each metric -----------------------------
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    for j, k in enumerate(ORDER):
        x = metric_value(k, draws[k])             # displayed metric (R^2 for corr_lambda)
        y = rmse
        ax = axes[j]
        ax.scatter(x, y, s=14, alpha=.55, color=COLORS[k], edgecolor="none")
        o = np.argsort(x); p = np.poly1d(np.polyfit(x, y, 1))
        ax.plot(x[o], p(x[o]), color="k", lw=1.6, ls="--")
        ax.grid(alpha=.25, ls=":")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylim(0, rmse.max()*1.08)
        ax.set_xlabel(XLABELS[k], fontsize=14)
        ax.tick_params(labelsize=13)              # tick number size
        if j == 0:
            ax.set_ylabel("RMSE", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, .96])
    plt.savefig(f"random_scenarios_{sc}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ---- best / worst visual reading ---------------------------------------
    best_i, worst_i = int(np.argmin(rmse)), int(np.argmax(rmse))
    for lab, i in [("BEST ", best_i), ("WORST", worst_i)]:
        vals = "  ".join(f"{k}={draws[k][i]:.2f}" for k in RANGES)
        print(f"\n{lab} scenario (#{i}): RMSE={rmse[i]:.4f} depth={depth[i]:.3f}")
        print(f"       {vals}")

    ex_b = run_scenario(*[draws[k][best_i]  for k in ORDER],
                        scenario=sc, pool_followup=True, n_seeds=1)
    ex_w = run_scenario(*[draws[k][worst_i] for k in ORDER],
                        scenario=sc, pool_followup=True, n_seeds=1)
    mask = ex_b["example"]["mask"]

    gm = load_gm() & mask            # GM voxels within the brain mask


    # colour range widens with the reduction depth
    VRANGE = {0.2: (0.7, 1.3), 0.4: (0.5, 1.5), 0.6: (0.3, 1.7)}
    vmin, vmax = VRANGE.get(round(red, 2), (0.7, 1.3))   # fallback = tightest

    fig2, axes2 = plt.subplots(1, 3, figsize=(10, 5.8))
    panels = [
        (axes2[0], ex_b["example"]["truth"],
         "Ground truth",                       f"true depth = {TRUE_DEPTH:.3f}"),
        (axes2[1], ex_b["example"]["recovered"],
         f"BEST   RMSE = {rmse[best_i]:.3f}",  caption(draws, best_i)),
        (axes2[2], ex_w["example"]["recovered"],
         f"WORST  RMSE = {rmse[worst_i]:.3f}", caption(draws, worst_i)),
    ]
    for ax, img, title, sub in panels:
        sliced_img, sliced_mask = _fixed_slice(img, gm, 60)
        im = ax.imshow(sliced_img, cmap="RdBu_r", vmin=vmin, vmax=vmax)
        ax.contour(sliced_mask, colors="k", linewidths=0.5, alpha=0.5)
        ax.set_title(title, fontsize=10, fontweight="bold", y =0.92)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_frame_on(False)
        ax.text(0.5, 0.04, sub, transform=ax.transAxes,
                ha="center", va="top", fontsize=8.5, linespacing=1.5)
    plt.colorbar(im, ax=axes2, fraction=.03, pad=.1, shrink=0.6, label="recovered ratio")

    plt.savefig(f"best_worst_{sc}.png", dpi=300, bbox_inches="tight")
    plt.close(fig2)
    print(f"\nfigures: random_scenarios_{sc}.png, best_worst_{sc}.png")


if __name__ == "__main__":
    for sc in SCENARIOS:
        run_experiment(sc)
