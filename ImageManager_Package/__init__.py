
def get_manager(method, input_path, tile_w=0, tile_h=0):
    if method == 'PyVips':
        from ImageManager_Package.Slide_Manager.pyvips_slide_manager import VipsSlideManager
        return VipsSlideManager(input_path, tile_w, tile_h)
    elif method == 'Dataset':
        from ImageManager_Package.Dataset_Manager.vips_dataset_manager import VipsDatasetManager
        return VipsDatasetManager(input_path)
    else:
        raise ValueError(f"Metodo {method} non supportato")

        # TODO decidere se implementare secondo metodo (TiffSlide):
    """
    elif method == 'method_2':
        from .method2_manager_module import Method2ImageManager
        return Method2ImageManager(file_path, tile_w, tile_h)
    """