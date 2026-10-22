# Acquisition files and FFT analysis: documented source-code paths

This note documents **what the supplied Python sources do**, not which acquisition
branch was used for any particular experiment. The laboratory contact has not
confirmed the origin of the individual `.npy` files analyzed by Tianhao Dong.

## How the historical analysis scripts work

The three preserved `analysis/legacy/plot_*.py` scripts load NumPy `.npy` files,
select a time window, calculate a windowed FFT and display or summarize the
spectrum. The newer blank-control script
`analysis/legacy/plot_energy_threold_0.5_new.py` analyzes a 0.4–0.6 MHz band
within 20–160 µs and summarizes up to 100 blank traces per input setting. It
expects an array shaped `(traces, samples, 2)`: time in seconds in column 0
and signal voltage in column 1. No intermediate conversion is coded in that
script; it reads this format directly. It does **not** calculate a validated
ADV event-classification threshold.

## Two acquisition branches found in the source

| Source branch | `.npy` array shape | Saved information | Directly accepted by historical scripts? |
| --- | --- | --- | --- |
| `acquisition/keysight.py`, `Oscilloscope.record` (SCPI/VISA) | `(traces, samples, 2)` | time in seconds and voltage inferred from instrument waveform preamble | **Yes, structurally.** Confirm channel scaling, time origin, and completeness of all segments. |
| `acquisition/picoscope.py`, `Oscilloscope.record` (PicoSDK) | `(traces, samples)` | raw oscilloscope ADC counts | **No.** Sampling interval, trigger timing and calibrated scaling are needed before equivalent interpretation. |

These are distinct acquisition implementations; no hardware model number needs
to be provided to describe this distinction. No actual experimental file was
supplied to establish which branch produced Tianhao's recordings.

### Recommended new analysis interface

`analysis/adv_analysis.py` is a safer, non-hardware CLI that accepts both
numeric array formats. For the 3-D time/voltage format:

```bash
python -m analysis.adv_analysis single --file PATH_TO_FILE.npy --trace-index 0 --window-us 20 160 --output-prefix analysis-results/trace
```

For the 2-D raw ADC format, **add** `--sample-rate-hz VALUE_FROM_ACQUISITION_METADATA`.
Without that metadata the software rejects the file instead of guessing the
time axis. A `--volts-per-count` factor is optional only when established
independently; raw ADC amplitudes cannot be reported as volts by default.

The time-window convention depends on the acquired trigger and is not
necessarily the acoustic arrival time. The 0.4–0.6 MHz frequency band and
20–160 µs window are analysis settings from the recent script, not a claim
that a validated ADV classification threshold has been obtained.

## Verification still required before public release

1. Confirm with Tianhao which acquisition branch produced the `.npy` files
   used for the published method description.
2. Open one **authorized, non-sensitive example** `.npy` and record its shape,
   dtype, units, sampling interval, trigger definition and number of traces.
   The example need not be distributed publicly.
3. Compare results from the new CLI and the actual laboratory script on that
   same file, with identical FFT normalization and window definitions.
4. Check the incomplete-segment behavior of `keysight.py`: in the present source,
   an unexpected segment length skips filling a row of an `np.empty` output
   buffer. Those rows must not be treated as valid measurements if this occurs.
5. Do not describe the analysis as fully implementing Method B or an experimentally
   validated ADV threshold until that claim is supported by tested code and data.
