from .folder_saver import FolderDataSetSaver
from .zip_saver import ZipDataSetSaver

def get_writer(method, output_path):
    if method == 'Cartella':
        return FolderDataSetSaver(output_path)

    # TODO Decidere se implementare metodo Zip
    """
    elif method == 'Zip':
        return ZipDataSetSaver(output_path)
        """

    else:
        raise ValueError(f"Metodo {method} non valido")