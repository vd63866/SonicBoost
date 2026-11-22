import math
import unittest

from audio.equalizer import PipeWireEqualizer


class TestSonicBoostEqualizer(unittest.TestCase):

    def setUp(self):
        self.eq = PipeWireEqualizer()
        self.flat = [0.0] * 10

    def test_flat_profile(self):
        result = self.eq.validate_gains(self.flat)
        self.assertEqual(result, self.flat)

    def test_reject_wrong_number_of_bands(self):
        with self.assertRaises(ValueError):
            self.eq.validate_gains([0, 0, 0])

    def test_reject_gain_above_limit(self):
        gains = [0.0] * 9 + [7.0]

        with self.assertRaises(ValueError):
            self.eq.validate_gains(gains)

    def test_reject_gain_below_limit(self):
        gains = [0.0] * 9 + [-7.0]

        with self.assertRaises(ValueError):
            self.eq.validate_gains(gains)

    def test_reject_nan(self):
        gains = [0.0] * 9 + [float("nan")]

        with self.assertRaises(ValueError):
            self.eq.validate_gains(gains)

    def test_flat_preamp(self):
        self.assertEqual(
            self.eq.calculate_preamp(self.flat),
            0.0
        )

    def test_generate_ten_filters(self):
        config = self.eq.render_config(self.flat)

        self.assertEqual(
            config.count("label = bq_peaking"),
            10
        )

    def test_generate_preamp(self):
        config = self.eq.render_config(self.flat)

        self.assertIn("name = preamp", config)

    def test_generate_audio_routing(self):
        config = self.eq.render_config(self.flat)

        self.assertIn(
            "effect_input.sonicboost",
            config
        )

        self.assertIn(
            "effect_output.sonicboost",
            config
        )


if __name__ == "__main__":
    unittest.main()
