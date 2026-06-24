import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

storage_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(storage_dir, ".."))

env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("OMDB_API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

data_dir = os.path.join(project_root, "data")
os.makedirs(data_dir, exist_ok=True)
DB_URL = f"sqlite:///{os.path.join(data_dir, 'movies_v2.db')}"

engine = create_engine(DB_URL, echo=False)

# Datenbanktabellen erstellen (mit Relationen)
with engine.connect() as connection:
    # 1. Users Tabelle
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """))
    # 2. Movies Tabelle erweitert um Spalten und Foreign Key
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster_url TEXT,
            imdb_id TEXT,
            country TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """))
    connection.commit()


# --- USER MANAGEMENT FUNCTIONS ---

def get_users():
    """Returns a dictionary of all users {id: username}."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, username FROM users"))
        return {row[0]: row[1] for row in result.fetchall()}


def create_user(username):
    """Creates a new user profile."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("INSERT INTO users (username) VALUES (:username)"),
                {"username": username}
            )
            connection.commit()
            return True
        except Exception:
            return False


# --- MOVIE FUNCTIONS ---

def fetch_movie_from_api(title):
    """Fetch extended movie details from OMDb API."""
    if not API_KEY:
        raise ValueError("API Key is missing. Please check your .env file.")

    try:
        response = requests.get(OMDB_URL, params={"apikey": API_KEY, "t": title}, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "False":
            return None

        try:
            rating_val = float(data.get("imdbRating", 0))
        except ValueError:
            rating_val = 0.0

        try:
            year_val = int(data.get("Year", "0")[:4])
        except ValueError:
            year_val = 0

        # Ersten ISO-Ländercode grob mappen (z.B. "USA, UK" -> "US")
        country_raw = data.get("Country", "").split(",")[0].strip()
        country_code = "US" if "USA" in country_raw or "United States" in country_raw else country_raw[:2].upper()

        return {
            "title": data.get("Title"),
            "year": year_val,
            "rating": rating_val,
            "poster_url": data.get("Poster"),
            "imdb_id": data.get("imdbID"),
            "country": country_code if country_code else "US"
        }
    except requests.exceptions.RequestException:
        raise ConnectionError("Could not connect to the OMDb API.")


def list_movies(user_id):
    """Retrieve all movies belonging strictly to the active user."""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT title, year, rating, poster_url, imdb_id, country, notes "
                 "FROM movies WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        movies = result.fetchall()

    return {
        row[0]: {
            "release_year": row[1],
            "rating": row[2],
            "poster_url": row[3],
            "imdb_id": row[4],
            "country": row[5],
            "notes": row[6] if row[6] else ""
        }
        for row in movies
    }


def add_movie(user_id, title, year, rating, poster_url, imdb_id, country):
    """Add a new movie to a specific user's database collection."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("INSERT INTO movies (user_id, title, year, rating, poster_url, imdb_id, country, notes) "
                     "VALUES (:user_id, :title, :year, :rating, :poster_url, :imdb_id, :country, '')"),
                {"user_id": user_id, "title": title, "year": year, "rating": rating,
                 "poster_url": poster_url, "imdb_id": imdb_id, "country": country}
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False


def delete_movie(user_id, title):
    """Delete a movie from the active user's collection."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("DELETE FROM movies WHERE user_id = :user_id AND title = :title"),
                {"user_id": user_id, "title": title}
            )
            connection.commit()
        except Exception as e:
            print(f"Error: {e}")


def update_movie_note(user_id, title, note):
    """Update or add a personal note to a movie."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("UPDATE movies SET notes = :note WHERE user_id = :user_id AND title = :title"),
                {"note": note, "user_id": user_id, "title": title}
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"Error updating note: {e}")
            return False


def get_movie_one_data(user_id, column):
    """Retrieve a dictionary filtering a single metric for the specific user."""
    db_column = "year" if column == "release_year" else "rating"
    with engine.connect() as connection:
        result = connection.execute(
            text(f"SELECT title, {db_column} FROM movies WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        movies = result.fetchall()

    return {row[0]: row[1] for row in movies}