import tkinter as tk
from tkinter import ttk, filedialog
import threading
from core.IO import FileExtension
from gui import Config

class SaveAsPopup(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title("Choose Save Format")
        self.geometry("300x150")
        self.transient(root)  # Makes it modal
        self.grab_set()  # Disable interactions with main window
        # Label
        tk.Label(self, text="Select File Format:").pack(pady=5)
        # Combobox
        # Get the available formats from the API
        # list[(export style name, export extension)]
        self.formats_dict : dict[str, FileExtension] = \
              Config.api.get_io().get_report_output_formats()
        formats = list(self.formats_dict.keys())
        # Create the combobox
        self.format_type_var = tk.StringVar(value=formats[0])
        format_menu = ttk.Combobox(
            self,
            textvariable=self.format_type_var,
            values=formats,
            state="readonly"
        )
        format_menu.pack(pady=5)
        # Confirm button
        tk.Button(
            self,
            text="Procurar",
            command=self.save_as
        ).pack(pady=10)

    def save_as(self):
        """ Opens file dialog and saves data in the selected format. """
        name : str = self.format_type_var.get()
        format : FileExtension = self.formats_dict[name]
        filetypes = [
            (name, '*' + format.value)
        ]
        file_path = filedialog.asksaveasfilename(
            defaultextension="", filetypes=filetypes
        )

        if not file_path:
            return
        self.root.save_as(file_path, self.format_type_var.get())
        


class ProgressPopup(tk.Toplevel):
    def __init__(self, root, thread_fuction, thread_args):
        super().__init__(root)
        self.root = root
        self.title("Aplicando pipeline")
        self.geometry("300x100")
        self.resizable(False, False)

        # Disable main window interactions
        self.transient(self.root)  # Keeps popup on top
        self.grab_set()  # Freezes main window

        # Label inside popup
        self.label = tk.Label(self, text="Aplicando pipeline...")
        self.label.pack(pady=10)

        # Label to show progress percentage
        self.progress_label = tk.Label(self, text="0%")
        self.progress_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack()

        # Handle popup closing
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start the long operation in a separate thread
        thread_args.insert(0, self)
        self.thread = threading.Thread(
            target=thread_fuction, args=thread_args, daemon=True
        )
        self.thread.start()



    def update_progress(self, img_name, value):
        if not self.running and not self.winfo_exists():
            return
        """Updates the progress bar safely from the main thread."""
        self.progress["value"] = value
        self.progress_label["text"] = f"{value:2f}%"
        self.label["text"] = img_name
        if value == 100:
            self.progress_label["text"] = "Done!"

    def on_close(self):
        self.running = False
        self.destroy()