# -*- coding: utf-8 -*-
"""Blank Control Group: Normalized Mean Band Energy with Standard Deviation

For each input voltage, analyze up to 100 time traces using FFT and plot
only one curve: normalized mean band energy with ±1 sigma error bars.
No ADV threshold or candidate markers are computed or shown.
"""

from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# User settings
# ============================================================
FOLDER = Path(".")
FILE_PATTERN = "{v}mVpp.npy"
VOLTAGE_START_MVPP = 40
VOLTAGE_END_MVPP = 130
VOLTAGE_STEP_MVPP = 5
MAX_SIGNALS = 100
T_START = 20e-6  # s
T_END = 160e-6  # s
F_LOW = 0.4e6   # Hz
F_HIGH = 0.6e6  # Hz
ENERGY_METHOD = "sum"  # 'sum' or 'trapz'

OUTPUT_FIGURE = "ADV_blank_control_mean_sigma.png"
OUTPUT_CSV = "ADV_blank_control_mean_sigma.csv"
SHOW_FIGURE = True


# ============================================================
# Signal processing
# ============================================================
def load_signals(filename):
    signals = np.load(filename, allow_pickle=True)
    if signals.ndim != 3 or signals.shape[2] != 2:
        raise ValueError(
            f"{filename}: expected shape (number_of_traces, N, 2), "
            f"received {signals.shape}"
        )
    print(f"Loaded {filename}: {signals.shape[0]} traces, {signals.shape[1]} points/trace")
    return signals


def get_signal(signals, i):
    trace = signals[i]
    return np.asarray(trace[:, 0], dtype=float), np.asarray(trace[:, 1], dtype=float)


def select_time_window(times, voltages, t_start, t_end):
    mask = (times >= t_start) & (times <= t_end)
    t = times[mask]
    y = voltages[mask]
    if t.size < 3:
        raise ValueError(f"Too few samples between {t_start:.3g} and {t_end:.3g} s")
    return t, y


def compute_fft(times, voltages):
    steps = np.diff(times)
    if np.any(steps <= 0):
        raise ValueError("Time values must be strictly increasing")
    dt = np.mean(steps)
    if not np.allclose(steps, dt, rtol=1e-3, atol=0):
        raise ValueError("Uneven sampling detected; standard FFT requires even sampling")
    n = len(voltages)
    signal = voltages - np.mean(voltages)
    window = np.hanning(n)
    coherent_gain = np.sum(window) / n
    freq = np.fft.rfftfreq(n, d=dt)
    amplitude = np.abs(np.fft.rfft(signal * window)) * (2.0 / (n * coherent_gain))
    # Correct self-conjugate bins (DC and Nyquist): only one-sided positive
    # frequencies have doubled amplitudes; DC has already been removed.
    amplitude[0] *= 0.5
    if n % 2 == 0:
        amplitude[-1] *= 0.5
    return freq, amplitude, 1.0 / dt


def calculate_band_energy(freqs, amplitude, f_low, f_high, method="sum"):
    mask = (freqs >= f_low) & (freqs <= f_high)
    f = freqs[mask]
    a = amplitude[mask]
    if len(f) < 2:
        raise ValueError(
            f"Only {len(f)} bins between {f_low / 1e6:.3f} and {f_high / 1e6:.3f} MHz"
        )
    if method == "sum":
        return float(np.sum(a ** 2))
    if method == "trapz":
        integrate = getattr(np, "trapezoid", None)
        if integrate is None:
            integrate = np.trapz
        return float(integrate(a ** 2, f))
    raise ValueError("ENERGY_METHOD must be 'sum' or 'trapz'")


def calculate_file_energy_statistics(filename):
    signals = load_signals(filename)
    count = min(MAX_SIGNALS, signals.shape[0])
    if count < 2:
        raise ValueError(f"{filename}: at least two traces are needed for SD")
    energies = []
    for i in range(count):
        times, volts = get_signal(signals, i)
        t, y = select_time_window(times, volts, T_START, T_END)
        freqs, amp, fs = compute_fft(t, y)
        if F_HIGH >= fs / 2:
            raise ValueError(f"Band upper limit {F_HIGH} Hz exceeds Nyquist {fs/2} Hz")
        energies.append(calculate_band_energy(freqs, amp, F_LOW, F_HIGH, ENERGY_METHOD))
    return np.asarray(energies, dtype=float)


# ============================================================
# Blank control statistics (mean +/- sigma)
# ============================================================
def batch_analyze_voltage_files(voltage_values_mVpp):
    rows = []
    for voltage in voltage_values_mVpp:
        voltage = int(voltage)
        filepath = FOLDER / FILE_PATTERN.format(v=voltage)
        if not filepath.is_file():
            print(f"Warning: file not found, skipped: {filepath}")
            rows.append({"voltage_mVpp": voltage, "n": 0,
                         "mean_raw": np.nan, "var_raw": np.nan,
                         "mean_norm": np.nan, "sd_norm": np.nan})
            continue
        energies = calculate_file_energy_statistics(filepath)
        vpp = voltage * 1e-3
        normalized = energies / (vpp ** 2)
        row = {
            "voltage_mVpp": voltage,
            "n": len(energies),
            "mean_raw": float(np.mean(energies)),
            "var_raw": float(np.var(energies, ddof=0)),
            "mean_norm": float(np.mean(normalized)),
            "sd_norm": float(np.std(normalized, ddof=0)),
        }
        rows.append(row)
        print(f"{voltage:3d} mVpp | N={len(energies):3d} | "
              f"normalized mean={row['mean_norm']:.6e} | "
              f"sigma={row['sd_norm']:.6e}")
    return rows


def plot_results(rows):
    x = np.array([r["voltage_mVpp"] for r in rows], dtype=float)
    mean = np.array([r["mean_norm"] for r in rows], dtype=float)
    sd = np.array([r["sd_norm"] for r in rows], dtype=float)
    if not np.isfinite(mean).any():
        raise ValueError("No voltage data available for plotting")

    fig, ax = plt.subplots(figsize=(11, 6))
    # Only one curve: normalized mean energy with +/- 1 sigma error bars.
    ax.errorbar(x, mean, yerr=sd, fmt="-s", color="tab:green",
                linewidth=1.8, markersize=5, capsize=4,
                label=r"Normalized mean $\pm \sigma$")

    ax.set_xlabel("Input voltage (mVpp)")
    ax.set_ylabel("Normalized band-energy indicator (FFT amplitude² / Vpp²)")
    ax.set_title(f"Blank control group | {F_LOW / 1e6:g}–{F_HIGH / 1e6:g} MHz | "
                 f"{T_START * 1e6:g}–{T_END * 1e6:g} μs")
    ax.set_ylim(0, 1.5 * np.nanmax(mean))
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()

    save_path = FOLDER / OUTPUT_FIGURE
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"Figure saved: {save_path.resolve()}")
    if SHOW_FIGURE:
        plt.show()
    plt.close(fig)


def save_table(rows):
    keys = ["voltage_mVpp", "n", "mean_raw", "var_raw", "mean_norm", "sd_norm"]
    save_path = FOLDER / OUTPUT_CSV
    with save_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Results saved: {save_path.resolve()}")


def main():
    voltages = np.arange(VOLTAGE_START_MVPP,
                         VOLTAGE_END_MVPP + VOLTAGE_STEP_MVPP,
                         VOLTAGE_STEP_MVPP)
    rows = batch_analyze_voltage_files(voltages)
    print("\nVoltage (mVpp) | normalized mean | sigma")
    for r in rows:
        print(f"{r['voltage_mVpp']:14d} | {r['mean_norm']:15.6e} | "
              f"{r['sd_norm']:13.6e}")
    save_table(rows)
    plot_results(rows)


if __name__ == "__main__":
    main()
