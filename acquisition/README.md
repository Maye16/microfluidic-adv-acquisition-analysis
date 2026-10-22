# Acquisition: original laboratory instrument-control software

This directory contains the **source code** for the hardware-oriented GUI and instrument drivers originally developed by Nicolas Taulier and subsequently modified by Tianhao Dong and Maja Pakula Lundheim.

- Entry point used in the laboratory: `python main.py` (requires hardware and vendor drivers; **not tested here**).
- Modules: `main.py`, `main_window.py`, `measurement.py`, `picoscope.py`, `instruments.py`, `keysight.py`, `agilent.py`, `rohde_schwarz.py`, `newport.py`, `motion.py`, and other support scripts.
- Reference dependencies from a historical Windows/Python 3.11.13 environment are listed in `requirements.txt` and `ENVIRONMENT.md`.
- The `icons/` assets were **excluded** until redistribution rights have been checked. The GUI may show empty device illustrations unless approved images are installed locally in `acquisition/icons/` (see `ICON_FILES_PENDING.md`).
- `devices.cfg` is a disabled/anonymized example. `configuration.cfg` retains old software defaults and does **not** describe the methods-paper ADV exposure settings.
- `picoscope.py` writes **ADC counts**, not calibrated pressure, and `.npy` files do not store the sampling rate or a voltage-conversion factor; record this in laboratory metadata.
- `keysight.py` writes `.npy` traces containing **time and voltage** using the oscilloscope waveform preamble; this is the same array layout required by the historical FFT scripts, subject to actual device settings and checking that every capture segment was read.
- Which acquisition backend produced Tianhao Dong's analyzed files **has not been independently confirmed**. See [`../DATA_FORMATS_AND_FFT.md`](../DATA_FORMATS_AND_FFT.md).

- `mapField.py` is an **unvalidated and incomplete prototype**. Its top-level automatic mapping call has been replaced with a disabled entry point. Do not use it for hardware scans without reviewing its logic and safety.

To test acquisition, use the laboratory's established safety controls and manually verify transducer identity, excitation limits, amplifier, generator, hydrophone channel/trigger settings, electrical and acoustic calibration, and vendor software. A source syntax check is not a hardware validation.

**Source modifications in this release candidate:** removed instrument serial-number examples, anonymized `devices.cfg` (in the prior preparation copy), removed automatic hardware mapping on running/importing `mapField.py`; original algorithms were otherwise not systematically refactored. Do not infer that the source matches a particular manuscript acquisition without checking measurement logs.

Additional safety changes: disabled hard-coded example file access in `data.py` and `access_npy.py`. `access_npy.py` is retained as commented source for traceability, since its illustrative ADC conversion is not an experimentally validated calibration.
