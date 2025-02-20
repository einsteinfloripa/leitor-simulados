import tkinter as tk

from core.definitions.question import TestQuestions
from core.definitions.blocks import TestBlocks
from core.detection import Detection

from api.data_structs import ImageCacheStruct
from api.builder import BuilderApi

from gui import (
    Config,
    EventBus
)

from .canvas import ImgCanvas
from .sidePanel import SidePanel



## AUXILIARY WIDGETS ##
class _footerButtons(tk.Frame):
    def __init__(self, root):
        super().__init__(root.footer, bg="lightblue")
        self.root = root

        # Previous Button
        self.previous_button = tk.Button(
            self,
            text="<<",
            command=lambda : EventBus.publish("<<previous_image>>"), 
            state=tk.DISABLED
        )
        self.previous_button.grid(row=0, column=0, padx=5, pady=5)
        # Text Label
        self.image_label = tk.Label(self, text="0/0", bg="lightblue")
        self.image_label.grid(row=0, column=1, padx=5, pady=5)
        # Next Button
        self.next_button = tk.Button(
            self,
            text=">>",
            command=lambda : EventBus.publish("<<next_image>>"),
            state=tk.DISABLED
            )
        self.next_button.grid(row=0, column=2, padx=5, pady=5)

        ## Subscribe to events ##
        EventBus.subscribe(
            self.update_footer_label,
            "<<update_all>>",
            "<<folder_loaded>>"
            )
        

    def update_footer_label(self, event=None):
        current = Config.current_image_index + 1
        total = Config.api.get_number_of_images()
        """Update the label with the current image index and total number."""
        self.image_label.config(text=f"{current}/{total}")
        if total > 1 and self.previous_button["state"] == tk.DISABLED:
            self.toggle_buttons()
        elif total <= 1 and self.previous_button["state"] == tk.NORMAL:
            self.toggle_buttons()
    
    def toggle_buttons(self):
        """Toggle the state of the previous and next buttons."""
        state = tk.NORMAL if self.previous_button["state"] == tk.DISABLED else tk.DISABLED
        self.previous_button.config(state=state)
        self.next_button.config(state=state)


## MAIN WIDGET ##
class ImageEditorApp(tk.Frame):

    def __init__(self, root):
        super().__init__(root, width=800, height=600, bg="white")
        self.root = root
        # Operation variables
        self.current_drawn_detections : dict[Detection.Type : list[Detection]] = None
        self.test_questions_report : TestQuestions = None

        # Make the frame responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Canvas configuration
        self.Canvas = ImgCanvas(self, width=800, height=600, bg="white")
        self.Canvas.grid(row=0, column=0, sticky="nswe") 
        # Side panel configuration
        self.sidePanel = SidePanel(self, root, bg="lightgray", width=200, height=500)
        self.sidePanel.place(
            relx=1, rely=0, x=-5, y=+5, anchor=tk.NE, width=200, relheight=.9
        )

        # Footer buttons
        self.footerButtons = _footerButtons(root)
        self.footerButtons.pack()


        EventBus.subscribe(
            self.update_detections,
            "<<detection_checkbox_clicked>>",
            "<<update_all>>"
        )
        EventBus.subscribe(
                self.update_questions_answers,
                "<<update_all>>",
                "<<build_answers>>",
                "<<build_all_answers>>",
            )
        EventBus.subscribe(self.load_next_image, "<<next_image>>")
        EventBus.subscribe(self.load_previous_image, "<<previous_image>>")
        EventBus.subscribe(self.clear, "<<clear_img_app>>")


    
    def update_detections(self, event=None):
        # Get the selected values for the detections
        detections_selected : dict[Detection.Type, bool]\
              = self.sidePanel.get_show_detection_values()
        # Get the cache
        cache : ImageCacheStruct = Config.api.cache.from_index(
            Config.current_image_index
        )

        if cache is not None:
            # Get the selected values
            selected : list[str] = [k for k, v in detections_selected.items() if v]
            # Filter the detections
            filtered_detections : dict[Detection.Type, list[Detection]] = \
                cache.container.get_by_type(selected)
            # Update the current detections
            self.current_drawn_detections = filtered_detections
        else:
            self.current_drawn_detections = {}

    def update_questions_answers(self, event):
        test_type = Config.selected_test_type
        do_build = True if event != "<<update_all>>" else False
        to_all = event == "<<build_all_answers>>"
        if to_all:
            indices = range(Config.api.get_number_of_images())
        else:
            indices = [Config.current_image_index]
        for index in indices:
            cache : ImageCacheStruct = Config.api.cache.from_index(
                index
            )
            if cache is not None and do_build:
                builder : BuilderApi = Config.api.get_builder(test_type)
                test_blocks : TestBlocks = cache.blocks
                test_questions_report : TestQuestions = builder.resolve_test(test_blocks)
                cache.questions = test_questions_report
        # Get the cache for the image on screen if to all was set
        if to_all:
            cache = Config.api.cache.from_index(Config.current_image_index)
            test_questions_report = cache.questions
        # Update the current questions report
        try:
            self.test_questions_report = cache.questions
        except:
            self.test_questions_report = None
        EventBus.publish("<<update_question_panel>>")
    
    def load_next_image(self, event=None):
        """Load the next image in the list."""
        # Get the new index
        index = Config.current_image_index
        new_index = (index + 1) % Config.api.get_number_of_images()
        # Load and set all the relevant data
        Config.api.select_image(new_index, do_cache=False)
        # Set the new index
        Config.current_image_index = new_index
        # Update all widgets and data
        EventBus.publish("<<update_all>>")
        # Make draw call
        EventBus.publish("<<center_draw_call>>")

    def load_previous_image(self, event=None):
        """Load the previous image in the list."""
        # Get the new index
        index = Config.current_image_index
        new_index = (index - 1) % Config.api.get_number_of_images()
        # Load and set all the relevant data
        Config.api.select_image(new_index, do_cache=False)
        # Set the new index
        Config.current_image_index = new_index
        # Update the detections
        EventBus.publish("<<update_all>>")
        # Make draw call
        EventBus.publish("<<center_draw_call>>")
    
    def clear(self, event):
        """Clear the canvas and the side panel."""
        self.current_drawn_detections = {}
        self.test_questions_report = None
