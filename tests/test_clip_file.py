import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from glimt_open.cli import build_ffmpeg_command, clip_file


class ClipCommandTests(unittest.TestCase):
    def test_builds_local_stream_copy_command(self):
        source = Path("gameplay.mp4")
        output = Path("clips/highlight.mp4")
        command = build_ffmpeg_command("ffmpeg.exe", source, output, 12.5, 30)
        self.assertEqual(command[0], "ffmpeg.exe")
        self.assertIn("-c", command)
        self.assertIn("copy", command)
        self.assertIn("12.500", command)
        self.assertIn("30.000", command)
        self.assertEqual(command[-1], str(output))

    def test_rejects_negative_start(self):
        with self.assertRaises(ValueError):
            build_ffmpeg_command("ffmpeg", Path("in.mp4"), Path("out.mp4"), -1, 5)

    def test_rejects_zero_duration(self):
        with self.assertRaises(ValueError):
            build_ffmpeg_command("ffmpeg", Path("in.mp4"), Path("out.mp4"), 0, 0)

    def test_rejects_non_finite_start_and_duration(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    build_ffmpeg_command("ffmpeg", Path("in.mp4"), Path("out.mp4"), value, 5)
                with self.assertRaises(ValueError):
                    build_ffmpeg_command("ffmpeg", Path("in.mp4"), Path("out.mp4"), 0, value)

    def test_rejects_overwriting_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "same.mp4"
            with self.assertRaises(ValueError):
                build_ffmpeg_command("ffmpeg", source, source, 0, 5)

    def test_rejects_output_without_extension(self):
        with self.assertRaises(ValueError):
            build_ffmpeg_command("ffmpeg", Path("in.mp4"), Path("out"), 0, 5)

    def test_clip_file_requires_existing_input(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "missing.mp4"
            output = Path(temp) / "out.mp4"
            with self.assertRaises(FileNotFoundError):
                clip_file(source, output, 0, 5)

    def test_success_atomically_replaces_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.mp4"
            output = root / "clips" / "highlight.mp4"
            source.write_bytes(b"source")
            output.parent.mkdir()
            output.write_bytes(b"old output")
            seen = {}

            def fake_run(command, **kwargs):
                seen["command"] = command
                seen["kwargs"] = kwargs
                Path(command[-1]).write_bytes(b"new clip")
                return SimpleNamespace(returncode=0)

            with patch("glimt_open.cli.shutil.which", return_value="ffmpeg-test"), patch(
                "glimt_open.cli.subprocess.run", side_effect=fake_run
            ):
                result = clip_file(source, output, 1, 5)

            self.assertEqual(result, 0)
            self.assertEqual(output.read_bytes(), b"new clip")
            self.assertIn(".partial.mp4", Path(seen["command"][-1]).name)
            self.assertNotIn("shell", seen["kwargs"])
            self.assertEqual(list(output.parent.glob("*.partial.mp4")), [])

    def test_failed_clip_preserves_existing_output_and_cleans_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.mp4"
            output = root / "highlight.mp4"
            source.write_bytes(b"source")
            output.write_bytes(b"keep this")
            partials = []

            def fake_run(command, **_kwargs):
                partial = Path(command[-1])
                partial.write_bytes(b"incomplete")
                partials.append(partial)
                return SimpleNamespace(returncode=1)

            with patch("glimt_open.cli.shutil.which", return_value="ffmpeg-test"), patch(
                "glimt_open.cli.subprocess.run", side_effect=fake_run
            ):
                result = clip_file(source, output, 1, 5)

            self.assertEqual(result, 1)
            self.assertEqual(output.read_bytes(), b"keep this")
            self.assertEqual(len(partials), 1)
            self.assertFalse(partials[0].exists())

    def test_success_without_output_is_reported_and_cleaned(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.mp4"
            output = root / "highlight.mp4"
            source.write_bytes(b"source")
            partials = []

            def fake_run(command, **_kwargs):
                partials.append(Path(command[-1]))
                return SimpleNamespace(returncode=0)

            with patch("glimt_open.cli.shutil.which", return_value="ffmpeg-test"), patch(
                "glimt_open.cli.subprocess.run", side_effect=fake_run
            ):
                with self.assertRaises(RuntimeError):
                    clip_file(source, output, 1, 5)

            self.assertFalse(output.exists())
            self.assertFalse(partials[0].exists())


if __name__ == "__main__":
    unittest.main()
