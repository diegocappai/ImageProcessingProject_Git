from PySide6.QtCore import QObject, Signal
from ImageManager_Package import get_manager
from Output_Package import get_writer



class Model(QObject):

    patch_ready = Signal(object)
    thumbnail_ready = Signal(object, int, int, int)
    session_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.method_input = None  # "Dataset" o "Slide"
        self.manager = None
        self.writer = None
        self.patch_generator = None
        self.method_show = None # Metodo visulizzazione "Patch" o "Slide"

        # Variabili temporanee per l'elemento corrente
        self.current_patch = None  # L'oggetto immagine (PyVips)
        self.current_meta = None  # Filename (per Dataset) o Coords (per Slide)
        self.ID_paziente = "Unknown"  # Solo per Slide

   # Settaggio iniziale model e writr
    def start_session(self, config):
        self.writer = get_writer(config['writer'], config['output_path']) #TODO valutare se inizializzare qui o più tardi (apre file .csv)
        self.method_input = config['method_input']

    # Settaggio sessione per visualizzazione in patch (Dataset/Slide)
    def setup_session(self, config):
        # Riceve un dizionario config con tutti i dati raccolti

        try:

            if self.method_input == "Dataset":
                self.manager = get_manager(config['manager'], config['folder_path'])
            elif self.method_input == "Slide":
                self.manager = get_manager(config['manager'],config['input_path'], int(config['tile_w']),
                                           int(config['tile_h']))
                self.method_show = config['method_show']
                self.ID_paziente = "DIEE"

            # Setup Generatore Patch
            self.patch_generator = self.manager.extract_iterator_patches(config['order_show'])

            # Avvio Writer
            self.writer.__enter__()

            # Carichiamo la prima patch
            self.next_patch()

        except Exception as e:
            print(f"errore setup:{e}")
            self.error_occurred.emit(str(e))

    # Settaggio sessione per visualizzazione slide intera
    def setup_session_slide(self, config):
        try:
            self.manager = get_manager(config['manager'], config['input_path'], int(config['tile_w']),
                                   int(config['tile_h']))
            self.ID_paziente = "DIEE" #TODO ragionare su diversa modalità inserimento e se necessario
            self.method_show = config['method_show']

            self.writer.__enter__()
            # Indice 1 per identificare che ci serve in page_show_slide TODO ragionare su metodo più scalabile
            self.setup_thumbnail_slide(1)


        except Exception as e:
            print(f"errore setup:{e}")

    # Generazione thumbnail per slide
    def setup_thumbnail_slide(self, index):
        original_w = self.manager.width
        original_h = self.manager.height
        thumbnail = self.manager.load_thumbnail_rgb()
        self.thumbnail_ready.emit(thumbnail, int(original_w), int(original_h), index)

    # Generazione thumbnail per griglia impostazione grandezza tile
    def setup_thumbnail_grid(self, thumbnail_path, index):
        self.manager = get_manager('PyVips', thumbnail_path, tile_w=0, tile_h=0)
        original_w =self.manager.width
        original_h =self.manager.height
        thumbnail = self.manager.load_thumbnail_rgb()
        self.thumbnail_ready.emit(thumbnail, int(original_w), int(original_h), index)

    #TODO ragione bene su setup_thumbnail_slide e setup_thumbnail_grid

    # Estrazione patch singola
    def estrai_patch(self, coord_x, coord_y):
        self.current_meta = self.manager.find_tile_coords(coord_x, coord_y)
        self.current_patch = self.manager.extract_patch(self.current_meta)
        return self.current_patch

    # Prende prossima patch dal generatore (Dataset o Coords)
    def next_patch(self):

        try:
            while True:
                item = next(self.patch_generator)

                # Caso input da Dataset
                if self.method_input == "Dataset":
                    patch, filename = item
                    self.current_patch = patch
                    self.current_meta = filename

                # Caso input da Slide
                elif self.method_input == "Slide":
                    patch, coords = item
                    self.current_patch = patch
                    self.current_meta = coords

                # Verifica tessuto patch
                if self.manager.is_patch_valid(self.current_patch, min_tissue_percent=0.5):
                    print(f"PATCH ACCETTATA! Coordinate: {self.current_meta}") # <--- DEBUG
                    self.patch_ready.emit(self.current_patch)
                    return

                else:
                    # --- DEBUG  ---
                    print(f"Patch scartata (vuota) a {self.current_meta}")
                    # ---------------



        except StopIteration:
            self.close_session()
            self.session_finished.emit()
        except Exception as e:
            print("errore in next patch (model)")
            self.error_occurred.emit(str(e))

    # Chiamato quando l'utente "etichetta"
    def save_annotation(self, label):
        if not self.writer or not self.current_patch:
            return

        try:
            patch = self.current_patch

            if self.method_input == "Dataset":
                fname = self.current_meta
                self.writer.save_file_Dataset(fname, label)
                self.next_patch()


            elif self.method_input == "Slide":
                coords = self.current_meta
                self.writer.save_patch_WSI(patch, coords, label, self.ID_paziente)
                if self.method_show == "Slide":
                    pass
                elif self.method_show == "Patch":
                    self.next_patch()


        except Exception as e:
            self.error_occurred.emit(str(e))

    def close_session(self):
        if self.writer:
            self.writer.__exit__(None, None, None)  # Chiudiamo il writer (salva file .csv)
            self.writer = None



