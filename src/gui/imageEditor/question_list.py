__all__ = ["QuestionAnswerPanel"]

import tkinter as tk
from tkinter import ttk

from core.definitions.question import TestReport, Question, NumericAnswer, AlphaAnswer
from api.data_structs import ImageCacheStruct

from ..event_system import EventBus
from .. import Config, regular_font, semititle_font

@EventBus.bind
class _InnerPanel(tk.Frame):
    """
    Private auxiliary widget for displaying and editing question answers.

    This widget creates a scrollable frame that holds input widgets for each
    question's answer, and couples them with the corresponding data from the cache.

    Parameters
    ----------
    parent : tk.Widget
        The parent widget.
    bind_index : int
        The index used to bind the panel to a specific image cache entry.
    *args : list
        Additional positional arguments for tk.Frame.
    **kwargs : dict
        Additional keyword arguments for tk.Frame.
    """

    def __init__(self, parent, bind_index):
        super().__init__(parent)
        self.parent : tk.Frame = parent

        # Tkinter boilerplate for scrollable frame
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)
        self.inner_frame.columnconfigure(0, minsize=80)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.on_frame_configure)


        # Data widgets configuration and API coupling
        
        # Create variable holders for the cpf and answers
        self.cpf_var = tk.StringVar(value="XXXXXXXXXXX")
        self.answer_vars = {}   # Stores answer variables (tk.StringVar)
        self.input_widgets = {}  # Stores input widgets (Combobox or Entry)

        # API coupling: retrieve data from the cache
        self.img_data: ImageCacheStruct = Config.api.cache.from_index(bind_index)
        self.test_report: TestReport = self.img_data.report
        cpf = self.test_report.get_owner_cpf()
        self.cpf_var.set(cpf)
        self.questions: list[Question] = self.test_report.get_questions()
        
        # Save the original answers/cpf to compare with the updated ones
        self.original_answers = [question.answer.name for question in self.questions]
        self.original_cpf = cpf

        # Determine the answer type and options based on the first question
        self.answer_type = self.questions[0].answer.__class__
        if self.answer_type is AlphaAnswer:
            self.use_combobox = True
            self.answer_options = [ans.name for ans in AlphaAnswer]
        else:
            self.use_combobox = False
            self.answer_options = None


        # Create widget for cpf
        def validate_entry(new_value):
            return (
                (new_value.isdigit() or new_value == '') 
                and len(new_value) <= 11
            )
        tk.Label(
            self.inner_frame,
            text="CPF",
            font=semititle_font
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        tk.Entry(
            self.inner_frame,
            textvariable=self.cpf_var,
            width=11,
            validate="key",
            validatecommand=(self.register(validate_entry), "%P")
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        # Create widgets for each question
        for i, question in enumerate(self.questions):
            # Create label for the question number
            tk.Label(
                self.inner_frame,
                text=f"Q{question.number}:",
                font=regular_font
            ).grid(row=i+2, column=0, padx=10, pady=5)

            # Create StringVar for answer
            answer_var = tk.StringVar(value=question.answer.name)
            self.answer_vars[i] = answer_var

            # Create input widget based on answer type
            if self.use_combobox:
                widget = ttk.Combobox(
                    self.inner_frame,
                    textvariable=answer_var,
                    values=self.answer_options,
                    state="readonly",
                    width=8
                )
                widget.current(question.answer.value + 1)
            else:
                widget = tk.Entry(
                    self.inner_frame,
                    textvariable=answer_var,
                    width=8
                )

            widget.grid(row=i+2, column=1, padx=10, pady=5)
            self.input_widgets[i] = widget

            # Trace changes to update the corresponding question answer
            self.answer_vars[i].trace_add("write", lambda *args, idx=i: self.on_update_answer(idx, *args))
            self.cpf_var.trace_add("write", self.on_update_cpf)
            # Add a control variable to not update the label on every key press
            self.pending_update = None


    def on_frame_configure(self, event=None):
        """
        Update the scrollable region when the inner frame is reconfigured.

        Parameters
        ----------
        event : optional
            The event that triggered this callback (default is None).
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_update_answer(self, index, *args):
        """
        Handle updates to an answer and propagate changes to the data cache.

        Parameters
        ----------
        index : int
            The index of the question whose answer was updated.
        *args : tuple
            Additional arguments passed by the trace callback.
        """
        updated_answer = self.answer_vars[index].get()
        question: Question = self.questions[index]
        question.answer = self.answer_type[updated_answer]

        # Determine if the answer has been updated compared to the original
        update = self.original_answers[index] != updated_answer
        self.test_report.update_answer(question, updated=update)

        # Trigger a redraw of the image
        EventBus.publish("<<draw_call>>")

    def on_update_cpf(self, *args):
        """
        Handle updates to the CPF and propagate changes to the data cache.

        Parameters
        ----------
        *args : tuple
            Additional arguments passed by the trace callback.
        """
        if self.pending_update:
            self.parent.after_cancel(self.pending_update)
        self.pending_update = self.parent.after(300, self.update_label)  # Wait 300ms

    def update_label(self):
        """
        Update the CPF label and propagate changes to the data cache.
        """

        updated_cpf = self.cpf_var.get()
        self.test_report.set_owner_cpf(updated_cpf)

        # Determine if the CPF has been updated compared to the original
        update = self.original_cpf != updated_cpf
        self.test_report.set_owner_cpf(updated_cpf, updated=update)

        # Trigger a redraw of the image
        EventBus.publish("<<draw_call>>")


@EventBus.bind
class QuestionAnswerPanel(tk.Frame):
    """
    Public widget that serves as a panel for displaying and editing question answers.

    This panel creates an inner panel that is dynamically updated based on the
    current image cache and listens for events to update its display.
    
    Parameters
    ----------
    sidePanel : tk.Widget
        The parent side panel widget.
    """

    def __init__(self, sidePanel):
        super().__init__(sidePanel, border=5, relief=tk.RIDGE)
        self.sidePanel = sidePanel

        # Create a placeholder inner panel
        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)


    @EventBus.subscribe("update_all", "<<update_question_panel>>")
    def update_panel(self, event):
        """
        Update the panel based on the current image cache.

        If there are no questions in the cache, hide the questions; otherwise,
        display the question editor.

        Parameters
        ----------
        event : any
            The event that triggered the update.
        """
        index = Config.current_image_index
        report = Config.api.get_report(index)
        if not report:
            self.__hide_questions()
        else:
            self.__show_questions(index)

    def __show_questions(self, index):
        """
        Display the inner panel with question answers bound to the given image index.

        Parameters
        ----------
        index : int
            The index of the image cache to bind the questions to.
        """
        # Destroy existing inner panel if it exists
        if self.inner_panel.winfo_exists():
            self.inner_panel.destroy()

        # Create a new inner panel for the given bind index
        self.inner_panel = _InnerPanel(self, index)
        self.inner_panel.pack(fill="both", expand=True)

    def __hide_questions(self):
        """
        Hide the questions by destroying the current inner panel and replacing it with a placeholder.
        """
        if self.inner_panel.winfo_exists():
            self.inner_panel.destroy()

        self.inner_panel = ttk.Frame(self)
        self.inner_panel.pack(fill="both", expand=True)
