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


def fetch_movie_from_api(title):
    """Fetch movie details from the OMDb API and handle potential errors."""
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

        return {
            "title": data.get("Title"),
            "year": year_val,
            "rating": rating_val,
            "poster_url": data.get("Poster")
        }
    except requests.exceptions.RequestException:
        raise ConnectionError("Could not connect to the OMDb API.")


def list_movies():
    """Retrieve all movies from the database and return them as a dict."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT title, year, rating, poster_url FROM movies"))
        movies = result.fetchall()

    return {row[0]: {"release_year": row[1], "rating": row[2], "poster_url": row[3]} for row in movies}


def add_movie(title, year, rating, poster_url):
    """Add a new movie to the database."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("INSERT INTO movies (title, year, rating, poster_url) "
                     "VALUES (:title, :year, :rating, :poster_url)"),
                {"title": title, "year": year, "rating": rating, "poster_url": poster_url}
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False


def delete_movie(title):
    """Delete a movie from the database by its title."""
    with engine.connect() as connection:
        try:
            connection.execute(
                text("DELETE FROM movies WHERE title = :title"),
                {"title": title}
            )
            connection.commit()
        except Exception as e:
            print(f"Error: {e}")


def get_movie_one_data(column):
    """Retrieve a dictionary mapping movie titles to a requested attribute."""
    if column == "release_year":
        db_column = "year"
    else:
        db_column = "rating"

    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT title, {db_column} FROM movies"))
        movies = result.fetchall()

    return {row[0]: row[1] for row in movies}