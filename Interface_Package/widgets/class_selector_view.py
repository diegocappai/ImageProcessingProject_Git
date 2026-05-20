from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QCheckBox, QLineEdit, QPushButton, QGridLayout, QMessageBox)


class ClassSelectorWidget(QWidget):
    """
    Componente UI riutilizzabile per la selezione e creazione dinamica di classi di etichettatura.
    """

    def __init__(self, default_classes=None, parent=None):
        super().__init__(parent)
        self.checkboxes = []
        self.default_classes = default_classes or ["Normale", "Tumore", "Stroma", "Necrosi"]
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Nessun margine perché sarà iniettato in altri layout

        labels_title = QLabel("<b>Classi di Etichettatura Richieste:</b>")
        layout.addWidget(labels_title)

        # Griglia per le classi
        self.grid_labels = QGridLayout()
        for i, class_name in enumerate(self.default_classes):
            self._add_checkbox(class_name, i)
        layout.addLayout(self.grid_labels)

        custom_layout = QHBoxLayout()
        self.input_custom = QLineEdit()
        self.input_custom.setPlaceholderText("Aggiungi classe personalizzata...")

        self.input_custom.returnPressed.connect(self.aggiungi_classe)

        btn_add = QPushButton("+ Aggiungi")
        btn_add.clicked.connect(self.aggiungi_classe)

        custom_layout.addWidget(self.input_custom)
        custom_layout.addWidget(btn_add)
        layout.addLayout(custom_layout)

    def _add_checkbox(self, name: str, index: int, checked: bool = None):
        """Utility interna per posizionare le checkbox nella griglia"""
        cb = QCheckBox(name)

        stato_finale = checked if checked is not None else (index < 2)
        cb.setChecked(stato_finale)

        cb.clicked.connect(self.verifica_limite_spunte)
        self.checkboxes.append(cb)
        self.grid_labels.addWidget(cb, index // 2, index % 2)  # 2 colonne automatiche

    def aggiungi_classe(self):
        """Logica di validazione e aggiunta"""
        testo = self.input_custom.text().strip()
        if not testo: return

        # Controllo limite massimo
        if len(self.get_selected_classes()) >= 9:
            QMessageBox.warning(self, "Limite Raggiunto",
                                "Hai già 9 etichette attive! Deseleziona almeno un classe esistente prima di aggiungerne una nuova.")
            return

        esistenti = [cb.text().lower() for cb in self.checkboxes]
        if testo.lower() in esistenti:
            QMessageBox.information(self, "Classe Esistente", "Questa classe è già presente.")
            return

        self._add_checkbox(testo, len(self.checkboxes), checked=True)
        self.input_custom.clear()

    def get_selected_classes(self) -> list:
        """API pubblica del componente: restituisce le classi scelte"""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]

    def verifica_limite_spunte(self):
        if len(self.get_selected_classes()) <= 9:
            return

        QMessageBox.warning(self,"Limite Massimo", "Puoi selezionare massimo 9 etichette.")

        checkbox_sel = self.sender()
        if checkbox_sel:
            checkbox_sel.blockSignals(True)
            checkbox_sel.setChecked(False)
            checkbox_sel.blockSignals(False)