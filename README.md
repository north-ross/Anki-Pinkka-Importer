# Anki Pinkka Importer

An Anki addon to convert plant image collections from [Pinkka](https://pinkka.laji.fi) to an Anki deck. Pinkka is a platform used by the University of Helsinki (and other Finnish organizations) for plant identification lessons. This set of functions can be used to collect data from Pinkka's API and convert them into Anki flashcards. Specifically it's useful for students who need to memorize scientific names before a test.

I have been studying Finnish plants using Pinkka, but I thought it would be useful to have the spaced repetition from Anki, plus the ability to organize the cards by family or other categories.

This is a distinct iteration on [Pinkka2Anki](https://github.com/north-ross/pinkka2anki), adapting it to work as an Anki addon instead of a Python tool to package a .apkg file (which used GenAnki instead of the native libraries).

Unfortunately, I couldn't get it to work using the image URLs, so it needs to download all the images. I used the medium-size "square" resolution as deafault, but the script can be configured to use "thumbnail" instead. For reference, four "square"-size images for 652 notes resulted in a 80 MB Anki package.

# Dependencies
- Python 3.4+
- `requests` (`pip install requests`)
- `anki`/`aqt` (packaged with Anki)

# Use
- See GUI instructions

# My Studing Tips
- Use the tags on the cards like family and sub-pinkka for [Custom Study](https://docs.ankiweb.net/filtered-decks.html?highlight=filtered%20deck#custom-study). You can also add your own tags, like "small-white-flower" or "aquatic" for example, to help with comparing different ones. 
    - Don't rely on this too much, since Anki works best by using large decks with a variety of terms to help your memory.

- Sometimes the images downloaded by the script will be missing an important ID feature. You can click on the scientific name to visit the Pinkka page and see all the images, then download a better one and edit the card to add it.

- You can sync to your Anki account and use the app to study on your phone. It's free on Android but the official iOS app is a bit expensive, although there are some free forks of it.

# Notes
The Anki deck that is created will have your desired number of images on the front of the flashcard, then the given scientific name, family and Finnish name on the back. You can customize the cards once you add them to Anki.

If you have found this useful this consider donating to the free and open source software [Anki](https://apps.ankiweb.net/).

Some was code adapted from [Anki Quizlet Importer Extended](https://github.com/sviatoslav-lebediev/anki-quizlet-importer-extended).

Some code advice came from [duck.ai](https://duck.ai) (Claude Haiku 4.5).
