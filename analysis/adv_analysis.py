"""Research-stage FFT band statistics for blank controls in acoustic ADV assays.

No validated ADV event classifier is implemented in this module. The numerical
indicator is the sum (or frequency integral) of squared, Hann-corrected FFT
amplitudes in a chosen band; it is NOT calibrated acoustic energy in joules.

No external hardware or experimental recording is bundled or accessed implicitly.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np


def load_traces(path: Path | str, sample_rate_hz: float | None = None,
                volts_per_count: float | None = None) -> tuple[np.ndarray, np.ndarray, str]:
    """Load numeric .npy traces as 2D time and sample arrays.

    Accepted formats: (traces, points, 2) with [seconds, voltage] columns,
    or (traces, points) raw ADC readings with a required sample rate.
    Pickled arrays are rejected; there is no silent ADC-to-voltage calibration.
    """
    path = Path(path)
    raw = np.load(path, allow_pickle=False)
    if raw.dtype.kind not in 'iuf':
        raise ValueError(f'{path}: numeric real-valued array required, got {raw.dtype}')
    if raw.ndim == 3 and raw.shape[2] == 2:
        if volts_per_count is not None:
            raise ValueError('--volts-per-count is only valid for 2-D raw ADC captures')
        times = raw[:, :, 0].astype(float)
        traces = raw[:, :, 1].astype(float)
        units = 'V (assumed by 3-D time/voltage format)'
    elif raw.ndim == 2:
        if sample_rate_hz is None or not np.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
            raise ValueError(f'{path}: 2-D ADC arrays require a positive --sample-rate-hz '
                             'obtained from the actual acquisition metadata')
        if volts_per_count is not None and (not np.isfinite(volts_per_count) or volts_per_count <= 0):
            raise ValueError('--volts-per-count must be positive')
        times = np.broadcast_to(np.arange(raw.shape[1], dtype=float) / sample_rate_hz,
                                raw.shape).copy()
        traces = raw.astype(float)
        units = 'ADC counts'
        if volts_per_count is not None:
            traces *= volts_per_count
            units = 'V (from user-supplied volts-per-count)'
    else:
        raise ValueError(f'{path}: expected (traces, samples, 2) or '
                         f'(traces, samples), received {raw.shape}')
    if traces.shape[0] < 1 or traces.shape[1] < 3:
        raise ValueError(f'{path}: need at least one trace with >=3 samples')
    if not (np.isfinite(times).all() and np.isfinite(traces).all()):
        raise ValueError(f'{path}: NaN or infinite values are not supported')
    return times, traces, units


def select_window(time: np.ndarray, amplitude: np.ndarray,
                  start_s: float, end_s: float) -> tuple[np.ndarray, np.ndarray]:
    if not (np.isfinite(start_s) and np.isfinite(end_s) and 0 <= start_s < end_s):
        raise ValueError('Need a finite increasing time window starting at >=0 s')
    keep = (time >= start_s) & (time <= end_s)
    if np.count_nonzero(keep) < 3:
        raise ValueError('Time window contains fewer than three samples; '
                         'check trigger timing and input units')
    return time[keep], amplitude[keep]


def fft_amplitude(time: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """One-sided, Hann-coherent-gain-corrected FFT amplitude spectrum."""
    time = np.asarray(time, dtype=float)
    values = np.asarray(values, dtype=float)
    if time.ndim != 1 or time.shape != values.shape or time.size < 3:
        raise ValueError('time and values must be 1-D vectors of equal length >=3')
    if not (np.isfinite(time).all() and np.isfinite(values).all()):
        raise ValueError('Non-finite data detected')
    dt = np.diff(time)
    if np.any(dt <= 0):
        raise ValueError('Time values must be strictly increasing')
    interval = float(np.mean(dt))
    if not np.allclose(dt, interval, rtol=1e-3, atol=0):
        raise ValueError('Nonuniform sampling: standard FFT requires uniform sampling')
    n = len(values)
    window = np.hanning(n)
    gain = np.sum(window) / n
    freq = np.fft.rfftfreq(n, d=interval)
    spectrum = np.abs(np.fft.rfft((values - np.mean(values)) * window)) * (2 / (n * gain))
    spectrum[0] *= .5
    if n % 2 == 0:
        spectrum[-1] *= .5
    return freq, spectrum


def band_indicator(freq: np.ndarray, amplitude: np.ndarray,
                   low_hz: float, high_hz: float, method: str = 'sum') -> float:
    """Return squared FFT amplitude indicator; NOT physical energy in joules."""
    if not (np.isfinite(low_hz) and np.isfinite(high_hz) and 0 <= low_hz < high_hz):
        raise ValueError('Band must have finite nonnegative increasing bounds')
    if high_hz >= freq[-1]:
        raise ValueError('High-frequency band limit must lie below Nyquist')
    keep = (freq >= low_hz) & (freq <= high_hz)
    if np.count_nonzero(keep) < 2:
        raise ValueError('Analysis band contains fewer than two frequency bins')
    powers = amplitude[keep] ** 2
    if method == 'sum':
        return float(np.sum(powers))
    if method == 'trapz':
        return float(np.trapezoid(powers, freq[keep]))
    raise ValueError("method must be 'sum' or 'trapz'")


def trace_indicators(time: np.ndarray, signals: np.ndarray, *,
                     max_traces: int = 100, window_us: tuple[float, float] = (20., 160.),
                     band_mhz: tuple[float, float] = (.4, .6),
                     method: str = 'sum') -> np.ndarray:
    if max_traces < 1:
        raise ValueError('max_traces must be positive')
    result = []
    for t, values in zip(time[:max_traces], signals[:max_traces]):
        tsel, ysel = select_window(t, values, window_us[0] * 1e-6, window_us[1] * 1e-6)
        freq, amp = fft_amplitude(tsel, ysel)
        result.append(band_indicator(freq, amp, band_mhz[0] * 1e6,
                                     band_mhz[1] * 1e6, method=method))
    return np.array(result, dtype=float)


def summarize_blank_controls(input_dir: Path, voltages_mvpp: list[int], pattern: str,
                             sample_rate_hz: float | None = None,
                             volts_per_count: float | None = None,
                             max_traces: int = 100,
                             window_us: tuple[float, float] = (20., 160.),
                             band_mhz: tuple[float, float] = (.4, .6),
                             method: str = 'sum') -> list[dict]:
    """Summarize droplet-free controls; do NOT classify ADV events."""
    rows = []
    for mvpp in voltages_mvpp:
        if mvpp <= 0:
            raise ValueError('Voltage Vpp must be strictly positive')
        filename = input_dir / pattern.format(v=mvpp)
        row = {'input_mVpp': int(mvpp), 'file': str(filename), 'n': 0,
               'mean_indicator': '', 'sd_indicator': '',
               'mean_indicator_over_Vpp2': '', 'sd_indicator_over_Vpp2': '',
               'amplitude_unit': '', 'status': ''}
        if not filename.is_file():
            row['status'] = 'missing_file'
            print(f'WARNING: missing: {filename}', file=sys.stderr)
        else:
            times, traces, unit = load_traces(filename, sample_rate_hz, volts_per_count)
            values = trace_indicators(times, traces, max_traces=max_traces,
                                      window_us=window_us, band_mhz=band_mhz, method=method)
            n = len(values)
            if n < 2:
                raise ValueError(f'{filename}: at least two blank traces are required for SD; received {n}')
            mean = float(np.mean(values))
            sd = float(np.std(values, ddof=0))  # Matches uploaded latest script.
            vpp = mvpp / 1e3
            row.update(n=n, mean_indicator=mean, sd_indicator=sd,
                       mean_indicator_over_Vpp2=mean / vpp**2,
                       sd_indicator_over_Vpp2=sd / vpp**2,
                       amplitude_unit=unit,
                       status='ok' if n == max_traces else 'fewer_than_requested_traces')
            if n != max_traces:
                print(f'WARNING: {filename}: only {n} traces of {max_traces} requested', file=sys.stderr)
        rows.append(row)
    return rows


def store_table(rows: list[dict], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_settings(args: argparse.Namespace, mode: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    settings = {'mode': mode, 'methodological_status': 'research-stage; not validated as ADV event classifier',
                'source_note': 'No experimental data or validated pressure threshold shipped',
                **{key: str(val) if isinstance(val, Path) else val for key, val in vars(args).items()}}
    target.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Unvalidated research-stage acoustic FFT analysis; no ADV classification')
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('blank', 'single'):
        p = sub.add_parser(name)
        p.add_argument('--sample-rate-hz', type=float, help='Required for 2-D ADC captures, from actual acquisition metadata')
        p.add_argument('--volts-per-count', type=float, help='Optional externally validated ADC scaling factor')
        p.add_argument('--window-us', nargs=2, type=float, default=[20., 160.], metavar=('START', 'END'))
        p.add_argument('--band-mhz', nargs=2, type=float, default=[.4, .6], metavar=('LOW', 'HIGH'))
        p.add_argument('--output-prefix', type=Path, default=Path('analysis-results/out'))
        p.add_argument('--plot', action='store_true', help='Save a plot (requires matplotlib)')
    b = sub.choices['blank']
    b.add_argument('--input-dir', type=Path, required=True)
    b.add_argument('--pattern', default='{v}mVpp.npy')
    b.add_argument('--voltage-start', type=int, default=40)
    b.add_argument('--voltage-end', type=int, default=130)
    b.add_argument('--voltage-step', type=int, default=5)
    b.add_argument('--max-traces', type=int, default=100)
    b.add_argument('--method', choices=['sum', 'trapz'], default='sum')
    s = sub.choices['single']
    s.add_argument('--file', type=Path, required=True)
    s.add_argument('--trace-index', type=int, default=0)
    return parser


def run(args: argparse.Namespace) -> None:
    prefix: Path = args.output_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == 'blank':
        if args.voltage_step <= 0 or args.voltage_start <= 0 or args.voltage_end < args.voltage_start:
            raise ValueError('Invalid voltage start/end/step')
        voltages = list(range(args.voltage_start, args.voltage_end + 1, args.voltage_step))
        rows = summarize_blank_controls(args.input_dir, voltages, args.pattern,
                                        args.sample_rate_hz, args.volts_per_count,
                                        args.max_traces, tuple(args.window_us),
                                        tuple(args.band_mhz), args.method)
        store_table(rows, Path(str(prefix) + '_summary.csv'))
        if args.plot:
            import matplotlib.pyplot as plt
            good = [r for r in rows if r['n'] >= 1]
            if good:
                fig, ax = plt.subplots()
                ax.errorbar([r['input_mVpp'] for r in good],
                            [r['mean_indicator_over_Vpp2'] for r in good],
                            yerr=[r['sd_indicator_over_Vpp2'] for r in good], fmt='-o', capsize=3)
                ax.set(xlabel='Generator input voltage (mVpp)',
                       ylabel='FFT band indicator / Vpp² (not pressure or physical energy)',
                       title='Blank controls: mean ± population SD')
                fig.tight_layout()
                fig.savefig(str(prefix) + '_plot.png', dpi=180)
                plt.close(fig)
            else:
                print('WARNING: no files, so no plot saved', file=sys.stderr)
        print(f'Saved: {prefix}_summary.csv')
    else:
        times, traces, units = load_traces(args.file, args.sample_rate_hz, args.volts_per_count)
        if not 0 <= args.trace_index < traces.shape[0]:
            raise ValueError(f'Trace index must be 0..{traces.shape[0]-1}')
        t, values = select_window(times[args.trace_index], traces[args.trace_index],
                                  args.window_us[0] * 1e-6, args.window_us[1] * 1e-6)
        f, amp = fft_amplitude(t, values)
        out = Path(str(prefix) + '_spectrum.csv')
        with out.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['frequency_Hz', f'fft_amplitude_{units}'])
            writer.writerows(zip(f, amp))
        if args.plot:
            import matplotlib.pyplot as plt
            fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(9, 7))
            ax0.plot(t * 1e6, values)
            ax0.set(xlabel='Time relative to trace start (µs)', ylabel=units)
            ax1.plot(f / 1e6, amp)
            ax1.set(xlabel='Frequency (MHz)', ylabel=f'FFT amplitude ({units})')
            fig.tight_layout()
            fig.savefig(str(prefix) + '_plot.png', dpi=180)
            plt.close(fig)
        print(f'Saved: {out}')
    save_settings(args, args.mode, Path(str(prefix) + '_settings.json'))


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
