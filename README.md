# Anki Pinkka Importer

An Anki addon to convert plant image collections from [Pinkka](https://pinkka.laji.fi) to an Anki deck. Pinkka is a platform used by the University of Helsinki (and other Finnish organizations) for plant identification lessons. This set of functions can be used to collect data from Pinkka's API and convert them into Anki flashcards. Specifically it's useful for students who need to memorize latin names before a test.

I have been studying Finnish plants using Pinkka, but I thought it would be useful to have the spaced repetition from Anki, plus the ability to study one family at a time.

This is a distinct iteration on [Pinkka2Anki](https://github.com/north-ross/pinkka2anki), adapting it to work as an Anki addon instead of a Python tool to package a .apkg file (which used GenAnki instead of the native libraries).

Unfortunately, I couldn't get it to work using the image URLs, so it needs to download all the images. I used the medium-size "square" resolution as deafault, but the script can be configured to use "thumbnail" instead. For reference, four "square"-size images for 652 notes resulted in a 80 MB Anki package.

# Dependencies
- Python 3.4+
- `requests` (`pip install requests`)
- `anki`/`aqt` (packaged with Anki)

# Use
- See GUI instructions

# Notes
The Anki deck that is created will have your desired number of images on the front of the flashcard, then the given scientific name, family and Finnish name on the back. You can customize the cards once you add them to Anki.

It also has the subpinkka, family and phylum as tags. Use the [Custom Study](https://docs.ankiweb.net/filtered-decks.html?highlight=filtered%20deck#custom-study) feature with certain tags, for example "family-Asteraceae" or "phylum-Tracheophyta".

You can sync to your Anki account and use the app to study on your phone. It's free on Android but the official iOS app is a bit expensive, although there are some free forks of it.

If you have found this useful this consider donating to the free and open source software [Anki](https://apps.ankiweb.net/).

Disclaimer: Some code advice came from [duck.ai](https://duck.ai) (Claude Haiku 4.5).
