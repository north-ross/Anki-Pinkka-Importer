import time
import json
from pathlib import Path
import urllib
import re
import requests
from aqt import mw
from aqt.qt import QMessageBox
from datetime import datetime

BASE_URL = "https://fmnh-ws-prod3.it.helsinki.fi/pinkka/api"
TESTING = False # set to true to just fetch the first four cards

def add_log_message(self, message, level="INFO"):
    """Generate timestamped log message

    Args:
        message (str): String to add to log
        level (str, optional): Level of severity (affects color). 
            Options: "INFO", "WARNING", "ERROR", "SUCCESS". Defaults to "INFO".
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": "black", "WARNING": "orange", "ERROR": "red", "SUCCESS": "green"}
    color = colors.get(level, "black")
    
    log_text = f'<span style="color: {color};">[{timestamp}] {level}: {message}</span>'
    self.log_display.append(log_text)
    self.log_display.verticalScrollBar().setValue(
        self.log_display.verticalScrollBar().maximum()
    )

# Get Pinkka ID, adapted from Quizlet plugin
def getPinkkaDeckID(self):
    # grab url input
    url = self.text_url.text()

    # validate quizlet URL
    if url == "":
        QMessageBox.critical(
            self,
            "Invalid Input",
            "You forgot the deck URL"
        )
        return
    elif not "pinkka.laji.fi" in url:
        QMessageBox.critical(
            self,
            "Invalid Input",
            "Not a Pinkka URL:\n" + url
        )
        return
    elif not re.search(r"https://pinkka.laji.fi/pinkat/#/pinkkas/[\d]+", url):
        print("Failed regex")
        QMessageBox.critical(
            self,
            "Invalid Input",
            "Please use the URL for the Pinkka collection e.g.\nhttps://pinkka.laji.fi/pinkat/#/pinkkas/8. You entered:\n" + url
        )
        return

    # validate and set Pinkka deck ID
    pinkkaDeckID = url.rsplit("/", 1)[-1]
    print(pinkkaDeckID)

    if pinkkaDeckID == "":
        QMessageBox.critical(
            self,
            "Invalid Input",
            "There was some problem with your URL. Enter e.g.\nhttps://pinkka.laji.fi/pinkat/#/pinkkas/8. You entered:\n" + url
        )
        return
    return pinkkaDeckID

# Create Anki model (front: image, back: species name)
# adapted from "Quizlet Plugin for Anki"
def add_custom_model(self, col):
    """Creates or updates existing Anki model

    Args:
        col (anki.collection.Collection): Current Anki collection (mw.col)

    Returns:
        _type_: Anki model object (NotetypeDict?)
    """

    # create custom model for imported deck
    mm = col.models
    existing = mm.by_name("Pinkka Importer")
    if existing:
        return existing
    m = mm.new("Pinkka Importer")

    # add fields
    mm.addField(m, mm.new_field("Species Name"))
    mm.addField(m, mm.new_field("Images"))
    mm.addField(m, mm.new_field("Family"))
    mm.addField(m, mm.new_field("Finnish Name"))
    mm.addField(m, mm.new_field("Swedish Name"))
    mm.addField(m, mm.new_field("English Name"))
    mm.addField(m, mm.new_field("Pinkka URL"))
    mm.addField(m, mm.new_field("Notes"))
    
    # add cards
    t = mm.new_template("ImageFront")

    # Choose which common name to show
    common_name_text = str(self.common_name_input.currentText())
    if common_name_text != "None":
        common_name_tag = "<br>{{" + common_name_text + "}}"
    else:
        common_name_tag = ""

    # front
    t['qfmt'] = "{{Images}}"
    t['afmt'] = '{{FrontSide}}<hr id="answer">'+\
        '<i><u><a href="{{Pinkka URL}}" style="color:white;">{{Species Name}}</a></u></i>'+\
        '<br><b>{{Family}}</b>'+common_name_tag+'<br>{{Notes}}'
    mm.addTemplate(m, t)
    mm.add(m)
    return m

def get_all_species_ids(self, pinkka_id):
    """Fetch all species IDs and sub name from a pinkka and its subPinkkas
    Returns a nested list with pairs of values (species ID, subPinkka name)"""

    self.status_label.setText(f"Getting species list")
    # Get the list of sub pinkkas
    pinkka_response = requests.get(f"{BASE_URL}/pinkkas/{pinkka_id}", timeout=120)
    pinkka_data = pinkka_response.json()
    
    sub_pinkkas = pinkka_data.get('subPinkkas', [])
    add_log_message(self, f"Found {len(sub_pinkkas)} subPinkkas")
    
    all_taxon_ids = []
    
    # Step 2: Loop through each subPinkka
    last_progress = datetime.now()
    for sub_pinkka in sub_pinkkas:
        sub_id = sub_pinkka['id']
        sub_name = sub_pinkka['name'].get('en', sub_pinkka['name'].get('fi', 'Unknown'))
        
        # Step 3: Get species from this subPinkka
        sub_response = requests.get(f"{BASE_URL}/subpinkkas/{sub_id}", timeout=120)
        sub_data = sub_response.json()

        # Extract species/taxon IDs (adjust key name based on actual JSON structure)
        species_in_sub = sub_data.get('speciesCards', [])  # or 'species', 'cards', etc.
        taxon_ids = [[s['id'], sub_name] for s in species_in_sub]

        all_taxon_ids.extend(taxon_ids)
        #TODO: Update all these to use progress.update() or whatever
        mw.taskman.run_on_main(
            lambda name=sub_name: add_log_message(self, f"\t{name}: {len(species_in_sub)} species")
        )
        if (datetime.now() - last_progress).total_seconds() >= 1:
            mw.taskman.run_on_main(lambda: mw.app.processEvents())
            last_progress = datetime.now()
    print("reached end of function")
    return all_taxon_ids

def fetch_species_data(species_id):
    """Fetch species card data from API"""
    try:
        response = requests.get(f"{BASE_URL}/speciescards/{species_id}", timeout=100)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(
            "Network Error",f"Error fetching species {species_id}: {e}")
        return None

def download_image(image_url, species_id, i):
    """_summary_

    Args:
        image_url (_type_): _description_
        species_id (str): _description_
        i (int): image number for this species

    Returns:
        pathlib.Path: path to to the saved image
    """

    filename = f"species_{species_id}_{i}.jpg"
    media_dir = Path( mw.col.media.dir())
    filepath = media_dir / filename

    # If image was already downloaded then skip
    if not filepath.exists():
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
                print(f"\twrote to {filepath}")
            return filepath
        except Exception as e:
            print(f"Error downloading image for {species_id}: {e}")
            return None
    else:
        print(f"\t{filepath} cached")
        return filepath

def create_note_list(self, species_list):
    """Extracts relevant info from Pinkka API for the given list of species into a list of dicts.

    Args:
        species_list (list): List of species IDs from Pinkka

    Returns:
        list: List of dictionaries containing species info for creating notes.
    """
    # TODO: adapt to use self 
    self.status_label.setText("Downloading species data")
    self.progress_bar.setVisible(True)
    print(f"LENgth of species list: {len(species_list)}")
    self.progress_bar.setMaximum(len(species_list))

    req_images_number = int(self.images_number_input.cleanText()) # set to self.req_images_number
    image_size = str(self.image_size.currentText())
    get_back_images = False
    lang = str(self.lang_input.currentText())

    media_list = []
    note_list = []
    
    if TESTING:
        species_list = species_list[0:4]

    i=0
    total = len(species_list)
    last_progress = datetime.now()
    for species in species_list:
        species_id = species[0]
        sub_pinkka = species[1]
        data = fetch_species_data(species_id)
        if not data:
            add_log_message(self,  f"Could not find species {species_id}", level="WARNING")
            if (datetime.now() - last_progress).total_seconds() >= 1:
                mw.taskman.run_on_main(lambda: mw.app.processEvents())
                last_progress = datetime.now()
            continue
        
        # Extract species name, image URLs, taxonomy info
        species_name = data.get('scientificName')

        add_log_message(self, f"Fetched {species_name}")
        taxon_id = data.get('taxonId')

        # Get common names
        common_names = {}
        for language in ['fi', 'sv', 'en']:
            try:
                common_names[language] = data.get('vernacularName')[language]
            except KeyError:
                common_names[language] = ""

        taxonomy_list = []
        family = ""
        for taxa in data.get('taxonomy'):
            if taxa['rankName']['en'] in ['phylum', 'family']:
                taxatag = f"{taxa['rankName'][lang]}-{taxa['scientificName']}"
                taxatag = taxatag.replace(" ", "_")
                taxonomy_list.append(taxatag)
                if taxa['rankName']['en'] == "family":
                    family = taxa['scientificName']

        # add sub pinkka as tag
        taxonomy_list.append(sub_pinkka.replace(" ", "_"))

        # If user requested more images than exist, limit to existing number
        max_images = len(data.get('images'))
        if req_images_number > max_images:
            images_number = max_images
        else: images_number = req_images_number

        # loop over images and download
        if images_number > 0:
            img_field = ""
            for i in range(0, images_number):
                # get first half of images from start
                if not get_back_images or (i+1) <= round(images_number/2):
                    image_i = i
                else: # get the rest of images from the end of the list
                    image_i = max_images - (images_number-i)
                image_url = data.get('images')[image_i]['urls'][image_size]
                image_path = download_image(image_url, taxon_id.replace(".", "-"), image_i)
                # add path to media list
                media_list.append(image_path)

                # format for field
                img_field = f"{img_field} <img src=\"{image_path.name}\">"
        else:
            add_log_message(self, "\tNo Images Available. Skipping", level="WARNING")
            if (datetime.now() - last_progress).total_seconds() >= 1:
                mw.taskman.run_on_main(lambda: mw.app.processEvents())
                last_progress = datetime.now()

            continue
        # Pinkka URL
        species_url = f"https://pinkka.laji.fi/pinkat/#/speciescards/{species_id}"

        # Create Anki note
        note = {
            'fields': {
                "Species Name": species_name, 
                "Images": img_field, 
                "Family": family, 
                "Finnish Name": common_names['fi'], 
                "Swedish Name": common_names['sv'], 
                "English Name": common_names['en'], 
                "Pinkka URL": species_url,
                "Notes": ""
                },
            'tags': taxonomy_list,
            'guid': taxon_id
        }
        note_list.append(note)
        
        i+=1
        if (datetime.now() - last_progress).total_seconds() >= 1:
            mw.taskman.run_on_main(
                lambda prog=i: self.progress_bar.setValue(prog)
            )
            mw.taskman.run_on_main(lambda: mw.app.processEvents())
            last_progress = datetime.now()
        
    note_count = len(note_list)
    mw.taskman.run_on_main(
        lambda notes=note_count: self.status_label.setText(f"Downloaded {notes} / {len(species_list)} species")
    )
    mw.taskman.run_on_main(lambda: mw.app.processEvents())
    return note_list
    

def create_anki_deck(self, note_list):
    progress = 0

    deck = mw.col.decks.get(mw.col.decks.id(self.deck_name_input.text()))
    model = add_custom_model(self, mw.col)

    # assign custom model to new deck
    mw.col.decks.select(deck["id"])
    mw.col.decks.save(deck)

    # assign new deck to custom model
    mw.col.models.set_current(model)
    model["did"] = deck["id"]
    mw.col.models.save(model)

    for item in note_list:
        note = mw.col.newNote()
        # Get field names from the model in order
        field_names = [f["name"] for f in model["flds"]]
        # Assign by index
        for idx, field_name in enumerate(field_names):
            if field_name in item["fields"]:
                note.fields[idx] = item["fields"][field_name]

        # Add all tags from dict
        for tag in item['tags']:
            note.add_tag(tag)

        # Add note to deck
        mw.col.addNote(note)

        progress += 1
        self.status_label.setText(
            (f"Imported {progress}/{len(note_list)}"))
        mw.app.processEvents()
