"""
Fatigue & Reliability Prediction Engine - Production v2 (Corrected)

Capabilities:
- Goodman mean stress correction
- Basquin S–N fatigue life
- Miner cumulative damage (variable amplitude)
- Monte Carlo uncertainty
- Weibull failure probability & MTBF
- Engineering plots saved automatically
"""

import math
import numpy as np
import matplotlib.pyplot as plt


# -------------------------------------------------
# Material Model
# -------------------------------------------------

class Material:
    def __init__(self, name, ultimate_strength, fatigue_strength_coeff, basquin_exponent):
        self.name = name
        self.sigma_u = ultimate_strength          # MPa
        self.sigma_f = fatigue_strength_coeff    # MPa
        self.b = basquin_exponent


# -------------------------------------------------
# Stress Utilities
# -------------------------------------------------

def alternating_stress(sig_max, sig_min):
    return 0.5 * (sig_max - sig_min)

def mean_stress(sig_max, sig_min):
    return 0.5 * (sig_max + sig_min)

def goodman(sig_a, sig_m, sigma_u):
    return sig_a / (1.0 - sig_m / sigma_u)


# -------------------------------------------------
# Fatigue Life (Basquin)
# -------------------------------------------------

def fatigue_cycles(material, sig_a_eq):
    return (material.sigma_f / sig_a_eq) ** (1.0 / material.b)


# -------------------------------------------------
# Miner Damage Accumulation
# -------------------------------------------------

def miner_damage(load_blocks, material):
    """
    load_blocks = [(sig_max, sig_min, cycles), ...]
    """
    D = 0.0
    block_results = []

    for sig_max, sig_min, n in load_blocks:
        sig_a = alternating_stress(sig_max, sig_min)
        sig_m = mean_stress(sig_max, sig_min)
        sig_eq = goodman(sig_a, sig_m, material.sigma_u)
        Nf = fatigue_cycles(material, sig_eq)

        d = n / Nf
        D += d

        block_results.append((sig_eq, Nf, d))

    return D, block_results


# -------------------------------------------------
# Weibull Reliability (Vectorized Safe)
# -------------------------------------------------

def weibull_failure_probability(t, beta, eta):
    t = np.asarray(t)
    return 1.0 - np.exp(- (t / eta) ** beta)

def mtbf_from_weibull(beta, eta):
    return eta * math.gamma(1.0 + 1.0 / beta)


# -------------------------------------------------
# Monte Carlo Reliability Simulation
# -------------------------------------------------

def monte_carlo_reliability(material, load_blocks, beta, eta, samples=10000):
    lives = []

    for _ in range(samples):
        strength_scale = np.random.normal(1.0, 0.05)

        mat = Material(
            material.name,
            material.sigma_u * strength_scale,
            material.sigma_f * strength_scale,
            material.b,
        )

        D, _ = miner_damage(load_blocks, mat)
        D_safe = max(D, 1e-6)

        life_cycles = (1.0 / D_safe) * eta
        lives.append(life_cycles)

    return np.array(lives)


# -------------------------------------------------
# Engineering Plots
# -------------------------------------------------

def plot_weibull(beta, eta):
    t = np.linspace(0, 2 * eta, 500)
    F = weibull_failure_probability(t, beta, eta)

    plt.figure()
    plt.plot(t, F)
    plt.xlabel("Cycles")
    plt.ylabel("Failure Probability")
    plt.title("Weibull Reliability Curve")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("weibull_reliability.png", dpi=150)
    plt.close()

def plot_monte_carlo(lives):
    plt.figure()
    plt.hist(lives, bins=60, density=True)
    plt.xlabel("Predicted Life (Cycles)")
    plt.ylabel("Probability Density")
    plt.title("Monte Carlo Fatigue Life Distribution")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("monte_carlo_life_distribution.png", dpi=150)
    plt.close()


# -------------------------------------------------
# Main Engineering Analysis
# -------------------------------------------------

def main():

    # --- Material Definition ---
    steel = Material(
        name="AISI 1045 Steel",
        ultimate_strength=625,     # MPa
        fatigue_strength_coeff=900,
        basquin_exponent=-0.11
    )

    # --- Variable Amplitude Load Spectrum ---
    load_blocks = [
        (320, 40, 120_000),   # High stress block
        (240, 60, 200_000),
        (180, 80, 500_000)
    ]

    # --- Damage Accumulation ---
    D, blocks = miner_damage(load_blocks, steel)

    print("\n=== FATIGUE DAMAGE REPORT ===")
    for i, (sig_eq, Nf, d) in enumerate(blocks, 1):
        print(f"Block {i}: σ_eq = {sig_eq:.1f} MPa | Nf = {Nf:,.0f} | Damage = {d:.4f}")

    print(f"\nTotal cumulative damage D = {D:.6f}")
    print("Status:", "FAILURE EXPECTED" if D >= 1.0 else "SAFE")

    # --- Weibull Reliability ---
    beta = 1.6

    MIN_D = 1e-6
    D_safe = max(D, MIN_D)
    eta = (1.0 / D_safe) * 1_000_000

    mtbf = mtbf_from_weibull(beta, eta)

    print("\n=== RELIABILITY MODEL ===")
    print(f"Weibull beta = {beta}")
    print(f"Weibull eta  = {eta:,.0f} cycles")
    print(f"MTBF         = {mtbf:,.0f} cycles")

    plot_weibull(beta, eta)

    # --- Monte Carlo Uncertainty ---
    lives = monte_carlo_reliability(steel, load_blocks, beta, eta)

    print("\n=== MONTE CARLO LIFE ===")
    print(f"Mean life = {np.mean(lives):,.0f} cycles")
    print(f"5% life   = {np.percentile(lives,5):,.0f} cycles")
    print(f"95% life  = {np.percentile(lives,95):,.0f} cycles")

    plot_monte_carlo(lives)


if __name__ == "__main__":
    main()
