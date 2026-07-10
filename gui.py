from aqt import mw
from aqt.qt import *
from aqt.operations import QueryOp
from aqt.utils import showInfo
from .pinkka2anki import getPinkkaDeckID, get_all_species_ids, create_note_list, create_anki_deck
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
        layout.addWidget(self.create_options_section())
        
        # Progress section
        layout.addWidget(self.create_progress_section())
        
        # Buttons section
        layout.addLayout(self.create_button_section())
        
        self.setLayout(layout)

    def create_input_section(self):
        """Create text input fields for Pinkka ID and deck name"""
        group = QGroupBox("Input")
        layout = QFormLayout()
        
        # Pinkka URL input
        self.text_url = QLineEdit()
        self.text_url.setPlaceholderText("e.g., https://pinkka.laji.fi/pinkat/#/pinkkas/8")
        layout.addRow("Pinkka Collection URL:", self.text_url)
        
        # Deck name input
        self.deck_name_input = QLineEdit()
        self.deck_name_input.setPlaceholderText("e.g., IPS-153 Flora of Subarctic Europe")
        layout.addRow("Deck Name:", self.deck_name_input)

        group.setLayout(layout)
        return group

    def create_options_section(self):
        """Create additional inputs for config options"""
        group = QGroupBox("Options")
        layout = QFormLayout()

        # max number of images to download
        self.images_number_input = QSpinBox()
        self.images_number_input.setRange(1,20)
        self.images_number_input.setValue(4)
        self.images_number_input.setToolTip("Max number of images per species to download.")
        layout.addRow("Number of Images (max):", self.images_number_input)

        # Image size (resolution)
        self.image_size = QComboBox()
        self.image_size.addItems(['square (~30kB)', 'large (~80 kB)', 'thumb (~10kB)'])
        self.image_size.setToolTip("Image resolution options. \"Square\" is usually sufficient for flashcards")
        layout.addRow("Image size:", self.image_size)

        # Which common name to include on flashcard
        self.common_name_input = QComboBox()
        self.common_name_input.addItems(['Finnish Name', 'Swedish Name', 'English Name', 'None'])
        self.common_name_input.setToolTip(
            "You can edit the template later to include multiple. Note that many collection have no English names in Pinkka.")
        layout.addRow("Common name to include on card:", self.common_name_input)


        self.lang_input = QComboBox()
        self.lang_input.addItems(['en', 'fi', 'sv'])
        self.lang_input.setToolTip(
            "Language to use for the taxonomic rank in the tags, e.g. family/heimo/familj")
        layout.addRow("Language for taxonomy tags:", self.lang_input)

        #TODO: Add these more options:
        # self.get_back_images = QCheckBox()
        # layout.addRow("Get half the images from the end of the list?", self.get_back_images)
        
        # self.subpinkka_tag = QCheckBox("", self) # include SubPinkka name as tag?
        # Choose which taxonomy levels to include as tags?

        group.setLayout(layout)
        return group

    def create_button_section(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Import button
        self.import_button = QPushButton("Import")
        self.import_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.import_button.clicked.connect(self.on_import_clicked)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(False)  # Disabled until import completes

        layout.addWidget(self.import_button)
        layout.addWidget(self.close_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        return layout

    def create_progress_section(self):
        group = QGroupBox("Progress & Log")
        layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Status")
        #self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("background-color: #f5f5f5; font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_display)
        
        group.setLayout(layout)
        return group

    def import_species(self, pinkka_id):
        """Fetch species IDs, then create notes from them."""
        
        def on_species_ids_fetched(species_ids):
            """Called when get_all_species_ids() completes."""
            self.status_label.setText(f"Found {len(species_ids)} species")
            
            # Now start the second operation with the result from the first
            QueryOp(
                parent=mw,
                op=lambda col: create_note_list(self, species_ids),
                success=lambda result: self.on_list_created(result)
            ).with_progress().run_in_background()
        
        # First operation: fetch species IDs
        QueryOp(
            parent=mw,
            op=lambda col: get_all_species_ids(self, pinkka_id),
            success=on_species_ids_fetched  # Pass the callback function
        ).with_progress().run_in_background()

    def on_list_created(self, note_list):
        """Called when create_note_list() completes."""
        create_anki_deck(self, note_list)

        # Update UI to show completion
        self.status_label.setText("✅ Import completed successfully!")
        self.progress_bar.setValue(100)

        # Refresh deck browser
        mw.deckBrowser.refresh()
        
        # Disable import button, enable close button
        self.import_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.close_button.setFocus()
        
    def on_import_clicked(self):
        # Parameters:
        pinkka_id = getPinkkaDeckID(self)
        self.import_species(pinkka_id)
