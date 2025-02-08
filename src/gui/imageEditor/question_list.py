from abc import ABC, abstractmethod

import tkinter as tk
from tkinter import ttk

from definitions import TestType
from definitions.question import (
    TestQuestions,
    Question,
    AlphaAnswer,
    NumericAnswer,
)

class QuestionAnswerPanel(tk.Frame, ABC):
    """Base class for a scrollable question-answer panel."""
    def __init__(self, parent, questions, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.questions : TestQuestions = questions 

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.on_frame_configure)

        self.answer_vars = {}  # Store answer variables
        self.populate_questions()

    @abstractmethod
    def populate_questions(self):
        """To be implemented by subclasses."""
        pass

    def on_frame_configure(self, event=None):
        """Update scrollable region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_answers(self):
        """Retrieve updated answers from the input fields."""
        return [(q_num, self.answer_vars[q_num].get()) for q_num, _ in self.questions]


class AlphaQuestionAnswerPanel(QuestionAnswerPanel):
    """Version using a dropdown Combobox for selecting answers."""
    def __init__(self, parent, test_type : TestType, *args, **kwargs):
        questions = TestQuestions.from_test_type(test_type)
        super().__init__(parent, questions, *args, **kwargs)

    def populate_questions(self):
        for i, (q_num, answer) in enumerate(self.questions):
            tk.Label(self.inner_frame, text=f"Q{q_num}:", font=("Arial", 12, "bold")).grid(row=i, column=0, padx=10, pady=5, sticky="w")

            answer_var = tk.StringVar(value=answer)
            self.answer_vars[q_num] = answer_var

            combobox = ttk.Combobox(self.inner_frame, textvariable=answer_var, values=self.answer_options, state="readonly")
            combobox.grid(row=i, column=1, padx=10, pady=5)
            combobox.current(self.answer_options.index(answer))


class NumericQuestionAnswerPanel(QuestionAnswerPanel):
    """Version using a standard Entry field for typing answers."""
    def populate_questions(self):
        for i, (q_num, answer) in enumerate(self.questions):
            tk.Label(self.inner_frame, text=f"Q{q_num}:", font=("Arial", 12, "bold")).grid(row=i, column=0, padx=10, pady=5, sticky="w")

            answer_var = tk.StringVar(value=answer)
            self.answer_vars[q_num] = answer_var

            entry = tk.Entry(self.inner_frame, textvariable=answer_var)
            entry.grid(row=i, column=1, padx=10, pady=5)


# Sample questions and initial answers
questions_data = [(1, "A"), (2, "B"), (3, "C"), (4, "D"), (5, "A"), (6, "C"), (7, "B"), (8, "D")]
answer_choices = ["A", "B", "C", "D"]

# Create main window
root = tk.Tk()
root.title("Question-Answer Panel")

# Frame with Combobox selection
panel_combo = AlphaQuestionAnswerPanel(root, questions_data, answer_choices, width=250, height=400)
panel_combo.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# Frame with Entry field
panel_entry = NumericQuestionAnswerPanel(root, questions_data, width=250, height=400)
panel_entry.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Button to print answers
def show_answers():
    print("ComboBox Answers:", panel_combo.get_answers())
    print("Entry Field Answers:", panel_entry.get_answers())

ttk.Button(root, text="Get Answers", command=show_answers).pack(pady=10)

root.mainloop()
