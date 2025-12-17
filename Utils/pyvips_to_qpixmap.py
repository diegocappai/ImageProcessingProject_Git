from PySide6.QtGui import QImage, QPixmap


def pyvips_to_qpixmap(patch):
    """
    Converte un oggetto pyvips.Image in QPixmap per PySide6.
    """
    # --- FIX CRUCIALE PER "OUT OF ORDER READ" ---
    # Questo comando forza libvips a leggere i dati dal file, decodificarli
    # e copiarli in un blocco di RAM sicuro.
    # Disaccoppia la patch dal file originale JPEG/WSI.
    vips_image = patch.copy_memory()
    # --------------------------------------------

    # Gestione canali e formato (Cast a 8-bit per sicurezza)
    if vips_image.format != 'uchar':
        vips_image = vips_image.cast('uchar')
    # Assicuriamoci che l'immagine sia in formato gestibile (RGB)
    # A volte PyVips usa formati complessi, convertiamo in sRGB standard
    if vips_image.bands > 3:
        # Se ha il canale Alpha, teniamolo, altrimenti appiattiamo
        vips_image = vips_image.flatten()

    # Scriviamo i dati in un buffer di memoria (bytes)
    # Questo è il passaggio chiave: PyVips -> Bytes
    memory_buffer = vips_image.write_to_memory()

    # Leggiamo le dimensioni
    width = vips_image.width
    height = vips_image.height
    bands = vips_image.bands  # Canali (3 per RGB, 1 per Grigio)

    # Creiamo la QImage dai bytes
    # Attenzione ai formati:
    if bands == 3:
        format_img = QImage.Format_RGB888
    elif bands == 4:
        format_img = QImage.Format_RGBA8888
    elif bands == 1:
        format_img = QImage.Format_Grayscale8
    else:
        # Fallback: forziamo a sRGB se ha formati strani
        vips_image = vips_image.colourspace('srgb')
        memory_buffer = vips_image.write_to_memory()
        format_img = QImage.Format_RGB888
        bands = 3

    # Calcoliamo i bytes per linea (stride)
    bytes_per_line = width * bands

    # Creiamo la QImage
    q_img = QImage(memory_buffer, width, height, bytes_per_line, format_img)

    # IMPORTANTE: .copy()
    # QImage di default punta al buffer originale. Se PyVips libera la memoria,
    # Qt crasha. .copy() crea una copia sicura dei dati per l'interfaccia.
    return QPixmap.fromImage(q_img.copy())