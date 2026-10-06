"""Provider-aware v2 transparency; legacy jobs retain their contract."""
import copy
import unittest
from unittest.mock import patch

from support import ROOT, cc, load


class ImageContext(cc.ValidationContext):
    @property
    def providers_dir(self):
        return ROOT / "integrations/image-production/providers"


class TransparentJobTests(unittest.TestCase):
    def setUp(self):
        self.job = load("skills/creative-craft/templates/image-job.json")
        self.job["provider_profile"] = "openai.gpt-image-2.5-sunburst.2026-09-08"
        self.job["canvas"]["background"] = "transparent"
        self.context = ImageContext()

    def test_capable_v2_profiles_accept_png_and_webp(self):
        for model in ("sunburst", "flare"):
            for fmt in ("png", "webp"):
                with self.subTest(model=model, fmt=fmt):
                    self.job["provider_profile"] = f"openai.gpt-image-2.5-{model}.2026-09-08"
                    self.job["canvas"]["format"] = fmt
                    _, result = cc.validate_data(self.job, context=self.context)
                    self.assertTrue(result.ok, result.errors)
                    self.assertIn("transparent", cc.compile_image_markdown(self.job))

    def test_transparent_jpeg_rejected(self):
        self.job["canvas"]["format"] = "jpeg"
        _, result = cc.validate_data(self.job, context=self.context)
        self.assertFalse(result.ok)
        self.assertTrue(any("PNG/WebP" in item for item in result.errors))

    def test_missing_or_non_boolean_capability_is_rejected(self):
        for value in (None, False, "true"):
            with self.subTest(value=value):
                profiles = copy.deepcopy(cc.provider_profiles(self.context.providers_dir))
                caps = profiles[self.job["provider_profile"]]["capabilities"]
                caps.pop("transparent_background")
                if value is not None:
                    caps["transparent_background"] = value
                with patch("creative_craft_contracts.provider_profiles", return_value=profiles):
                    _, result = cc.validate_data(self.job, context=self.context)
                self.assertFalse(result.ok)
                self.assertTrue(any("capable v2 provider" in item for item in result.errors))

    def test_original_provider_and_v1_remain_rejected(self):
        self.job["provider_profile"] = "openai.gpt-image-2.2026-04-21"
        _, result = cc.validate_data(self.job)
        self.assertFalse(result.ok)
        self.assertTrue(any("capable v2 provider" in item for item in result.errors))
        legacy = load("tests/fixtures/legacy/image-job-v1.json")
        legacy["canvas"]["background"] = "transparent"
        legacy["provider_profile"] = "openai.gpt-image-2.5-sunburst.2026-09-08"
        result = cc.validate_image_job(legacy, context=self.context)
        self.assertFalse(result.ok)

    def test_ordinary_backgrounds_keep_working(self):
        for background in ("opaque", "auto"):
            with self.subTest(background=background):
                self.job["canvas"]["background"] = background
                _, result = cc.validate_data(self.job, context=self.context)
                self.assertTrue(result.ok, result.errors)


if __name__ == "__main__":
    unittest.main()
