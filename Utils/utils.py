import os


def crea_cartella_univoca(percorso_base, nome_progetto):
    """Crea una cartella. Se esiste già, aggiunge (1), (2), ecc."""
    percorso_finale = os.path.join(percorso_base, nome_progetto)
    nome_finale = nome_progetto
    contatore = 1

    while os.path.exists(percorso_finale):
        nome_finale = f"{nome_progetto} ({contatore})"
        percorso_finale = os.path.join(percorso_base, nome_finale)
        contatore += 1

    os.makedirs(percorso_finale)
    return percorso_finale, nome_finale