import tkinter as tk
from tkinter import filedialog

from core.definitions.question import TestType
from core.definitions import Stage
from core.IO import MODELS_PATH

from gui import (
    Config,
    EventBus,
    title_font,
    semititle_font
)

 
 # SECTION: Pipeline Sidebar Widgets

class _testFrame(tk.Frame):
    def __init__(self, sidebar):
        super().__init__(sidebar, border=2, relief="groove")
        self.columnconfigure(0, weight=1)

        # Config vars
        self.test_name = tk.StringVar(value="PS_ALUNOS")
        self.options = ["PS_ALUNOS", "SIMULINHO", "SIMUFSC", "SIMUENEM"]

        # Create bullet buttons
        self.label = tk.Label(self, text="Tipo de Prova", font=title_font)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.radio_buttons = []
        for i, option in enumerate(self.options):
            bt = tk.Radiobutton(
                    self,
                    text=option,  # Displayed text
                    value=option,  # Value to store when selected
                    variable=self.test_name,  # Shared variable
                    command=self.set_global_test_type
            )
            bt.grid(row=i+1, column=0, sticky="ew")
            self.radio_buttons.append(bt)
        self.radio_buttons[0].config(bg="dark sea green")


    ## Event handlers ##

    def set_global_test_type(self):
        test_type_str = self.test_name.get()
        Config.selected_test_type = TestType[test_type_str]
        for rb in self.radio_buttons:
            if rb.cget("value") == test_type_str:
                rb.config(bg="dark sea green")
            else:
                rb.config(bg="lightgray")

    def activate_buttons(self):
        self.load_button.config(state=tk.NORMAL)


class _modelFrame(tk.Frame):
    def __init__(self, sidebar, modelstage : Stage = Stage.NULL, load_callback=None):
        super().__init__(sidebar, border=2, relief="groove")
        self.columnconfigure(0, weight=1)
        self.load_callback = load_callback
        self.stage = modelstage
        
        # Config vars
        self.model_path = tk.StringVar(value="Nao selecionado")
        self.score_threshold = tk.DoubleVar(value=0)

        # Create widgets
        # Top label
        text = "Primeiro Estágio" if modelstage == Stage.FIRST else "Segundo Estágio"
        self.label = tk.Label(self, text=text, font=semititle_font)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # Row 1 - Model selection
        top_frame = tk.Frame(self, border=2, relief="groove")
        top_frame.columnconfigure(0, weight=1)
        # Button
        self.load_button = tk.Button(top_frame, text="Select Model", command=self.load_model)
        self.load_button.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # Model Name Label
        self.model_path_label = tk.Label(
            top_frame,
            textvariable=self.model_path,
            wraplength=200,
            fg="gray",
        )
        self.model_path_label.grid(row=1, column=0, sticky="nsew")
        top_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        # Row 2 - Config widgets
        # Score Threshold input
        self.score_threshold_frame = tk.Frame(self, border=2, relief="groove")
        self.score_threshold_frame.columnconfigure(0, weight=1)
        self.score_threshold_frame.grid(row=2, column=0, padx=5, sticky="nsew")
        # Label
        self.score_threshold_label = tk.Label(
            self.score_threshold_frame, text="Score Threshold", fg="gray"
        )
        self.score_threshold_label.grid(row=0, column=0, sticky="nsew")
        # Scale
        self.score_threshold_scale = tk.Scale(
            self.score_threshold_frame,
            from_=0,
            to=1,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            variable=self.score_threshold,
            state=tk.DISABLED
        )
        self.score_threshold_scale.grid(row=1, column=0, sticky="nsew")


    def load_model(self):
        model_path = filedialog.askopenfilename(
            filetypes=[("Model files", "*.py *.pt *.tflite")],
            initialdir=MODELS_PATH
        )
        if not model_path:
            return
        # Get the relative path
        self.model_path.set(model_path)
        # Try to load the model to context
        loaded = Config.api.io.load_model(
            model_path, stage=self.stage
        )
        self.__activate_panel()
        if loaded:
            self.__model_success_status()
        else:
            self.__model_error_status()


    ## Getters && Setters ##

    def get_info(self):

        return {
            "model_path": self.model_path.get(),
            "st": self.score_threshold.get(),
        }


    ## Internal event handlers ##

    def __activate_panel(self):
        # Activate the buttons
        self.score_threshold_scale.config(state=tk.NORMAL)
        # Activate the labels
        self.model_path_label.config(fg="black")
        self.score_threshold_label.config(fg="black")
        self.score_threshold.set(0.5)

    def __model_success_status(self):
        self.model_path_label.config(bg="dark sea green")

    def __model_error_status(self):
        self.model_path_label.config(bg="indian red")



# SECTION: Pipeline Sidebar Main Widget

class PipelineSideBar(tk.Frame):
    
    def __init__(self, root):
        super().__init__(root)
        self.columnconfigure(0, weight=1)

        # Save the parent reference
        self.root = root

        # Create widgets
        # Test selection Frame
        self.test_frame = _testFrame(self)
        self.test_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Pipeline label
        tk.Label(self, text="Pipeline", font=title_font, bg='light salmon').grid(
            row=1, column=0, padx=5, pady=5, sticky="nsew"
        )

        # First Stage Model
        self.first_stage = _modelFrame(self, Stage.FIRST, None)
        self.first_stage.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # Second Stage Model
        self.second_stage = _modelFrame(self, Stage.SECOND, None)
        self.second_stage.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        # Apply button
        self.apply_button = tk.Button(
            self,
            text="Rodar Pipeline",
            command=self.publish,
            state=tk.DISABLED
        )
        self.apply_button.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

        # Apply to all checkbox
        self.apply_to_all = tk.BooleanVar(value=False)
        self.apply_to_all_check = tk.Checkbutton(
            self,
            text="Aplicar a todas as imagens",
            variable=self.apply_to_all,
            state=tk.DISABLED
        )
        self.apply_to_all_check.grid(row=5, column=0, padx=5, pady=5, sticky="nsew")

        # Subscribe to events
        EventBus.subscribe(self.on_folder_loaded, "<<folder_loaded>>")


    ## Getters && Setters ##

    def get_pipeline(self):
        test = Config.selected_test_type
        fs = self.first_stage.get_info()
        ss = self.second_stage.get_info()
        
        return {
            'test': test,
            'fs': fs,
            'ss': ss
        }


    ## Event handlers ##

    def publish(self):
        if self.apply_to_all.get():
            EventBus.publish("<<apply_model_to_all>>")
        else:
            EventBus.publish("<<apply_model>>")


    def on_folder_loaded(self, event):
        self.apply_button.config(state=tk.NORMAL)
        self.apply_to_all_check.config(state=tk.NORMAL)