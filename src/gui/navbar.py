import tkinter as tk
from tkinter import filedialog

class Navbar(tk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, bg="lightblue", height=50)
        self.root = root
        self.grid_columnconfigure(0, weight=1)  # Left column (takes extra space if needed)
        self.grid_columnconfigure(1, weight=0)  # Center column (takes extra space if needed)
        self.grid_columnconfigure(2, weight=1)  # Right column (optional)
        
        # Attach a menu to the root window
        open_folder_button = tk.Button(self, text="Open Folder", command=self.open_folder)
        open_folder_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    def open_folder(self):
        file = filedialog.askdirectory(
            title="Select a folder",
            initialdir=".",
            mustexist=True
        )
        if file:
            self.root.open_folder(file)