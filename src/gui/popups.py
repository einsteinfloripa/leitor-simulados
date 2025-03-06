import tkinter as tk
from tkinter import ttk, filedialog
import threading
from pathlib import Path

from gui import Config, semititle_font
from api.sync_channel import ProgressTracker

class TimeBombPopup(tk.Toplevel):
    """
    A temporary popup window that auto-closes after a set timer.

    Parameters
    ----------
    root : tk.Tk
        The root application window.
    parent : tk.Widget
        The parent widget that created this popup.
    title : str
        Title of the popup window.
    message : str
        Message to display in the popup.
    timer : int, optional
        Time (in seconds) before the popup auto-closes (default is 3 seconds).
    destroy_parent : bool, optional
        Whether to destroy the parent widget upon closing (default is False).
    """
    def __init__(self, root, parent, title, message, timer=3, destroy_parent=False):
        super().__init__(root)
        self.title(title)
        self.destroy_parent = destroy_parent
        self.timer = timer
        self.parent = parent
        self.root = root
        self.geometry("200x100")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=message).pack(pady=10)
        tk.Button(self, text="OK", command=self.destroy).pack(pady=10)
        self.after(timer * 1000, self.destroy)

    def destroy(self):
        """Closes the popup and optionally destroys the parent widget."""
        super().destroy()
        if self.destroy_parent:
            self.parent.destroy()


class ExportYoloPopup(tk.Toplevel):
    """
    A popup window to configure and export YOLO-formatted data.

    Parameters
    ----------
    root : tk.Tk
        The root application window.
    """
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title("Exportar YOLO")
        self.geometry("350x200")
        self.resizable(False, False)
        self.transient(root)
        self.grab_set()
        
        tk.Label(self, text="Selecione a pasta de destino:", font=semititle_font).grid(row=0, column=0, columnspan=2, pady=5)
        
        self.base_folder_var = tk.StringVar(value="Nenhuma pasta selecionada")
        self.folder_label = tk.Label(self, textvariable=self.base_folder_var)
        self.folder_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        tk.Button(self, text="Procurar", command=self.select_base_folder).grid(row=2, column=0, pady=5, padx=5)
        
        self.save_images_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Salvar imagens", variable=self.save_images_var).grid(row=2, column=1, pady=5, padx=5)
        
        tk.Label(self, text="Nome da pasta:", font=semititle_font).grid(row=3, column=0, pady=5, padx=5)
        
        self.folder_name_var = tk.StringVar(value="detections")
        tk.Entry(self, textvariable=self.folder_name_var).grid(row=3, column=1, pady=5, padx=5)
        
        tk.Button(self, text="Exportar", command=self.export_yolo, width=25).grid(row=4, columnspan=2, column=0, pady=5)

    def select_base_folder(self):
        """Opens a file dialog to select the base folder for export."""
        base_folder = filedialog.askdirectory()
        self.base_folder_var.set(base_folder or "Nenhuma pasta selecionada")

    def export_yolo(self):
        """Exports data in YOLO format to the selected directory."""
        base_folder = self.base_folder_var.get()
        if base_folder == "Nenhuma pasta selecionada":
            return
        folder_name = self.folder_name_var.get()
        save_images = self.save_images_var.get()
        fullpath = Path(base_folder) / folder_name
        success = Config.api.export_yolo(fullpath, save_images)
        
        title = "Success" if success else "Error"
        message = "Exported successfully!" if success else "Error exporting data"
        TimeBombPopup(self.root, self, title, message, destroy_parent=success)


class SaveAsPopup(tk.Toplevel):
    """
    A popup window for selecting a file format and saving a report.

    Parameters
    ----------
    root : tk.Tk
        The root application window.
    """
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title("Choose Save Format")
        self.geometry("300x150")
        self.transient(root)
        self.grab_set()
        
        tk.Label(self, text="Select File Format:").pack(pady=5)
        
        self.formats_dict = Config.api.get_report_output_formats()
        formats = list(self.formats_dict.keys())
        
        self.format_type_var = tk.StringVar(value=formats[0])
        format_menu = ttk.Combobox(self, textvariable=self.format_type_var, values=formats, state="readonly")
        format_menu.pack(pady=5)
        
        tk.Button(self, text="Procurar", command=self.save_as).pack(pady=10)

    def save_as(self):
        """Opens a file dialog and saves the report in the selected format."""
        exporter_name = self.format_type_var.get()
        format_ext = self.formats_dict[exporter_name]
        filetypes = [(exporter_name, '*' + format_ext.value)]
        fullpath = filedialog.asksaveasfilename(defaultextension="", filetypes=filetypes)
        
        if fullpath:
            try:
                Config.api.save_report(fullpath, exporter_name)
                TimeBombPopup(self.root, self, "Success", "Report saved successfully!", destroy_parent=True)
            except Exception as e:
                TimeBombPopup(self.root, self, "Error", str(e), destroy_parent=False)
                raise e

class ProgressPopup(tk.Toplevel):
    """
    A popup window displaying a progress bar for long-running tasks.

    Parameters
    ----------
    root : tk.Tk
        The root application window.
    thread_function : callable
        The function to execute in a separate thread.
    thread_args : list
        Arguments to pass to the thread function.
    """
    def __init__(
            self,
            root,
            thread_function,
            thread_args,
            progress_tracker,
            img_files
        ):
        super().__init__(root)
        self.root = root
        self.title("Aplicando pipeline")
        self.geometry("300x100")
        self.resizable(False, False)
        self.transient(self.root)
        self.grab_set()
        
        self.__init_widgets()
        
        self.names = [Path(img_file).name for img_file in img_files]
        self.float_interval = 100 / len(self.names)
        self.progress_tracker : ProgressTracker = progress_tracker
        self.protocol("WM_DELETE_WINDOW", self.__on_close)
        
        # Start the worker and waching thread
        self.thread = threading.Thread(
            target=thread_function, args=thread_args, daemon=True
        )
        self.waching_thread = threading.Thread(
            target=self.__update_progress, daemon=True
        )
        self.thread.start()
        self.waching_thread.start()


    def __init_widgets(self):
        """Initializes the widgets in the popup window."""
        self.label = tk.Label(self, text="Aplicando pipeline...")
        self.label.pack(pady=10)
        
        self.progress_label = tk.Label(self, text="0%")
        self.progress_label.pack()
        
        self.progress = ttk.Progressbar(
            self, orient="horizontal", length=300, mode="determinate"
        )
        self.progress.pack()

    def __update_progress(self):
        """Updates the progress bar safely from the main thread."""
        
        while True:
            # get_step() is a blocking call
            step = self.progress_tracker.get_step()

            if not self.progress_tracker.running():
                break
            elif self.progress_tracker.is_finished():
                self.progress["value"] = 100.0
                self.progress_label["text"] = "100%"
                self.label["text"] = "Concluido!"
                break

            value = self.float_interval * step
            name = self.names[step]

            self.progress["value"] = value
            self.progress_label["text"] = f"{value:.2f}%"
            self.label["text"] = name


    def __on_close(self):
        """Handles the popup closing event."""
        self.progress_tracker.shutdown()
        self.destroy()