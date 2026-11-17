# Glimt Open — Reference Toolkit

Glimt Open is a small, independent reference project for developers experimenting with local video clipping workflows.

It demonstrates one narrow task: extracting a time window from an existing local media file with FFmpeg. It is **not** the Glimt desktop application and does not implement live desktop capture, a rolling capture buffer, automated gameplay detection, voice triggers, or the commercial product's internal pipeline.

## Included

- A lightweight desktop interface built with Python's standard-library Tkinter.
- A command-line wrapper around FFmpeg.
- Manual source, start-time, duration, and output controls.
- Local-only processing; no account, telemetry, upload, or network calls.
- Safe output handling: failed clipping attempts do not replace an existing destination file.
- Offline unit tests and cross-platform GitHub Actions.

## Requirements

- Windows, macOS, or Linux
- Python 3.11+
- FFmpeg available on PATH
- Tkinter (included with most standard Python installations; some Linux distributions package it separately)

## Install

From the repository directory:

    python -m pip install -e .

## Launch the desktop UI

    glimt-open-gui

Or run directly from the source checkout:

    python -m glimt_open.gui

## Use the CLI

    glimt-open clip ./gameplay.mp4 --start 125 --duration 30 --output ./clips/highlight.mp4

You can also run:

    python -m glimt_open clip ./gameplay.mp4 --start 125 --duration 30 --output ./clips/highlight.mp4

The command copies selected streams without re-encoding. With stream-copy mode, exact cut boundaries depend on keyframe placement in the source media. This is a small reference utility, not a promise of frame-accurate editing. The source file is never overwritten. A failed FFmpeg run leaves an existing output file intact.

## Tests

    python -m unittest discover -s tests -v

The test suite uses mocked FFmpeg calls and does not require a media file or network access.

## Relationship to Glimt

This repository is developed separately from the commercial Glimt Free and Glimt Pro applications. It contains no copied commercial application source, product assets, private build configuration, or proprietary Pro trigger implementation. It is intended as a transparent starting point for discussion and community contributions.

## Project status

Early reference implementation. Contributions and focused technical feedback are welcome. Please open an issue with a reproducible example.

## License

MIT. See [LICENSE](LICENSE).
