import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Any, Optional
from pathlib import Path
from PIL import Image, ImageTk
import io

try:
    from tkinterdnd2 import Tk as DnDTk, DND_FILES
except ImportError:
    DnDTk = tk.Tk
    DND_FILES = "DND_Files"

from .config import APP_TITLE, APP_VERSION, DEFAULT_DPI
from .exceptions import PDFImageToolkitError
from .logger import get_logger
from .operations import (
    images_to_pdf,
    pdf_to_word,
    pdf_to_images,
    merge_pdfs,
    split_pdf,
    resize_image,
    resize_pdf,
    get_pdf_page_count,
    get_pdf_info,
)
from .workers import BackgroundWorker
from .prefs import get_preferences
from .paths import get_app_data_dir
from .ui_utils import format_file_size, get_total_file_size, get_listbox_count_text, load_icon_safe


logger = get_logger()



class PDFImageToolkitApp(DnDTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("945x790")
        self.minsize(780, 600)
        self.is_processing = False
        self.current_worker: Optional[BackgroundWorker] = None
        self.prefs = get_preferences()
        self.image_paths: list[str] = []
        self.merge_paths: list[str] = []
        self._merge_drag_start_index: Optional[int] = None
        self._image_drag_start_index: Optional[int] = None

        # Try to load custom favicon
        self._set_favicon()

        self._configure_style()
        self._build_ui()

        logger.info("%s started", APP_TITLE)

    def _set_favicon(self):
        """Load custom favicon if available, otherwise use default Tk icon."""
        # Determine base directory (supports PyInstaller bundles)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent

        # Candidate favicon files
        favicon_paths = [
            Path(__file__).parent.parent / "favicon.ico",
            base_dir / "favicon.ico",
            base_dir / "favicon.png",
            get_app_data_dir() / "favicon.ico",
        ]

        for favicon_path in favicon_paths:
            if not favicon_path.exists():
                continue

            try:
                # Try native iconbitmap first
                try:
                    self.iconbitmap(str(favicon_path))
                    logger.info("Loaded favicon from: %s", favicon_path)
                    return
                except Exception:
                    pass

                # Fallback: load with PIL and use iconphoto
                img = Image.open(favicon_path)
                photo = ImageTk.PhotoImage(img)
                self._icon_photo = photo  # Keep reference to prevent GC
                self.iconphoto(False, photo)
                logger.info("Loaded favicon from: %s", favicon_path)
                return
            except Exception as e:
                logger.debug("Failed to load favicon from %s: %s", favicon_path, e)

        logger.debug("No custom favicon found, using default icon")

    def _configure_style(self):
        self.configure(bg="#0f172a")

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background="#f8fafc")
        style.configure("Body.TFrame", background="#f8fafc")
        style.configure("Header.TFrame", background="#0f172a")
        style.configure("Header.TLabel", background="#0f172a", font=("Segoe UI", 18, "bold"), foreground="#ffffff")
        style.configure("Header.Subtext.TLabel", background="#0f172a", font=("Segoe UI", 10), foreground="#e2e8f0")
        style.configure("Subheader.TLabel", background="#f8fafc", font=("Segoe UI", 10), foreground="#475569")
        style.configure("TButton", font=("Segoe UI", 10), padding=10, relief="flat")
        style.map("TButton", background=[("active", "#e2e8f0"), ("!disabled", "#f8fafc")])
        style.configure("Rounded.TButton", font=("Segoe UI", 10), padding=10, relief="flat", background="#e2e8f0", foreground="#0f172a")
        style.map("Rounded.TButton", background=[("active", "#dbeafe"), ("!disabled", "#e2e8f0")], foreground=[("!disabled", "#0f172a")])
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10, relief="flat", background="#2563eb", foreground="#ffffff")
        style.map("Action.TButton", background=[("active", "#1d4ed8"), ("!disabled", "#2563eb")], foreground=[("!disabled", "#ffffff")])
        style.configure("TLabel", background="#f8fafc", font=("Segoe UI", 10), foreground="#0f172a")
        style.configure("Status.TLabel", background="#f8fafc", foreground="#475569", font=("Segoe UI", 9))
        style.configure("Footer.TLabel", background="#f8fafc", foreground="#475569", font=("Segoe UI", 9, "italic"))
        style.configure("File.Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#0f172a", rowheight=24)
        style.configure("File.Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        style.configure("TEntry", background="#f8fafc", fieldbackground="#f8fafc", padding=8)
        style.configure("TCombobox", fieldbackground="#f8fafc", background="#f8fafc", padding=8)
        style.configure("TSpinbox", fieldbackground="#f8fafc", background="#f8fafc", padding=8)
        style.configure("Horizontal.TProgressbar", troughcolor="#e2e8f0", background="#22c55e", thickness=10)
        style.map("Horizontal.TProgressbar", background=[("!disabled", "#22c55e")])

        style.configure("TNotebook", background="#f8fafc", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[12, 8], background="#dbeafe", foreground="#0f172a")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#0f172a")])

    def _build_ui(self):
        main = ttk.Frame(self, padding=0, style="Body.TFrame")
        main.pack(fill="both", expand=True)

        header_bar = ttk.Frame(main, padding=20, style="Header.TFrame")
        header_bar.pack(fill="x")

        ttk.Label(header_bar, text=APP_TITLE, style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header_bar,
            text="Lightweight tool for image/PDF conversion, merge, and split.",
            style="Header.Subtext.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(main, padding=24, style="Body.TFrame")
        content.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True)

        self._build_images_to_pdf_tab()
        self._build_pdf_to_word_tab()
        self._build_pdf_to_images_tab()
        self._build_resize_tab()
        self._build_merge_pdf_tab()
        self._build_split_pdf_tab()

        # Progress section with cancel button
        progress_frame = ttk.Frame(content)
        progress_frame.pack(fill="x", pady=(12, 4))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode="determinate",
            maximum=100,
            style="Horizontal.TProgressbar",
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)

        self.cancel_button = ttk.Button(
            progress_frame,
            text="Cancel",
            command=self._cancel_operation,
            state="disabled",
            style="TButton",
        )
        self.cancel_button.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(content, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

        ttk.Label(main, text=f"{APP_TITLE} v{APP_VERSION} for official use only.", style="Footer.TLabel").pack(fill="x", pady=(16, 0))

    def _set_status(self, message: str):
        self.status_var.set(message)
        self.update_idletasks()

    def _cancel_operation(self):
        """Request cancellation of current operation."""
        if self.current_worker:
            self._set_status("Cancelling...")
            self.current_worker.stop()
            self.cancel_button.config(state="disabled")

    def _set_progress(self, current: int, total: int):
        # Raise an error to break out of long-running operations in the background worker
        if self.current_worker and self.current_worker.is_cancelled():
            raise InterruptedError("Operation cancelled by user.")

        if total <= 0:
            percent = 0
        else:
            percent = min(100, max(0, (current / total) * 100))

        self.after(0, lambda: self.progress_var.set(percent))

    def _reset_progress(self):
        self.progress_var.set(0)

    def _friendly_error_message(self, exc: Exception) -> str:
        if isinstance(exc, PDFImageToolkitError):
            return str(exc)

        if isinstance(exc, PermissionError):
            return "The file cannot be saved or opened. Please close it if it is open in another app, then try again."

        if isinstance(exc, FileNotFoundError):
            return "The selected file could not be found. Please select it again."

        return "Something went wrong. Please check the app log for technical details."

    def _check_file_size_warning(self, file_paths: list[str | Path], operation_name: str) -> bool:
        """Check if files exceed warning threshold. Returns True if user wants to continue."""
        total_size_mb = get_total_file_size(file_paths) / (1024 * 1024)
        threshold_mb = self.prefs.get_file_size_warning_mb()

        if total_size_mb > threshold_mb:
            response = messagebox.askyesno(
                APP_TITLE,
                f"{operation_name} will process {format_file_size(total_size_mb * 1024 * 1024)} of data.\n\nContinue?",
            )
            return response
        return True

    def _run_task(
        self,
        task_name: str,
        task: Callable[[], Any],
        success_message: str,
        file_paths: Optional[list] = None,
        cancellable: bool = True,
    ):
        if self.is_processing:
            messagebox.showwarning(APP_TITLE, "Another task is already running. Please wait for it to finish.")
            return

        # Check file size warnings if provided
        if file_paths:
            if not self._check_file_size_warning(file_paths, task_name):
                return

        self.is_processing = True
        self._reset_progress()
        self._set_status(f"{task_name}...")
        self.cancel_button.config(state="normal" if cancellable else "disabled")

        logger.info("Task started: %s", task_name)

        def on_success(result):
            def update_ui():
                self._set_progress(1, 1)
                self._set_status("Done")

                if isinstance(result, list):
                    detail = f"{len(result)} file(s) created."
                else:
                    detail = f"Created: {result}"

                logger.info("Task completed: %s | Result: %s", task_name, detail)
                messagebox.showinfo(APP_TITLE, f"{success_message}\n\n{detail}")

            self.after(0, update_ui)

        def on_error(exc):
            is_cancellation = isinstance(exc, InterruptedError)

            if is_cancellation:
                logger.info("Task cancelled by user: %s", task_name)
            else:
                logger.exception("Task failed: %s", task_name)

            def update_ui():
                if is_cancellation:
                    self._set_status("Cancelled")
                else:
                    self._set_status("Failed")
                    messagebox.showerror(APP_TITLE, self._friendly_error_message(exc))

            self.after(0, update_ui)

        def on_finally():
            worker = self.current_worker

            def update_ui():
                self.is_processing = False
                # Some tasks (e.g. single blocking library calls) never reach a
                # progress checkpoint, so cancellation is only visible here.
                if worker is not None and worker.is_cancelled() and self.status_var.get() not in ("Cancelled", "Failed", "Done"):
                    self._set_status("Cancelled")
                self.current_worker = None
                self.cancel_button.config(state="disabled")

            self.after(0, update_ui)

        self.current_worker = BackgroundWorker(task, on_success=on_success, on_error=on_error, on_finally=on_finally)
        self.current_worker.start()

    def _add_action_panel(self, parent, buttons_config: list[tuple[str, callable, bool]]) -> ttk.Frame:
        """Create a persistent action panel at the bottom of a tab."""
        panel_frame = ttk.Frame(parent)
        panel_frame.pack(fill="x", pady=12, side="bottom")
        return self._add_action_buttons(panel_frame, buttons_config)

    def _add_action_buttons(self, parent, buttons_config: list[tuple[str, callable, bool]]):
        """Add action buttons directly (non-collapsible)."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=8)

        for label, command, is_action in buttons_config:
            style = "Action.TButton" if is_action else "Rounded.TButton"
            ttk.Button(btn_frame, text=label, command=command, style=style).pack(side="left", padx=4)

        return btn_frame

    def _register_drop_target(self, widget, callback):
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", callback)
        except Exception:
            pass

    def _parse_drop_files(self, data: str) -> list[str]:
        if not data:
            return []
        try:
            raw_paths = self.tk.splitlist(data)
        except Exception:
            raw_paths = [data]
        return [path.strip("{}") for path in raw_paths if path.strip("{}")]

    def _create_file_table(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(8, 8))

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 4))
        label = ttk.Label(header, text="Selected files:", style="Status.TLabel")
        label.pack(side="left")

        count_label = ttk.Label(header, text="(0 files)", style="Status.TLabel")
        count_label.pack(side="left", padx=(4, 0))

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame,
            columns=[col[0] for col in columns],
            show="headings",
            style="File.Treeview",
            selectmode=tk.EXTENDED,
            height=8,
        )

        for name, text, width, anchor in columns:
            tree.heading(name, text=text)
            tree.column(name, width=width, anchor=anchor, stretch=True)

        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        return tree, count_label

    def _add_file_list(self, parent, columns=None):
        if columns is None:
            columns = [("sn", "#", 40, "center"), ("name", "Name", 260, "w"), ("size", "Size", 120, "center")]
        return self._create_file_table(parent, columns)

    def _refresh_table(self, tree, rows):
        tree.delete(*tree.get_children())
        for idx, row in enumerate(rows, start=1):
            tree.insert("", "end", iid=str(idx - 1), values=(str(idx),) + row)

    def _update_count_label(self, count_label, count):
        count_label.config(text=get_listbox_count_text(count))

    def _format_file_row(self, path: str) -> tuple[str, str]:
        p = Path(path)
        name = p.name
        size = format_file_size(p.stat().st_size) if p.exists() else "Unknown"
        return name, size

    def _on_images_drop(self, event):
        for path in self._parse_drop_files(event.data):
            if Path(path).suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"]:
                self.image_paths.append(path)
        self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
        self._update_count_label(self.image_count_label, len(self.image_paths))

    def _on_merge_drop(self, event):
        for path in self._parse_drop_files(event.data):
            if Path(path).suffix.lower() == ".pdf":
                self.merge_paths.append(path)
        self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
        self._update_count_label(self.merge_count_label, len(self.merge_paths))

    def _on_pdf_word_drop(self, event):
        dropped = self._parse_drop_files(event.data)
        if dropped:
            path = dropped[0]
            if Path(path).suffix.lower() == ".pdf":
                self.pdf_word_path.set(path)
            else:
                messagebox.showwarning(APP_TITLE, "Please drop a PDF file.")

    def _on_pdf_images_drop(self, event):
        dropped = self._parse_drop_files(event.data)
        if dropped:
            path = dropped[0]
            if Path(path).suffix.lower() == ".pdf":
                self.pdf_images_path.set(path)
            else:
                messagebox.showwarning(APP_TITLE, "Please drop a PDF file.")

    def _file_picker(self, parent, variable, button_text, filetypes, last_folder_key: Optional[str] = None):
        """File picker with optional remember-last-folder support."""
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill="x", pady=12)

        entry = ttk.Entry(wrapper, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True)

        def browse():
            kwargs = {"title": button_text, "filetypes": filetypes}
            
            # Set initial directory to last used folder
            if last_folder_key:
                last_folder = self.prefs.get_last_output_folder(last_folder_key)
                if last_folder:
                    kwargs["initialdir"] = last_folder

            path = filedialog.askopenfilename(**kwargs)
            if path:
                variable.set(path)

        ttk.Button(wrapper, text=button_text, command=browse, style="Rounded.TButton").pack(side="left", padx=(8, 0))

    def _build_images_to_pdf_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="Images to PDF")

        ttk.Label(tab, text="Convert selected images into one PDF.").pack(anchor="w")
        ttk.Label(
            tab,
            text="Large images are automatically resized to reduce memory usage.",
            style="Subheader.TLabel",
        ).pack(anchor="w", pady=(3, 6))

        self.image_tree, self.image_count_label = self._add_file_list(tab)
        self._register_drop_target(tab, self._on_images_drop)
        self._register_drop_target(self.image_tree, self._on_images_drop)
        self.image_tree.bind("<ButtonPress-1>", self._start_image_drag)
        self.image_tree.bind("<B1-Motion>", self._drag_image_motion)
        self.image_tree.bind("<ButtonRelease-1>", self._end_image_drag)

        action_buttons = [
            ("Add Images", self._select_images, False),
            ("Remove Selected", self._remove_selected_images, False),
            ("Clear", self._clear_images, False),
            ("↑ Move Up", self._move_image_up, False),
            ("Move Down ↓", self._move_image_down, False),
            ("Convert", self._convert_images_to_pdf, True),
        ]
        self._add_action_panel(tab, action_buttons)

    def _select_images(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("All files", "*.*"),
            ],
        )

        for path in paths:
            if Path(path).suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"]:
                self.image_paths.append(path)

        self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
        self._update_count_label(self.image_count_label, len(self.image_paths))

    def _remove_selected_images(self):
        selected = sorted([int(item) for item in self.image_tree.selection()], reverse=True)
        for index in selected:
            del self.image_paths[index]

        self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
        self._update_count_label(self.image_count_label, len(self.image_paths))

    def _clear_images(self):
        self.image_paths.clear()
        self._refresh_table(self.image_tree, [])
        self._update_count_label(self.image_count_label, 0)

    def _convert_images_to_pdf(self):
        image_paths = list(self.image_paths)

        if not image_paths:
            messagebox.showwarning(APP_TITLE, "Select at least one image first.")
            return

        output = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
            initialdir=self.prefs.get_last_output_folder("images_to_pdf"),
        )

        if not output:
            return

        # Remember output folder
        self.prefs.set_last_output_folder("images_to_pdf", str(Path(output).parent))

        self._run_task(
            "Converting images to PDF",
            lambda: images_to_pdf(image_paths, output, progress_callback=self._set_progress),
            "Images converted to PDF successfully.",
            file_paths=image_paths,
        )

    def _move_image_up(self):
        selected = sorted([int(item) for item in self.image_tree.selection()])
        if not selected or selected[0] == 0:
            return

        index = selected[0]
        self.image_paths[index - 1], self.image_paths[index] = (
            self.image_paths[index],
            self.image_paths[index - 1],
        )
        self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
        self.image_tree.selection_set(str(index - 1))
        self._update_count_label(self.image_count_label, len(self.image_paths))

    def _move_image_down(self):
        selected = sorted([int(item) for item in self.image_tree.selection()])
        if not selected:
            return

        index = selected[-1]
        if index == len(self.image_paths) - 1:
            return

        self.image_paths[index], self.image_paths[index + 1] = (
            self.image_paths[index + 1],
            self.image_paths[index],
        )
        self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
        self.image_tree.selection_set(str(index + 1))
        self._update_count_label(self.image_count_label, len(self.image_paths))

    def _start_image_drag(self, event):
        row_id = self.image_tree.identify_row(event.y)
        if not row_id:
            self._image_drag_start_index = None
            return

        self._image_drag_start_index = int(row_id)
        self.image_tree.selection_set(row_id)

    def _drag_image_motion(self, event):
        if self._image_drag_start_index is None:
            return

        row_id = self.image_tree.identify_row(event.y)
        if not row_id:
            return

        target_index = int(row_id)
        if target_index != self._image_drag_start_index and 0 <= target_index < len(self.image_paths):
            image_path = self.image_paths.pop(self._image_drag_start_index)
            self.image_paths.insert(target_index, image_path)
            self._image_drag_start_index = target_index
            self._refresh_table(self.image_tree, [self._format_file_row(p) for p in self.image_paths])
            self.image_tree.selection_set(str(target_index))

    def _end_image_drag(self, event):
        self._image_drag_start_index = None

    def _build_pdf_to_word_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="PDF to Word")

        ttk.Label(tab, text="Convert a PDF into a DOCX Word document.").pack(anchor="w")
        ttk.Label(
            tab,
            text="Works best with text-based PDFs. Scanned PDFs may require OCR.",
            style="Subheader.TLabel",
        ).pack(anchor="w", pady=(3, 6))
        ttk.Label(
            tab,
            text="This conversion runs as a single step and cannot be cancelled once started.",
            style="Subheader.TLabel",
        ).pack(anchor="w", pady=(0, 6))

        self.pdf_word_path = tk.StringVar()

        self._file_picker(tab, self.pdf_word_path, "Select PDF", [("PDF files", "*.pdf")])
        self._register_drop_target(tab, self._on_pdf_word_drop)

        action_buttons = [
            ("Convert to Word", self._convert_pdf_to_word, True),
        ]
        self._add_action_buttons(tab, action_buttons)

    def _convert_pdf_to_word(self):
        pdf_path = self.pdf_word_path.get()

        if not pdf_path:
            messagebox.showwarning(APP_TITLE, "Select a PDF file first.")
            return

        output = filedialog.asksaveasfilename(
            title="Save Word Document As",
            defaultextension=".docx",
            filetypes=[("Word document", "*.docx")],
            initialdir=self.prefs.get_last_output_folder("pdf_to_word"),
        )

        if not output:
            return

        # Remember output folder
        self.prefs.set_last_output_folder("pdf_to_word", str(Path(output).parent))

        self._run_task(
            "Converting PDF to Word",
            lambda: pdf_to_word(pdf_path, output, progress_callback=self._set_progress),
            "PDF converted to Word successfully.",
            file_paths=[pdf_path],
            cancellable=False,
        )

    def _build_pdf_to_images_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="PDF to Images")

        ttk.Label(tab, text="Export PDF pages as PNG or JPG images.").pack(anchor="w")

        self.pdf_images_path = tk.StringVar()
        self.image_format = tk.StringVar(value="png")
        self.dpi_value = tk.IntVar(value=DEFAULT_DPI)

        self._file_picker(tab, self.pdf_images_path, "Select PDF", [("PDF files", "*.pdf")])

        options = ttk.Frame(tab)
        options.pack(fill="x", pady=12)

        ttk.Label(options, text="Format:").pack(side="left")
        ttk.Combobox(
            options,
            textvariable=self.image_format,
            values=["png", "jpg"],
            width=8,
            state="readonly",
        ).pack(side="left", padx=(6, 20))

        ttk.Label(options, text="DPI:").pack(side="left")
        ttk.Spinbox(options, from_=72, to=600, textvariable=self.dpi_value, width=8).pack(side="left", padx=6)
        self._register_drop_target(tab, self._on_pdf_images_drop)

        action_buttons = [
            ("Export Images", self._convert_pdf_to_images, True),
        ]
        self._add_action_buttons(tab, action_buttons)

    def _convert_pdf_to_images(self):
        pdf_path = self.pdf_images_path.get()

        if not pdf_path:
            messagebox.showwarning(APP_TITLE, "Select a PDF file first.")
            return

        output_folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.prefs.get_last_output_folder("pdf_to_images"),
        )

        if not output_folder:
            return

        # Remember output folder
        self.prefs.set_last_output_folder("pdf_to_images", output_folder)

        self._run_task(
            "Exporting PDF pages as images",
            lambda: pdf_to_images(
                pdf_path,
                output_folder,
                self.image_format.get(),
                self.dpi_value.get(),
                progress_callback=self._set_progress,
            ),
            "PDF pages exported as images successfully.",
            file_paths=[pdf_path],
        )

    def _build_resize_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="Resize PDF/Image")

        ttk.Label(tab, text="Resize a PDF or image and preview the estimated output size.").pack(anchor="w")
        ttk.Label(
            tab,
            text="Select any PDF or supported image file, choose a scale percentage, and save the resized version.",
            style="Subheader.TLabel",
        ).pack(anchor="w", pady=(3, 6))

        self.resize_path = tk.StringVar()
        self.resize_scale = tk.IntVar(value=100)
        self.resize_estimate = tk.StringVar(value="Select a file to estimate output size.")

        self._file_picker(tab, self.resize_path, "Select PDF/Image", [("PDF and images", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp")])
        self._register_drop_target(tab, self._on_resize_drop)

        options = ttk.Frame(tab)
        options.pack(fill="x", pady=12)

        ttk.Label(options, text="Scale (%):").pack(side="left")
        ttk.Spinbox(options, from_=10, to=300, textvariable=self.resize_scale, width=8).pack(side="left", padx=(6, 20))
        ttk.Label(options, textvariable=self.resize_estimate, style="Status.TLabel").pack(side="left")

        self.resize_scale.trace_add("write", lambda *args: self._update_resize_estimate())
        self.resize_path.trace_add("write", lambda *args: self._update_resize_estimate())

        action_buttons = [
            ("Resize", self._resize_file, True),
        ]
        self._add_action_buttons(tab, action_buttons)

    def _on_resize_drop(self, event):
        dropped = self._parse_drop_files(event.data)
        if dropped:
            self.resize_path.set(dropped[0])

    def _update_resize_estimate(self):
        path = self.resize_path.get().strip()
        if not path:
            self.resize_estimate.set("Select a file to estimate output size.")
            return

        actual_path = Path(path)
        if not actual_path.exists() or not actual_path.is_file():
            self.resize_estimate.set("Selected file is not available.")
            return

        try:
            scale = max(1, min(300, int(self.resize_scale.get())))
        except (ValueError, TypeError):
            scale = 100

        estimate_bytes = int(actual_path.stat().st_size * ((scale / 100.0) ** 2))
        self.resize_estimate.set(f"Estimated output size: {format_file_size(estimate_bytes)}")

    def _resize_file(self):
        input_path = self.resize_path.get().strip()
        if not input_path:
            messagebox.showwarning(APP_TITLE, "Select a PDF or image file first.")
            return

        input_file = Path(input_path)
        if not input_file.exists() or not input_file.is_file():
            messagebox.showwarning(APP_TITLE, "The selected file cannot be found.")
            return

        scale_value = self.resize_scale.get()
        output = filedialog.asksaveasfilename(
            title="Save Resized File As",
            defaultextension=input_file.suffix if input_file.suffix.lower() != ".pdf" else ".pdf",
            filetypes=[
                ("PDF file", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("All files", "*.*"),
            ],
            initialdir=self.prefs.get_last_output_folder("resize_file"),
        )

        if not output:
            return

        self.prefs.set_last_output_folder("resize_file", str(Path(output).parent))

        if input_file.suffix.lower() == ".pdf":
            task = lambda: resize_pdf(input_file, output, scale_percent=scale_value, progress_callback=self._set_progress)
        else:
            task = lambda: resize_image(input_file, output, scale_percent=scale_value, progress_callback=self._set_progress)

        self._run_task(
            "Resizing file",
            task,
            "File resized successfully.",
            file_paths=[input_path],
        )

    def _build_merge_pdf_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="Merge PDFs")

        ttk.Label(tab, text="Merge multiple PDFs into one PDF in the selected order.").pack(anchor="w")

        self.merge_tree, self.merge_count_label = self._add_file_list(tab)
        self._register_drop_target(tab, self._on_merge_drop)
        self._register_drop_target(self.merge_tree, self._on_merge_drop)
        self.merge_tree.bind("<ButtonPress-1>", self._start_merge_drag)
        self.merge_tree.bind("<B1-Motion>", self._drag_merge_motion)
        self.merge_tree.bind("<ButtonRelease-1>", self._end_merge_drag)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=12)

        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side="left")

        ttk.Button(left_btns, text="Add PDFs", command=self._select_merge_pdfs, style="Rounded.TButton").pack(side="left")
        ttk.Button(left_btns, text="Remove", command=self._remove_selected_merge_pdfs, style="Rounded.TButton").pack(side="left", padx=8)
        ttk.Button(left_btns, text="Clear All", command=self._clear_merge_pdfs, style="Rounded.TButton").pack(side="left")

        mid_btns = ttk.Frame(btn_frame)
        mid_btns.pack(side="left", padx=20)

        ttk.Button(mid_btns, text="↑ Move Up", command=self._move_merge_pdf_up, style="Rounded.TButton").pack(side="left")
        ttk.Button(mid_btns, text="Move Down ↓", command=self._move_merge_pdf_down, style="Rounded.TButton").pack(side="left", padx=8)

        ttk.Button(btn_frame, text="Merge", style="Action.TButton", command=self._merge_pdfs).pack(side="right")

    def _move_merge_pdf_up(self):
        selected = sorted([int(item) for item in self.merge_tree.selection()])
        if not selected or selected[0] == 0:
            return

        index = selected[0]
        self.merge_paths[index - 1], self.merge_paths[index] = (
            self.merge_paths[index],
            self.merge_paths[index - 1],
        )
        self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
        self.merge_tree.selection_set(str(index - 1))
        self._update_count_label(self.merge_count_label, len(self.merge_paths))

    def _move_merge_pdf_down(self):
        selected = sorted([int(item) for item in self.merge_tree.selection()])
        if not selected:
            return

        index = selected[-1]
        if index == len(self.merge_paths) - 1:
            return

        self.merge_paths[index], self.merge_paths[index + 1] = (
            self.merge_paths[index + 1],
            self.merge_paths[index],
        )
        self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
        self.merge_tree.selection_set(str(index + 1))
        self._update_count_label(self.merge_count_label, len(self.merge_paths))

    def _start_merge_drag(self, event):
        row_id = self.merge_tree.identify_row(event.y)
        if not row_id:
            self._merge_drag_start_index = None
            return

        self._merge_drag_start_index = int(row_id)
        self.merge_tree.selection_set(row_id)

    def _drag_merge_motion(self, event):
        if self._merge_drag_start_index is None:
            return

        row_id = self.merge_tree.identify_row(event.y)
        if not row_id:
            return

        target_index = int(row_id)
        if target_index != self._merge_drag_start_index and 0 <= target_index < len(self.merge_paths):
            pdf_path = self.merge_paths.pop(self._merge_drag_start_index)
            self.merge_paths.insert(target_index, pdf_path)
            self._merge_drag_start_index = target_index
            self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
            self.merge_tree.selection_set(str(target_index))

    def _end_merge_drag(self, event):
        self._merge_drag_start_index = None

    def _clear_merge_pdfs(self):
        """Clear all PDFs from merge list."""
        self.merge_paths.clear()
        self._refresh_table(self.merge_tree, [])
        self._update_count_label(self.merge_count_label, 0)

    def _select_merge_pdfs(self):
        paths = filedialog.askopenfilenames(
            title="Select PDFs",
            filetypes=[("PDF files", "*.pdf")],
        )

        for path in paths:
            if Path(path).suffix.lower() == ".pdf":
                self.merge_paths.append(path)
        self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
        self._update_count_label(self.merge_count_label, len(self.merge_paths))

    def _remove_selected_merge_pdfs(self):
        selected = sorted([int(item) for item in self.merge_tree.selection()], reverse=True)
        for index in selected:
            del self.merge_paths[index]
        self._refresh_table(self.merge_tree, [self._format_file_row(p) for p in self.merge_paths])
        self._update_count_label(self.merge_count_label, len(self.merge_paths))

    def _merge_pdfs(self):
        pdf_paths = list(self.merge_paths)

        if not pdf_paths:
            messagebox.showwarning(APP_TITLE, "Select at least one PDF first.")
            return

        output = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
            initialdir=self.prefs.get_last_output_folder("merge_pdf"),
        )

        if not output:
            return

        # Remember output folder
        self.prefs.set_last_output_folder("merge_pdf", str(Path(output).parent))

        self._run_task(
            "Merging PDFs",
            lambda: merge_pdfs(pdf_paths, output, progress_callback=self._set_progress),
            "PDFs merged successfully.",
            file_paths=pdf_paths,
        )

    def _build_split_pdf_tab(self):
        tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(tab, text="Split PDF")

        ttk.Label(tab, text="Split every page or extract a page range from a PDF.").pack(anchor="w")

        self.split_pdf_path = tk.StringVar()
        self.split_start_page = tk.StringVar()
        self.split_end_page = tk.StringVar()
        self.split_mode = tk.StringVar(value="all")

        self._file_picker(tab, self.split_pdf_path, "Select PDF", [("PDF files", "*.pdf")])

        mode_frame = ttk.Frame(tab)
        mode_frame.pack(fill="x", pady=12)

        ttk.Radiobutton(
            mode_frame,
            text="Split every page into separate PDFs",
            variable=self.split_mode,
            value="all",
        ).pack(anchor="w")

        ttk.Radiobutton(
            mode_frame,
            text="Extract page range",
            variable=self.split_mode,
            value="range",
        ).pack(anchor="w", pady=(6, 0))

        range_frame = ttk.Frame(tab)
        range_frame.pack(fill="x", pady=8)

        ttk.Label(range_frame, text="Start page:").pack(side="left")
        ttk.Entry(range_frame, textvariable=self.split_start_page, width=8).pack(side="left", padx=(6, 18))

        ttk.Label(range_frame, text="End page:").pack(side="left")
        ttk.Entry(range_frame, textvariable=self.split_end_page, width=8).pack(side="left", padx=6)

        action_buttons = [
            ("Split PDF", self._split_pdf, True),
        ]
        self._add_action_buttons(tab, action_buttons)

    def _split_pdf(self):
        pdf_path = self.split_pdf_path.get()

        if not pdf_path:
            messagebox.showwarning(APP_TITLE, "Select a PDF file first.")
            return

        output_folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.prefs.get_last_output_folder("split_pdf"),
        )

        if not output_folder:
            return

        # Remember output folder
        self.prefs.set_last_output_folder("split_pdf", output_folder)

        if self.split_mode.get() == "all":
            task = lambda: split_pdf(pdf_path, output_folder, progress_callback=self._set_progress)
        else:
            try:
                start = int(self.split_start_page.get())
                end = int(self.split_end_page.get())
            except ValueError:
                messagebox.showwarning(APP_TITLE, "Start page and end page must be valid numbers.")
                return

            task = lambda: split_pdf(pdf_path, output_folder, start, end, progress_callback=self._set_progress)

        self._run_task("Splitting PDF", task, "PDF split successfully.", file_paths=[pdf_path])


def run_app():
    app = PDFImageToolkitApp()
    app.mainloop()