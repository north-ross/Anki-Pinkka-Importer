import time
import json
from pathlib import Path
import requests
import re
import urllib

BASE_URL = "https://fmnh-ws-prod3.it.helsinki.fi/pinkka/api"

# Get Pinkka ID, adapted from Quizlet plugin
def getPinkkaDeckID(self):
        # grab url input
        url = self.text_url.text()

        # validate quizlet URL
        if url == "":
            self.label_results.setText("You forgot the deck URL :(")
            return
        elif not "pinkka.laji.fi" in url:
            self.label_results.setText("Oops! That's not a Pinkka URL :(")
            return
        elif not re.search(r"https://pinkka.laji.fi/pinkat/#/pinkkas/[\d]+", url):
            self.label_results.setText("Oops! Please use the full deck URL, e.g. https://pinkka.laji.fi/pinkat/#/pinkkas/8 :(")
            return

        # voodoo needed for some error handling
        if urllib.parse.urlparse(url).scheme:
            urlPath = urllib.parse.urlparse(url).path
        else:
            urlPath = urllib.parse.urlparse("https://"+url).path

        # validate and set Quizlet deck ID
        pinkkaDeckID = urlPath.strip("/")

        if pinkkaDeckID == "":
            self.label_results.setText("Oops! Please use the full deck URL, e.g. https://pinkka.laji.fi/pinkat/#/pinkkas/8 :(")
            return

        return pinkkaDeckID

# Create Anki model (front: image, back: species name)
# adapted from "Quizlet Plugin for Anki"
def add_custom_model(col):
    """Creates or updates existing Anki model

    Args:
        col (anki.collection.Collection): Current Anki collection (mw.col)

    Returns:
        _type_: Anki model object (NotetypeDict?)
    """

    # create custom model for imported deck
    mm = col.models
    existing = mm.by_name("Pinkka Species")
    if existing:
        return existing
    m = mm.new("Pinkka Species")

    # add fields
    mm.addField(m, mm.newField("Species Name"))
    mm.addField(m, mm.newField("Images"))
    mm.addField(m, mm.newField("Family"))
    mm.addField(m, mm.newField("Finnish Name"))
    mm.addField(m, mm.newField("Pinkka URL"))
    
    # add cards
    t = mm.newTemplate("ImageFront")

    # front
    t['qfmt'] = "{{Images}}"
    t['afmt'] = '{{FrontSide}}<hr id="answer">'+\
        '<i><u><a href="{{Pinkka URL}}" style="color:white;">{{Species Name}}</a></u></i>'+\
        '<br><b>{{Family}}</b><br>{{Finnish Name}}'
    mm.addTemplate(m, t)
    mm.add(m)
    return m

def get_all_species_ids(pinkka_id):
    """Fetch all species IDs and sub name from a pinkka and its subPinkkas
    Returns a nested list with pairs of values (species ID, subPinkka name)"""
    
    # Get the list of sub pinkkas
    pinkka_response = requests.get(f"{BASE_URL}/pinkkas/{pinkka_id}", timeout=120)
    pinkka_data = pinkka_response.json()
    
    sub_pinkkas = pinkka_data.get('subPinkkas', [])
    print(f"Found {len(sub_pinkkas)} subPinkkas")
    
    all_taxon_ids = []
    
    # Step 2: Loop through each subPinkka
    for sub_pinkka in sub_pinkkas:
        sub_id = sub_pinkka['id']
        sub_name = sub_pinkka['name'].get('en', sub_pinkka['name'].get('fi', 'Unknown'))
        
        # Step 3: Get species from this subPinkka
        sub_response = requests.get(f"{BASE_URL}/subpinkkas/{sub_id}", timeout=120)
        sub_data = sub_response.json()

        # Extract species/taxon IDs (adjust key name based on actual JSON structure)
        species_in_sub = sub_data.get('speciesCards', [])  # or 'species', 'cards', etc.
        taxon_ids = [[s['id'], sub_name] for s in species_in_sub]

        print(f"  {sub_name}: {len(taxon_ids)} species")
        all_taxon_ids.extend(taxon_ids)

    print(f"\nTotal species across all subPinkkas: {len(all_taxon_ids)}")
    return all_taxon_ids

def fetch_species_data(species_id):
    """Fetch species card data from API"""
    try:
        response = requests.get(f"{BASE_URL}/speciescards/{species_id}", timeout=100)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching species {species_id}: {e}")
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
    # Create media folder
    media_dir = Path("pinkka_media")
    media_dir.mkdir(exist_ok=True)

    filename = f"species_{species_id}_{i}.jpg"
    filepath = media_dir / filename

    # If image was already downloaded then skip
    if not filepath.exists():
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
        except Exception as e:
            print(f"Error downloading image for {species_id}: {e}")
            return None
    else:
        return filepath


def create_anki_deck(species_list, req_images_number=4, image_size="square", lang='en', pinkka_name = 'My Pinkka Deck', make_subdecks=False):
    # TODO: Adapt to get parameters from self. insetad of arguments
    """Creates an Anki package (.apkg) from a provided list of species IDs. 
        Downloads the specified number of images. 

    Args:
        species_list (list): List of species IDs from the Pinkka API. 
            Get using pinkka2anki.get_all_species_ids().
        req_images_number (int, optional): Number of requested images to download and include in the card. 
            Choose 100 for maximum (will not cause error). Defaults to 4.
        image_size (str, optional): Set size of downloaded images: "original" > "full" > "large" > "square" > "thumbnail". 
        lang (str, optional): Language used for taxonomy tags (fi, sv or en). Defaults to 'en'.
        pinkka_name (str, optional): Language used for taxonomy tags (fi, sv or en). Defaults to 'en'.
        make_subdecks (boolean, optional): Generate subdecks from the subPinkkas
    """
    if make_subdecks:
        sub_pinkkas = set([x[1] for x in species_list])
        subdecks_dict = {}
        deck_id=1
        for sub_pinkka in sub_pinkkas:
            subdeck = Deck(deck_id, f"{pinkka_name}::{sub_pinkka}" )
            subdecks_dict[sub_pinkka] = subdeck
            print(f"{subdeck.name} created")
            deck_id+=1

    else:
        deck_id = int(time.time() * 1000)  # Unique deck ID safe for SQLite integer
        deck = Deck(deck_id, f'{pinkka_name}')


    media_list = []
    
    for species in species_list:
        species_id = species[0]
        sub_pinkka = species[1]
        data = fetch_species_data(species_id)
        print(f"got data for {species_id} ({data.get('scientificName')})")
        if not data:
            print(f"Could not find species {species_id}")
            continue
        
        # Extract species name, image URLs, taxonomy info
        species_name = data.get('scientificName')
        taxon_id = data.get('taxonId')
        try:
            finnish_name = data.get('vernacularName')['fi']
        except KeyError:
            finnish_name = ""

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
            print("\t", images_number, "images available")
            for i in range(0, images_number):
                # get first half of images from start
                if i <= round(images_number/2):
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
            print("\tNo Images Available. Skipping")
            continue
        # Pinkka URL
        species_url = f"https://pinkka.laji.fi/pinkat/#/speciescards/{species_id}"

        ## TODO: edit from here to use anki lib
        # Create Anki note
        note = Note(
            model=MODEL,
            fields=[species_name, img_field, family, finnish_name, species_url],
            tags= taxonomy_list,
            guid=taxon_id
        )
        if make_subdecks:
            subdecks_dict[sub_pinkka].add_note(note)
            print(f"\tadded to {subdecks_dict[sub_pinkka].name}")
        else:
            deck.add_note(note)

    # pack to package with media
    if make_subdecks:
        package = Package(subdecks_dict.values())
        print(f"Decks: {[x.name for x in subdecks_dict.values()]}")
        total_notes = sum([len(deck.notes) for deck in subdecks_dict.values()])
    else: 
        package = Package(deck)
        total_notes = len(deck.notes)
    print(f"Created notes for {total_notes} / {len(species_list)} species")
    package.media_files = media_list
    
    # Save deck
    outfile = f'pinkka_{pinkka_name.replace(" ", "_")}.apkg'
    package.write_to_file(outfile)
    print(f"Anki deck created: {outfile}")
