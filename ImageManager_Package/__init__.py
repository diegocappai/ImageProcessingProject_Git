
def get_manager(method, file_path, tile_w, tile_h):
    if method == 'PyVips':
        from .pyvips_manager_module import VipsImageManager
        return VipsImageManager(file_path, tile_w, tile_h)

    # TODO decidere se implementare secondo metodo:
    """
    elif method == 'method_2':
        from .method2_manager_module import Method2ImageManager
        return Method2ImageManager(file_path, tile_w, tile_h)
    """
    else:
        raise ValueError(f"Metodo {method} non supportato")