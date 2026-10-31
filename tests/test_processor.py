"""Unit tests for the Image Processor and Aspect Ratio Math."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from src.core.config import (
    ASPECT_RATIOS,
    RESIZE_FILTERS,
    SCALE_MULTIPLIERS,
    ProcessingOptions,
)
from src.core.detector import ImageMagickDetector
from src.core.processor import ImageProcessor


class TestImageProcessorMath(unittest.TestCase):
    """Tests the aspect ratio cropping mathematics and bounding boxes."""

    def test_original_ratio_no_crop(self):
        w, h = ImageProcessor.calculate_crop_dimensions(1920, 1080, None)
        self.assertEqual((w, h), (1920, 1080))

    def test_square_crop_from_landscape(self):
        # 1920x1080 -> 1:1 should crop sides to 1080x1080
        w, h = ImageProcessor.calculate_crop_dimensions(1920, 1080, (1, 1))
        self.assertEqual((w, h), (1080, 1080))

    def test_square_crop_from_portrait(self):
        # 1080x1920 -> 1:1 should crop top/bottom to 1080x1080
        w, h = ImageProcessor.calculate_crop_dimensions(1080, 1920, (1, 1))
        self.assertEqual((w, h), (1080, 1080))

    def test_16_9_crop_from_4_3(self):
        # 1600x1200 (4:3) -> 16:9 widescreen: width 1600, height = 1600 / (16/9) = 900
        w, h = ImageProcessor.calculate_crop_dimensions(1600, 1200, (16, 9))
        self.assertEqual((w, h), (1600, 900))

    def test_4_3_crop_from_16_9(self):
        # 1920x1080 (16:9) -> 4:3: height 1080, width = 1080 * (4/3) = 1440
        w, h = ImageProcessor.calculate_crop_dimensions(1920, 1080, (4, 3))
        self.assertEqual((w, h), (1440, 1080))

    def test_vertical_9_16_from_landscape(self):
        # 1920x1080 -> 9:16: height 1080, width = 1080 * (9/16) = 608
        w, h = ImageProcessor.calculate_crop_dimensions(1920, 1080, (9, 16))
        self.assertEqual((w, h), (608, 1080))

    def test_portrait_3_4_from_square(self):
        # 1000x1000 -> 3:4: height 1000, width = 1000 * (3/4) = 750
        w, h = ImageProcessor.calculate_crop_dimensions(1000, 1000, (3, 4))
        self.assertEqual((w, h), (750, 1000))


class TestCommandBuilding(unittest.TestCase):
    """Verifies safe argument list generation for ImageMagick CLI."""

    def setUp(self):
        self.detector = ImageMagickDetector()
        self.info = self.detector.get_info()
        if not self.info.is_available:
            self.skipTest("ImageMagick is not available on this machine")
        self.processor = ImageProcessor(self.info)

    def test_command_list_structure(self):
        # Test paths with spaces, non-ASCII, and special symbols
        input_path = Path("/Users/test/My Photos/家族 写真 (2026) & $100.jpg")
        output_path = Path("/Users/test/My Photos_upscaled/家族 写真 (2026) & $100_2x_1-1.jpg")

        cmd, (final_w, final_h) = self.processor.build_command(
            input_path=input_path,
            output_path=output_path,
            orig_width=1920,
            orig_height=1080,
            scale=SCALE_MULTIPLIERS["2x"],
            aspect_ratio=ASPECT_RATIOS["1:1"],
            filter_opt=RESIZE_FILTERS["Lanczos"],
            output_format="jpg",
            jpeg_quality=92,
        )

        # Ensure command is a list of strings (no raw shell string)
        self.assertIsInstance(cmd, list)
        self.assertTrue(all(isinstance(arg, str) for arg in cmd))

        # Check essential flags
        self.assertIn("-gravity", cmd)
        self.assertIn("center", cmd)
        self.assertIn("-crop", cmd)
        self.assertIn("1080x1080+0+0", cmd)
        self.assertIn("+repage", cmd)
        self.assertIn("-filter", cmd)
        self.assertIn("Lanczos", cmd)
        self.assertIn("-resize", cmd)
        self.assertIn("200%", cmd)

        # Expected final dimensions: 1080 * 2 = 2160
        self.assertEqual((final_w, final_h), (2160, 2160))


class TestEndToEndExecution(unittest.TestCase):
    """Runs a real ImageMagick conversion on a synthetic image."""

    def setUp(self):
        self.detector = ImageMagickDetector()
        self.info = self.detector.get_info()
        if not self.info.is_available:
            self.skipTest("ImageMagick is not available on this machine")
        self.processor = ImageProcessor(self.info)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="resizer_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_real_crop_and_upscale(self):
        # Create a 200x150 test image with spaces and unicode in filename
        test_file = self.temp_dir / "Test Photo 📸 (2026).png"
        create_cmd = [
            str(self.info.binary_path),
            "-size", "200x150",
            "xc:darkblue",
            "-fill", "white",
            "-draw", "circle 100,75 100,100",
            str(test_file),
        ]
        subprocess.run(create_cmd, check=True, capture_output=True)

        # Verify probe
        w, h = self.processor.get_image_dimensions(test_file)
        self.assertEqual((w, h), (200, 150))

        # Process: 1:1 Square + 3x upscale + Lanczos filter
        options = ProcessingOptions(
            input_paths=[test_file],
            output_dir=self.temp_dir / "output",
            scale=SCALE_MULTIPLIERS["3x"],
            aspect_ratio=ASPECT_RATIOS["1:1"],
            filter_option=RESIZE_FILTERS["Lanczos"],
            output_format="png",
        )

        result = self.processor.process_image(test_file, options)
        self.assertTrue(result.success, f"Processing failed: {result.error_message}")
        self.assertIsNotNone(result.output_path)
        self.assertTrue(result.output_path.exists())

        # 200x150 cropped to 1:1 is 150x150. Scaled 3x is 450x450.
        out_w, out_h = self.processor.get_image_dimensions(result.output_path)
        self.assertEqual((out_w, out_h), (450, 450))
        self.assertGreater(result.execution_time_seconds, 0.0)


class TestCrossPlatformSupport(unittest.TestCase):
    """Verifies cross-platform detection and path handling for Windows, macOS, and Linux."""

    def test_detector_install_hints_per_os(self):
        detector = ImageMagickDetector()

        # Test macOS hint
        detector.system = "Darwin"
        hint_mac = detector._get_install_hint()
        self.assertIn("brew install", hint_mac)

        # Test Windows hint
        detector.system = "Windows"
        hint_win = detector._get_install_hint()
        self.assertIn("winget install", hint_win)

        # Test Linux hint
        detector.system = "Linux"
        hint_linux = detector._get_install_hint()
        self.assertIn("apt install", hint_linux)
        self.assertIn("pacman -S", hint_linux)

    def test_subprocess_extra_kwargs_type(self):
        detector = ImageMagickDetector()
        info = detector.get_info()
        if info.is_available:
            processor = ImageProcessor(info)
            kwargs = processor._get_subprocess_extra_kwargs()
            self.assertIsInstance(kwargs, dict)


if __name__ == "__main__":
    unittest.main()
