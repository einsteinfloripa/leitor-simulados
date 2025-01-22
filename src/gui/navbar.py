import tkinter as tk


class Navbar(tk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, bg="lightblue", height=50)
        self.grid_columnconfigure(0, weight=1)  # Left column (takes extra space if needed)
        self.grid_columnconfigure(1, weight=0)  # Center column (takes extra space if needed)
        self.grid_columnconfigure(2, weight=1)  # Right column (optional)
        
        # Attach a menu to the root window
        open_folder_button = tk.Button(self, text="Open Folder", command=root.open_folder)
        open_folder_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")