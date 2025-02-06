import tkinter as tk

from core.detection import (
    Detection,
    DEFAULT_FIRST_STAGE_LABEL_MAP,
    DEFAULT_SECOND_STAGE_LABEL_MAP
)
from core.model import EFScanAlgoModel
from definitions.question import TestType

from gui.navbar import Navbar
from gui.imageEditor import ImageEditorApp
from gui.modelsSidebar import PipelineSideBar

from gui import api_instance, folder_loaded_callback

class WindowApplication(tk.Tk):


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
    
    def open_folder(self, path : str):
        open = api_instance.open_folder(path)
        if open:
            self.imgEditor.current_image_index = 0
            api_instance.load_image(0)
            self.imgEditor.update_detections()
            self.imgEditor.display_image(self.imgEditor.current_image_index)
            folder_loaded_callback.call()


    def apply_model(self, to_all=False):
        # Get the current pipeline configuration
        info = self.modelsSideBar.get_pipeline()
        test : TestType = info['test']
        fs_config = info['fs']
        ss_config = info['ss']
        fs_model = api_instance.get_fs_model()
        ss_model = api_instance.get_ss_model()
        # Lazy init EFscanAlgo if needed
        if isinstance(fs_model, EFScanAlgoModel):
            fs_model.init(test)
        if isinstance(ss_model, EFScanAlgoModel):
            ss_model.init(test)
        # Select the relevant images
        if to_all:
            indexes = range(api_instance.get_number_of_images())
        else:
            indexes = [self.imgEditor.current_image_index]
        # Apply the model to the images
        for i in indexes:
            api_instance.load_image(i, do_cache=False)
            image = api_instance.get_image()
            # First stage
            Detection.set_label_map(DEFAULT_FIRST_STAGE_LABEL_MAP)        
            image.make_detections_with_model(
                fs_model, fs_config['st']
            )
            # Crop image in the detected areas
            image.make_cropped()
            # Second stage
            Detection.set_label_map(DEFAULT_SECOND_STAGE_LABEL_MAP)
            for crop in image.crops:
                crop.make_detections_with_model(
                    ss_model, ss_config['st']
                )

            # Make the detections cache
            api_instance.get_cache().cache_image(i, image)
        
        self.imgEditor.update_detections()
        self.imgEditor.display_image(self.imgEditor.current_image_index)
