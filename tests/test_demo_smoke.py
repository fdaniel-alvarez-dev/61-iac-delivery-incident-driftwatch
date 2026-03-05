from __future__ import annotations

import os
import pathlib
import subprocess
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class DemoSmokeTests(unittest.TestCase):
    def test_validate_passes_with_examples(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        cp = subprocess.run(
            [
                "python3",
                "-m",
                "portfolio_proof",
                "validate",
                "--examples",
                "examples/baseline",
                "--now",
                "2026-03-01T00:00:00Z",
            ],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")

    def test_report_is_generated(self) -> None:
        artifacts = REPO_ROOT / "artifacts"
        if artifacts.exists():
            for p in artifacts.glob("*"):
                p.unlink()
        artifacts.mkdir(exist_ok=True)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        cp = subprocess.run(
            [
                "python3",
                "-m",
                "portfolio_proof",
                "report",
                "--examples",
                "examples/drifted",
                "--artifacts",
                "artifacts",
                "--now",
                "2026-03-01T00:00:00Z",
            ],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        report = artifacts / "report.md"
        self.assertTrue(report.exists(), "artifacts/report.md not created")
        text = report.read_text(encoding="utf-8")
        self.assertIn("Pain Point 1", text)
        self.assertIn("Pain Point 2", text)
        self.assertIn("Pain Point 3", text)
