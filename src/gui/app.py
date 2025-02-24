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


# =============================================================================
# Main Application Class
# =============================================================================

class WindowApplication(tk.Tk):
    """
    The main application window for the image detection system.

    This class initializes and manages the GUI layout, event subscriptions, 
    and interactions with the underlying detection models.

    Attributes
    ----------
    modelsSideBar : PipelineSideBar
        Sidebar containing model configuration options.
    imgEditor : ImageEditorApp
        The main image editor component.
    footer : tk.Frame
        The footer frame of the application.
    """

    def __init__(self):
        """Initialize the main application window and its components."""
        super().__init__()
        self.title("Leitor de simulados")
        self.resizable(True, True)

        # Grid configuration
        self._configure_grid()

        # Initialize UI components
        self._initialize_ui()

        # Subscribe to event bus
        EventBus.subscribe(self.open_folder, "<<open_folder>>")
        EventBus.subscribe(
            self.apply_model,
            "<<apply_model>>",
            "<<apply_model_to_all>>",
        )

    # =============================================================================
    # Public Methods
    # =============================================================================
    
    def open_folder(self, event: str, path: str):
        """
        Opens a folder containing images and updates the application state.

        Parameters
        ----------
        event : str
            The event name (unused).
        path : str
            The path to the folder containing images.
        """
        if Config.api.open_folder(path, Config.selected_test_type):
            EventBus.publish("<<clear_img_app>>")
            Config.current_image_index = 0
            Config.api.select_image(0)
            EventBus.publish("<<folder_loaded>>")
            EventBus.publish("<<center_draw_call>>")


    def apply_model(self, event: str):
        """
        Applies the selected detection model to the current image or all images.

        Parameters
        ----------
        event : str
            The event triggering the model application.
        """
        apply_to_all = event == "<<apply_model_to_all>>"

        # Retrieve pipeline configuration
        pipeline_config = self.modelsSideBar.get_pipeline()
        test: TestType = pipeline_config['test']
        fs_config = pipeline_config['fs']
        ss_config = pipeline_config['ss']
        fs_model = Config.api.fs_model
        ss_model = Config.api.ss_model

        # Initialize EFScanAlgo models if needed
        self._initialize_models_if_needed(fs_model, ss_model, test)

        # Apply models
        if apply_to_all:
            ProgressPopup(
                self,
                self._thread_apply_to_all,
                [fs_model, ss_model, fs_config, ss_config]
            )
        else:
            self._apply_model_to_single_image(fs_model, ss_model, fs_config, ss_config)

        # Refresh UI
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")

    # =============================================================================
    # Private Methods
    # =============================================================================
    
    def _configure_grid(self):
        """Configures the application's grid layout."""
        self.grid_rowconfigure(0, weight=0)  # Header row (fixed size)
        self.grid_rowconfigure(1, weight=1, minsize=400)  # Middle row (expandable)
        self.grid_rowconfigure(2, weight=0, minsize=30)  # Footer row (fixed size)

        self.grid_columnconfigure(0, weight=0, minsize=250)  # Left panel (fixed size)
        self.grid_columnconfigure(1, weight=1, minsize=600)  # Middle column (expandable)

    def _initialize_ui(self):
        """Initializes the UI components."""
        menu = TopMenu(self)
        self.config(menu=menu)

        self.footer = tk.Frame(self, bg="lightblue", height=30)
        self.footer.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.modelsSideBar = PipelineSideBar(self)
        self.modelsSideBar.grid(row=1, column=0, sticky="nswe")

        self.imgEditor = ImageEditorApp(self)
        self.imgEditor.grid(row=1, column=1, sticky="nswe")

    def _initialize_models_if_needed(self, fs_model, ss_model, test: TestType):
        """
        Initializes EFScanAlgo models if they haven't been initialized.

        Parameters
        ----------
        fs_model : EFScanAlgoModel
            First-stage detection model.
        ss_model : EFScanAlgoModel
            Second-stage detection model.
        test : TestType
            The test type being processed.
        """
        if isinstance(fs_model, EFScanAlgoModel):
            fs_model.init(test)
        if isinstance(ss_model, EFScanAlgoModel):
            ss_model.init(test)

    def _apply_model_to_single_image(self, fs_model, ss_model, fs_config, ss_config):
        """
        Applies the detection model to a single image.

        Parameters
        ----------
        fs_model : EFScanAlgoModel
            First-stage detection model.
        ss_model : EFScanAlgoModel
            Second-stage detection model.
        fs_config : dict
            Configuration for the first-stage model.
        ss_config : dict
            Configuration for the second-stage model.
        """
        index = Config.current_image_index
        Config.api.select_image(index, do_cache=False)
        image = Config.api.image

        # Apply first-stage model
        Detection.set_label_map(DEFAULT_FIRST_STAGE_LABEL_MAP)
        image.make_detections_with_model(fs_model, fs_config['st'])

        # Crop image based on detected areas
        image.make_cropped()

        # Apply second-stage model
        Detection.set_label_map(DEFAULT_SECOND_STAGE_LABEL_MAP)
        for crop in image.crops:
            crop.make_detections_with_model(ss_model, ss_config['st'])

        # Cache the detections
        Config.api.cache.cache_image(index, image)

        # Refresh the UI
        Config.api.select_image(index)

    def _thread_apply_to_all(self, popup: ProgressPopup, fs_model, ss_model, fs_config, ss_config):
        """
        Applies the detection model to all images in a separate thread.

        Parameters
        ----------
        popup : ProgressPopup
            The progress popup to update the UI during processing.
        fs_model : EFScanAlgoModel
            First-stage detection model.
        ss_model : EFScanAlgoModel
            Second-stage detection model.
        fs_config : dict
            Configuration for the first-stage model.
        ss_config : dict
            Configuration for the second-stage model.
        """
        num_images = Config.api.number_of_images

        for i in range(num_images):
            if not popup.running:
                break

            Config.api.select_image(i, do_cache=False)
            image = Config.api.image

            # Update UI progress
            popup.update_progress(image.name, (i + 1) / num_images * 100)

            # Apply first-stage model
            Detection.set_label_map(DEFAULT_FIRST_STAGE_LABEL_MAP)
            image.make_detections_with_model(fs_model, fs_config['st'])

            # Crop image based on detected areas
            image.make_cropped()

            # Apply second-stage model
            Detection.set_label_map(DEFAULT_SECOND_STAGE_LABEL_MAP)
            for crop in image.crops:
                crop.make_detections_with_model(ss_model, ss_config['st'])

            # Cache the detections
            Config.api.cache.cache_image(i, image)

        # Refresh UI
        Config.api.select_image(Config.current_image_index)
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")
