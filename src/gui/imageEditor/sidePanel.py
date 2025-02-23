__all__ = ["SidePanel"]

import tkinter as tk
from tkinter import ttk

from core.detection.base import Detection
from gui import Config, EventBus, title_font
from .question_list import QuestionAnswerPanel


# =============================================================================
# Auxiliary Widgets
# =============================================================================

class _ShowDetectionsBox(tk.Frame):
    """
    A widget that displays checkboxes for different detection types.

    This widget shows checkboxes to control the visibility of various
    detection types (selected balls, unselected balls, CPF blocks, and question blocks).

    Parameters
    ----------
    parent : tk.Widget
        The parent widget.
    root : tk.Widget
        The root widget containing application-level attributes.
    imgApp : tk.Widget
        The image application widget for which the detections are managed.
    *args : list
        Additional positional arguments for tk.Frame.
    **kwargs : dict
        Additional keyword arguments for tk.Frame.
    """

    class _ButtonList(tk.Frame):
        """
        A nested widget that contains the list of detection checkbuttons.

        Attributes
        ----------
        sb_var : tk.BooleanVar
            Variable for the "Selected Balls" checkbox.
        ub_var : tk.BooleanVar
            Variable for the "Unselected Balls" checkbox.
        cb_var : tk.BooleanVar
            Variable for the "CPF Blocks" checkbox.
        qb_var : tk.BooleanVar
            Variable for the "Question Blocks" checkbox.
        """

        def __init__(self, parent, imgApp, *args, **kwargs):
            super().__init__(parent, *args, **kwargs)
            self.imgApp = imgApp
            self.columnconfigure(0, weight=1)

            # Create control variables
            self.sb_var = tk.BooleanVar()
            self.ub_var = tk.BooleanVar()
            self.cb_var = tk.BooleanVar()
            self.qb_var = tk.BooleanVar()

            # Create checkbuttons for each detection type
            self.sb_button = tk.Checkbutton(
                self,
                text="Selected Balls",
                state=tk.DISABLED,
                variable=self.sb_var,
                command=self.publish_event
            )
            self.sb_button.pack(anchor=tk.W, expand=True, fill=tk.X)

            self.ub_button = tk.Checkbutton(
                self,
                text="Unselected Balls",
                state=tk.DISABLED,
                variable=self.ub_var,
                command=self.publish_event
            )
            self.ub_button.pack(anchor=tk.W, expand=True, fill=tk.X)

            self.cb_button = tk.Checkbutton(
                self,
                text="Cpf Blocks",
                state=tk.DISABLED,
                variable=self.cb_var,
                command=self.publish_event
            )
            self.cb_button.pack(anchor=tk.W, expand=True, fill=tk.X)

            self.qb_button = tk.Checkbutton(
                self,
                text="Question Blocks",
                state=tk.DISABLED,
                variable=self.qb_var,
                command=self.publish_event
            )
            self.qb_button.pack(anchor=tk.W, expand=True, fill=tk.X)

        def publish_event(self):
            """
            Publish events to notify that a detection checkbox has been clicked.
            """
            EventBus.publish("<<detection_checkbox_clicked>>")
            EventBus.publish("<<draw_call>>")

        def get_info(self):
            """
            Retrieve the current state of each detection checkbox.

            Returns
            -------
            dict
                A dictionary mapping detection types to their Boolean state.
            """
            values = {
                Detection.Type.SELECTED_BALL: self.sb_var.get(),
                Detection.Type.UNSELECTED_BALL: self.ub_var.get(),
                Detection.Type.CPF_BLOCK: self.cb_var.get(),
                Detection.Type.QUESTION_BLOCK: self.qb_var.get()
            }
            return values

    def __init__(self, parent, root, imgApp, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, border=1, relief=tk.RAISED)
        self.root = root
        self.imgApp = imgApp

        # Create widgets
        tk.Label(self, text="Detecções", pady=5, font=title_font).pack()
        self.buttonList = self._ButtonList(self, imgApp)
        self.buttonList.pack(expand=True, fill=tk.X)

        # Subscribe to events to activate the detection checkboxes
        EventBus.subscribe(self.on_activate, "<<folder_loaded>>")

    def on_activate(self, event):
        """
        Activate the detection checkboxes when a folder is loaded.

        Parameters
        ----------
        event : any
            The event that triggered activation.
        """
        self.buttonList.sb_button.config(state=tk.NORMAL)
        self.buttonList.ub_button.config(state=tk.NORMAL)
        self.buttonList.cb_button.config(state=tk.NORMAL)
        self.buttonList.qb_button.config(state=tk.NORMAL)


class _BuilderPanel(tk.Frame):
    """
    A widget that provides controls for building and displaying answers.

    This panel includes options to show answers, update individual or all answers,
    and publish drawing events.

    Parameters
    ----------
    sidepanel : tk.Widget
        The parent side panel widget.
    imgApp : tk.Widget
        The image application widget.
    """

    def __init__(self, sidepanel, imgApp):
        super().__init__(sidepanel, border=1, relief=tk.RAISED)
        self.sidepanel = sidepanel
        self.imgApp = imgApp

        # Create top label for the panel
        tk.Label(
            self, text="Respostas", pady=5, font=title_font
        ).grid(row=0, column=0, columnspan=2)

        # Checkbox to show answers
        self.show_answers_var = tk.BooleanVar()
        self.show_answers_checkbox = tk.Checkbutton(
            self,
            text="Mostrar respostas",
            variable=self.show_answers_var,
            command=sidepanel.imgApp.Canvas.display_image,
            state=tk.DISABLED
        )
        self.show_answers_checkbox.grid(row=1, column=0, columnspan=2)

        # Update button for building answers
        self.update_button = tk.Button(
            self,
            text="Procurar",
            command=self.publish,
            state=tk.DISABLED
        )
        self.update_button.grid(row=2, column=0, columnspan=1)

        # Checkbox to update all answers
        self.update_all_var = tk.BooleanVar()
        self.update_all_checkbox = tk.Checkbutton(
            self,
            text="Todas",
            variable=self.update_all_var,
            state=tk.DISABLED
        )
        self.update_all_checkbox.grid(row=2, column=1, columnspan=1)

        # Subscribe to event to activate update controls
        EventBus.subscribe(self.activate_update_button, "<<folder_loaded>>")

    def publish(self):
        """
        Publish events to build answers based on the update mode.
        """
        to_all = self.update_all_var.get()
        if to_all:
            EventBus.publish("<<build_all_answers>>")
        else:
            EventBus.publish("<<build_answers>>")
        EventBus.publish("<<draw_call>>")

    def get_show_answers(self):
        """
        Get the current state of the "show answers" checkbox.

        Returns
        -------
        bool
            True if "show answers" is enabled; otherwise, False.
        """
        return self.show_answers_var.get()

    def activate_update_button(self, event):
        """
        Activate the update controls when a folder is loaded.

        Parameters
        ----------
        event : any
            The event that triggered this activation.
        """
        self.update_button.config(state=tk.NORMAL)
        self.show_answers_checkbox.config(state=tk.NORMAL)
        self.update_all_checkbox.config(state=tk.NORMAL)


# =============================================================================
# Main Widget
# =============================================================================

class SidePanel(tk.Frame):
    """
    Main side panel widget that aggregates detection controls, builder controls,
    and the question-answer panel.

    Parameters
    ----------
    imgApp : tk.Widget
        The image application widget.
    root : tk.Widget
        The root widget of the application.
    *args : list
        Additional positional arguments for tk.Frame.
    **kwargs : dict
        Additional keyword arguments for tk.Frame.
    """

    def __init__(self, imgApp, root, *args, **kwargs):
        super().__init__(imgApp, *args, **kwargs)
        self.imgApp = imgApp
        self.root = root

        # Create and pack the detection box widget
        self.showDetectionsBox = _ShowDetectionsBox(self, root, imgApp)
        self.showDetectionsBox.pack(fill=tk.X, pady=2, padx=2)

        # Create and pack the builder panel
        self.builder_panel = _BuilderPanel(self, imgApp)
        self.builder_panel.pack(fill=tk.X, pady=2, padx=2)

        # Create and pack the question-answer panel
        self.question_panel = QuestionAnswerPanel(self)
        self.question_panel.pack(fill=tk.BOTH, expand=True, pady=2, padx=2)

    def get_show_detection_values(self):
        """
        Retrieve the current detection checkbox states.

        Returns
        -------
        dict
            A dictionary mapping detection types to their Boolean states.
        """
        return self.showDetectionsBox.buttonList.get_info()

    def get_show_answers(self):
        """
        Retrieve the current state of the "show answers" option.

        Returns
        -------
        bool
            True if "show answers" is enabled; otherwise, False.
        """
        return self.builder_panel.get_show_answers()

    def activate(self):
        """
        Activate the side panel (custom logic can be added here).
        """
        pass
