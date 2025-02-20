import tkinter as tk

from core.definitions.question import TestType
from core.detection import (
    Detection,
    DEFAULT_FIRST_STAGE_LABEL_MAP,
    DEFAULT_SECOND_STAGE_LABEL_MAP
)
from core.model import EFScanAlgoModel
from gui.top_menu import TopMenu
from gui.imageEditor import ImageEditorApp
from gui.modelsSidebar import PipelineSideBar
from gui.popups import ProgressPopup
from gui import Config, EventBus


# SECTION: Main Application class

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


        menu = TopMenu(self)
        self.config(menu=menu)

        self.footer = tk.Frame(self, bg="lightblue", height=30)
        self.footer.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.modelsSideBar = PipelineSideBar(self)
        self.modelsSideBar.grid(row=1, column=0, sticky="nswe")

        self.imgEditor = ImageEditorApp(self)
        self.imgEditor.grid(row=1, column=1, sticky="nswe")

        EventBus.subscribe(self.open_folder, "<<open_folder>>")
        EventBus.subscribe(
            self.apply_model,
            "<<apply_model>>",
            "<<apply_model_to_all>>",
        )


    # SECTION: Public methods
    def open_folder(self, event : str, path : str):
        open = Config.api.io.open_folder(path)
        if open:
            EventBus.publish("<<clear_img_app>>")
            Config.current_image_index = 0
            Config.api.select_image(0)
            EventBus.publish("<<folder_loaded>>")
            EventBus.publish("<<center_draw_call>>")


    def apply_model(self, event):
        # Check if the model should be applied to all images
        to_all = event == "<<apply_model_to_all>>"

        # Get the current pipeline configuration
        info = self.modelsSideBar.get_pipeline()
        test : TestType = info['test']
        fs_config = info['fs']
        ss_config = info['ss']
        fs_model = Config.api.get_fs_model()
        ss_model = Config.api.get_ss_model()

        # Lazy init EFscanAlgo if needed
        if isinstance(fs_model, EFScanAlgoModel):
            fs_model.init(test)
        if isinstance(ss_model, EFScanAlgoModel):
            ss_model.init(test)

        # Select the relevant images
        if to_all:
            ProgressPopup(
                self,
                self._thread_apply_to_all,
                [fs_model, ss_model, fs_config, ss_config]
            )
        else:
            index = Config.current_image_index
            Config.api.select_image(index, do_cache=False)
            image = Config.api.get_image()

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
            Config.api.cache.cache_image(index, image)
        
        # Load the image selected again
        index = Config.current_image_index
        Config.api.select_image(index)

        # Update the UI
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")




    # SECTION: Private auxiliary methods

    def _thread_apply_to_all(self,
                popup : ProgressPopup,
                fs_model,
                ss_model,
                fs_config,
                ss_config
            ):        
        indexes = range(Config.api.get_number_of_images())
        # Apply the model to the images
        for i in indexes:
            if not popup.running:
                break
            Config.api.select_image(i, do_cache=False)
            image = Config.api.get_image()
            # Update UI popup
            popup.update_progress(image.name, (i+1) / len(indexes) * 100)
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
            Config.api.cache.cache_image(i, image)
        
        # Load the image selected again
        index = Config.current_image_index
        Config.api.select_image(index)
        # Update the UI
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")
        
    