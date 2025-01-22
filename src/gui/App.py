
if __name__ == "__main__":
    import sys
    import pathlib
    sys.path.append(str(pathlib.Path(__file__).parent.parent))

from pathlib import Path

import tkinter as tk
from tkinter import filedialog

from core.image import Image as CoreImage

from image_editor import ImageEditorApp

class WindowApplication(tk.Tk):

    # Non gui variables
    image_files = [] # List of images paths
    model_files = [] # List of models paths

    # Activate event handlers
    # Activate occurs when a new valid folder is opened
    activate_callbacks = []
    # Register a function to be called when the activate event occurs
    def on_activate(self, func : callable) -> None:
        self.activate_callbacks.append(func)
    # Call all the functions registered to the activate event
    def activate(self) -> None:
        for func in self.activate_callbacks:
            func()


    def __init__(self):
        super().__init__()
        self.title("Image Display Application")
        self.resizable(True, True)

        # Image variables
        self.image : CoreImage = None


        # Grid configuration
        self.grid_rowconfigure(0, weight=0)  # Header row (fixed size)
        self.grid_rowconfigure(1, weight=1, minsize=400)  # Middle row (expandable)
        self.grid_rowconfigure(2, weight=0, minsize=30)  # Footer row (fixed size)

        self.grid_columnconfigure(0, weight=0, minsize=200)  # Left panel (fixed size)
        self.grid_columnconfigure(1, weight=1, minsize=600)  # Middle column (expandable)


        self.header = tk.Frame(self, bg="lightblue", height=50)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)  # Left column (takes extra space if needed)
        self.header.grid_columnconfigure(1, weight=0)  # Center column (takes extra space if needed)
        self.header.grid_columnconfigure(2, weight=1)  # Right column (optional)

        self.footer = tk.Frame(self, bg="lightblue", height=30)
        self.footer.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.left_panel = tk.Frame(self, bg="lightgray")
        self.left_panel.grid(row=1, column=0, sticky="nswe")

        label_left = tk.Label(self.left_panel, text="Left Panel", bg="lightgray")
        label_left.pack(pady=10)

        self.imgEditor = ImageEditorApp(self)
        self.imgEditor.grid(row=1, column=1, sticky="nswe")


        # Button and button functions
        open_folder_button = tk.Button(
            self.header, text="Open Folder", command=self.open_folder
        )
        open_folder_button.pack(side=tk.LEFT, padx=5, pady=5)


    def open_folder(self):
        folder_path = filedialog.askdirectory()  # Open folder dialog
        if folder_path:
            folder = Path(folder_path)
            self.image_files = [
                str(f) for f in folder.glob('*.*') if \
                    f.suffix.lower() in {'.png', '.jpg', '.jpeg'}
                ]
        if self.image_files:
            self.load_image(0)
            self.imgEditor.current_image_index = 0
            self.imgEditor.number_of_images = len(self.image_files)
            self.imgEditor.show_image(0)
            self.activate()
        
    def load_image(self, index):
        self.image = CoreImage.from_path(self.image_files[index])



if __name__ == "__main__":
    app = WindowApplication()
    app.mainloop()