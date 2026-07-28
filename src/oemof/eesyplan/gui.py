try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None
    ttk = None


def select_value(choices) -> str:
    if tk is None:
        raise ImportError("Tkinter not installed. Try 'pip install tkinter'")

    selected_value = None

    def on_select(event):
        nonlocal selected_value
        selected_value = combo.get()
        root.destroy()

    root = tk.Tk()
    root.title("Model Selection")
    root.geometry("450x80")

    ttk.Label(root, text="Select a model:").pack(pady=(15, 5))
    combo = ttk.Combobox(root, values=choices, width=50, state="readonly")
    combo.pack()
    combo.bind("<<ComboboxSelected>>", on_select)

    root.mainloop()

    return selected_value if selected_value is not None else "None"
