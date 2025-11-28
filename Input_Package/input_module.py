import tkinter as tk
from tkinter import filedialog


def scegli_file_svs():
    """Apre una finestra di dialogo per selezionare un file .svs
    e restituisce il percorso selezionato come stringa."""

    # Crea finestra Tkinter invisibile (solo per usare il file dialog)
    root = tk.Tk()
    root.withdraw()  # Nasconde la finestra principale
    root.update()

    percorso = filedialog.askopenfilename(
        title="Seleziona un file .svs",
        filetypes=[("File SVS", "*.svs"), ("Tutti i file", "*.*")]
    )

    root.destroy()  # Chiude Tkinter

    # Restituisce il percorso (stringa vuota se l’utente annulla)
    return percorso
