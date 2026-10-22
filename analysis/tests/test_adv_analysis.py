"""Synthetic software tests only; not validation against measured ADV signals."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from analysis.adv_analysis import (load_traces, select_window, fft_amplitude,
                                   band_indicator, trace_indicators,
                                   summarize_blank_controls)


class TestSyntheticAcousticProcessing(unittest.TestCase):
    def setUp(self):
        self.rate = 10_000_000
        self.t = np.arange(2000) / self.rate
        self.half = np.sin(2 * np.pi * 500_000 * self.t)
        self.off = np.sin(2 * np.pi * 1_500_000 * self.t)

    def test_reject_raw_adc_without_sample_rate(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.npy'
            np.save(path, np.vstack([self.half, self.half]))
            with self.assertRaisesRegex(ValueError, 'sample-rate-hz'):
                load_traces(path)
            t, x, unit = load_traces(path, sample_rate_hz=self.rate)
            self.assertEqual(t.shape, (2, 2000))
            self.assertEqual(x.shape, (2, 2000))
            self.assertEqual(unit, 'ADC counts')

    def test_time_voltage_format_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'pairs.npy'
            a = np.stack([self.t, self.half], axis=1)
            np.save(path, np.stack([a, a, a]))
            times, y, unit = load_traces(path)
            self.assertEqual(times.shape, (3, 2000))
            self.assertTrue(np.allclose(y[0], self.half))
            self.assertTrue(unit.startswith('V'))

    def test_band_detects_synthetic_half_frequency(self):
        t, h = select_window(self.t, self.half, 20e-6, 160e-6)
        f, a = fft_amplitude(t, h)
        on = band_indicator(f, a, .4e6, .6e6)
        t, h = select_window(self.t, self.off, 20e-6, 160e-6)
        f, a = fft_amplitude(t, h)
        off = band_indicator(f, a, .4e6, .6e6)
        self.assertGreater(on, 1e4 * off)

    def test_blank_statistics_shape_and_variance(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            base = np.stack([self.t, self.half], axis=1)
            np.save(folder / '100mVpp.npy', np.stack([base, base, base]))
            rows = summarize_blank_controls(folder, [100, 110], '{v}mVpp.npy', max_traces=3)
            self.assertEqual(rows[0]['status'], 'ok')
            self.assertEqual(rows[0]['n'], 3)
            self.assertAlmostEqual(rows[0]['sd_indicator'], 0)
            self.assertEqual(rows[1]['status'], 'missing_file')

    def test_reject_pickle_and_nonuniform_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'objects.npy'
            np.save(p, np.array([{'secret': 1}], dtype=object))
            with self.assertRaises(ValueError):
                load_traces(p)
        times = self.t.copy()
        times[200:] += .1e-6
        with self.assertRaisesRegex(ValueError, 'Nonuniform'):
            fft_amplitude(times, self.half)


if __name__ == '__main__':
    unittest.main()
