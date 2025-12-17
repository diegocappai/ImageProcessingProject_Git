import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Slot

# Import pagine della View per gestire i tipi di dati
from Interface_Package.views.page_setting_dataset import PageRequestDataset
from Interface_Package.views.page_setting_slide import PageRequestSlide
from Interface_Package.main_window import MainWindow, PageID

# Import del Model
from model import Model

# Import funzione di utilità per convertire oggetti PyVips
from Utils.pyvips_to_qpixmap import pyvips_to_qpixmap


class Controller(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)

        # Inizializzo il Model
        self.model = Model()
        # Inizializzo la View (Main Window)
        self.view = MainWindow()

        # === CABLAGGIO ===

        # Setup Segnali View
        self.view.richiesta_uscita.connect(lambda: self.termina_sessione("close"))

        # Setup Segnali page_start
        self.view.page_start.richiesta_start.connect(self.gestisci_start_setting)

        # Setup Segnali page_setting_dataset
        self.view.page_setting_dataset.richiesta_back.connect(self.back_home)
        self.view.page_setting_dataset.richiesta_play.connect(self.gestisci_play_dataset)

        # Setup Segnali page_setting_slide
        self.view.page_setting_slide.richiesta_back.connect(self.back_home)
        self.view.page_setting_slide.richiesta_play.connect(self.gestisci_play_slide)
        self.view.page_setting_slide.richiesta_set_grid.connect(self.gestisci_setting_grid)

        # Setup Segnali page_set_grid
        self.view.page_set_grid.richiesta_size.connect(self.imposta_size)



        # Setup Segnali page_show_patch
        self.view.page_show_patch.etichetta.connect(self.handle_save)
        self.view.page_show_patch.richiesta_salvataggio.connect(lambda: self.termina_sessione("salvataggio_parziale"))

        # Setup Segnali page_show_slide
        self.view.page_show_slide.estrai_patch.connect(self.estrai_patch)
        self.view.page_show_slide.etichetta.connect(self.handle_save)
        self.view.page_show_slide.richiesta_salvataggio.connect(lambda: self.termina_sessione("salvataggio_parziale"))

        # Setup Segnali dal Model
        self.model.patch_ready.connect(self.show_patch_in_view)
        self.model.session_finished.connect(lambda: self.termina_sessione("salvataggio completo"))
        self.model.error_occurred.connect(self.print_error)
        self.model.thumbnail_ready.connect(self.show_thumbnail_in_view)

        # Mostriamo finestra
        self.view.show()

    # Torna alla pagina di start
    def back_home(self):
        self.view.switch_page(PageID.START)

    # Gestione dati input iniziali
    @Slot(int, str)
    def gestisci_start_setting(self, method_input, output_path):

        # Cambio pagina in base al metodo di input
        if method_input == "Slide":
            self.view.switch_page(PageID.SET_SLIDE)
        elif method_input == "Dataset":
            self.view.switch_page(PageID.SET_DATASET)

        # Dizionario con i primi dati
        config = {
            'writer' : "Cartella", # Tipo di salvataggio (per ora inserito così) TODO ragionare su inserimento diverso
            'method_input' : method_input,
            'output_path' : output_path,
        }
        # Inizia a configurare il Model
        self.model.start_session(config)

    # Gestisce dati input da setting_dataset
    @Slot(object)
    def gestisci_play_dataset(self, data: PageRequestDataset):
        # Dizionario con dati per il Model
        config = {
            'manager' : "Cartella",
            'folder_path' : data.path_directory,
            'order_show' : data.order_show,
        }
        # Configura la sessione completa del Model e cambia pagina
        self.model.setup_session(config)
        self.view.switch_page(PageID.SHOW_PATCH)

    # Gestisce dati input da setting_slide
    @Slot(object)
    def gestisci_play_slide(self, data: PageRequestSlide):

        # Modalità visualizzazione Patch singole
        if data.method_show == "Patch":
            config = {
                'manager' : "PyVips",
                'input_path': data.path_slide,
                'tile_w': data.tile_w,
                'tile_h': data.tile_h,
                'method_show': data.method_show,
                'order_show': data.order_show
            }
            self.model.setup_session(config)
            self.view.switch_page(PageID.SHOW_PATCH)

        # Modalità visualizzazione Slide Intera
        elif data.method_show == "Slide":
                config = {
                    'manager' : "PyVips",
                    'input_path' : data.path_slide,
                    'tile_w' : data.tile_w,
                    'tile_h' : data.tile_h,
                    'method_show' : data.method_show
                }
                # Chiamiamo un metodo del model diverso
                self.model.setup_session_slide(config)
                self.view.switch_page(PageID.SHOW_SLIDE)


    # Gestisce selezione della dimensione della tile visivamente
    @Slot(int, int, str)
    def gestisci_setting_grid(self, w, h, thumbnail_path):
        self.view.page_set_grid.set_initial_size(w, h)
        # Chiede al model di preparare la thumbnail per la griglia
        self.model.setup_thumbnail_grid(thumbnail_path, 0)
        self.view.switch_page(PageID.SET_GRID)

    # Setta i valori impostati visivamente in page_set_grid
    @Slot(int, int)
    def imposta_size(self, w, h):
        self.view.page_setting_slide.menu_widht.setCurrentText(w)
        self.view.page_setting_slide.menu_height.setCurrentText(h)
        self.view.switch_page(PageID.SET_SLIDE)

    # Gestisce estrazione patch da coordinate doppio-click
    @Slot(int, int)
    def estrai_patch(self, coord_x, coord_y):
        # Recupero dimensioni reali slide
        real_w_image = self.model.manager.width
        real_h_image = self.model.manager.height

        # Recupero dimensioni thumbnail visualizzata a schermo
        thumb_w = self.view.page_show_slide.viewer_slide.original_pixmap.width()
        thumb_h = self.view.page_show_slide.viewer_slide.original_pixmap.height()

        # Calcolo fattore di scala
        ratio_x = real_w_image / thumb_w
        ratio_y = real_h_image / thumb_h

        # Converto le coordinate del click
        real_x = int(coord_x * ratio_x)
        real_y = int(coord_y * ratio_y)

        # Chiedo al Model di estrarre la vera patch
        patch = self.model.estrai_patch(real_x, real_y)

        # Converto e mostro TODO esiste già metodo show_patch_in_view ragionare
        pixmap = pyvips_to_qpixmap(patch)
        self.view.page_show_slide.mostra_patch(pixmap)

    # Chiamato quando il model emette il segnale 'patch_ready'
    @Slot(object)
    def show_patch_in_view(self, patch):
        """Riceve l'immagine raw dal Model, converte e mostra."""
        pixmap = pyvips_to_qpixmap(patch)
        self.view.page_show_patch.mostra_patch(pixmap)

    # Chiamato quando il Model ha generato la thumbnail della slide intera
    @Slot(object)
    def show_thumbnail_in_view(self, thumbnail_obj, w_original, h_original, index):
        pixmap = pyvips_to_qpixmap(thumbnail_obj)
        # index 0 serve per visualizzare nella pagina page_set_grid
        if index == 0:
            self.view.page_set_grid.set_thumbnail(pixmap, w_original, h_original)
        # index 1 serve per visualizzare nella pagina page_show_slide
        elif index ==1:
            self.view.page_show_slide.set_thumbnail(pixmap, w_original, h_original, self.model.manager.tile_w, self.model.manager.tile_h)

    # Gestisce salvataggio etichetta quando utente preme bottone
    @Slot(str)
    def handle_save(self, etichetta):
        # Delega al Model il salvataggio dei dati (CSV)
        self.model.save_annotation(etichetta)
        # TODO ragionare su visualizzazione loading...
        #self.view.page_show_slide.viewer_patch.mostra_loading()

    @Slot(str)
    def termina_sessione(self, mode):
        # Chiude i file aperti nel Model (writer)
        self.model.close_session()

        if mode == "close":
            pass # L'app si chiude in automatico all'evento close
        # Caso salvataggio durante etichettatura
        elif mode == "salvataggio_parziale":
            self.view.show_info_message("Dati salvati corretamente!")
            self.view.switch_page(PageID.START)
        # Caso salvataggio per termine etichettatura
        elif mode == "salvataggio_completo":
            self.view.show_info_message("Dataset completato!\n Dati salvati corretamente.")
            self.view.switch_page(PageID.START)


    def print_error(self, errore):
        print(f"Errore {errore}")


    def run(self):
        sys.exit(self.app.exec())