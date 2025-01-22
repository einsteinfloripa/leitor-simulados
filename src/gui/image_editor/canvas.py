import tkinter as tk

import cv2
from PIL import Image, ImageTk

from core.image import Image as CoreImage
from core.detection import Detection


## AUXILIARY WIDGETS ##
class _zoomButtons(tk.Frame):
    font = ("Helvetica", 16)
    def __init__(self, parent, root, zoom_in_callback, zoom_out_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Create buttons in the bottom left corner
        self.zoom_out_button = tk.Button(
            self,
            text="-",
            width=1,
            height=1,
            command=zoom_out_callback,
            font=self.font,
            state=tk.DISABLED
            )
        self.zoom_out_button.pack(side=tk.LEFT)
        self.zoom_in_button = tk.Button(
            self,
            text="+",
            width=1,
            height=1,
            command=zoom_in_callback,
            font=self.font,
            state=tk.DISABLED
            )
        self.zoom_in_button.pack(side=tk.RIGHT)

        root.on_activate(self.activate)

    def activate(self):
        self.zoom_out_button.config(state=tk.NORMAL)
        self.zoom_in_button.config(state=tk.NORMAL)


## MAIN WIDGET ##
class ImgCanvas(tk.Canvas):

    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Save the parent reference
        self.imgApp = parent
        
        # Set the initial state and variables
        self.zoom_factor = 1.0
        self.offset_x = 0  # Offset for image dragging
        self.offset_y = 0
        self.drag_start = None  # Starting point of the drag

        # Create the zoom buttons
        self.zoomButtons = _zoomButtons(
            self, root, self.zoom_in, self.zoom_out
        )
        self.zoomButtons.place(
            relx=0.0, rely=1.0, anchor=tk.SW, x=5, y=-5
        )

        # Bind events
        self.bind("<Button-3>", self.start_drag)  # Right mouse button to start dragging
        self.bind("<B3-Motion>", self.drag_image)  # Motion while holding right mouse button
        self.bind("<ButtonRelease-3>", self.stop_drag)  # Release right mouse button to stop dragging
        self.bind("<MouseWheel>", self.mouse_zoom)  # Zoom using mouse scroll


    def display_image(self):
        """Display the current image on the canvas."""
        img = self.imgApp.brg_image_raw
        # Resize the image based on the zoom factor
        height, width, _ = img.shape
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)
        self.display_image_cv = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

        # Convert OpenCV image to PhotoImage for Tkinter
        display_image_pil = Image.fromarray(self.display_image_cv)
        self.photo_image = ImageTk.PhotoImage(display_image_pil)

        # Clear the canvas and display the image
        self.delete("all")
        self.create_image(self.offset_x, self.offset_y, image=self.photo_image, anchor=tk.NW)
        # Draw rectangles
        if self.imgApp.current_detections:
            self.draw_detections()

    def center_image(self):
        """Center the image and scale it to fit within the canvas."""
        # Get the image's size and the canvas's size
        img_height, img_width, _ = self.imgApp.brg_image_raw.shape
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

    def draw_detections(self):
        """Draw rectangles on the image."""
        colors = ['green', 'blue', 'yellow', 'red']
        order = ["question_block", "cpf_block", "unselected_ball", "selected_ball"]
        # Sort the detections based on the order
        sorted_detections : list[Detection] = sorted(
            self.imgApp.current_detections,
            key=lambda d: order.index(d.class_name)
        )
        # Get the rectangles
        info_rect = [(d.to_pixels(), colors[d.class_id]) for d in sorted_detections]
        for rect, color in info_rect:
            x1, y1, x2, y2 = rect
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
    def zoom_in(self):
        """Zoom in the image."""
        self.zoom_factor *= 1.2
        self.display_image()

    def zoom_out(self):
        """Zoom out the image."""
        self.zoom_factor /= 1.2
        self.display_image()

    def mouse_zoom(self, event):
        """Zoom the image using the mouse scroll."""
        if event.delta > 0:  # Scroll up to zoom in
            self.zoom_in()
        elif event.delta < 0:  # Scroll down to zoom out
            self.zoom_out()

    def start_drag(self, event):
        """Start dragging the image."""
        self.drag_start = (event.x, event.y)

    def drag_image(self, event):
        """Drag the image."""
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.display_image()

    def stop_drag(self, event):
        """Stop dragging the image."""
        self.drag_start = None
               

