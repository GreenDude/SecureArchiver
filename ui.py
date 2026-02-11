import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pyzipper  # for compression constants


class SecureArchiverUI(ttk.Frame):
    def __init__(self, master: tk.Tk, archive_builder):
        super().__init__(master, padding=12)
        self.master = master
        self.builder = archive_builder

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # ===== Top area
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Files list + scrollbar
        files_frame = ttk.LabelFrame(top, text="FILES")
        files_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        top.columnconfigure(0, weight=2)
        top.rowconfigure(0, weight=1)

        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)

        self.files_list = tk.Listbox(files_frame, height=10, activestyle="none")
        self.files_list.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.files_list.configure(yscrollcommand=scrollbar.set)

        # Options panel
        options_frame = ttk.Frame(top)
        options_frame.grid(row=0, column=1, sticky="nsew")
        top.columnconfigure(1, weight=2)

        # Compression
        compression_box = ttk.LabelFrame(options_frame, text="Compression")
        compression_box.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        options_frame.columnconfigure(0, weight=1)

        self.compression_var = tk.StringVar(value="medium")
        for i, opt in enumerate(["none", "small", "medium", "large"]):
            ttk.Radiobutton(compression_box, text=opt, value=opt, variable=self.compression_var)\
                .grid(row=i, column=0, sticky="w", padx=8, pady=2)

        # Encryption
        encryption_box = ttk.LabelFrame(options_frame, text="Encryption")
        encryption_box.grid(row=1, column=0, sticky="ew")

        # By default, the encryption is set to the maximum value of 256
        self.encryption_var = tk.StringVar(value="256")
        for i, opt in enumerate(["128", "192", "256"]):
            ttk.Radiobutton(encryption_box, text=opt, value=opt, variable=self.encryption_var)\
                .grid(row=i, column=0, sticky="w", padx=8, pady=2)

        # Separator
        ttk.Separator(self, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=12)

        # Password
        pw_frame = ttk.Frame(self)
        pw_frame.grid(row=2, column=0, sticky="ew")
        pw_frame.columnconfigure(1, weight=1)

        ttk.Label(pw_frame, text="Password:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(pw_frame, textvariable=self.password_var, show="•")
        self.password_entry.grid(row=0, column=1, sticky="ew")

        # Status + progress
        status_frame = ttk.Frame(self)
        status_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(status_frame, length=220, mode="indeterminate")
        self.progress.grid(row=0, column=1, sticky="e")

        # Buttons
        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Button(buttons, text="ADD FILE", command=self.on_add_files)\
            .grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(buttons, text="ARCHIVE", command=self.on_archive)\
            .grid(row=0, column=1, sticky="ew", padx=(8, 0))

    # ===== UI actions
    def on_add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Select files to archive")
        if not paths:
            return
        for p in paths:
            self.files_list.insert(tk.END, p)

    def on_archive(self) -> None:
        files = list(self.files_list.get(0, tk.END))
        if not files:
            messagebox.showwarning("Nothing to archive", "Please add at least one file.")
            return

        enc = self.encryption_var.get()
        pwd = self.password_var.get()

        if enc != "none" and not pwd:
            messagebox.showwarning("Password required", "Please set a password when encryption is enabled.")
            return

        # Run in background thread
        self._set_busy(True)
        t = threading.Thread(target=self._archive_worker, args=(files, enc, pwd), daemon=True)
        t.start()

    def _archive_worker(self, files: list[str], enc: str, pwd: str) -> None:
        try:
            self._set_status("Preparing…")

            # IMPORTANT: your builder keeps state (_sources etc.)
            # So we re-create it each run to avoid old files sticking around.
            # If you prefer, we can add builder.reset() instead.
            builder = type(self.builder)()  # new instance of ArchiveBuilder

            # add sources
            for f in files:
                builder.add_source(f)

            # compression mapping
            comp_ui = self.compression_var.get()
            comp_map = {
                "none": pyzipper.ZIP_STORED,
                "small": pyzipper.ZIP_DEFLATED,
                "medium": pyzipper.ZIP_BZIP2,
                "large": pyzipper.ZIP_LZMA,
            }
            builder.set_compression_strength(comp_map.get(comp_ui, pyzipper.ZIP_DEFLATED))

            # encryption mapping
            if enc == "none":
                builder.set_password("")  # no encryption
            else:
                builder.set_encryption_strength(int(enc))
                builder.set_password(pwd)

            self._set_status("Archiving…")
            builder.archive()

            self.master.after(0, lambda: messagebox.showinfo("Done", "Archive created in the output folder."))

        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.master.after(0, lambda: self._set_busy(False))
            self._set_status("Ready")

    # ===== UI helpers (thread-safe-ish)
    def _set_busy(self, busy: bool) -> None:
        def apply():
            if busy:
                self.progress.start(10)
            else:
                self.progress.stop()
        self.master.after(0, apply)

    def _set_status(self, text: str) -> None:
        self.master.after(0, lambda: self.status_var.set(text))