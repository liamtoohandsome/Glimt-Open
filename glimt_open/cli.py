from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Sequence


def build_ffmpeg_command(
    executable: str,
    source: Path,
    output: Path,
    start_seconds: float,
    duration_seconds: float,
) -> list[str]:
    """Build a local FFmpeg stream-copy command for a selected time window."""
    source = Path(source)
    output = Path(output)
    if not math.isfinite(start_seconds) or start_seconds < 0:
        raise ValueError("Start time must be finite and zero or greater.")
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("Duration must be finite and greater than zero.")
    if source.resolve() == output.resolve():
        raise ValueError("Output must not overwrite the source file.")
    if not output.suffix:
        raise ValueError("Output path must include a media file extension.")

    return [
        executable,
        "-hide_banner",
        "-y",
        "-ss",
        f"{start_seconds:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration_seconds:.3f}",
        "-map",
        "0",
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        str(output),
    ]


def clip_file(
    source: Path,
    output: Path,
    start_seconds: float,
    duration_seconds: float,
    ffmpeg: str = "ffmpeg",
) -> int:
    """Extract a local time window without damaging an existing output on failure."""
    source = Path(source)
    output = Path(output)

    if not source.is_file():
        raise FileNotFoundError(f"Input media file does not exist: {source}")
    executable = shutil.which(ffmpeg)
    if executable is None:
        raise FileNotFoundError(
            f"Could not find '{ffmpeg}'. Install FFmpeg and add it to PATH."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(
        f".{output.stem}.{uuid.uuid4().hex}.partial{output.suffix}"
    )
    command = build_ffmpeg_command(
        executable, source, temporary_output, start_seconds, duration_seconds
    )
    try:
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return int(result.returncode)
        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise RuntimeError(
                "FFmpeg reported success but did not create a non-empty output."
            )
        # The temporary file lives beside the destination, so replacement is atomic
        # on the same filesystem and a failed encode cannot leave a partial final clip.
        os.replace(temporary_output, output)
        return 0
    finally:
        try:
            temporary_output.unlink(missing_ok=True)
        except OSError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glimt-open",
        description="Extract a time window from a local media file using FFmpeg.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    clip = commands.add_parser("clip", help="Extract a local clip without re-encoding.")
    clip.add_argument("source", type=Path, help="Input media file")
    clip.add_argument("--start", type=float, required=True, help="Start time in seconds")
    clip.add_argument("--duration", type=float, required=True, help="Clip duration in seconds")
    clip.add_argument("--output", type=Path, required=True, help="Output media file")
    clip.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg executable name or path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "clip":
        try:
            return clip_file(
                args.source, args.output, args.start, args.duration, args.ffmpeg
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"glimt-open: error: {exc}", file=sys.stderr)
            return 2
    return 2
