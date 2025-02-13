__all__ = ["QuestionAnswerPanel"]

import tkinter as tk
from tkinter import ttk

from definitions.question import (
    TestQuestions,
    Question,
    NumericAnswer,
    AlphaAnswer
)
from api.data_structs import ImageCacheStruct


from gui import (
    Config,
    regular_font,
    title_font
)


# SECTION: Private auxiliary widget

class _innerPanel(tk.Frame):


    ## Initialization ##
    def __init__(self, parent, bind_index, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)


        ## Tkinter boilerplate ##        
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.inner_frame = tk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_window = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw"
        )
        self.inner_frame.bind("<Configure>", self.on_frame_configure)


        ## Data widgets configuration and api coupling ##
        
        # Varibles
        self.answer_vars = {}  # Store answer variables
        self.input_widgets = {}  # Store input widgets (Combobox or Entry)

        # Api coupling
        self.img_data : ImageCacheStruct = \
            Config.api.get_cache().from_index(bind_index)
        self.test_questions : TestQuestions = self.img_data.questions
        self.questions : list[Question] = self.test_questions.get_questions()
        self.answer_type : NumericAnswer | AlphaAnswer = \
            self.questions[0].answer.__class__
        if self.answer_type is AlphaAnswer:
            self.use_combobox = True
            self.answer_options = [ans.name for ans in AlphaAnswer]
        else:
            self.use_combobox = False
            self.answer_options = None

        # Widgets creation
        for i, question in enumerate(self.questions):
            tk.Label(
                self.inner_frame,
                text=f"Q{question.number}:",
                font=regular_font
            ).grid(row=i, column=0, padx=10, pady=5, sticky="w")

            answer_var = tk.StringVar(value=question.answer.name)
            self.answer_vars[i] = answer_var
            self.answer_vars[i].trace_add(
                "write", lambda *args, idx=i: self.on_update_answer(idx, *args)
            )
            
            if self.use_combobox:
                widget = ttk.Combobox(
                    self.inner_frame,
                    textvariable=answer_var,
                    values=self.answer_options,
                    state="readonly",
                )
                widget.current(question.answer.value)
            else:
                widget = tk.Entry(self.inner_frame, textvariable=answer_var)

            widget.grid(row=i, column=1, padx=10, pady=5)
            self.input_widgets[i] = widget  # Store for reference
            

    ## Event handlers ##
    def on_frame_configure(self):
        """Update scrollable region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_update_answer(self, index, *args):
        # Get the updated answer and update the question
        updateted_answer = self.answer_vars[index].get()
        question : Question = self.questions[index]
        question.answer = self.answer_type[updateted_answer]
        question.updated = True

        # Save in the cache
        self.test_questions.update_answer(question)
        


# SECTION: Pubic parent widget

class QuestionAnswerPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, border=5, relief=tk.RIDGE)

        # Placeholder panel
        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)

        # Callbacks
        Config.detection_updated_callback.bind(
            lambda : self.show_questions(0)
        )



    def show_questions(self, bind_index):
        # Check if the image has questions
        cache : ImageCacheStruct = Config.api.get_cache().from_index(bind_index)
        if not cache.questions:
            return
        self.inner_panel.destroy()
        self.inner_panel = _innerPanel(self, bind_index)
        self.inner_panel.pack(fill="both", expand=True)

    def hide_questions(self):
        self.inner_panel.destroy()
        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)

