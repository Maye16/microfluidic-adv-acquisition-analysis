# -*- coding: utf-8 -*-
"""
Batch analysis of the energy within the 0.4–0.6 MHz frequency band at different input voltages to calculate its mean and standard deviation, thereby facilitating the determination of the band-energy threshold for acoustic droplet vaporization (ADV).


For each file:
1. Load 100 groups of time-domain signals
2. Select only the signal in a user-defined time window
3. Compute FFT using only this selected time window
4. Calculate the energy in a user-defined frequency band
5. Calculate the mean and variance of the energy values
6. Normalize the mean energy by the square of the input Vpp voltage
7. Plot normalized mean energy with ±1 standard deviation
"""

import numpy as np
import matplotlib.pyplot as plt
import os


# ============================================================
# User settings
# ============================================================

# Folder and file settings
FOLDER = "."
FILE_PATTERN = "{v}mVpp.npy"


# Voltage settings, unit: mVpp
VOLTAGE_START_MVPP = 40
VOLTAGE_END_MVPP = 130
VOLTAGE_STEP_MVPP = 5

# Signal number used from each file
MAX_SIGNALS = 100

# Time window, unit: seconds
T_START = 40e-6
T_END = 160e-6
# T_END = 120e-6

# Frequency band, unit: Hz
F_LOW = 0.4e6
F_HIGH = 0.6e6

# Energy calculation method
# "sum": energy = sum(amplitude_band ** 2)
# "trapz": energy = trapz(amplitude_band ** 2, freq_band)
ENERGY_METHOD = "sum"


# ============================================================
# Functions
# ============================================================

def load_signals(filename):
    """
    Load signal data from a .npy file.

    Expected data format:
        signals.shape = (100, N, 2)

    Column 0: time
    Column 1: voltage
    """
    signals = np.load(filename, allow_pickle=True)

    print(f"Loaded file: {filename}")
    print("Data shape:", signals.shape)
    print(f"Total number of signals: {signals.shape[0]}")

    return signals


def get_signal(signals, i):
    """
    Get time and voltage data from the i-th signal.
    """
    signal = signals[i]
    times = signal[:, 0]
    voltages = signal[:, 1]

    return times, voltages


def select_time_window(times, voltages, t_start, t_end):
    """
    Select only the signal segment within a given time window.
    """
    time_mask = (times >= t_start) & (times <= t_end)

    times_window = times[time_mask]
    voltages_window = voltages[time_mask]

    if len(times_window) < 2:
        raise ValueError(
            f"Not enough data points in the selected time window "
            f"{t_start * 1e6:.1f}–{t_end * 1e6:.1f} us."
        )

    return times_window, voltages_window


def compute_fft(times, voltages):
    """
    Compute the frequency-domain amplitude spectrum of one signal.
    """
    dt = np.mean(np.diff(times))
    fs = 1 / dt

    # Remove DC component
    voltages_detrended = voltages - np.mean(voltages)

    # Apply Hann window
    window = np.hanning(len(voltages_detrended))
    voltages_windowed = voltages_detrended * window

    n = len(voltages_windowed)

    fft_values = np.fft.fft(voltages_windowed)
    freqs = np.fft.fftfreq(n, d=dt)

    # Keep only positive frequencies
    positive_mask = freqs >= 0
    freqs = freqs[positive_mask]

    # Amplitude correction for Hann window
    window_correction = np.sum(window) / n
    amplitude = np.abs(fft_values[positive_mask]) * 2 / n / window_correction

    return freqs, amplitude, fs


def calculate_band_energy(freqs, amplitude, f_low, f_high, method="sum"):
    """
    Calculate energy in the selected frequency band.

    method="sum":
        energy = sum(amplitude_band ** 2)

    method="trapz":
        energy = trapz(amplitude_band ** 2, freq_band)
    """
    band_mask = (freqs >= f_low) & (freqs <= f_high)

    freq_band = freqs[band_mask]
    amplitude_band = amplitude[band_mask]

    if len(amplitude_band) < 2:
        raise ValueError(
            f"Not enough frequency points in the selected band "
            f"{f_low / 1e6:.3f}–{f_high / 1e6:.3f} MHz."
        )

    if method == "sum":
        energy = np.sum(amplitude_band ** 2)
    elif method == "trapz":
        energy = np.trapz(amplitude_band ** 2, freq_band)
    else:
        raise ValueError("method must be either 'sum' or 'trapz'.")

    return energy


def calculate_file_energy_statistics(
    filename,
    max_signals,
    t_start,
    t_end,
    f_low,
    f_high,
    energy_method
):
    """
    Calculate the mean and variance of band energy for one .npy file.
    """
    signals = load_signals(filename)

    num_signals = min(max_signals, signals.shape[0])

    energies = []

    for i in range(num_signals):
        times, voltages = get_signal(signals, i)

        times_window, voltages_window = select_time_window(
            times,
            voltages,
            t_start=t_start,
            t_end=t_end
        )

        freqs, amplitude, fs = compute_fft(times_window, voltages_window)

        energy = calculate_band_energy(
            freqs,
            amplitude,
            f_low=f_low,
            f_high=f_high,
            method=energy_method
        )

        energies.append(energy)

    energies = np.array(energies)

    mean_energy = np.mean(energies)
    var_energy = np.var(energies)

    return energies, mean_energy, var_energy


def batch_analyze_voltage_files(
    voltage_values_mVpp,
    folder,
    file_pattern,
    max_signals,
    t_start,
    t_end,
    f_low,
    f_high,
    energy_method
):
    """
    Batch analyze multiple .npy files with different input Vpp values.
    """
    mean_energies = []
    var_energies = []
    normalized_values = []
    all_energies = []

    for v_mVpp in voltage_values_mVpp:
        filename = file_pattern.format(v=int(v_mVpp))
        filepath = os.path.join(folder, filename)

        if not os.path.exists(filepath):
            print(f"Warning: file not found, skipped: {filepath}")
            mean_energies.append(np.nan)
            var_energies.append(np.nan)
            normalized_values.append(np.nan)
            all_energies.append(None)
            continue

        energies, mean_energy, var_energy = calculate_file_energy_statistics(
            filepath,
            max_signals=max_signals,
            t_start=t_start,
            t_end=t_end,
            f_low=f_low,
            f_high=f_high,
            energy_method=energy_method
        )

        # Convert mVpp to Vpp
        v_Vpp = v_mVpp * 1e-3

        # Normalize mean band energy by Vpp squared
        normalized_value = mean_energy / (v_Vpp ** 2)

        mean_energies.append(mean_energy)
        var_energies.append(var_energy)
        normalized_values.append(normalized_value)
        all_energies.append(energies)

        print("----------------------------------------")
        print(f"Voltage: {v_mVpp:.0f} mVpp")
        print(f"Time window: {t_start * 1e6:.1f} us to {t_end * 1e6:.1f} us")
        print(f"Frequency band: {f_low / 1e6:.3f} MHz to {f_high / 1e6:.3f} MHz")
        print(f"Energy method: {energy_method}")
        print(f"Mean energy: {mean_energy:.6e}")
        print(f"Variance of energy: {var_energy:.6e}")
        print(f"Mean energy / Vpp^2: {normalized_value:.6e}")
        print("----------------------------------------")

    result_dict = {
        "voltage_mVpp": np.array(voltage_values_mVpp),
        "mean_energy": np.array(mean_energies),
        "var_energy": np.array(var_energies),
        "normalized_value": np.array(normalized_values),
        "all_energies": all_energies,
        "t_start": t_start,
        "t_end": t_end,
        "f_low": f_low,
        "f_high": f_high,
        "energy_method": energy_method
    }

    return result_dict


def plot_normalized_energy_with_sd(result_dict):

    voltage_mVpp = result_dict["voltage_mVpp"]
    normalized_value = result_dict["normalized_value"]
    var_energy = result_dict["var_energy"]

    t_start = result_dict["t_start"]
    t_end = result_dict["t_end"]
    f_low = result_dict["f_low"]
    f_high = result_dict["f_high"]


    #  np.std(energies / Vpp**2, ddof=0) 。
    voltage_Vpp = voltage_mVpp * 1e-3
    normalized_std = np.sqrt(var_energy) / voltage_Vpp**2

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.errorbar(
        voltage_mVpp,
        normalized_value,
        yerr=normalized_std,
        fmt="-s",
        color="tab:green",
        linewidth=1.8,
        markersize=5,
        capsize=4,
        label="Normalized Mean Energy ± SD (100 runs)"
    )

    ax.set_xlabel("Input Voltage (mVpp)")
    ax.set_ylabel("Normalized Band Energy (Energy / Vpp²)")
    # Y-axis range: 0 to 1.5 times the maximum value
    ax.set_ylim(0, 1.5 * np.nanmax(normalized_value))
    ax.set_title(
        "Normalized Band Energy with Standard Deviation\n"
        f"{f_low / 1e6:.3f}–{f_high / 1e6:.3f} MHz, "
        f"Time Window: {t_start * 1e6:.1f}–{t_end * 1e6:.1f} us"
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    # save_path = os.path.join(FOLDER, OUTPUT_FIGURE)
    # fig.savefig(save_path, dpi=300, bbox_inches="tight")
    # print(f"Green normalized-energy figure saved to: {os.path.abspath(save_path)}")
    # plt.close(fig)


def print_result_table(result_dict):
    """
    Print all analysis results as a table.
    """
    voltage_mVpp = result_dict["voltage_mVpp"]
    mean_energy = result_dict["mean_energy"]
    var_energy = result_dict["var_energy"]
    normalized_value = result_dict["normalized_value"]

    print("\nFinal Results:")
    print("Voltage(mVpp)    Mean Energy        Variance          Mean Energy / Vpp^2")
    print("--------------------------------------------------------------------------")

    for v, mean_e, var_e, norm_e in zip(
        voltage_mVpp,
        mean_energy,
        var_energy,
        normalized_value
    ):
        print(f"{v:10.0f}      {mean_e:12.6e}    {var_e:12.6e}    {norm_e:12.6e}")


# ============================================================
# Main program
# ============================================================

voltage_values_mVpp = np.arange(
    VOLTAGE_START_MVPP,
    VOLTAGE_END_MVPP + VOLTAGE_STEP_MVPP,
    VOLTAGE_STEP_MVPP
)

results = batch_analyze_voltage_files(
    voltage_values_mVpp,
    folder=FOLDER,
    file_pattern=FILE_PATTERN,
    max_signals=MAX_SIGNALS,
    t_start=T_START,
    t_end=T_END,
    f_low=F_LOW,
    f_high=F_HIGH,
    energy_method=ENERGY_METHOD
)

print_result_table(results)


plot_normalized_energy_with_sd(results)