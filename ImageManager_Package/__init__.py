
def get_manager(method, input_path, tile_w=0, tile_h=0):
    if method == 'Slide':
        from ImageManager_Package.Slide_Manager.pyvips_slide_manager import VipsSlideManager
        return VipsSlideManager(input_path, tile_w=tile_w, tile_h=tile_h)
    elif method == 'Folder':
        from ImageManager_Package.Dataset_Manager.vips_dataset_manager import VipsDatasetManager
        return VipsDatasetManager(input_path)
    else:
        raise ValueError(f"Metodo input {method} non supportato")

