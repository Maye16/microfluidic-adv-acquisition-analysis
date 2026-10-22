# Analysis: blank controls and individual acoustic traces

The legacy scripts from the laboratory are preserved in `legacy/` for traceability. They are **not run by the CI**, some use `np.load(..., allow_pickle=True)` and two execute analysis immediately upon import; do not import them as a package. See [`../CONTRIBUTORS.md`](../CONTRIBUTORS.md) for contributor attribution.

The new import-safe CLI is `python -m analysis.adv_analysis` (run from repository root). It computes the **squared-amplitude FFT band indicator** for each trace, groups blank-reference traces by electrical excitation amplitude, and exports the mean/SD of the indicator. It is **not** a validated diagnostic or a new detection-threshold result.

## Input formats

The acquisition sources implement two distinct file formats: the Keysight
SCPI/VISA `Oscilloscope.record` writes the 3-D time/voltage layout used by
the historical FFT scripts, while `picoscope.py` saves 2-D ADC arrays. See
[`../DATA_FORMATS_AND_FFT.md`](../DATA_FORMATS_AND_FFT.md). The input format
of the laboratory recordings has not yet been checked directly.

- **3-D (traces, samples, 2):** columns must contain time **in seconds** and measured signal **in volts** (or another consistently documented amplitude unit). Do not silently assume the raw acquisition output has this format.
- **2-D (traces, samples):** raw ADC counts from the acquisition code; pass `--sample-rate-hz` explicitly. Counts are not volts. Optionally pass `--volts-per-count` only if an independently verified ADC conversion is known.
- `.npy` must contain a numeric array; loading uses `allow_pickle=False` for safer handling. There is no automatic object-array deserialization.
- For *both* formats, the selected 20–160 µs time window is relative to the trace time axis/trigger, and therefore depends on documented timing and signal onset.

## Background statistics example

```bash
python -m pip install -r analysis/requirements.txt
python -m analysis.adv_analysis blank --input-dir ./my_controls --voltage-start 40 --voltage-end 130 --voltage-step 5 --pattern '{v}mVpp.npy' --max-traces 100 --window-us 20 160 --band-mhz 0.4 0.6 --method sum --output-prefix analysis-results/blank_controls --plot
```

If the files contain **2-D ADC counts**, specify e.g. `--sample-rate-hz SAMPLE_RATE_FROM_ACQUISITION_METADATA` (supply a real number; **do not invent this**). If a voltage conversion is established, optionally set `--volts-per-count CALIBRATED_FACTOR`. The script records the selected settings in a separate JSON file and writes a CSV that includes the actual number of traces analyzed at each voltage.

`--method sum` is the historical latest script's sum of squared, window-normalized FFT amplitudes in the band. This is **not a physical energy in joules**. `--method trapz` instead integrates squared amplitudes with respect to frequency; the two are **not interchangeable** and their numeric thresholds differ. Voltage normalization divides values by `(electrical input Vpp)^2` and does not yield calibrated acoustic pressure.

## Single-trace spectrum

```bash
python -m analysis.adv_analysis single --file ./my_controls/100mVpp.npy --trace-index 0 --window-us 20 160 --output-prefix analysis-results/signal_0 --plot
```

For 2-D ADC inputs, add `--sample-rate-hz ...` as above. This saves a numerical spectrum CSV; the plot is optional.

## Relation to Method B (Ramesh et al., Langmuir 2023)

The manuscript refers to Method B as the **published methodological reference** for comparisons with a droplet-free background. The published criterion `background mean + 7 standard deviations` is **not experimentally validated for this new setup**. This script intentionally **does not classify droplet ADV events or derive pressure thresholds**. The statistical control summary is a preparatory processing component, not an end-to-end reproduction of the literature method. No new ADV observations or experimental files are contained in this archive.

The newest uploaded script (`legacy/plot_energy_threold_0.5_new.py`) uses 20–160 µs, unlike the earlier `legacy/plot_energy_threold_0.5.py` (40–160 µs). The interactive single-trace script uses another example window (40–100 µs). Do not combine outputs without aligning settings and confirming preprocessing.

## Tests

```bash
python -m unittest discover -s analysis/tests -v
```

Unit tests generate artificial sinusoidal arrays locally to check file-format handling and numerical band selection. They are **software tests only**, not verification on ADV experimental data.
