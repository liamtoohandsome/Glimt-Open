# Example workflow

1. Confirm FFmpeg is available with: ffmpeg -version
2. Choose a local source file you are allowed to edit.
3. Run:

       python -m glimt_open clip ./gameplay.mp4 --start 125 --duration 30 --output ./clips/highlight.mp4

4. Open the resulting file and verify its audio/video streams.

This example uses stream copy to avoid a second encode. Some formats only cut cleanly at keyframes; re-encoding for frame-accurate cuts is a possible future contribution.
