__all__ = ["QuestionAnswerPanel"]

import tkinter as tk
from tkinter import ttk

from core.definitions.question import (
    TestQuestions,
    Question,
    NumericAnswer,
    AlphaAnswer
)
from api.data_structs import ImageCacheStruct


from gui import (
    Config,
    EventBus,
    regular_font
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
        # Get relevant data from the cache
        self.img_data : ImageCacheStruct = \
            Config.api.cache.from_index(bind_index)
        self.test_questions : TestQuestions = self.img_data.questions
        self.questions : list[Question] = self.test_questions.get_questions()
        
        # Create some auxiliary variables
        self.answer_type : NumericAnswer | AlphaAnswer = \
            self.questions[0].answer.__class__
        if self.answer_type is AlphaAnswer:
            self.use_combobox = True
            self.answer_options = [ans.name for ans in AlphaAnswer]
        else:
            self.use_combobox = False
            self.answer_options = None
        self.original_answers = [question.answer.name for question in self.questions]

        # Widgets creation
        for i, question in enumerate(self.questions):
            
            # Create the top label
            tk.Label(
                self.inner_frame,
                text=f"Q{question.number}:",
                font=regular_font
            ).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            # Variables
            answer_var = tk.StringVar(value=question.answer.name)
            self.answer_vars[i] = answer_var

            # Create the input widget depending on the answer type
            if self.use_combobox:
                widget = ttk.Combobox(
                    self.inner_frame,
                    textvariable=answer_var,
                    values=self.answer_options,
                    state="readonly",
                )
                widget.current(question.answer.value + 1)
            else:
                widget = tk.Entry(self.inner_frame, textvariable=answer_var)

            widget.grid(row=i, column=1, padx=10, pady=5)
            self.input_widgets[i] = widget  # Store for reference
            
            # Watch for changes in the answers
            self.answer_vars[i].trace_add(
                "write", lambda *args, idx=i: self.on_update_answer(idx, *args)
            )


    ## Event handlers ##
    def on_frame_configure(self, event=None):
        """Update scrollable region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_update_answer(self, index, *args):
        
        # Get the updated answer and update the question
        updateted_answer = self.answer_vars[index].get()
        question : Question = self.questions[index]
        question.answer = self.answer_type[updateted_answer]

        # Save in the cache
        update = self.original_answers[index] != updateted_answer
        self.test_questions.update_answer(question, updated=update)
        
        # Redraw the image
        EventBus.publish("<<draw_call>>")
        


# SECTION: Pubic parent widget

class QuestionAnswerPanel(tk.Frame):
    def __init__(self, sidePanel):
        super().__init__(sidePanel, border=5, relief=tk.RIDGE)
        self.sidePanel = sidePanel

        # Placeholder panel
        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)


        ## Subscribe to events ##
        EventBus.subscribe(
            self.update_panel,
            "<<update_all>>",
            "<<update_question_panel>>",
        )

    def update_panel(self, event):
        index = Config.current_image_index
        cache : ImageCacheStruct = Config.api.cache.from_index(index)
        if not cache or not cache.questions:
            self.__hide_questions()
        else:
            self.__show_questions(index)
        
        

    def __show_questions(self, bind_index):

        # Chec if the inner panel exists, destroy it.
        if self.inner_panel.winfo_exists():
            self.inner_panel.destroy()
        
        # Create the inner panel
        self.inner_panel = _innerPanel(self, bind_index)
        self.inner_panel.pack(fill="both", expand=True)

    def __hide_questions(self):
        
        # Chec if the inner panel exists, destroy it.
        if self.inner_panel.winfo_exists():
            self.inner_panel.destroy()

        # Create a placeholder panel
        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)

