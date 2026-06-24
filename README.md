My Movie Database App

A Python-based CLI application to manage your personal movie collection. It automatically fetches movie metadata from the OMDb API, stores it in a SQLite database, and can generate a static HTML website to showcase your collection.

## Features
- **OMDb API Integration**: Simply type a movie title, and the app fetches the year, rating, and poster URL.
- **SQLite Database**: Secure and structured storage using SQLAlchemy.
- **Fuzzy Search**: Find movies even if you misspell the title.
- **Statistics & Visualizations**: View rating distribution and release year histograms via Matplotlib.
- **Web Generation**: Export your collection into a clean, modern HTML grid view.

## Requirements
Before running the app, ensure you have Python installed and install the required dependencies:
```bash
pip install -r requirements.txt
Setup
Get a free API Key from OMDb API.

Create a .env file in the root directory.

Add your key to the .env file:

Code-Snippet
OMDB_API_KEY=your_8_digit_key_here
Usage
Run the main application:

Bash
python movie_project_main.py
Follow the interactive on-screen terminal menu (Options 0–12).


---

## 3. Das `storage`-Package erstellen

1. Erstelle einen neuen Ordner namens `storage`.
2. Erstelle darin eine leere Datei namens `__init__.py`. (Diese sagt Python, dass dieser Ordner ein Package ist).
3. Verschiebe deine `movie_storage_sql.py` in diesen Ordner.

### Pfadanpassung in `storage/movie_storage_sql.py`
Da die Datenbank jetzt im Ordner `data/` liegen soll, müssen wir den Pfad anpassen. Zudem ermitteln wir das Hauptverzeichnis des Projekts relativ zu dieser Datei. Ersetze den oberen Teil von `movie_storage_sql.py` mit folgendem Code:

```python
import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Pfade ermitteln (Diese Datei liegt in /storage, das Hauptverzeichnis ist ein Ordner drüber)
storage_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(storage_dir)

# .env liegt im Hauptverzeichnis
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

API_KEY = os.getenv("OMDB_API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

# Datenbank im /data Ordner ablegen
data_dir = os.path.join(project_root, "data")
os.makedirs(data_dir, exist_ok=True)  # Erstellt den data-Ordner, falls er nicht existiert
DB_URL = f"sqlite:///{os.path.join(data_dir, 'movies.db')}"

engine = create_engine(DB_URL, echo=False)

with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster_url TEXT
        )
    """))
    connection.commit()

# ... (Der Rest der Funktionen fetch_movie_from_api, list_movies, etc. bleibt absolut identisch!)