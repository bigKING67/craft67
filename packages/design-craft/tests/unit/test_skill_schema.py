from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.design_craft.validation.skill_schema import validate_skill


class SkillSchemaTests(unittest.TestCase):
    def validate_text(self, text: str, directory: str = "design-craft") -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / directory
            root.mkdir()
            (root / "SKILL.md").write_text(text, encoding="utf-8")
            return validate_skill(root)

    def test_accepts_canonical_frontmatter(self) -> None:
        payload = self.validate_text(
            '---\nname: design-craft\ndescription: "A focused skill."\n---\n'
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["name"], "design-craft")

    def test_rejects_schema_and_identity_violations(self) -> None:
        unexpected = self.validate_text(
            "---\nname: design-craft\ndescription: valid\nlicense: MIT\n---\n"
        )
        self.assertFalse(unexpected["ok"])
        self.assertIn("unsupported SKILL.md frontmatter field", unexpected["errors"][0])

        wrong_directory = self.validate_text(
            "---\nname: design-craft\ndescription: valid\n---\n",
            directory="other-skill",
        )
        self.assertFalse(wrong_directory["ok"])
        self.assertTrue(
            any("name must match" in str(error) for error in wrong_directory["errors"])
        )

        unsafe_description = self.validate_text(
            '---\nname: design-craft\ndescription: "Use <script>."\n---\n'
        )
        self.assertFalse(unsafe_description["ok"])
        self.assertIn("description must not contain angle brackets", unsafe_description["errors"])

        empty_description = self.validate_text(
            '---\nname: design-craft\ndescription: ""\n---\n'
        )
        self.assertFalse(empty_description["ok"])
        self.assertIn("non-empty string", empty_description["errors"][0])


if __name__ == "__main__":
    unittest.main()
