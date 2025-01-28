import tkinter as tk

import cv2

from core.detection import Detection, DetectionCoords

from .canvas import ImgCanvas
from .sidePanel import SidePanel
from .drawingContext import DrawingContext
from ..context import AppContextData




## AUXILIARY WIDGETS ##
class _footerButtons(tk.Frame):
    def __init__(self,
                parent,
                previous_image_callback,
                next_image_callback
        ):
        super().__init__(parent, bg="lightblue")
        # Save the parent reference
        self.parent = parent

        # Previous Button
        self.previous_button = tk.Button(
            self, text="<<", command=previous_image_callback, state=tk.DISABLED
        )
        self.previous_button.grid(row=0, column=0, padx=5, pady=5)
        # Text Label
        self.image_label = tk.Label(self, text="0/0", bg="lightblue")
        self.image_label.grid(row=0, column=1, padx=5, pady=5)
        # Next Button
        self.next_button = tk.Button(
            self, text=">>", command=next_image_callback, state=tk.DISABLED
            )
        self.next_button.grid(row=0, column=2, padx=5, pady=5)

    def update(self, current, total):
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
        # Operation variables
        self.current_image_index = -1
        
        # Make the frame responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Canvas configuration
        self.Canvas = ImgCanvas(self, root, width=800, height=600, bg="white")
        self.Canvas.grid(row=0, column=0, sticky="nswe") 
        # Side panel configuration
        self.sidePanel = SidePanel(self, root, bg="lightgray", width=200, height=500)
        self.sidePanel.place(relx=1, rely=0, x=-5, y=+5, anchor=tk.NE, width=200, height=500)

        # Footer buttons
        self.footerButtons = _footerButtons(
            self.root.footer, self.load_previous_image, self.load_next_image
            )
        self.footerButtons.pack()

    def display_image(self, image_index):
        """Show the image at the given index."""
        self.Canvas.center_image()
        self.footerButtons.update(image_index + 1, AppContextData.number_of_images)
    
    def update_detections(self):
        detections_selected = self.sidePanel.get_show_detection_values()
        if DrawingContext.has_detections():
            # Get the selected values
            selected : list[str] = [k for k, v in detections_selected.items() if v]
            # Filter the detections
            filtered_detections : dict[str, list[DetectionCoords]] = {}
            for class_name in selected:
                try:
                    filtered_detections[class_name] = DrawingContext.detection_coords[class_name]
                except KeyError:
                    pass
            # Update the current detections
            self.Canvas.current_drawn_detections = filtered_detections


    ## Event Handlers ##   
    def _load_next_image(self):
        """Load the next image in the list."""
        # Get the new index
        new_index = (self.current_image_index + 1) % AppContextData.number_of_images
        # Load and set all the relevant data
        AppContextData.load_image_to_context(new_index)
        self.update_detections()
        self.current_image_index = new_index
        # Make draw call
        self.display_image(new_index)

    def _load_previous_image(self):
        """Load the previous image in the list."""
        # Get the new index
        new_index = (self.current_image_index - 1) % AppContextData.number_of_images
        # Load and set all the relevant data
        AppContextData.load_image_to_context(new_index)
        self.update_detections()
        self.current_image_index = new_index
        # Make draw call
        self.display_image(new_index)
