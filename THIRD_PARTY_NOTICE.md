# Third-party software and graphical assets

The MIT license in `LICENSE` applies to the project-owned source code and project-authored documentation contained in this repository, as authorized by its contributors and laboratory. It **does not** change the terms for separately obtained vendor SDKs, instrument drivers, Python dependencies, hardware firmware or third-party graphics.

- PicoScope/other instrument SDKs and drivers: install and use under their respective vendors' terms. The repository includes application integration code, **not** a grant of rights over these SDKs.
- Third-party Python packages (`PyQt6`, `numpy`, `scipy`, `PyVISA`, etc.): consult each package's own license. Their installation is not governed by the project's `LICENSE`.
- GUI device icons from the private source archive: **excluded** from this repository because redistribution rights are unknown. If needed, replace with original graphics or appropriately licensed assets. See `acquisition/ICON_FILES_PENDING.md`.

The software remains **unverified on laboratory hardware**; obtaining permission to reuse source code does not imply that the instrument-control routines are suitable for unattended operation.
