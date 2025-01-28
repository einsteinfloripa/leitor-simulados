from pathlib import Path

import tkinter as tk
from tkinter import filedialog

from core.image import Image as CoreImage
from core.detection import Detection
from core.models import load_model

from gui.context import AppContextData

from gui.navbar import Navbar
from gui.imageEditor import ImageEditorApp
from gui.modelsSidebar import PipelineSideBar

class WindowApplication(tk.Tk, AppContextData):


    def __init__(self):
        super().__init__()
        self.title("Leitor de simulados")
        self.resizable(True, True)

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


    def apply_model(self):
        fs_config, ss_config = self.modelsSideBar.get_pipeline()

        for i, path in enumerate(self.image_files):
            image = CoreImage.from_path(path)
            self.fs_model = load_model(fs_config)
            self.ss_model = load_model(ss_config)        
            
            Detection.set_label_map(['cpf_block', 'question_block'])
            image.make_detections_with_model(self.fs_model, fs_config['st'])

            image.make_cropped()
            Detection.set_label_map([
                "cpf_column",
                "question_line",
                "selected_ball",
                "unselected_ball",
                "question_number",
            ])

            for crop in image.crops:
                crop.make_detections_with_model(self.ss_model, ss_config['st'])


            # Cache the detections if needed
            if self.img_cache[i] is None:
                self.img_cache[i] = image.to_cache()
        
        self.imgEditor.cache_detection_coords(self.imgEditor.current_image_index)
        self.imgEditor.update_detections()
        self.imgEditor.display_image(self.imgEditor.current_image_index)
