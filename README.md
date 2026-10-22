# Microfluidic ADV: acquisition and acoustic signal analysis

Open-source laboratory software for acoustic droplet vaporization (ADV) experiments. This repository contains two distinct components:

- **[`acquisition/`](acquisition/README.md)** — instrument communication, signal acquisition and a laboratory GUI.
- **[`analysis/`](analysis/README.md)** — FFT-based signal processing, subharmonic-band indicators and blank-control statistics.

The acquisition software was originally developed by **Nicolas Taulier** and subsequently improved by **Tianhao Dong** and **Maja Pakula Lundheim**. The analysis scripts include work by Tianhao Dong. All project-owned code is released under the [MIT License](LICENSE).

## Analysis quick start

Requires Python 3 and NumPy. From the repository root:

```bash
python -m pip install -r analysis/requirements.txt
python -m unittest discover -s analysis/tests -v
python -m analysis.adv_analysis --help
```

For experimental use, consult [`analysis/README.md`](analysis/README.md). The typical blank-control processing settings are a **20–160 µs** time window and a **0.4–0.6 MHz** frequency band. These settings are adjustable and must be checked for the actual acquisition timing. The analysis accepts time/voltage arrays and raw ADC arrays, with acquisition metadata required in the latter case; see [`DATA_FORMATS_AND_FFT.md`](DATA_FORMATS_AND_FFT.md).

## Acquisition

The acquisition GUI relies on laboratory hardware and external instrument drivers. Consult [`acquisition/README.md`](acquisition/README.md) and [`acquisition/ENVIRONMENT.md`](acquisition/ENVIRONMENT.md) before attempting to operate instruments. **No hardware compatibility or safe operation is guaranteed by the software tests.** Some device images have been omitted because redistribution permission is not established.

## Scope and limitations

This repository provides code, **not experimental ADV datasets**. Five synthetic software tests cover parts of the analysis only. Experimental event-detection thresholds, pressure calibration and hardware behavior have **not** been validated as part of this public package. In particular, this repository does not establish a new ADV pressure threshold, and the background statistics should not be interpreted as a validated event classifier. The historical scripts in `analysis/legacy/` are retained for provenance.

## Citation

See [`CITATION.cff`](CITATION.cff). A persistent software DOI will be added after the first GitHub release is archived on **Zenodo** (DOI: XXX). Zotero can import the Zenodo citation once available.

## License and third-party packages

Project-owned code and documentation: [MIT](LICENSE). Commercial instrument SDKs, drivers and third-party dependencies retain their respective licenses; see [`THIRD_PARTY_NOTICE.md`](THIRD_PARTY_NOTICE.md).
