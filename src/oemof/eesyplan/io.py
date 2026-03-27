import tempfile
import zipfile
from tkinter import Tk
from tkinter import ttk


def unzip_package(zip_path, ext_path=None):
    """
    Extract a zip file to a temporary directory.

    Returns:
        TemporaryDirectory object (caller must manage cleanup)
    """
    if ext_path is None:
        ext_path = tempfile.TemporaryDirectory()

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(ext_path.name)

    return ext_path


def select_value(choices) -> str:
    selected_value = "None"

    def on_select(event):
        nonlocal selected_value
        selected_value = combo.get()
        root.destroy()

    # Create window
    root = Tk()
    root.title("Model Selection")
    root.geometry("450x80")

    # Dropdown
    ttk.Label(root, text="Select a model:").pack(pady=(15, 5))
    combo = ttk.Combobox(root, values=choices, width=50, state="readonly")
    combo.pack()
    combo.bind("<<ComboboxSelected>>", on_select)

    root.mainloop()

    return selected_value
