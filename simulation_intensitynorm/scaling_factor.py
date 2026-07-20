"""
Direct sampling of scaling factors from their four group-level properties.
==========================================================================

No generative mechanism is assumed. There is no global uptake factor, no
decomposition of the scaling factor into parts, and no presupposed relationship
between the properties. Scaling factors are simply DRAWN so that the four
quantities a study would measure come out at requested values.

The four properties
-------------------
  1. mean_drop     difference in mean between groups.
                   mean(SF_dlb) = mean(SF_hc) * (1 - mean_drop)
                   Always a DECREASE: a reference region loses uptake in
                   neurodegeneration, never gains it. 0 = groups aligned.

  2. corr_lambda   correlation, within patients, between each subject's scaling
                   factor and that subject's disease severity lambda.
                   Magnitude in [0, 1]; the sign is forced NEGATIVE, because a
                   sicker subject has a lower scaling factor.
                   0 = disease-independent, 1 = fully disease-driven.

  3. cv            coefficient of variation of the scaling factors within the
                   patient group. Low = interindividually stable.

  4. long_decline  in the follow-up subgroup, the group-level fractional DROP
                   of the scaling factor from baseline to follow-up.
                   Always a decrease. 0 = longitudinally stable.
     long_noise    random, unbiased per-scan wobble on top of that drop. Adds
                   variance to the measured change without biasing it.

What is and is not assumed
--------------------------
Two moments and one correlation do not determine a distribution uniquely, so
some family must be chosen. We draw from the MAXIMUM-ENTROPY distribution
consistent with the constraints (the Gaussian one), which adds no structure
beyond what was requested. This is the least-committal option, but it is still
a choice: it fixes a linear dependence on lambda and suppresses tail behaviour.
Because a scaling factor that strays near zero destroys individual scans
irrespective of its group-level properties, `dist="student_t"` is provided as a
robustness check.

How the correlation is imposed
------------------------------
    SF = mu + sd * u,        mu = mean_hc * (1 - mean_drop),   sd = cv * mu
    u  = -rho * z_lambda + sqrt(1 - rho^2) * z_perp

z_lambda is standardized lambda, z_perp is standardized noise from which the
lambda component has been regressed out. Then var(u) = 1 and corr(u, lambda) =
-rho, both exactly. Note that mu and sd cannot disturb the correlation:
correlation is invariant to additive shifts and positive rescaling. So the three
cross-sectional properties are independent knobs by construction, and no
orthogonalization between them is needed -- only between the noise and lambda.
"""
import numpy as np


# ---------------------------------------------------------------- helpers
def _standardize(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / (s if s > 0 else 1.0)


def _orthogonalize(y, x):
    """Standardized residual of y after regressing out x."""
    xs = _standardize(x)
    y = np.asarray(y, float)
    resid = y - (np.dot(y, xs) / len(xs)) * xs
    return _standardize(resid)


def _draw(n, dist, rng):
    if dist == "student_t":
        return rng.standard_t(3, n)      # heavy tails: robustness check
    return rng.normal(0.0, 1.0, n)


# ---------------------------------------------------------------- HC group
def sample_sf_control(n, hc_mean=1.0, hc_cv=0.02, dist="gaussian", rng=None):
    """Scaling factors for healthy controls: the normative reference level."""
    if rng is None:
        rng = np.random.default_rng()
    sf = hc_mean * (1.0 + hc_cv * _standardize(_draw(n, dist, rng)))
    return np.clip(sf, 1e-6, None)


# ---------------------------------------------------------------- patients
def sample_sf_disease(lams,
                      hc_mean=1.0,       # the HC mean the drop is measured against
                      mean_drop=0.0,     # property 1: fractional decrease vs HC
                      corr_lambda=0.0,   # property 2: |corr| with severity
                      cv=0.02,           # property 3: CV within patients
                      dist="gaussian",
                      rng=None):
    """
    Draw baseline scaling factors for patients satisfying properties 1-3.
    `lams` is each patient's disease severity, needed only to impose property 2.
    """
    if rng is None:
        rng = np.random.default_rng()
    lams = np.asarray(lams, float)
    n = len(lams)

    mu = hc_mean * (1.0 - mean_drop)      # property 1
    sd = cv * mu                          # property 3
    rho = float(np.clip(corr_lambda, 0.0, 1.0))

    noise = _draw(n, dist, rng)
    if lams.std() > 0 and rho > 0:
        z_lam = _standardize(lams)
        z_perp = _orthogonalize(noise, lams)          # remove accidental corr
        u = -rho * z_lam + np.sqrt(1.0 - rho ** 2) * z_perp   # property 2
    else:
        u = _standardize(noise)

    return np.clip(mu + sd * u, 1e-6, None)


# ---------------------------------------------------------------- follow-up
def sample_sf_followup(sf_baseline,
                       long_decline=0.0,   # property 4: group-level fractional drop
                       long_noise=0.0,     # unbiased per-scan wobble
                       dist="gaussian",
                       rng=None):
    """
    Draw follow-up scaling factors for the SAME patients.

    Property 4 is a within-subject property, so the follow-up values are derived
    from each subject's own baseline rather than drawn independently. The group
    mean falls by `long_decline`; `long_noise` adds unbiased scatter around it.
    """
    if rng is None:
        rng = np.random.default_rng()
    sf_baseline = np.asarray(sf_baseline, float)
    n = len(sf_baseline)

    sf = sf_baseline * (1.0 - long_decline)           # systematic group decrease
    if long_noise > 0:
        wobble = long_noise * _standardize(_draw(n, dist, rng))
        sf = sf * (1.0 + wobble)                      # unbiased: mean(wobble)=0
    return np.clip(sf, 1e-6, None)


# ---------------------------------------------------------------- metrics
def compute_metrics(sf_hc, sf_dlb, lams_dlb, sf_bl=None, sf_fu=None):
    """The four properties, measured directly on the scaling factors."""
    mean_drop = 1.0 - sf_dlb.mean() / sf_hc.mean()     # >0 : patients lower
    corr_lam = np.corrcoef(sf_dlb, lams_dlb)[0, 1]     # negative by design
    cv = sf_dlb.std() / sf_dlb.mean()
    longit = np.nan
    if sf_bl is not None and sf_fu is not None:
        longit = 1.0 - sf_fu.mean() / sf_bl.mean()     # >0 : declined
    return mean_drop, corr_lam, cv, longit


# ---------------------------------------------------------------- demo
if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 4000
    lam = np.clip(rng.normal(1.0, 0.25, n), 0.0, None)

    def check(dist="gaussian", **kw):
        r = np.random.default_rng(1)
        hc = sample_sf_control(n, dist=dist, rng=r)
        bl = sample_sf_disease(lam, mean_drop=kw.get("mean_drop", 0.0),
                               corr_lambda=kw.get("corr_lambda", 0.0),
                               cv=kw.get("cv", 0.02), dist=dist, rng=r)
        fu = sample_sf_followup(bl, long_decline=kw.get("long_decline", 0.0),
                                long_noise=kw.get("long_noise", 0.0),
                                dist=dist, rng=r)
        return compute_metrics(hc, bl, lam, bl, fu)

    print("Each property is drawn to target, independently of the others.\n")
    print(f"{'requested':<34}{'measured':<40}")
    print(f"{'drop':>7}{'corr':>7}{'cv':>7}{'decl':>7}{'':>6}"
          f"{'drop':>8}{'corr':>9}{'cv':>8}{'decl':>8}")
    print("-" * 74)
    grid = [(0.00, 0.00, 0.02, 0.00),
            (0.25, 0.00, 0.02, 0.00),    # only the mean difference
            (0.00, 0.80, 0.02, 0.00),    # only the correlation
            (0.00, 0.00, 0.25, 0.00),    # only the CV
            (0.00, 0.00, 0.02, 0.12),    # only the longitudinal decline
            (0.25, 0.80, 0.25, 0.12)]    # all four at once
    for md, cl, c, dc in grid:
        r = check(mean_drop=md, corr_lambda=cl, cv=c, long_decline=dc)
        print(f"{md:>7.2f}{cl:>7.2f}{c:>7.2f}{dc:>7.2f}{'':>6}"
              f"{r[0]:>8.3f}{r[1]:>9.3f}{r[2]:>8.3f}{r[3]:>8.3f}")
    print("\n(corr is negative by construction: sicker subject -> lower SF)")

    print("\nlong_noise adds variance to the measured change, not bias:")
    for ln in [0.0, 0.05, 0.15]:
        r = check(long_decline=0.10, long_noise=ln)
        print(f"  long_noise={ln:.2f} -> measured decline={r[3]:.4f} (target 0.10)")

    print("\nRobustness: same moments, heavy-tailed draw")
    for d in ["gaussian", "student_t"]:
        r = check(dist=d, mean_drop=0.10, corr_lambda=0.5, cv=0.25)
        print(f"  {d:<10} drop={r[0]:+.3f} corr={r[1]:+.3f} cv={r[2]:.3f}")
