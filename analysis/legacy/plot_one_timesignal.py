# -*- coding: utf-8 -*-
"""
@author: Tianhao Dong

Single-signal time-domain and frequency-domain analysis.

This program extracts a selected time-domain signal from a .npy file
and calculates its FFT spectrum within a specified time window.

The time window can be interactively adjusted using the mouse.

No averaging is performed across multiple signals.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector


# ============================================================
# FFT calculation
# ============================================================

def calculate_fft(times, voltages):
    """
    Calculate the FFT amplitude spectrum of a single time-domain signal
    without averaging.

    Args:
        times (np.ndarray):
            Time values, in seconds (s).

        voltages (np.ndarray):
            Voltage values, in volts (V).

    Returns:
        freqs (np.ndarray):
            Positive frequency values, in hertz (Hz).

        amplitude (np.ndarray):
            FFT amplitude spectrum.
    """

    if len(times) < 2:
        return np.array([]), np.array([])

    # Calculate the sampling time interval
    dt = np.median(np.diff(times))

    # Remove the DC component
    v = voltages - np.mean(voltages)

    # Apply a Hann window to reduce spectral leakage
    window = np.hanning(len(v))
    v_windowed = v * window

    # Compute the real-valued FFT
    fft_values = np.fft.rfft(v_windowed)

    freqs = np.fft.rfftfreq(
        len(v_windowed),
        d=dt
    )

    # Normalize the FFT amplitude
    amplitude = np.abs(fft_values) / len(v_windowed)

    return freqs, amplitude


# ============================================================
# Time-domain signal and FFT spectrum visualization
# ============================================================

def plot_i_th_signal_and_spectrum(
    filename,
    i=8,
    window_us=(50, 250)
):
    """
    Plot the time-domain signal of the i-th acquisition
    and its FFT spectrum within a selected time window.

    No averaging is performed across multiple acquisitions.

    Args:
        filename (str):
            Path to the .npy data file.

        i (int):
            Index of the signal to analyze, starting from 0.

        window_us (tuple):
            Time window used for FFT calculation,
            in microseconds (us).

            Example: (50, 250).
    """

    # Load the signal data
    signals = np.load(filename, allow_pickle=True)

    n_signals = signals.shape[0]

    print(f"Total number of signals: {n_signals}")

    if n_signals == 0:
        print("No signals available for visualization.")
        return

    if i < 0 or i >= n_signals:
        raise ValueError(
            f"Signal index i = {i} is out of range. "
            f"Valid range: 0 to {n_signals - 1}"
        )

    # Select only the i-th signal without averaging
    signal_i = signals[i]

    times = signal_i[:, 0]

    voltages = signal_i[:, 1]

    # Display signal information
    print(f"Displaying signal index i = {i}")

    print(f"Number of data points: {len(times)}")

    print(
        f"Sampling frequency: "
        f"{1 / (times[1] - times[0]) * 1e-9:.3f} GHz"
    )

    print(f"Minimum voltage: {voltages.min():.3f} V")

    print(f"Maximum voltage: {voltages.max():.3f} V")

    # Convert time from seconds to microseconds for visualization
    times_us = times * 1e6

    # Create two subplots
    fig, (ax_time, ax_freq) = plt.subplots(
        2,
        1,
        figsize=(11, 8)
    )

    # Plot the i-th time-domain signal
    ax_time.plot(
        times_us,
        voltages,
        label=f"Signal i = {i}"
    )

    ax_time.set_xlabel("Time (µs)")

    ax_time.set_ylabel("Voltage (V)")

    ax_time.set_title(
        f"Time-Domain Signal — Signal i = {i}"
    )

    ax_time.grid(True)

    ax_time.legend()

    selection_region = None

    # ============================================================
    # Update FFT based on the selected time window
    # ============================================================

    def update_fft(t_min_us, t_max_us):
        """
        Calculate and update the FFT spectrum of the i-th signal
        within the selected time window.
        """

        nonlocal selection_region

        # Ensure the correct order of time boundaries
        if t_min_us > t_max_us:
            t_min_us, t_max_us = t_max_us, t_min_us

        # Select data within the specified time window
        mask = (
            (times_us >= t_min_us)
            & (times_us <= t_max_us)
        )

        if np.sum(mask) < 2:
            print(
                "Selected time window is too short: "
                "not enough data points for FFT calculation."
            )
            return

        times_selected = times[mask]

        voltages_selected = voltages[mask]

        # Calculate FFT of the selected signal segment
        # No averaging is performed
        freqs, amplitude = calculate_fft(
            times_selected,
            voltages_selected
        )

        # Update the highlighted time window
        if selection_region is not None:
            selection_region.remove()

        selection_region = ax_time.axvspan(
            t_min_us,
            t_max_us,
            color="lightblue",
            alpha=0.45,
            label="Time Window Used for FFT"
        )

        ax_time.legend(loc="upper right")

        # Update the frequency-domain spectrum
        ax_freq.clear()

        ax_freq.plot(
            freqs / 1e6,
            amplitude,
            marker="o",
            lw=3
        )

        ax_freq.set_xlabel(
            "Frequency (MHz)",
            fontsize=14
        )

        ax_freq.set_ylabel("Amplitude")

        ax_freq.set_title(
            f"FFT Spectrum — Signal i = {i}, "
            f"Time Window: {t_min_us:.2f}–{t_max_us:.2f} µs"
        )

        ax_freq.grid(True)

        ax_freq.set_xlim(0, 2)

        # Refresh the figure
        fig.canvas.draw_idle()

    # ============================================================
    # Initial FFT calculation
    # ============================================================

    update_fft(
        window_us[0],
        window_us[1]
    )

    # ============================================================
    # Interactive time-window selection using the mouse
    # ============================================================

    span = SpanSelector(
        ax_time,
        update_fft,
        "horizontal",
        useblit=True,
        props=dict(
            alpha=0.25,
            facecolor="lightblue"
        ),
        interactive=True,
        drag_from_anywhere=True
    )

    plt.tight_layout()

    plt.show()


# ============================================================
# Example usage
# ============================================================

plot_i_th_signal_and_spectrum(
    # "350mVpp_10cycles_22mm.npy",
    "100mVpp.npy",
    i=99,
    window_us=(40, 100)
)