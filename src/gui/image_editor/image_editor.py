import tkinter as tk

import cv2

from core.detection import Detection, DetectionCoords

from .canvas import ImgCanvas
from .sidePanel import SidePanel


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
        # Save the parent reference
        self.root = root
        # Make the frame responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # State variable
        self.panel_active = False

        # Canvas configuration
        self.Canvas = ImgCanvas(self, root, width=800, height=600, bg="white")
        self.Canvas.grid(row=0, column=0, sticky="nswe") 
        # Side panel configuration
        self.sidePanel = SidePanel(self, root, bg="lightgray", width=200, height=500)
        self.sidePanel.place(relx=1, rely=0, x=-5, y=+5, anchor=tk.NE, width=200, height=500)

        # Image control variables
        self.brg_image_raw = None  # Displayed image (OpenCV format)
        self.current_image_index = -1  # Index of the current image
        self.number_of_images = 0  # Total number of images
        # Detection
        # Detection selected to be shown
        self.current_drawn_detections = {}
        # This is a map the has the detection buinding box in reltion to the root image
        # as key and the values are the cached detections of the image
        self.detection_map = None
        # All the DetectionCoordenates of the current image by class name
        self.current_detections = {}

        # Footer buttons
        self.footerButtons = _footerButtons(
            self.root.footer, self.load_previous_image, self.load_next_image
            )
        self.footerButtons.pack()


    def cache_detection_coords(self, index):
        # Clear the current detections
        self.current_detections = {}
        # If there is no cache for the image, return
        if not self.root.img_cache[index]:
            self.current_detections = {}
            self.current_drawn_detections = {}
            return
        # Get all the detections in the image cached data    
        detections : list[Detection] = []
        detections.extend(self.root.img_cache[index]['detections'])
        cropped_imgs = self.root.img_cache[index]['crops']
        for img in cropped_imgs:
            detections.extend(img.detections)
        # Convert the detection to DetectionCoords
        # Make a map from DetectionCoords to Detection
        self.detection_map = {}
        for detection in detections:
            # Convert the detection to DetectionCoords
            coords : DetectionCoords = detection.to_coords()
            # Add the detection to the map
            self.detection_map[coords] = detection
            # Add the detection to the current_detections
            try:
                self.current_detections[coords.class_name].append(coords)
            except KeyError:
                self.current_detections[coords.class_name] = [coords]


    def show_image(self, image_index):
        """Show the image at the given index."""
        if not self.root.image_files:
            return
        if image_index != self.current_image_index:
            self.root.load_image(image_index)
            self.current_image_index = image_index
        self.brg_image_raw = cv2.cvtColor(self.root.image.raw, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for Tkinter
        self.Canvas.center_image()  # Display the image
        self.footerButtons.update(image_index + 1, len(self.root.image_files))
    
    def load_next_image(self):
        """Load the next image in the list."""
        new_index = (self.current_image_index + 1) % self.number_of_images
        self.cache_detection_coords(new_index)
        self.update_detections()
        self.show_image(new_index)

    def load_previous_image(self):
        """Load the previous image in the list."""
        new_index = (self.current_image_index - 1) % self.number_of_images
        self.cache_detection_coords(new_index)
        self.update_detections()
        self.show_image(new_index)

    def update_detections(self):
        values_dict = self.sidePanel.get_show_detection_values()
        if self.current_detections:
            # Get the selected values
            selected : list[str] = [k for k, v in values_dict.items() if v]
            # Filter the detections
            filtered_detections : dict[str, list[DetectionCoords]] = {}
            for class_name in selected:
                try:
                    filtered_detections[class_name] = self.current_detections[class_name]
                except KeyError:
                    pass
            # Update the current detections
            self.current_drawn_detections = filtered_detections
            # Redraw the canvas
            self.Canvas.display_image() 