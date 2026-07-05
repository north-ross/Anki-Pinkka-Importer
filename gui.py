from aqt import mw
from aqt.qt import *
from aqt.operations import QueryOp
from aqt.utils import showInfo
from .pinkka2anki import getPinkkaDeckID, get_all_species_ids, create_anki_deck
import time

class PinkkaImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Pinkka Deck")
        self.setGeometry(100, 100, 500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Pinkka Importer")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Input fields section
        layout.addWidget(self.create_input_section())
        
        # Options section
        # layout.addWidget(self.create_options_section())
        
        # Progress section
        # layout.addWidget(self.create_progress_section())
        
        # Buttons section
        layout.addLayout(self.create_button_section())
        
        self.setLayout(layout)

    def create_input_section(self):
        """Create text input fields for Pinkka ID and deck name"""
        group = QGroupBox("Input")
        layout = QFormLayout()
        
        # Pinkka URL input
        self.pinkka_id_input = QLineEdit()
        self.pinkka_id_input.setPlaceholderText("e.g., https://pinkka.laji.fi/pinkat/#/pinkkas/8")
        layout.addRow("Pinkka Deck URL:", self.pinkka_id_input)
        
        # Deck name input
        self.deck_name_input = QLineEdit()
        self.deck_name_input.setPlaceholderText("e.g., IPS-153 Flora of Subarctic Europe")
        layout.addRow("Deck Name:", self.deck_name_input)

        # self.lang_input = QHBoxLayout() # This should be replaced with a dropdown or something
        # self.images_number_input = QLineEdit()
        # image_size = self.input_field.text() # This should also be a dropdown

        group.setLayout(layout)
        return group

    def create_button_section(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Import button
        self.import_button = QPushButton("Import")
        self.import_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.import_button.clicked.connect(self.on_import_clicked)
        layout.addWidget(self.import_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        return layout

    def species_list_success(self, species_list) -> None:
        showInfo(f"Found {len(species_list)} species")

    def on_import_clicked(self):
        # Parameters:
        pinkka_id = getPinkkaDeckID(self)

        species_ids = QueryOp(
            # the active window (main window in this case)
            parent=mw,
            # the operation is passed the collection for convenience; you can
            # ignore it if you wish
            op=get_all_species_ids(pinkka_id),
            # this function will be called if op completes successfully,
            # and it is given the return value of the op
            success = PinkkaImportDialog.species_list_success()
        )
        species_ids.with_progress().run_in_background()

        notes = QueryOp(
            # the active window (main window in this case)
            parent=mw,
            # the operation is passed the collection for convenience; you can
            # ignore it if you wish
            op=lambda species_ids: create_anki_deck(self.mw.col, species_ids),  # add arguments
            # Write to Anki database,
            success = showInfo("Successfully downloaded data and created deck")
        )
        notes.with_progress().run_in_background()