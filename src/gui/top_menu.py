import tkinter as tk
from tkinter import Menu, filedialog

from . import EventBus
from .popups import SaveAsPopup, ExportYoloPopup

class TopMenu(tk.Menu):
    def __init__(self, root):
        super().__init__(root, bg="lightblue")
        self.root = root

        # Menu Arquivo
        menu_arquivo = Menu(self, tearoff=0)
        menu_arquivo.add_command(label="Abrir Pasta", command=self.open_folder)
        menu_arquivo.add_command(
            label="Salvar respostas", command=self.sabe_report
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
        file = filedialog.askdirectory()
        if file:
            EventBus.publish("<<open_folder>>", file)
    
    def sabe_report(self):
        pop = SaveAsPopup(self.root)
        pop.mainloop()
    
    def export_yolo(self):
        # Iterate over all images
        pop = ExportYoloPopup(self.root)
        pop.mainloop()