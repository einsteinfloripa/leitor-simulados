import tkinter as tk
from tkinter import filedialog

from utils.filehandler import FileHandler
from definitions.question import TestType
from definitions import Stage

from gui import api_instance


class _testFrame(tk.Frame):
    def __init__(self, sidebar):
        super().__init__(sidebar, border=2, relief="groove")
        self.columnconfigure(0, weight=1)

        # Config vars
        self.test_name = tk.StringVar(value="PS")
        self.options = ["PS", "SIMULINHO", "SIMUFSC", "SIMUENEM"]

        # Create bullet buttons
        self.label = tk.Label(self, text="Tipo de Prova")
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        radio_buttons = []
        for i, option in enumerate(self.options):
            bt =tk.Radiobutton(
                    self,
                    text=option,  # Displayed text
                    value=option,  # Value to store when selected
                    variable=self.test_name,  # Shared variable
            )
            bt.grid(row=i+1, column=0)
            radio_buttons.append(bt)

    def get_info(self):
        return {'test_name' : self.test_name.get()}

    def set_test(self):
        test_path = filedialog.askopenfilename(
            filetypes=[("Test files", "*.py *.pt *.tflite")],
            initialdir=FileHandler.TESTS_PATH
        )
        if not test_path:
            return
        # Get the relative path
        cropped_path = test_path.split("/tests")[-1]
        self.test_path.set(cropped_path)
        # Update the test name in the label
        self.test_name.set(test_path.split("/")[-1])

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
        self.label = tk.Label(self, text=modelstage)
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
            initialdir=FileHandler.MODELS_PATH
        )
        if not model_path:
            return
        # Get the relative path
        self.model_path.set(model_path)
        # Try to load the model to context
        loaded = api_instance.load_model(
            model_path, stage=self.stage
        )
        self.activate_panel()
        if loaded:
            self.model_success_status()
        else:
            self.model_error_status()


    # Event handlers

    def activate_panel(self):
        # Activate the buttons
        self.score_threshold_scale.config(state=tk.NORMAL)
        # Activate the labels
        self.model_path_label.config(fg="black")
        self.score_threshold_label.config(fg="black")
        self.score_threshold.set(0.5)

    def get_info(self):
        return {
            "model_path": self.model_path.get(),
            "st": self.score_threshold.get(),
        }

    def model_success_status(self):
        self.model_path_label.config(bg="aquamarine2")

    def model_error_status(self):
        self.model_path_label.config(bg="indian red")

class PipelineSideBar(tk.Frame):
    
    def __init__(self, root):
        super().__init__(root)
        self.columnconfigure(0, weight=1)
        # Save the parent reference
        self.root = root
        # Create widgets
        # Top label
        tk.Label(self, text="Pipeline", bg='light salmon').grid(
            row=0, column=0, padx=5, pady=5, sticky="nsew"
        )
        # Test selection Frame
        self.test_frame = _testFrame(self)
        self.test_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # First Stage Model
        self.first_stage = _modelFrame(self, Stage.FIRST, None)
        self.first_stage.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        # Second Stage Model
        self.second_stage = _modelFrame(self, Stage.SECOND, None)
        self.second_stage.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        # Apply button
        self.apply_button = tk.Button(self, text="Run Pipeline", command=self.root.apply_model)
        self.apply_button.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

    def get_pipeline(self):
        test_map = {
            "PS": TestType.PS_ALUNOS,
            "SIMULINHO": TestType.SIMULINHO,
            "SIMUFSC": TestType.SIMUFSC,
            "SIMUENEM": TestType.SIMUENEM
        }
        test = self.test_frame.get_info()
        test = test_map[test['test_name']]
        fs = self.first_stage.get_info()
        ss = self.second_stage.get_info()
        
        return {
            'test': test,
            'fs': fs,
            'ss': ss
        }
