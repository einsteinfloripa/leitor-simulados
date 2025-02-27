__all__ = ["PipelineSideBar"]

import tkinter as tk
from tkinter import filedialog, ttk

from core.definitions.enums import TestType, Stage
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
        self.locked = False

        self.label = tk.Label(self, text="Tipo de Prova", font=title_font)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.radio_buttons = []
        for i, option in enumerate(self.options):
            bt = tk.Radiobutton(
                self, text=option, value=option, variable=self.test_name, 
            )
            bt.grid(row=i+1, column=0, sticky="ew")
            self.radio_buttons.append(bt)
    
        EventBus.subscribe(self.lock_on, "<<folder_loaded>>")

    def lock_on(self, envent=None):
        """
        Lock the test type selection.
        """
        test_type_str = self.test_name.get()
        Config.selected_test_type = TestType[test_type_str]
        for rb in self.radio_buttons:
            rb.config(bg="dark sea green" if rb.cget("value") == test_type_str else "lightgray")
        self.locked = True

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
        
        # Secction title
        text = "Primeiro Estágio" if modelstage == Stage.FIRST else "Segundo Estágio"
        tk.Label(self, text=text, font=semititle_font).grid(
            row=0, column=0, padx=5, pady=5, sticky="nsew"
        )

        # Variable creation
        self.avalaible_models = {
            str(m) : m for m in Config.api.get_available_models() \
            if m.target_stage == modelstage or m.target_stage == Stage.BOTH
        }
        self.options = ['Nao selecionado'] + list(self.avalaible_models.keys())
        self.selected_option = tk.StringVar(value=self.options[0])
        self.score_threshold = tk.DoubleVar(value=0)
                
        # ComboBox widget
        self.combobox = ttk.Combobox(
            self,
            values=self.options,
            textvariable=self.selected_option,
            state="readonly"
        )
        self.combobox.grid(
            row=1, column=0, padx=5, pady=5, sticky="nsew"
        )

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
    
        # Set trace to update the panel
        self.selected_option.trace_add("write", lambda *args: self.__update_panel())

    def get_info(self):
        """
        Get model configuration.

        Returns
        -------
        dict
            Dictionary containing model path and score threshold.
        """
        model = self.avalaible_models[self.selected_option.get()]
        return {"model": model, "st": self.score_threshold.get()}
    
    def __update_panel(self):
        """
        Activate the panel for model configuration.
        """
        def deactivate_panel(self):
            self.score_threshold_scale.config(state=tk.DISABLED)
            self.score_threshold_label.config(fg="gray")
            self.score_threshold.set(0)

        def activate_panel(self):
            self.score_threshold_scale.config(state=tk.NORMAL)
            self.score_threshold_label.config(fg="black")
            self.score_threshold.set(0.5)

        option = self.selected_option.get()
        if option == 'Nao selecionado':
            deactivate_panel(self)
        else:
            activate_panel(self)


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
        fs = self.first_stage.get_info()
        ss = self.second_stage.get_info()
        
        return {
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