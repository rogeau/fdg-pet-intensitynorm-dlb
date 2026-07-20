"""
END-TO-END: which scaling-factor properties recover the true pattern?
====================================================================

  1. PATTERN   : hoffman_nii/wpet_brain_only.nii = normal pattern (real GM/WM
                 contrast). Disease = UNIFORM reduction inside a binary ROI.
  2. SAMPLE    : image = normal * (1 - max_red*lambda*effect) * g + noise
                 A 1/5 subset of patients is RE-SCANNED at follow-up with
                 progressed disease (lambda x (1+PROGRESSION)).
  3. SCALING   : SF with four adjustable properties (see scaling_factor.py)
  4. NORMALIZE : image / SF
  5. RECOVER   : cross-sectional -> mean(DLB_norm) / mean(HC_norm)
                 longitudinal    -> mean(FU_norm)  / mean(BL_norm)  [subset]
  6. SCORE     : vs KNOWN ground truth
                 depth      : recovered lesion depth (drifts to 1.0 = MASKED)
                 RMSE       : whole-brain error
                 prog       : recovered progression (drifts to 1.0 = MASKED)

THREE INDEPENDENT EXPERIMENTS, one per ROI:
    L_parietal      ROI_L_parietal.nii             20% reduction
    bilat_TP        ROI_bilat_temporoparietal.nii  40% reduction
    bilat_PFC_PTO   ROI_bilat_PFC_PTO.nii          60% reduction
Each is a separate cohort with its own ground truth. The full factorial (or
random-scenario) analysis is run once per ROI.

Because the effect map is BINARY, `core` is the entire ROI and `true_depth` is
exactly 1 - max_reduction. RMSE now measures how faithfully normalization
reproduces a step edge, not gradient fidelity.

Two cross-sectional variants are run:
  POOL_FOLLOWUP = False (PRIMARY)   patient group = baseline scans only.
      Gives a clean DOUBLE DISSOCIATION: long_decline is structurally invisible
      cross-sectionally and shows up only longitudinally.

  POOL_FOLLOWUP = True  (SECONDARY) patient group = baseline + follow-up scans.
      A declining reference now contaminates the cross-sectional contrast too.
      The size of that contamination depends on the MIXING RATIO (how many
      repeat scans are pooled), not on the reference region itself.

CAUTION on the pooled analysis: pooled follow-up scans come from genuinely
sicker subjects, which deepens the apparent lesion; a declining denominator
inflates them back up. Near decline ~ PROGRESSION the two effects CANCEL and
`depth` looks accurate while RMSE is already degrading. Read RMSE, not depth.
"""
import itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pattern import (make_diseased, get_effect_map, default_reduction, load_gm,
                     SCENARIOS)
from sampling import sample_subjects, sample_followup, unflatten
from scaling_factor import (sample_sf_control, sample_sf_disease,
                            sample_sf_followup, compute_metrics)


GOOD_BAD = {
    "align":  {"good": 0.00, "bad": 0.25},   # mean_drop
    "indep":  {"good": 0.00, "bad": 0.80},   # corr_lambda (magnitude)
    "stable": {"good": 0.02, "bad": 0.25},   # cv
    "longit": {"good": 0.00, "bad": 0.12},   # long_decline
}

N_SUBJ      = 50
FRAC_LONG   = 0.20          # 1/5 of patients re-scanned
PROGRESSION = 0.30          # disease worsens 30% by follow-up
N_SEEDS     = 1

DEFAULT_SCENARIO = "bilat_TP"


def _mean_image(imgs, sf):
    """
    Mean of imgs / sf over subjects. `imgs` is flat (n, n_brain_vox).

    Computed as a matrix-vector product (1/sf) @ imgs / n, which BLAS does in
    one pass with no temporary. The obvious `(imgs / sf[:,None]).mean(0)`
    allocates a full second copy of the stack.
    """
    w = (1.0 / np.asarray(sf, dtype=np.float64)) / len(sf)
    return w @ imgs


def run_once(mean_drop, corr_lambda, cv, long_decline, seed,
             scenario=DEFAULT_SCENARIO, pool_followup=False, n=None,
             keep_example=False):
    # `None` sentinels: reading the module global at CALL time means
    # `pipeline.N_SUBJ = 40` actually takes effect. A default of `n=N_SUBJ`
    # would bind once at import and silently ignore later reassignment.
    if n is None:
        n = N_SUBJ
    rng = np.random.default_rng(seed)
    max_reduction = default_reduction(scenario)

    # ---- ground truth -----------------------------------------------------
    diseased_img, truth, mask = make_diseased(scenario)
    effect_map, _ = get_effect_map(scenario)
    core = mask & (effect_map > 0.90)          # binary map -> core == whole ROI
    true_depth = truth[core].mean()            # == 1 - max_reduction

    # ---- cohorts ----------------------------------------------------------
    hc,  lam_hc,  g_hc,  _ = sample_subjects(n, scenario, group="normal",  rng=rng)
    dlb, lam_dlb, g_dlb, _ = sample_subjects(n, scenario, group="disease", rng=rng)

    sf_hc  = sample_sf_control(n, rng=rng)
    sf_dlb = sample_sf_disease(lam_dlb, mean_drop=mean_drop,
                               corr_lambda=corr_lambda, cv=cv, rng=rng)

    # ---- longitudinal subset (1/5 of patients, re-scanned) ---------------
    k = max(2, int(round(FRAC_LONG * n)))
    sub = rng.choice(n, k, replace=False)
    bl = dlb[sub]
    fu, lam_fu, g_fu, _ = sample_followup(lam_dlb[sub], scenario,
                                          progression=PROGRESSION, rng=rng)

    sf_bl = sf_dlb[sub]                       # same subjects, their own baseline SF
    sf_fu = sample_sf_followup(sf_bl, long_decline=long_decline, rng=rng)

    # ---- CROSS-SECTIONAL recovery ----------------------------------------
    # patient group is either baseline only, or baseline + pooled follow-ups
    hc_mean = _mean_image(hc, sf_hc)
    if pool_followup:
        dlb_all = np.concatenate([dlb, fu], axis=0)
        sf_all  = np.concatenate([sf_dlb, sf_fu], axis=0)
        dlb_mean = _mean_image(dlb_all, sf_all)
    else:
        dlb_mean = _mean_image(dlb, sf_dlb)

    rec_flat  = dlb_mean / hc_mean               # flat, in-mask
    truth_flat = truth[mask]
    core_flat  = core[mask]
    gm_flat    = load_gm()[mask]

    rmse  = np.sqrt(np.mean((rec_flat - truth_flat) ** 2))
    depth = rec_flat[core_flat].mean()

    # ---- LONGITUDINAL recovery (always the repeat subset) ----------------
    bl_mean = _mean_image(bl, sf_bl)[core_flat]
    fu_mean = _mean_image(fu, sf_fu)[core_flat]

    e_core = effect_map[core].mean()                # == 1.0 for a binary map
    tp = 1.0 - max_reduction * lam_fu.mean()       * e_core
    tb = 1.0 - max_reduction * lam_dlb[sub].mean() * e_core
    true_prog = tp / tb                            # < 1.0 : disease worsened
    rec_prog  = fu_mean.mean() / bl_mean.mean()

    # ---- metrics a real study could measure ------------------------------
    a, dc, cvm, lg = compute_metrics(sf_hc, sf_dlb, lam_dlb, sf_bl, sf_fu)

    out = dict(rmse=rmse, depth=depth, true_depth=true_depth,
               rec_prog=rec_prog, true_prog=true_prog,
               align=a, corr=dc, cv=cvm, longit=lg,
               n_long=k, scenario=scenario)
    if keep_example:
        out.update(recovered=unflatten(rec_flat, mask, fill=1.0),
                   truth=truth, mask=mask, core=core,
                   diseased=diseased_img,
                   dlb_mean=unflatten(dlb.mean(0), mask, fill=0.0))
    return out


def run_scenario(mean_drop, corr_lambda, cv, long_decline,
                 scenario=DEFAULT_SCENARIO, pool_followup=False,
                 n_seeds=None):
    if n_seeds is None:
        n_seeds = N_SEEDS
    reps = [run_once(mean_drop, corr_lambda, cv, long_decline, seed=s,
                     scenario=scenario, pool_followup=pool_followup,
                     keep_example=(s == 0))
            for s in range(n_seeds)]
    keys = ("rmse","depth","true_depth","rec_prog","true_prog",
            "align","corr","cv","longit")
    agg = {k: float(np.mean([r[k] for r in reps])) for k in keys}
    agg["example"]  = reps[0]
    agg["n_long"]   = reps[0]["n_long"]
    agg["scenario"] = scenario
    return agg


def all_scenarios(pool_followup, scenario=DEFAULT_SCENARIO):
    labels = ["align", "indep", "stable", "longit"]
    results = {}
    for combo in itertools.product(["good","bad"], repeat=4):
        cfg = dict(zip(labels, combo))
        r = run_scenario(GOOD_BAD["align"][cfg["align"]],
                         GOOD_BAD["indep"][cfg["indep"]],
                         GOOD_BAD["stable"][cfg["stable"]],
                         GOOD_BAD["longit"][cfg["longit"]],
                         scenario=scenario, pool_followup=pool_followup)
        key = "/".join(c[:1].upper() if c=="good" else c[:1] for c in combo)
        results[key] = r
    return labels, results


def marginals(labels, results, metric):
    out = {}
    for j, prop in enumerate(labels):
        good = [metric(v) for k,v in results.items() if k.split("/")[j]=="G"]
        bad  = [metric(v) for k,v in results.items() if k.split("/")[j]=="b"]
        out[prop] = np.mean(bad) - np.mean(good)
    return out


# ------------------------------------------------------------------ display
def _mid_slice(vol, mask):
    """Axial slice through the centre of mass of the mask, as a 2D array."""
    zs = np.where(mask.any(axis=(0, 1)))[0]
    z = int(round(zs.mean()))
    sl = np.where(mask[:, :, z], vol[:, :, z], np.nan)
    return np.rot90(sl)


def _run_one_experiment(scenario):
    red = default_reduction(scenario)
    n_fu = int(round(FRAC_LONG * N_SUBJ))
    print(f"\n\n{'#'*92}")
    print(f"# EXPERIMENT: {scenario}   (uniform {red:.0%} reduction inside ROI)")
    print(f"{'#'*92}")
    print(f"n={N_SUBJ} per group; {n_fu} patients re-scanned "
          f"(progression +{PROGRESSION:.0%})")

    summary = {}
    for pool in [False, True]:
        tag = "SECONDARY: POOLED (baseline + follow-up)" if pool \
              else "PRIMARY: BASELINE ONLY"
        labels, results = all_scenarios(pool, scenario=scenario)
        summary[pool] = (labels, results)

        print(f"\n{'='*92}\n{tag}\n{'='*92}")
        hdr = (f"{'align/indep/stable/longit':<30}{'RMSE':>8}{'depth':>8}"
               f"{'prog':>8}{'|':>2}{'m_align':>9}{'m_corr':>8}{'m_CV':>7}{'m_long':>8}")
        print(hdr); print("-"*len(hdr))
        for key, r in results.items():
            pretty = "/".join(f"{'good' if c=='G' else 'bad':<5}" for c in key.split("/"))
            print(f"{pretty:<30}{r['rmse']:>8.3f}{r['depth']:>8.3f}"
                  f"{r['rec_prog']:>8.3f}{'|':>2}{r['align']:>9.3f}"
                  f"{r['corr']:>8.3f}{r['cv']:>7.3f}{r['longit']:>8.3f}")

        ex = results["G/G/G/G"]
        print(f"\ntrue depth = {ex['true_depth']:.3f}   "
              f"true progression = {ex['true_prog']:.3f}")

        mx = marginals(labels, results, lambda v: v["rmse"])
        print("\nMarginal effect on CROSS-SECTIONAL RMSE (bad - good):")
        for p, v in mx.items():
            print(f"  {p:<8}: {v:+.4f}")

        ml = marginals(labels, results,
                       lambda v: abs(v["rec_prog"] - v["true_prog"]))
        print("Marginal effect on LONGITUDINAL error |rec_prog - true_prog|:")
        for p, v in ml.items():
            print(f"  {p:<8}: {v:+.4f}")

    # ---------------- headline comparison ---------------------------------
    lb, res_base = summary[False]
    _,  res_pool = summary[True]
    mb = marginals(lb, res_base, lambda v: v["rmse"])
    mp = marginals(lb, res_pool, lambda v: v["rmse"])
    print(f"\n{'='*92}\nEFFECT OF POOLING on the cross-sectional marginals\n{'='*92}")
    print(f"{'property':<10}{'baseline-only':>16}{'pooled':>12}{'change':>12}")
    for p in lb:
        print(f"{p:<10}{mb[p]:>16.4f}{mp[p]:>12.4f}{mp[p]-mb[p]:>+12.4f}")
    print(f"\n-> 'longit' is exactly 0 when baseline-only (structurally invisible),")
    print(f"   and becomes non-zero once follow-up scans are pooled. Its pooled")
    print(f"   magnitude scales with the mixing ratio ({n_fu}/{N_SUBJ+n_fu} scans),")
    print(f"   not with any property of the reference region.")

    # ---------------- figure (primary analysis) ---------------------------
    best  = min(res_base.items(), key=lambda kv: kv[1]["rmse"])
    worst = max(res_base.items(), key=lambda kv: kv[1]["rmse"])
    mask = best[1]["example"]["mask"]
    fig, axes = plt.subplots(1, 3, figsize=(9, 5.4))
    for ax,img,ttl in [(axes[0], best[1]["example"]["truth"], "Ground truth"),
                       (axes[1], best[1]["example"]["recovered"],  f"BEST {best[0]}"),
                       (axes[2], worst[1]["example"]["recovered"], f"WORST {worst[0]}")]:
        im = ax.imshow(_mid_slice(img, mask), cmap="RdBu_r", vmin=0.3, vmax=1.15)
        ax.set_title(ttl, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
        ax.set_frame_on(False)
    fig.suptitle(f"{scenario}  ({red:.0%} reduction)", fontsize=10)
    plt.colorbar(im, ax=axes, fraction=0.03, pad=0.02)
    out = f"recovery_{scenario}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nfigure written: {out}")
    return summary


if __name__ == "__main__":
    for sc in SCENARIOS:
        _run_one_experiment(sc)
