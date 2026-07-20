"""
Figure: how scaling factors are generated from their four group-level properties.

Each panel isolates ONE property, holding the other three at their neutral
(no-effect) values, so the reader sees exactly what each knob does to the
distribution of scaling factors.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import sf_sampling as sf

# ----------------------------------------------------------------- palette
HC_COLOR   = "#4C72B0"   # healthy controls
DLB_COLOR  = "#C44E52"   # patients (baseline)
FU_COLOR   = "#8172B3"   # follow-up
ACCENT     = "#55A868"   # trend / regression line
GRID       = "#D9D9D9"

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "figure.dpi": 120,
})

# ----------------------------------------------------------------- data
rng  = np.random.default_rng(7)
N    = 4000
lam  = np.clip(rng.normal(1.0, 0.25, N), 0.0, None)   # disease severity
HCM  = 1.0

# neutral baseline patient sample (all properties off)
def draw_patients(mean_drop=0.0, corr_lambda=0.0, cv=0.02, seed=1):
    r = np.random.default_rng(seed)
    return sf.sample_sf_disease(lam, hc_mean=HCM, mean_drop=mean_drop,
                                corr_lambda=corr_lambda, cv=cv, rng=r)

hc = sf.sample_sf_control(N, hc_mean=HCM, hc_cv=0.02,
                          rng=np.random.default_rng(2))

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
fig.subplots_adjust(hspace=0.38, wspace=0.28,
                    top=0.90, bottom=0.10, left=0.08, right=0.97)

# ============================================================ Panel 1: mean_drop
ax = axes[0, 0]
dlb = draw_patients(mean_drop=0.15, cv=0.05)
bins = np.linspace(0.75, 1.15, 45)
ax.hist(hc,  bins=bins, color=HC_COLOR,  alpha=0.65, label="HC")
ax.hist(dlb, bins=bins, color=DLB_COLOR, alpha=0.65, label="DLB")
ax.axvline(hc.mean(),  color=HC_COLOR,  lw=2, ls="--")
ax.axvline(dlb.mean(), color=DLB_COLOR, lw=2, ls="--")
ax.annotate("", xy=(dlb.mean(), 360), xytext=(hc.mean(), 360),
            arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.4))
ax.text((hc.mean()+dlb.mean())/2, 385, "Δμ",
        ha="center", fontsize=9, style="italic")
ax.set_title("Δμ (property 1)", fontsize=10, weight="bold")
ax.set_xlabel("SF value"); ax.set_ylabel("frequency")
ax.legend(frameon=False, loc="upper left", fontsize=9)

# ============================================================ Panel 2: corr_lambda
ax = axes[0, 1]
dlb = draw_patients(corr_lambda=0.8, cv=0.08)
ax.scatter(lam, dlb, s=6, color=DLB_COLOR, alpha=0.25, edgecolors="none")
# regression line
b1, b0 = np.polyfit(lam, dlb, 1)
xs = np.linspace(lam.min(), lam.max(), 50)
ax.plot(xs, b0 + b1*xs, color=ACCENT, lw=2.5,
        label=f"fit (ρ = {np.corrcoef(lam, dlb)[0,1]:+.2f})")
ax.set_title("Pearson's ρ with λ (property 2)",
             fontsize=10, weight="bold")
ax.set_xlabel("λ"); ax.set_ylabel("SF value")
ax.legend(frameon=False, loc="upper right", fontsize=9)

# ============================================================ Panel 3: cv
ax = axes[1, 0]
bins = np.linspace(0.7, 1.3, 55)
for c, col, a in [(0.02, "#3C6E9C", 0.75), (0.10, "#C44E52", 0.55),
                  (0.20, "#E8A020", 0.45)]:
    d = draw_patients(cv=c, seed=int(c*100)+3)
    ax.hist(d, bins=bins, color=col, alpha=a, label=f"cv = {c:.2f}")
ax.set_title("CV with μ fixed (property 3)",
             fontsize=10, weight="bold")
ax.set_xlabel("SF value"); ax.set_ylabel("frequency")
ax.legend(frameon=False, loc="upper right", fontsize=9)

# ============================================================ Panel 4: longitudinal
ax = axes[1, 1]
r = np.random.default_rng(11)
sub = rng.choice(N, 200, replace=False)     # follow-up subgroup
bl  = draw_patients(mean_drop=0.10, cv=0.06, seed=5)[sub]
fu  = sf.sample_sf_followup(bl, long_decline=0.12, long_noise=0.05, rng=r)
for xb, xf in zip(bl, fu):
    ax.plot([0, 1], [xb, xf], color="#BBBBBB", lw=0.4, alpha=0.5, zorder=1)
ax.scatter(np.zeros_like(bl), bl, s=10, color=DLB_COLOR, zorder=3, label="baseline")
ax.scatter(np.ones_like(fu),  fu, s=10, color=FU_COLOR,  zorder=3, label="follow-up")
ax.plot([0, 1], [bl.mean(), fu.mean()], color="black", lw=2.5, zorder=4,
        marker="o", label="group mean")
ax.set_xlim(-0.3, 1.3)
ax.set_xticks([0, 1]); ax.set_xticklabels(["baseline", "follow-up"])
ax.set_title("ROC (property 4)",
             fontsize=10, weight="bold")
ax.set_ylabel("SF value")
ax.legend(frameon=False, loc="upper right", fontsize=8)


fig.savefig("scaling_factor_generation.png", dpi=300, bbox_inches="tight")
print("figure written")