import tkinter as tk
from tkinter import Menu, filedialog

from .event_system import EventBus
from .popups import SaveAsPopup, ExportYoloPopup

class TopMenu(tk.Menu):
    """Represents the top menu bar in the GUI.
    
    Attributes
    ----------
    root : tk.Tk
        The root Tkinter window.
    """
    
    def __init__(self, root):
        """Initializes the top menu bar with different menu options.
        
        Parameters
        ----------
        root : tk.Tk
            The root Tkinter window.
        """
        super().__init__(root, bg="lightblue")
        self.root = root

        # Menu Arquivo
        menu_arquivo = Menu(self, tearoff=0)
        menu_arquivo.add_command(label="Abrir Pasta", command=self.open_folder)
        menu_arquivo.add_command(
            label="Salvar respostas", command=self.save_report
        )
        self.add_cascade(label="Arquivo", menu=menu_arquivo)

        # Menu Ferramentas
        menu_ferramentas = Menu(self, tearoff=0)
        menu_ferramentas.add_checkbutton(label="Debug")
        self.add_cascade(label="Ferramentas", menu=menu_ferramentas)

        # Menu Detecções
        menu_deteccoes = Menu(self, tearoff=0)
        menu_deteccoes.add_command(
            label="Exportar YOLO",
            command=self.export_yolo
        )
        self.add_cascade(label="Detecções", menu=menu_deteccoes)

    def open_folder(self):
        """Opens a folder selection dialog and publishes the selected folder path."""
        file = filedialog.askdirectory()
        if file:
            EventBus.publish("<<open_folder>>", file)
    
    def save_report(self):
        """Opens the 'Save As' popup to allow the user to save a report."""
        SaveAsPopup(self.root)

    def export_yolo(self):
        """Opens the 'Export YOLO' popup for exporting image detections."""
        ExportYoloPopup(self.root)
