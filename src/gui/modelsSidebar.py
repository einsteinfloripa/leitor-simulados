__all__ = ["PipelineSideBar"]

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

class _TestFrame(tk.Frame):
    """Frame for selecting the test type."""

    def __init__(self, sidebar):
        """
        Initialize the test type selection frame.

        Parameters
        ----------
        sidebar : tk.Frame
            Parent sidebar frame.
        """
        super().__init__(sidebar, border=2, relief="groove")
        self.columnconfigure(0, weight=1)

        self.test_name = tk.StringVar(value="PS_ALUNOS")
        self.options = ["PS_ALUNOS", "SIMULINHO", "SIMUFSC", "SIMUENEM"]

        self.label = tk.Label(self, text="Tipo de Prova", font=title_font)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.radio_buttons = []
        for i, option in enumerate(self.options):
            bt = tk.Radiobutton(
                self, text=option, value=option, variable=self.test_name, 
                command=self.set_global_test_type
            )
            bt.grid(row=i+1, column=0, sticky="ew")
            self.radio_buttons.append(bt)
        self.radio_buttons[0].config(bg="dark sea green")

    def set_global_test_type(self):
        """
        Update the global test type in the configuration.
        """
        test_type_str = self.test_name.get()
        Config.selected_test_type = TestType[test_type_str]
        for rb in self.radio_buttons:
            rb.config(bg="dark sea green" if rb.cget("value") == test_type_str else "lightgray")


class _ModelFrame(tk.Frame):
    """Frame for selecting and configuring a model."""

    def __init__(self, sidebar, modelstage: Stage = Stage.NULL):
        """
        Initialize the model selection frame.

        Parameters
        ----------
        sidebar : tk.Frame
            Parent sidebar frame.
        modelstage : Stage, optional
            Stage of the model (FIRST or SECOND), by default Stage.NULL.
        """
        super().__init__(sidebar, border=2, relief="groove")
        self.columnconfigure(0, weight=1)
        self.stage = modelstage
        
        self.model_path = tk.StringVar(value="Não selecionado")
        self.score_threshold = tk.DoubleVar(value=0)

        text = "Primeiro Estágio" if modelstage == Stage.FIRST else "Segundo Estágio"
        tk.Label(self, text=text, font=semititle_font).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        top_frame = tk.Frame(self, border=2, relief="groove")
        top_frame.columnconfigure(0, weight=1)
        tk.Button(top_frame, text="Select Model", command=self.load_model).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.model_path_label = tk.Label(top_frame, textvariable=self.model_path, wraplength=200, fg="gray")
        self.model_path_label.grid(row=1, column=0, sticky="nsew")
        top_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.score_threshold_frame = tk.Frame(self, border=2, relief="groove")
        self.score_threshold_frame.columnconfigure(0, weight=1)
        self.score_threshold_frame.grid(row=2, column=0, padx=5, sticky="nsew")
        
        self.score_threshold_label = tk.Label(self.score_threshold_frame, text="Score Threshold", fg="gray")
        self.score_threshold_label.grid(row=0, column=0, sticky="nsew")
        self.score_threshold_scale = tk.Scale(
            self.score_threshold_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, 
            variable=self.score_threshold, state=tk.DISABLED
        )
        self.score_threshold_scale.grid(row=1, column=0, sticky="nsew")
    
    def load_model(self):
        """
        Open file dialog to select and load a model.
        """
        model_path = filedialog.askopenfilename(filetypes=[("Model files", "*.py *.pt *.tflite")], initialdir=MODELS_PATH)
        if not model_path:
            return
        self.model_path.set(model_path)
        loaded = Config.api.io.load_model(model_path, stage=self.stage)
        self.__activate_panel()
        self.__model_success_status() if loaded else self.__model_error_status()
    
    def get_info(self):
        """
        Get model configuration.

        Returns
        -------
        dict
            Dictionary containing model path and score threshold.
        """
        return {"model_path": self.model_path.get(), "st": self.score_threshold.get()}
    
    def __activate_panel(self):
        """
        Activate the panel for model configuration.
        """
        self.score_threshold_scale.config(state=tk.NORMAL)
        self.model_path_label.config(fg="black")
        self.score_threshold_label.config(fg="black")
        self.score_threshold.set(0.5)
    
    def __model_success_status(self):
        """
        Indicate successful model loading.
        """
        self.model_path_label.config(bg="dark sea green")
    
    def __model_error_status(self):
        """
        Indicate model loading failure.
        """
        self.model_path_label.config(bg="indian red")


class PipelineSideBar(tk.Frame):
    """Sidebar for configuring the test pipeline."""

    def __init__(self, root):
        """
        Initialize the pipeline sidebar.

        Parameters
        ----------
        root : tk.Tk
            Root application window.
        """
        super().__init__(root)
        self.columnconfigure(0, weight=1)

        self.test_frame = _TestFrame(self)
        self.test_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(self, text="Pipeline", font=title_font, bg='light salmon').grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.first_stage = _ModelFrame(self, Stage.FIRST)
        self.first_stage.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.second_stage = _ModelFrame(self, Stage.SECOND)
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