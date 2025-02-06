import tkinter as tk

from core.detection.base import Detection

from gui import folder_loaded_callback

## AUXILIARY WIDGETS ##


class _showDetectionsBox(tk.Frame):
    class _buttonList(tk.Frame):

        sb_var = None
        ub_var = None
        cb_var = None
        qb_var = None

        def __init__(self, parent, imgApp, *args, **kwargs):
            super().__init__(parent, imgApp, *args, **kwargs)
            self.imgApp = imgApp
            self.columnconfigure(0, weight=1)
            # Save the callback reference
            
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
                command=self.update_detections
            )
            self.sb_button.pack(anchor=tk.W, expand=True, fill=tk.X)
            self.ub_button = tk.Checkbutton(
                self,
                text="Unselected Balls",
                state=tk.DISABLED,
                variable=self.ub_var,
                command=self.update_detections
            )
            self.ub_button.pack(anchor=tk.W, expand=True, fill=tk.X)
            self.cb_button = tk.Checkbutton(
                self,
                text="Cpf Blocks",
                state=tk.DISABLED,
                variable=self.cb_var,
                command=self.update_detections
            )
            self.cb_button.pack(anchor=tk.W, expand=True, fill=tk.X)
            self.qb_button = tk.Checkbutton(
                self,
                text="Question Blocks",
                state=tk.DISABLED,
                variable=self.qb_var,
                command=self.update_detections
            )
            self.qb_button.pack(anchor=tk.W, expand=True, fill=tk.X)

        def update_detections(self):
            self.imgApp.update_detections()
        
        def get_info(self):
            values = {
                Detection.Type.SELECTED_BALL   : self.sb_var.get(),
                Detection.Type.UNSELECTED_BALL : self.ub_var.get(),
                Detection.Type.CPF_BLOCK       : self.cb_var.get(),
                Detection.Type.QUESTION_BLOCK  : self.qb_var.get()
            }
            return values
        
    
    def __init__(self, parent, root, imgApp, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Save the parent reference
        self.imgApp = parent
        self.root = root

        # Control variables

        # Create widgets
        # Top label
        tk.Label(self,text="Show Detections").pack()
        # Button list
        self.buttonList = self._buttonList(self, imgApp)
        self.buttonList.pack(expand=True, fill=tk.X)
        # Register the activate event
        folder_loaded_callback.bind(self.on_activate)


    def on_activate(self):
        self.buttonList.sb_button.config(state=tk.NORMAL)
        self.buttonList.ub_button.config(state=tk.NORMAL)
        self.buttonList.cb_button.config(state=tk.NORMAL)
        self.buttonList.qb_button.config(state=tk.NORMAL)


#### MAIN WIDGET ####

class SidePanel(tk.Frame):

    def __init__(self, imgApp, root, *args, **kwargs):
        super().__init__(imgApp, *args, **kwargs)
        # Save the parent reference
        self.imgApp = imgApp
        self.root = root
        # Create widgets
        self.showDetectionsBox = _showDetectionsBox(
            self,
            root,
            imgApp
        )
        self.showDetectionsBox.pack(fill="x")

    def get_show_detection_values(self):
        return self.showDetectionsBox.buttonList.get_info()

    def activate(self):
        pass

