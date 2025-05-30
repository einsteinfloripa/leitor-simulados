import tkinter as tk

from core.definitions.enums import Stage

from api import ProgressTracker

from gui.top_menu import TopMenu
from gui.imageEditor import ImageEditorApp
from gui.modelsSidebar import PipelineSideBar
from gui.popups import ProgressPopup
from gui import Config
from gui.event_system import EventBus


# =============================================================================
# Main Application Class
# =============================================================================

@EventBus.bind
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

    # =============================================================================
    # Public Methods
    # =============================================================================
    
    @EventBus.subscribe("<<open_folder>>")
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
            Config.api.select_image(0, force_reload=True)
            EventBus.publish("<<successfully_folder_loaded>>")

    @EventBus.subscribe("<<apply_model>>", "<<apply_model_to_all>>")
    def apply_model(self, event: str):
        """
        Applies the selected detection model to the current image or all images.

        Parameters
        ----------
        event : str
            The event triggering the model application.
        """
        apply_to_all = event == "<<apply_model_to_all>>"

        # TODO: Refactor this to use the pipeline configuration
        # Retrieve pipeline configuration
        pipeline_config = self.modelsSideBar.get_pipeline()
        test = Config.selected_test_type

        # Initialize detection parameters
        fs_config = pipeline_config['fs']
        ss_config = pipeline_config['ss']
                
        fs_model = fs_config['model']
        Config.api.select_model(fs_model, Stage.FIRST)
        ss_model = ss_config['model']
        Config.api.select_model(ss_model, Stage.SECOND)

        fs_score_threshold = fs_config['st']
        ss_score_threshold = ss_config['st']

        # Apply models
        if apply_to_all:
            tracker = ProgressTracker()
            ProgressPopup(
                self,
                Config.api.run_detection_pipeline_for_all,
                [fs_score_threshold, ss_score_threshold, tracker],
                tracker,
                Config.api.image_files
            )
        else:
            Config.api.run_detection_pipeline(
                fs_score_threshold,
                ss_score_threshold,
            )

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
