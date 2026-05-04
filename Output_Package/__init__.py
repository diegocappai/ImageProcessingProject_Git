from .folder_saver import FolderDataSetSaver
from .zip_saver import ZipDataSetSaver
from .json_dataset_saver import JsonDatasetSaver

def get_writer(method, output_path):
    if method == 'Cartella':
        return FolderDataSetSaver(output_path)
    elif method == 'JSON':
        return JsonDatasetSaver(output_path)
    else:
        raise ValueError(f"Metodo {method} non valido")


    # TODO Decidere se implementare metodo Zip
"""
    elif method == 'Zip':
        return ZipDataSetSaver(output_path)
        """