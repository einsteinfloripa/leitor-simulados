import tkinter as tk

import cv2
from PIL import Image, ImageTk

from core.image import Image as CoreImage
from core.detection import Detection

## AUXILIARY WIDGETS ##

class _buttonList(tk.Frame):

    sb_var = None
    ub_var = None
    cb_var = None
    qb_var = None

    def __init__(self, parent, on_checked_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Save the callback reference
        self.on_checked_callback = on_checked_callback
        
        # Create control variables
        self.sb_var = tk.BooleanVar()
        self.ub_var = tk.BooleanVar()
        self.cb_var = tk.BooleanVar()
        self.qb_var = tk.BooleanVar()
        
        # Create widgets
        self.sb_button = tk.Checkbutton(
            self,
            text="Selected Balls",
            state=tk.DISABLED,
            variable=self.sb_var,
            command=self.on_checked
        )
        self.sb_button.pack(anchor=tk.W)
        self.ub_button = tk.Checkbutton(
            self,
            text="Unselected Balls",
            state=tk.DISABLED,
            variable=self.ub_var,
            command=self.on_checked
        )
        self.ub_button.pack(anchor=tk.W)
        self.cb_button = tk.Checkbutton(
            self,
            text="Cpf Blocks",
            state=tk.DISABLED,
            variable=self.cb_var,
            command=self.on_checked
        )
        self.cb_button.pack(anchor=tk.W)
        self.qb_button = tk.Checkbutton(
            self,
            text="Question Blocks",
            state=tk.DISABLED,
            variable=self.qb_var,
            command=self.on_checked
        )
        self.qb_button.pack(anchor=tk.W)


    def on_checked(self):
        values = {
            "selected_ball": self.sb_var.get(),
            "unselected_ball": self.ub_var.get(),
            "cpf_block": self.cb_var.get(),
            "question_block": self.qb_var.get()
        }
        self.on_checked_callback(values)

class _showDetectionsBox(tk.Frame):
    
    def __init__(self, parent, root, on_check_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Save the parent reference
        self.imgApp = parent
        self.root = root

        # Control variables

        # Create widgets
        # Top label
        tk.Label(self,text="Show Detections").pack()
        # Button list
        self.buttonList = _buttonList(self, on_check_callback)
        self.buttonList.pack(expand=True, fill=tk.BOTH, anchor=tk.W)
        # Register the activate event
        root.on_activate(self.activate)


    def activate(self):
        self.buttonList.sb_button.config(state=tk.NORMAL)
        self.buttonList.ub_button.config(state=tk.NORMAL)
        self.buttonList.cb_button.config(state=tk.NORMAL)
        self.buttonList.qb_button.config(state=tk.NORMAL)

#### MAIN WIDGET ####

class SidePanel(tk.Frame):

    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Save the parent reference
        self.imgApp = parent
        self.root = root
        # Create widgets
        self.showDetectionsBox = _showDetectionsBox(
            self,
            root,
            self.imgApp.update_detections
        )
        self.showDetectionsBox.pack(fill="x")

    
    def activate(self):
        pass

