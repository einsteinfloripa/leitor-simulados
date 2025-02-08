import tkinter as tk
from tkinter import ttk
import threading
import time


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