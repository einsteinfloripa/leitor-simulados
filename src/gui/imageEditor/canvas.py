import tkinter as tk
import cv2
from PIL import Image, ImageTk

from core.definitions.test_defs import TestType
from core.detection.base import Detection
from core.definitions.question import Question
from core.definitions.geometry import IntBoundingBox, IntPoint

from api.data_structs import ImageCacheStruct

from .. import Config, title_font, semititle_font
from ..event_system import EventBus, Calltime


@EventBus.bind
class _ZoomButtons(tk.Frame):
    """
    Auxiliary widget for zoom controls.

    This widget creates two buttons for zooming in and out of the image displayed
    on the canvas. It subscribes to a folder-loaded event to activate the buttons.

    Parameters
    ----------
    canvas : tk.Canvas
        The canvas widget that displays the image and handles zooming.
    *args : list
        Additional positional arguments passed to the tk.Frame initializer.
    **kwargs : dict
        Additional keyword arguments passed to the tk.Frame initializer.
    """
    #TODO: Change font
    font = ("Helvetica", 16)

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        # Create zoom out button
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
        # Create zoom in button
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

    @EventBus.subscribe("<<successfully_folder_loaded>>")
    def activate(self, event):
        """
        Activate the zoom buttons when a folder is loaded.

        Parameters
        ----------
        event : any
            The event that triggered the activation.
        """
        self.zoom_out_button.config(state=tk.NORMAL)
        self.zoom_in_button.config(state=tk.NORMAL)


@EventBus.bind
class ImgCanvas(tk.Canvas):
    """
    A canvas widget for displaying, zooming, and interacting with images.

    This widget displays an image from the API, supports zooming and dragging,
    and overlays detection rectangles, question annotations, and CPF information.

    Parameters
    ----------
    imgEditor : tk.Widget
        The parent image editor widget.
    *args : list
        Additional positional arguments passed to the tk.Canvas initializer.
    **kwargs : dict
        Additional keyword arguments passed to the tk.Canvas initializer.
    """

    def __init__(self, imgEditor, *args, **kwargs):
        super().__init__(imgEditor, *args, **kwargs)
        self.imgEditor = imgEditor

        # Initialize state variables
        self.zoom_factor: float = 1.0
        self.offset_x: int = 0  # Horizontal offset for dragging
        self.offset_y: int = 0  # Vertical offset for dragging
        self.drag_start = None  # Starting point for dragging

        # Create and position the zoom buttons
        self.zoomButtons = _ZoomButtons(self)
        self.zoomButtons.place(relx=0.0, rely=1.0, anchor=tk.SW, x=5, y=-5)

        # Bind mouse events for dragging and zooming
        self.bind("<Button-3>", self._start_drag)       # Right-click starts drag
        self.bind("<B3-Motion>", self._drag_image)        # Drag motion
        self.bind("<ButtonRelease-3>", self._stop_drag)   # Stop dragging
        self.bind("<MouseWheel>", self._mouse_zoom)       # Mouse wheel for zoom


    @EventBus.subscribe("<<draw_call>>")
    def display_image(self, event=None):
        """
        Display the current image on the canvas, scaling it based on the zoom factor.

        Also overlays detection rectangles, question annotations, and CPF information.
        
        Parameters
        ----------
        event : optional
            The event that triggered the display update (default is None).
        """
        # Retrieve image and its dimensions
        image = Config.api.image
        height, width, _ = image.raw.shape
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)
        
        # Resize the image using OpenCV
        self.display_image_cv = cv2.resize(
            Config.api.rgb_image_raw,
            (new_width, new_height),
            interpolation=cv2.INTER_LINEAR
        )
        # Convert to a PIL image then to a PhotoImage for Tkinter
        display_image_pil = Image.fromarray(self.display_image_cv)
        self.photo_image = ImageTk.PhotoImage(display_image_pil)

        # Clear the canvas and draw the image
        self.delete("all")
        if hasattr(self, "nameframe") and self.nameframe:
            self.nameframe.destroy()

        # Make a new image on the canvas
        self.create_image(self.offset_x, self.offset_y, image=self.photo_image, anchor=tk.NW)
        
        # Draw image on the middle of the canvas
        self.nameframe = tk.Label(
            self, text=image.name, font=title_font, bg="light gray", fg="DarkSlateGray",
        )
        self.nameframe.place(relx=0.5, y=10, anchor=tk.N)

        # Draw overlay elements
        if self.imgEditor.current_drawn_detections:
            self.__draw_detections()
        has_report = Config.api.has_report()
        if has_report and self.imgEditor.sidePanel.get_show_answers():
            self.__draw_questions()
            self.__draw_cpf()

    @EventBus.subscribe("<<center_draw_call>>")
    @EventBus.subscribe("<<successfully_folder_loaded>>", calltime=Calltime.LATE)
    def center_image(self, event=None):
        """
        Center and scale the image to fit within the canvas while preserving aspect ratio.

        Parameters
        ----------
        event : optional
            The event that triggered centering (default is None).
        """
        img_height, img_width, _ = Config.api.rgb_image_raw.shape
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()

        # Calculate scale factor to fit the image in the canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale_factor = min(scale_x, scale_y)

        self.zoom_factor = scale_factor
        self.offset_x = (canvas_width - int(img_width * scale_factor)) / 2
        self.offset_y = (canvas_height - int(img_height * scale_factor)) / 2

        self.display_image()

    def __draw_detections(self):
        """
        Draw detection bounding boxes on the image.

        Detections are drawn in a specific order with distinct colors.
        """
        colors = ['green', 'blue', 'yellow', 'red']
        order = [
            Detection.Type.QUESTION_BLOCK,
            Detection.Type.CPF_BLOCK,
            Detection.Type.UNSELECTED_BALL,
            Detection.Type.SELECTED_BALL
        ]
        detections: dict[Detection.Type, list[Detection]] = self.imgEditor.current_drawn_detections
        for i, class_type in enumerate(order):
            if not detections:
                continue
            bboxs: list[IntBoundingBox] = [
                d.global_pixel_bounding_box for d in detections.get(class_type, [])
            ]
            for bbox in bboxs:
                x1, y1, x2, y2 = bbox
                # Scale and apply offset to coordinates
                scaled_x1 = self.offset_x + x1 * self.zoom_factor
                scaled_y1 = self.offset_y + y1 * self.zoom_factor
                scaled_x2 = self.offset_x + x2 * self.zoom_factor
                scaled_y2 = self.offset_y + y2 * self.zoom_factor
                self.create_rectangle(
                    scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                    fill="",
                    outline=colors[i],
                    width=2
                )

    def __draw_questions(self):
        """
        Draw question annotations on the image.

        Annotations include question numbers and their answers, colored based on update status.
        """
        questions: list[Question] = Config.api.get_report().get_questions()
        
        test_type = Config.selected_test_type

        if test_type == TestType.SIMUFSC:
            
            index = Config.api.current_set_index
            cache: ImageCacheStruct = Config.api.cache.from_index(index)
            question_block_detection: Detection = \
                cache.blocks.questions_blocks[0].root_detection
            offset_y = question_block_detection.pixel_height
            offset_x = question_block_detection.pixel_width // 2

            # Draw in the side
            for question in questions:
                if question.position is None:
                    continue
                
                x = question.position.x + offset_x
                y = question.position.y + offset_y
                scaled_x = self.offset_x + x * self.zoom_factor
                scaled_y = self.offset_y + y * self.zoom_factor

                if question.answer.value == 0:
                    text = "BRANCO"
                elif question.answer.value == -1:
                    text = "NAO DETECTADO"
                else:
                    text = f"{question.answer.name}"

                color = "indian red" if not question.updated else "orange2"
                self.create_text(
                    scaled_x, scaled_y,
                    text=text,
                    fill=color,
                    font=semititle_font
                )
        else:
            for question in questions:
                if question.position is None:
                    continue
                x, y = question.position
                # Scale and offset the coordinates
                scaled_x = self.offset_x + x * self.zoom_factor
                scaled_y = self.offset_y + y * self.zoom_factor

                if question.answer.value == 0:
                    text = "BRANCO"
                elif question.answer.value == -1:
                    text = "NAO DETECTADO"
                else:
                    text = f"{question.number} : {question.answer.name}"

                color = "indian red" if not question.updated else "orange2"
                self.create_text(
                    scaled_x, scaled_y,
                    text=text,
                    fill=color,
                    font=title_font
                )

    def __draw_cpf(self):
        """
        Draw the CPF (Cadastro de Pessoa Física) annotation on the image.
        
        Retrieves the CPF from the test questions report and draws it near the corresponding detection.
        """
        report = Config.api.get_report()
        cpf = report.get_owner_cpf()

        index = Config.api.current_set_index
        cache: ImageCacheStruct = Config.api.cache.from_index(index)
        cpf_detection: Detection = cache.blocks.cpf_block.root_detection
        middle_point: IntPoint = cpf_detection.pixel_middle_point
        offset_x = cpf_detection.pixel_width
        x = middle_point.x + offset_x
        y = middle_point.y
        # Scale and apply offset
        scaled_x = self.offset_x + x * self.zoom_factor
        scaled_y = self.offset_y + y * self.zoom_factor

        updated = report.get_cpf_updated()
        color = "indian red" if not updated else "orange2"
        self.create_text(
            scaled_x, scaled_y,
            text=f"CPF: {cpf}",
            fill=color,
            font=title_font
        )

    # Event Handlers
    def _zoom_in(self):
        """
        Zoom in the image by increasing the zoom factor.
        """
        self.zoom_factor *= 1.2
        self.display_image()

    def _zoom_out(self):
        """
        Zoom out the image by decreasing the zoom factor.
        """
        self.zoom_factor /= 1.2
        self.display_image()

    def _mouse_zoom(self, event):
        """
        Zoom the image using the mouse scroll.

        Parameters
        ----------
        event : tk.Event
            The event containing the scroll delta.
        """
        if event.delta > 0:
            self._zoom_in()
        elif event.delta < 0:
            self._zoom_out()

    def _start_drag(self, event):
        """
        Start dragging the image.

        Parameters
        ----------
        event : tk.Event
            The event containing the initial drag coordinates.
        """
        self.drag_start = (event.x, event.y)

    def _drag_image(self, event):
        """
        Update the image offset during a drag operation.

        Parameters
        ----------
        event : tk.Event
            The event containing the new mouse position.
        """
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.display_image()

    def _stop_drag(self, event):
        """
        End the drag operation.

        Parameters
        ----------
        event : tk.Event
            The event indicating the drag has stopped.
        """
        self.drag_start = None
