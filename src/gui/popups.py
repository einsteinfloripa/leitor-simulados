import tkinter as tk
from tkinter import ttk, filedialog
import threading
from time import sleep
from pathlib import Path

from core.IO import FileExtension

from gui import (
    Config,
    semititle_font
)


# SECTION: Time popups

class TimeBombPopup(tk.Toplevel):

    def __init__(
            self,
            root,
            parent,
            title,
            message,
            timer=3,
            destroy_parent=False
        ):
        super().__init__(root)
        self.title(title)
        self.destroy_parent = destroy_parent
        self.timer = timer
        self.parent = parent
        self.root = root
        self.title("Success")
        self.geometry("200x100")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Label
        tk.Label(self, text=message).pack(pady=10)

        # Confirm button
        tk.Button(
            self,
            text="OK",
            command=self.destroy
        ).pack(pady=10)

        # Start the timer
        self.after(timer*1000, self.destroy)


    def destroy(self):
        super().destroy()
        if self.destroy_parent:
            self.parent.destroy()




# SECTION: Export popup

class ExportYoloPopup(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title("Exportar YOLO")
        self.geometry("350x200")
        self.resizable(False, False)
        self.transient(root)
        self.grab_set()
        
        # Label
        tk.Label(
            self,
            text="Selecione a pasta de destino:",
            font=semititle_font
        ).grid(row=0, column=0, columnspan=2, pady=5)

        # Label to show the selected folder
        self.base_folder_var = tk.StringVar()
        self.base_folder_var.set("Nenhuma pasta selecionada")
        self.folder_label = tk.Label(self, textvariable=self.base_folder_var)
        self.folder_label.grid(row=1, column=0, columnspan=2, pady=5)

        # Button
        tk.Button(
            self,
            text="Procurar",
            command=self.select_base_folder
        ).grid(row=2, column=0, pady=5, padx=5)

        # Save images checkbox
        self.save_images_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text="Salvar imagens",
            variable=self.save_images_var
        ).grid(row=2, column=1, pady=5, padx=5)

        # Folder name label
        tk.Label(
            self,
            text="Nome da pasta:",
            font=semititle_font
        ).grid(row=3, column=0, pady=5, padx=5)

        # Entry for folder name
        self.folder_name_var = tk.StringVar()
        self.folder_name_var.set("detections")
        tk.Entry(
            self,
            textvariable=self.folder_name_var
        ).grid(row=3, column=1, pady=5, padx=5)


        # Confirm button
        tk.Button(
            self,
            text="Exportar",
            command=self.export_yolo,
            width=25
        ).grid(row=4, columnspan=2, column=0, pady=5)



    def select_base_folder(self):
        """ Opens file dialog and saves data in the selected format. """
        base_folder = filedialog.askdirectory()
        if not base_folder:
            self.base_folder_var.set("Nenhuma pasta selecionada")
            return
        self.base_folder_var.set(base_folder)

    def export_yolo(self):
        """ Opens file dialog and saves data in the selected format. """
        base_folder = self.base_folder_var.get()
        if base_folder == "Nenhuma pasta selecionada":
            return
        folder_name = self.folder_name_var.get()
        save_images = self.save_images_var.get()
        fullpath = Path(base_folder) / folder_name
        success = Config.api.io.export_yolo(
            fullpath,
            save_images
        )
        if success:
            TimeBombPopup(
                self.root,
                self,
                "Success",
                message="Success!",
                destroy_parent=True
            )
        else:
            TimeBombPopup(
                self.root,
                self,
                "Error",
                message="Erro ao exportar",
                destroy_parent=False
            )

        
    


# SECTION: Save as popup

class SaveAsPopup(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title("Choose Save Format")
        self.geometry("300x150")
        self.transient(root)  # Makes it modal
        self.grab_set()  # Disable interactions with main window
        # Label
        tk.Label(self, text="Select File Format:").pack(pady=5)
        # Combobox
        # Get the available formats from the API
        # list[(export style name, export extension)]
        self.formats_dict : dict[str, FileExtension] = \
              Config.api.io.get_report_output_formats()
        formats = list(self.formats_dict.keys())
        # Create the combobox
        self.format_type_var = tk.StringVar(value=formats[0])
        format_menu = ttk.Combobox(
            self,
            textvariable=self.format_type_var,
            values=formats,
            state="readonly"
        )
        format_menu.pack(pady=5)
        # Confirm button
        tk.Button(
            self,
            text="Procurar",
            command=self.save_as
        ).pack(pady=10)

    def save_as(self):
        """ Opens file dialog and saves data in the selected format. """
        exporter_name : str = self.format_type_var.get()
        format : FileExtension = self.formats_dict[exporter_name]
        filetypes = [
            (exporter_name, '*' + format.value)
        ]
        fullpaht = filedialog.asksaveasfilename(
            defaultextension="", filetypes=filetypes
        )

        if not fullpaht:
            return
              
        Config.api.io.save_report(
            Config.selected_test_type,
            fullpaht,
            exporter_name
        )
        


# SECTION: Progress popup

class ProgressPopup(tk.Toplevel):
    def __init__(self, root, thread_fuction, thread_args):
        super().__init__(root)
        self.root = root
        self.title("Aplicando pipeline")
        self.geometry("300x100")
        self.resizable(False, False)

        # Disable main window interactions
        self.transient(self.root)  # Keeps popup on top
        self.grab_set()  # Freezes main window

        # Label inside popup
        self.label = tk.Label(self, text="Aplicando pipeline...")
        self.label.pack(pady=10)

        # Label to show progress percentage
        self.progress_label = tk.Label(self, text="0%")
        self.progress_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack()

        # Handle popup closing
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start the long operation in a separate thread
        thread_args.insert(0, self)
        self.thread = threading.Thread(
            target=thread_fuction, args=thread_args, daemon=True
        )
        self.thread.start()



    def update_progress(self, img_name, value):
        if not self.running and not self.winfo_exists():
            return
        """Updates the progress bar safely from the main thread."""
        self.progress["value"] = value
        self.progress_label["text"] = f"{value:2f}%"
        self.label["text"] = img_name
        if value == 100:
            self.progress_label["text"] = "Done!"

    def on_close(self):
        self.running = False
        self.destroy()
