import tkinter as tk

import cv2
from PIL import Image, ImageTk

from core.detection import DetectionCoords, Detection

from .drawingContext import DrawingContext
from ..context import AppContextData


## AUXILIARY WIDGETS ##
class _zoomButtons(tk.Frame):
    font = ("Helvetica", 16)
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        # Create buttons in the bottom left corner
        self.zoom_out_button = tk.Button(
            self,
            text="-",
            width=1,
            height=1,
            command=canvas._zoom_out,
            font=self.font,
            state=tk.DISABLED
            )
        self.zoom_out_button.pack(side=tk.LEFT)
        self.zoom_in_button = tk.Button(
            self,
            text="+",
            width=1,
            height=1,
            command=canvas._zoom_in,
            font=self.font,
            state=tk.DISABLED
            )
        self.zoom_in_button.pack(side=tk.RIGHT)

        AppContextData.folder_loaded_callback.add_callback(self.activate)

    def activate(self):
        self.zoom_out_button.config(state=tk.NORMAL)
        self.zoom_in_button.config(state=tk.NORMAL)


## MAIN WIDGET ##
class ImgCanvas(tk.Canvas):

    def __init__(self, imgEditor, *args, **kwargs):
        super().__init__(imgEditor, *args, **kwargs)
        # Set the initial state and variables
        # Image
        self.zoom_factor : float = 1.0
        self.offset_x : int = 0  # Offset for image dragging
        self.offset_y : int = 0
        # Detections
        self.current_drawn_detections : dict[str:DetectionCoords] = None
        # Operational
        self.drag_start = None  # Starting point of the drag

        # Create the zoom buttons
        self.zoomButtons = _zoomButtons(self)
        self.zoomButtons.place(
            relx=0.0, rely=1.0, anchor=tk.SW, x=5, y=-5
        )

        # Bind events
        self.bind("<Button-3>", self._start_drag)  # Right mouse button to start dragging
        self.bind("<B3-Motion>", self._drag_image)  # Motion while holding right mouse button
        self.bind("<ButtonRelease-3>", self._stop_drag)  # Release right mouse button to stop dragging
        self.bind("<MouseWheel>", self._mouse_zoom)  # Zoom using mouse scroll


    def display_image(self):
        """Display the current image on the canvas."""
        # Resize the image based on the zoom factor
        height, width, _ = DrawingContext.brg_image_raw.shape
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)
        self.display_image_cv = cv2.resize(
            DrawingContext.brg_image_raw,
            (new_width, new_height),
            interpolation=cv2.INTER_LINEAR
        )
        # Convert OpenCV image to PhotoImage for Tkinter
        display_image_pil = Image.fromarray(self.display_image_cv)
        self.photo_image = ImageTk.PhotoImage(display_image_pil)

        # Clear the canvas and display the image
        self.delete("all")
        self.create_image(self.offset_x, self.offset_y, image=self.photo_image, anchor=tk.NW)
        # Draw rectangles
        if self.current_drawn_detections:
            self.__draw_detections()

    def center_image(self):
        """Center the image and scale it to fit within the canvas."""
        # Get the image's size and the canvas's size
        img_height, img_width, _ = DrawingContext.brg_image_raw.shape
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        # Calculate the scale factor to fit the image inside the canvas while maintaining aspect ratio
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale_factor = min(scale_x, scale_y)

        # Update zoom factor and reset the offsets
        self.zoom_factor = scale_factor
        self.offset_x = (canvas_width - int(img_width * scale_factor)) / 2
        self.offset_y = (canvas_height - int(img_height * scale_factor)) / 2

        self.display_image()


    ## Private functions ##
    def __draw_detections(self):
        """Draw rectangles on the image."""
        colors = ['green', 'blue', 'yellow', 'red']
        order = [
            Detection.Type.QUESTION_BLOCK,
            Detection.Type.CPF_BLOCK,
            Detection.Type.UNSELECTED_BALL,
            Detection.Type.SELECTED_BALL
        ]
        # Sort the detections based on the order
        detections : dict[Detection.Type, list[DetectionCoords]] = self.current_drawn_detections
        for i, class_type in enumerate(order):
            if not detections: continue
            # Get the rectangles

            bboxs = [d.bbox for d in detections.get(class_type, [])]
            for bbox in bboxs:
                x1, y1, x2, y2 = bbox
                color = colors[i]
                # Scale and offset the coordinates
                scaled_x1 = self.offset_x + x1 * self.zoom_factor
                scaled_y1 = self.offset_y + y1 * self.zoom_factor
                scaled_x2 = self.offset_x + x2 * self.zoom_factor
                scaled_y2 = self.offset_y + y2 * self.zoom_factor


                self.create_rectangle(
                    scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                    fill="", outline=color, width=2
                )
                # self.create_rectangle(
                #     scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                #     fill=color, stipple="gray25", outline=""
                # )


    # Event handlers
    def _zoom_in(self):
        """Zoom in the image."""
        self.zoom_factor *= 1.2
        self.display_image()

    def _zoom_out(self):
        """Zoom out the image."""
        self.zoom_factor /= 1.2
        self.display_image()

    def _mouse_zoom(self, event):
        """Zoom the image using the mouse scroll."""
        if event.delta > 0:  # Scroll up to zoom in
            self.zoom_in()
        elif event.delta < 0:  # Scroll down to zoom out
            self.zoom_out()

    def _start_drag(self, event):
        """Start dragging the image."""
        self.drag_start = (event.x, event.y)

    def _drag_image(self, event):
        """Drag the image."""
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.display_image()

    def _stop_drag(self, event):
        """Stop dragging the image."""
        self.drag_start = None
               

