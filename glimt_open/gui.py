from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .cli import clip_file


class GlimtOpenApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Glimt Open")
        root.geometry("720x500")
        root.minsize(620, 440)
        root.configure(bg="#101114")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#101114")
        style.configure("Panel.TFrame", background="#191b20")
        style.configure("TLabel", background="#101114", foreground="#f2f3f5", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#101114", foreground="#9da3ad")
        style.configure("Panel.TLabel", background="#191b20", foreground="#f2f3f5")
        style.configure("TEntry", fieldbackground="#24272e", foreground="#f2f3f5", insertcolor="#f2f3f5")
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
        style.configure("Accent.TButton", background="#a7f3d0", foreground="#10231c", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#82e8bd"), ("disabled", "#52645d")])

        outer = ttk.Frame(root, padding=28)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="GLIMT OPEN", font=("Segoe UI", 10, "bold"), foreground="#a7f3d0").pack(anchor="w")
        ttk.Label(outer, text="Local clipper", font=("Segoe UI Semibold", 25)).pack(anchor="w", pady=(7, 2))
        ttk.Label(outer, text="Create a clip from a video file on this device. Nothing is uploaded.", style="Muted.TLabel").pack(anchor="w", pady=(0, 22))

        panel = ttk.Frame(outer, style="Panel.TFrame", padding=20)
        panel.pack(fill="x")
        self.source = tk.StringVar()
        self.output = tk.StringVar(value=str(Path.home() / "Videos" / "Glimt Open" / "highlight.mp4"))
        self.start = tk.StringVar(value="0")
        self.duration = tk.StringVar(value="30")

        self._field(panel, "SOURCE VIDEO", self.source, self._pick_source)
        self._field(panel, "SAVE CLIP AS", self.output, self._pick_output, top=16)

        controls = ttk.Frame(panel, style="Panel.TFrame")
        controls.pack(fill="x", pady=(18, 0))
        for label, variable in (("START (SECONDS)", self.start), ("DURATION (SECONDS)", self.duration)):
            group = ttk.Frame(controls, style="Panel.TFrame")
            group.pack(side="left", fill="x", expand=True, padx=(0, 18))
            ttk.Label(group, text=label, style="Panel.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))
            ttk.Entry(group, textvariable=variable, width=18).pack(fill="x")

        self.run_button = ttk.Button(outer, text="Create clip", style="Accent.TButton", command=self._run)
        self.run_button.pack(anchor="w", pady=(18, 10))
        self.status = tk.StringVar(value="Ready · FFmpeg must be installed and available on PATH")
        ttk.Label(outer, textvariable=self.status, style="Muted.TLabel", wraplength=650).pack(anchor="w")
        ttk.Label(outer, text="Glimt Open is an independent community reference utility · MIT License", style="Muted.TLabel").pack(side="bottom", anchor="w", pady=(24, 0))

    def _field(self, parent, label, variable, command, top=0):
        group = ttk.Frame(parent, style="Panel.TFrame")
        group.pack(fill="x", pady=(top, 0))
        ttk.Label(group, text=label, style="Panel.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 6))
        line = ttk.Frame(group, style="Panel.TFrame")
        line.pack(fill="x")
        ttk.Entry(line, textvariable=variable).pack(side="left", fill="x", expand=True)
        ttk.Button(line, text="Browse", command=command).pack(side="left", padx=(8, 0))

    def _pick_source(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm"), ("All files", "*.*")])
        if path:
            self.source.set(path)
            if self.output.get().endswith("highlight.mp4"):
                self.output.set(str(Path.home() / "Videos" / "Glimt Open" / f"{Path(path).stem}-clip.mp4"))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 video", "*.mp4"), ("MKV video", "*.mkv"), ("MOV video", "*.mov")])
        if path:
            self.output.set(path)

    def _run(self):
        try:
            start = float(self.start.get())
            duration = float(self.duration.get())
            source = Path(self.source.get())
            output = Path(self.output.get())
            if not self.source.get() or not self.output.get():
                raise ValueError("Choose a source video and an output path.")
            if start < 0 or duration <= 0:
                raise ValueError("Start must be zero or greater; duration must be greater than zero.")
        except ValueError as exc:
            messagebox.showerror("Check your settings", str(exc))
            return
        self.run_button.configure(state="disabled")
        self.status.set("Creating clip?")
        thread = threading.Thread(target=self._worker, args=(source, output, start, duration), daemon=True)
        thread.start()

    def _worker(self, source, output, start, duration):
        try:
            code = clip_file(source, output, start, duration)
            if code == 0:
                self.root.after(0, self._finish, True, f"Clip saved: {output}")
            else:
                self.root.after(0, self._finish, False, f"FFmpeg exited with code {code}. Check the source file and codec support.")
        except Exception as exc:
            self.root.after(0, self._finish, False, str(exc))
    def _finish(self, success, message):
        self.run_button.configure(state="normal")
        self.status.set(message)
        if success:
            messagebox.showinfo("Clip created", message)
        else:
            messagebox.showerror("Could not create clip", message)


def main() -> int:
    root = tk.Tk()
    GlimtOpenApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
