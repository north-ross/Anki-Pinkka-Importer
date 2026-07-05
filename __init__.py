from aqt import mw
from aqt.qt import *
from aqt.utils import qconnect
from .gui import PinkkaImportDialog

def open_pinkka_dialog():
    dialog = PinkkaImportDialog(mw)
    dialog.exec()

# Register menu
action = QAction("Import Pinkka Deck", mw)
qconnect(action.triggered, open_pinkka_dialog)
mw.form.menuTools.addAction(action)
