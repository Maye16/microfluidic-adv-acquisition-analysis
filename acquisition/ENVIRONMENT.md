# Reference Python environment

This document describes the **uploaded historical laboratory virtual environment**, without redistributing it or executing its contents.

- **Operating system**: Windows (inferred from `Scripts/`, Windows-specific Python paths, and native `.exe` tools).
- **Python interpreter**: CPython **3.11.13**.
- **Distribution count**: 28 installed packages, including build tools and transitive dependencies.
- **Accompanying files**:
  - `requirements.txt`: versions of eight **direct dependencies found in the source**, suitable as a starting point for installation.
  - `requirements-environment-snapshot.txt`: installed distribution snapshot (the broader environment, not a formally reproducible lock file).

### Recommended clean installation (Windows)

From the repository directory on a lab computer where you are authorized to connect instrumentation:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Manufacturer PicoSDK dynamic libraries, oscilloscope drivers, serial/USB instrument drivers, and a functioning VISA installation (or an appropriate compatible backend) may be required **in addition to Python packages**. These external libraries and drivers are **not included** in the repository. `pyvisa.ResourceManager('@py')` is called in the application as a fallback, but `pyvisa-py` does **not appear** among the supplied environment's installed distributions: this backend would need a separate check if intended for use.

The project's local `picoscope.py` module is separate from the installed third-party `picoscope` distribution; the latter appears in the full environment snapshot but was not added to the direct-dependency list. Please verify whether any auxiliary workflow actually requires it.

### Important limitations

1. **Not an installation-validation claim:** packages were identified from `.dist-info/METADATA` in the supplied archive; no hardware-connected test was performed.
2. **No portable virtual-environment archive:** copied virtual environments contain platform-specific binaries, hard-coded interpreter paths, cache files and potentially identifying local paths. Recreate `.venv` on each machine instead of committing the original.
3. **No published scoring implementation identified:** a validated `f_0/2` ADV Method-B event-scoring script was not found in the supplied source and is not supplied by this environment.
4. **Reference protocol parameters are separate:** installed package versions and configuration defaults do not demonstrate that the stated 25 Hz PRF, five cycles, 1.1 MHz, and 37 °C were used in a particular experiment.
5. **Code and GUI redistribution:** contributor approval, a release license, and permission for the GUI icon assets should be resolved before public release.
6. **Do not launch `mapField.py` on connected instruments without review:** it initiates a measurement from top-level code.

### What was excluded

No `venv`, `.venv`, `.idea`, `__pycache__`, binary `.exe` files, or machine-specific Python paths are included in this candidate repository. Only version metadata was used to prepare the dependency files.
