#!/bin/bash

# Aktiviere virtuelle Umgebung
source /Users/karlgohlke/venv/bin/activate

# Wechsle ins richtige Verzeichnis (wo manage.py liegt!)
cd "/Users/karlgohlke/Desktop/Gohlke Kunden/Ralph Vogelsang/Cbvgoodwill" || exit

# Starte den Server
python manage.py runserver


