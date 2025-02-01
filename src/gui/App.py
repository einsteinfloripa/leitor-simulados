import tkinter as tk

from core.detection import (
    Detection,
    DEFAULT_FIRST_STAGE_LABEL_MAP,
    DEFAULT_SECOND_STAGE_LABEL_MAP
)
from core.models import EFScanAlgoModel

from gui.context import AppContextData
from gui.imageEditor.drawingContext import DrawingContext

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


    def open_folder(self, path):
        AppContextData.open_folder(path)
        DrawingContext.build_context(
            AppContextData.image_cache[0],
            AppContextData.image.raw,
        )
        self.imgEditor.display_image(0)
        AppContextData.folder_loaded_callback()

    def apply_model(self, to_all=False):
        # Get the current pipeline configuration
        config = self.modelsSideBar.get_pipeline()
        test = config['test']
        fs_config = config['fs']
        ss_config = config['ss']
        # Lazy init EFscanAlgo if needed
        if isinstance(AppContextData.fs_model, EFScanAlgoModel):
            AppContextData.fs_model.init(test)
        if isinstance(AppContextData.ss_model, EFScanAlgoModel):
            AppContextData.ss_model.init(test)
        # Select the relevant images
        if to_all:
            indexes = range(len(self.image_files))
        else:
            indexes = [self.imgEditor.current_image_index]
        # Apply the model to the images
        for i in indexes:
            AppContextData.load_image_to_context(i, do_cache=False)
            image = AppContextData.image
            # First stage
            Detection.set_label_map(DEFAULT_FIRST_STAGE_LABEL_MAP)        
            image.make_detections_with_model(
                AppContextData.fs_model, fs_config['st']
            )
            # Crop image in the detected areas
            image.make_cropped()
            # Second stage
            Detection.set_label_map(DEFAULT_SECOND_STAGE_LABEL_MAP)
            for crop in image.crops:
                crop.make_detections_with_model(
                    AppContextData.ss_model, ss_config['st']
                )

            # Make the detections cache
            AppContextData.image_cache[i] = image.to_cache()
        
        DrawingContext.build_context(
            AppContextData.image_cache[indexes[0]],
            AppContextData.image.raw,
        )
        self.imgEditor.update_detections()
        self.imgEditor.display_image(self.imgEditor.current_image_index)
