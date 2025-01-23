from pathlib import Path

import tkinter as tk
from tkinter import filedialog

from core.image import Image as CoreImage
from core.detection import Detection
from core.models import load_model, LegacyModel, YOLOModel, EFScanAlgoModel

from gui.navbar import Navbar
from gui.image_editor import ImageEditorApp
from gui.models_sidebar import PipelineSideBar

class WindowApplication(tk.Tk):

    # Non gui variables
    image_files = [] # List of images paths
    # Detections
    detections = [] # List of detections
    


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
        self.title("Leitor de simulados")
        self.resizable(True, True)

        # Image variables
        # Main image class data
        self.image : CoreImage = None
        # Models
        self.fs_model : LegacyModel | EFScanAlgoModel | YOLOModel | None = None
        self.ss_model : LegacyModel | EFScanAlgoModel | YOLOModel | None = None
        # Detection cache
        self.img_cache = []

        # Grid configuration
        self.grid_rowconfigure(0, weight=0)  # Header row (fixed size)
        self.grid_rowconfigure(1, weight=1, minsize=400)  # Middle row (expandable)
        self.grid_rowconfigure(2, weight=0, minsize=30)  # Footer row (fixed size)

        self.grid_columnconfigure(0, weight=0, minsize=250)  # Left panel (fixed size)
        self.grid_columnconfigure(1, weight=1, minsize=600)  # Middle column (expandable)


        self.header = Navbar(self)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.footer = tk.Frame(self, bg="lightblue", height=30)
        self.footer.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.modelsSideBar = PipelineSideBar(self)
        self.modelsSideBar.grid(row=1, column=0, sticky="nswe")

        self.imgEditor = ImageEditorApp(self)
        self.imgEditor.grid(row=1, column=1, sticky="nswe")


    def load_image(self, index):
        self.image = CoreImage.from_path(self.image_files[index])


    # Callback functions
    def open_folder(self):
        folder_path = filedialog.askdirectory()  # Open folder dialog
        if folder_path:
            folder = Path(folder_path)
            self.image_files = [
                str(f) for f in folder.glob('*.*') if \
                    f.suffix.lower() in {'.png', '.jpg', '.jpeg'}
                ]
        if self.image_files:
            self.img_cache = [None] * len(self.image_files)
            self.load_image(0)
            self.imgEditor.current_image_index = 0
            self.imgEditor.number_of_images = len(self.image_files)
            self.imgEditor.show_image(0)
            self.activate()

    def apply_model(self, fs_config, ss_config):
        self.fs_model = load_model(fs_config)
        self.ss_model = load_model(ss_config)        
        
        Detection.set_label_map(['cpf_block', 'question_block'])
        self.image.make_detections_with_model(self.fs_model, fs_config['st'])
        self.image.make_cropped()
        Detection.set_label_map([
            "cpf_column",
            "question_line",
            "selected_ball",
            "unselected_ball",
            "question_number",
        ])

        for crop in self.image.crops:
            crop.make_detections_with_model(self.ss_model, ss_config['st'])
        
        # Cache the detections if needed
        index = self.imgEditor.current_image_index
        if self.img_cache[index] is None:
            self.img_cache[index] = self.image.to_cache()
            self.imgEditor.cache_detection_coords(index)

        self.imgEditor.show_image(self.imgEditor.current_image_index)
