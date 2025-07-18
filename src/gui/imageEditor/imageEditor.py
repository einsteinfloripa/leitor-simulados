__all__ = ["ImageEditorApp"]

import tkinter as tk
import cv2

from core.definitions.question import TestReport, Question
from core.detection import Detection
from core.IO.export.export_image import ImageReportExportData, ImageReportExporter

from api.data_structs import ImageCacheStruct

from .. import Config
from ..event_system import EventBus
from .canvas import ImgCanvas
from .sidePanel import SidePanel

@EventBus.bind
class _FooterButtons(tk.Frame):
    """
    Auxiliary widget for footer buttons, displaying image navigation controls.

    Parameters
    ----------
    root : tk.Tk or tk.Widget
        The parent widget that contains a footer attribute.
    """

    def __init__(self, root):
        super().__init__(root.footer, bg="lightblue")
        self.root = root

        # Previous Button
        self.previous_button = tk.Button(
            self,
            text="<<",
            command=lambda: EventBus.publish("<<previous_image_button_clicked>>"),
            state=tk.DISABLED
        )
        self.previous_button.grid(row=0, column=0, padx=5, pady=5)

        # Image Label
        self.image_label = tk.Label(self, text="0/0", bg="lightblue")
        self.image_label.grid(row=0, column=1, padx=5, pady=5)

        # Next Button
        self.next_button = tk.Button(
            self,
            text=">>",
            command=lambda: EventBus.publish("<<next_image_button_clicked>>"),
            state=tk.DISABLED
        )
        self.next_button.grid(row=0, column=2, padx=5, pady=5)

    @EventBus.subscribe("<<update_all>>", "<<successfully_folder_loaded>>")
    def update_footer_label(self, event=None):
        """
        Update the footer label with the current image index and total number of images.

        Parameters
        ----------
        event : optional
            The event that triggered the update (default is None).
        """
        current = Config.current_image_index + 1
        total = Config.api.number_of_images
        self.image_label.config(text=f"{current}/{total}")

        if total > 1 and self.previous_button["state"] == tk.DISABLED:
            self.toggle_buttons()
        elif total <= 1 and self.previous_button["state"] == tk.NORMAL:
            self.toggle_buttons()

    def toggle_buttons(self):
        """
        Toggle the state of the previous and next buttons between NORMAL and DISABLED.
        """
        state = tk.NORMAL if self.previous_button["state"] == tk.DISABLED else tk.DISABLED
        self.previous_button.config(state=state)
        self.next_button.config(state=state)

@EventBus.bind
class ImageEditorApp(tk.Frame):
    """
    Main widget for the image editor application.

    Parameters
    ----------
    root : tk.Tk or tk.Widget
        The parent widget.
    """

    def __init__(self, root):
        super().__init__(root, width=800, height=600, bg="white")
        self.root = root

        # Operation variables
        self.current_drawn_detections: dict[Detection.Type, list[Detection]] = None
        self.test_questions_report: TestReport = None

        # Configure grid responsiveness
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Canvas configuration
        self.Canvas = ImgCanvas(self, width=800, height=600, bg="white")
        self.Canvas.grid(row=0, column=0, sticky="nswe")

        # Side panel configuration
        self.sidePanel = SidePanel(self, root, bg="lightgray", width=200, height=500)
        self.sidePanel.place(
            relx=1, rely=0, x=-5, y=+5, anchor=tk.NE, width=200, relheight=0.9
        )

        # Footer buttons
        self.footerButtons = _FooterButtons(root)
        self.footerButtons.pack()

    @EventBus.subscribe("<<detection_checkbox_clicked>>","<<update_all>>")
    def update_detections(self, event=None):
        """
        Update the current drawn detections based on side panel selections.

        Parameters
        ----------
        event : optional
            The event that triggered the update (default is None).
        """
        # Get the selected detection types to show
        detections_selected: dict[Detection.Type, bool] = self.sidePanel.get_show_detection_values()
        # Retrieve cache for the current image
        cache: ImageCacheStruct = Config.api.cache.from_index(Config.current_image_index)

        if cache is not None:
            selected = [k for k, v in detections_selected.items() if v]
            filtered_detections: dict[Detection.Type, list[Detection]] = \
                cache.container.get_by_type(selected)
            self.current_drawn_detections = filtered_detections
        else:
            self.current_drawn_detections = {}

    @EventBus.subscribe(
        "<<build_answers>>", "<<build_all_answers>>", "<<update_all>>"
    )
    def update_questions_answers(self, event):
        """
        Update the questions and answers report based on current image(s).

        Parameters
        ----------
        event : str
            The event that triggered the update.
        """

        do_build = (event != "<<update_all>>")
        to_all = (event == "<<build_all_answers>>")

        indices = range(Config.api.number_of_images) \
                  if to_all else [Config.current_image_index]

        for index in indices:
            cache = Config.api.cache.from_index(index)
            has_detection_cached = (
                cache is not None and cache.has_detections()
            )

            if has_detection_cached and do_build:
                # try:
                Config.api.build_report(index)
                # except Exception as e:  
                #     continue

        EventBus.publish("<<update_question_panel>>")

    @EventBus.subscribe("<<next_image_button_clicked>>")
    def load_next_image(self, event=None):
        """
        Load the next image in the list, update relevant data, and trigger a redraw.

        Parameters
        ----------
        event : optional
            The event that triggered the image load (default is None).
        """
        index = Config.current_image_index
        new_index = (index + 1) % Config.api.number_of_images
        Config.api.select_image(new_index)
        Config.current_image_index = new_index
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")

    @EventBus.subscribe("<<previous_image_button_clicked>>")
    def load_previous_image(self, event=None):
        """
        Load the previous image in the list, update relevant data, and trigger a redraw.

        Parameters
        ----------
        event : optional
            The event that triggered the image load (default is None).
        """
        index = Config.current_image_index
        new_index = (index - 1) % Config.api.number_of_images
        Config.api.select_image(new_index)
        Config.current_image_index = new_index
        EventBus.publish("<<update_all>>")
        EventBus.publish("<<center_draw_call>>")

    @EventBus.subscribe("<<clear_img_app>>")
    def clear(self, event):
        """
        Clear the canvas and side panel data.

        Parameters
        ----------
        event : any
            The event that triggered the clear action.
        """
        self.current_drawn_detections = {}
        self.test_questions_report = None

    @EventBus.subscribe("<<export_report_images>>")
    def export_images(self, event, export_path):
        """
        Export the images with detections to a selected folder.

        Parameters
        ----------
        event : any
            The event that triggered the export action.
        """
        data = ImageReportExportData(
            images=Config.api.image_files,
            reports=Config.api.get_all_reports()
        )
        exporter = ImageReportExporter()
        exporter.export(export_path, data)