import numpy as np

def _standardize(x):
    x = np.asarray(x, float)
    s = x.std()
    return (x - x.mean()) / (s if s > 0 else 1.0)

def _orthogonalize(y, x):
    xs = _standardize(x)
    y = np.asarray(y, float)
    resid = y - (np.dot(y, xs) / len(xs)) * xs
    return _standardize(resid)

def _draw(n, dist, rng):
    if dist == "student_t":
        return rng.standard_t(3, n)
    return rng.normal(0.0, 1.0, n)

def sample_sf_control(n, hc_mean=1.0, hc_cv=0.02, dist="gaussian", rng=None):
    if rng is None:
        rng = np.random.default_rng()
    sf = hc_mean * (1.0 + hc_cv * _standardize(_draw(n, dist, rng)))
    return np.clip(sf, 1e-6, None)

def sample_sf_disease(lams, hc_mean=1.0, mean_drop=0.0, corr_lambda=0.0,
                      cv=0.02, dist="gaussian", rng=None):
    if rng is None:
        rng = np.random.default_rng()
    lams = np.asarray(lams, float)
    n = len(lams)
    mu = hc_mean * (1.0 - mean_drop)
    sd = cv * mu
    rho = float(np.clip(corr_lambda, 0.0, 1.0))
    noise = _draw(n, dist, rng)
    if lams.std() > 0 and rho > 0:
        z_lam = _standardize(lams)
        z_perp = _orthogonalize(noise, lams)
        u = -rho * z_lam + np.sqrt(1.0 - rho ** 2) * z_perp
    else:
        u = _standardize(noise)
    return np.clip(mu + sd * u, 1e-6, None)

def sample_sf_followup(sf_baseline, long_decline=0.0, long_noise=0.0,
                       dist="gaussian", rng=None):
    if rng is None:
        rng = np.random.default_rng()
    sf_baseline = np.asarray(sf_baseline, float)
    n = len(sf_baseline)
    sf = sf_baseline * (1.0 - long_decline)
    if long_noise > 0:
        wobble = long_noise * _standardize(_draw(n, dist, rng))
        sf = sf * (1.0 + wobble)
    return np.clip(sf, 1e-6, None)