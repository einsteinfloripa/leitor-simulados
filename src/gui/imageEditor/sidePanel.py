import tkinter as tk

from core.detection.base import Detection

from gui import (
    folder_loaded_callback,
    api_instance,
    title_font
)

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
        super().__init__(parent, *args, **kwargs, border=1, relief=tk.RAISED)
        # Save the parent reference
        self.imgApp = parent
        self.root = root

        # Control variables

        # Create widgets
        # Top label
        tk.Label(self,text="Detecções", pady=5, font=title_font).pack()
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


class _builderPanel(tk.Frame):
    def __init__(self, sidepanel, imgApp):
        super().__init__(sidepanel, border=1, relief=tk.RAISED)
        self.sidepanel = sidepanel
        self.imgApp = imgApp

        self.top_label = tk.Label(
            self, text="Respostas", pady=5, font=title_font
        ).grid(row=0, column=0, columnspan=2)

        self.show_answers_var = tk.BooleanVar()
        self.show_answers_checkbox = tk.Checkbutton(
            self,
            text="Mostrar respostas",
            variable=self.show_answers_var,
            command=sidepanel.imgApp.Canvas.display_image,
            state=tk.DISABLED
        )
        self.show_answers_checkbox.grid(row=1, column=0, columnspan=2)
        # Update button
        self.update_button = tk.Button(
            self,
            text="Procurar",
            command=self.update,
            state=tk.DISABLED
        )
        self.update_button.grid(row=2, column=0, columnspan=1)
        # Update all checkbox
        self.update_all_var = tk.BooleanVar()
        self.update_all_checkbox = tk.Checkbutton(
            self,
            text="Todas",
            variable=self.update_all_var,
            state=tk.DISABLED
        )
        self.update_all_checkbox.grid(row=2, column=1, columnspan=1)

        folder_loaded_callback.bind(self.activate_update_button)

    def update(self):
        self.imgApp.update_questions_answers(
            build=True,
            to_all=self.update_all_var.get()
        )
    
    def get_show_answers(self):
        return self.show_answers_var.get()
    
    def activate_update_button(self):
        self.update_button.config(state=tk.NORMAL)
        self.show_answers_checkbox.config(state=tk.NORMAL)
        self.update_all_checkbox.config(state=tk.NORMAL)
        



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
        self.showDetectionsBox.pack(fill=tk.X, pady=2, padx=2)
        # Builder Panel
        self.builder_panel = _builderPanel(self, imgApp)
        self.builder_panel.pack(fill=tk.X, pady=2, padx=2)


    def get_show_detection_values(self):
        return self.showDetectionsBox.buttonList.get_info()
    
    def get_show_answers(self):
        return self.builder_panel.get_show_answers()

    def activate(self):
        pass

