import os
import statistics as stat
import random as rm
import difflib

import colorama as cr
import matplotlib.pyplot as plt

from storage import movie_storage_sql as ms

# Globale Variablen für die Session-Steuerung
ACTIVE_USER_ID = None
ACTIVE_USERNAME = ""


def user_login_screen():
	"""Handles the initial profile selection or user creation screen."""
	global ACTIVE_USER_ID, ACTIVE_USERNAME
	while True:
		print(cr.Fore.CYAN + "\n=== Welcome to the Movie App! 🎬 ===")
		users = ms.get_users()

		# Nutzer auflisten
		counter = 1
		user_mapping = {}
		for u_id, u_name in users.items():
			print(f"{counter}. {u_name}")
			user_mapping[counter] = (u_id, u_name)
			counter += 1

		print(f"{counter}. Create new user")

		try:
			choice = int(input(cr.Fore.LIGHTBLUE_EX + "\nEnter choice: "))
		except ValueError:
			print(cr.Fore.RED + "Please enter a valid option number.")
			continue

		if choice == counter:
			new_name = input(cr.Fore.LIGHTBLUE_EX + "Enter new username: ").strip()
			if new_name:
				if ms.create_user(new_name):
					print(cr.Fore.GREEN + f"User '{new_name}' successfully created!")
				else:
					print(cr.Fore.RED + "User already exists or database error.")
			else:
				print(cr.Fore.RED + "Username cannot be empty.")
		elif choice in user_mapping:
			ACTIVE_USER_ID, ACTIVE_USERNAME = user_mapping[choice]
			print(cr.Fore.GREEN + f"\nWelcome back, {ACTIVE_USERNAME}!")
			return
		else:
			print(cr.Fore.RED + "Invalid choice.")


def print_menu_movie_catalog():
	"""Shows active user menu on terminal."""
	print(cr.Fore.MAGENTA + f"\nMenu ({ACTIVE_USERNAME}'s Collection):")
	print("0. Exit")
	print("1. List movies")
	print("2. Add movie")
	print("3. Delete movie")
	print("4. Update movie (Add Note)")
	print("5. Stats")
	print("6. Random movie")
	print("7. Search movie")
	print("8. Movie sorted by rating")
	print("9. Movie sorted by year")
	print("10. Movie filter")
	print("11. Create rating histogramm")
	print("12. Create year histogramm")
	print("13. Generate Website")
	print("14. Switch User\n")


def get_user_menu_number():
	"""Returns a valid user input from the menu options."""
	while True:
		try:
			user_choice = int(input(cr.Fore.LIGHTBLUE_EX + "Enter choice (0-14)   "))
		except ValueError:
			print(cr.Fore.RED + "Invalid input, choose a number from 0 to 14")
		else:
			if 0 <= user_choice <= 14:
				return user_choice
			else:
				print(cr.Fore.RED + "Invalid input, choose a number from 0 to 14")


def show_movie_catalog(movie_catalog):
	"""Displays the data entries from the active user's database."""
	if not movie_catalog:
		print(cr.Fore.YELLOW + f"{ACTIVE_USERNAME}, your collection is empty. Add some movies!")
		return
	print(f"{len(movie_catalog)} movies in total")
	for movie, data in movie_catalog.items():
		note_str = f" [Note: {data['notes']}]" if data['notes'] else ""
		print(f"{movie} ({data['release_year']}): {data['rating']} {note_str}")


def add_movie_catalog(movie_catalog):
	"""Queries OMDb API and binds the new movie to the active user."""
	movie_title = input(cr.Fore.LIGHTBLUE_EX + "Please enter the movie title to search and add: ").strip()
	if len(movie_title) < 1:
		print(cr.Fore.RED + "Movie name must not be empty.")
		return

	print(cr.Fore.YELLOW + f"Searching for '{movie_title}' on OMDb...")

	try:
		movie_data = ms.fetch_movie_from_api(movie_title)
		if movie_data is None:
			print(cr.Fore.RED + f"Movie '{movie_title}' not found on OMDb.")
			return

		if movie_data["title"] in movie_catalog:
			print(cr.Fore.RED + f"'{movie_data['title']}' already exists in your collection.")
			return

		success = ms.add_movie(
			ACTIVE_USER_ID, movie_data["title"], movie_data["year"],
			movie_data["rating"], movie_data["poster_url"],
			movie_data["imdb_id"], movie_data["country"]
		)

		if success:
			print(cr.Fore.GREEN + f"\nMovie successfully added to {ACTIVE_USERNAME}'s collection!")
	except Exception as e:
		print(cr.Fore.RED + f"Error adding movie: {e}")


def delete_movie_catalog(movie_catalog):
	"""Delete a movie from the active user's database collection."""
	delete_title = input(cr.Fore.LIGHTBLUE_EX + "Please enter the title to be deleted: ").strip()
	if delete_title in movie_catalog:
		ms.delete_movie(ACTIVE_USER_ID, delete_title)
		print(cr.Fore.MAGENTA + f"The movie '{delete_title}' was deleted.")
	else:
		print(cr.Fore.RED + f"The title '{delete_title}' does not exist!")


def update_movie_catalog(movie_catalog):
	"""Asks for a movie title and appends a personal text note to it."""
	title = input(cr.Fore.LIGHTBLUE_EX + "Enter movie name: ").strip()
	if title not in movie_catalog:
		print(cr.Fore.RED + f"The movie '{title}' is not in your database collection.")
		return

	note = input(cr.Fore.LIGHTBLUE_EX + "Enter movie note: ").strip()
	if ms.update_movie_note(ACTIVE_USER_ID, title, note):
		print(cr.Fore.GREEN + f"Movie {title} successfully updated with note!")


def stat_movie_catalog():
	"""Display metrics for active user."""
	movie_catalog_data = ms.get_movie_one_data(ACTIVE_USER_ID, "rating")
	if not movie_catalog_data:
		print(cr.Fore.RED + "No movies in database.")
		return

	evaluations = list(movie_catalog_data.values())
	print(f"Average rating: {stat.mean(evaluations):.1f}")
	print(f"Median of movies: {stat.median(evaluations)} ")

	max_eval, min_eval = max(evaluations), min(evaluations)
	best = [t for t, e in movie_catalog_data.items() if e == max_eval]
	worst = [t for t, e in movie_catalog_data.items() if e == min_eval]
	print(f"Best movie(s): {', '.join(best)}, {max_eval}")
	print(f"Worst movie(s): {', '.join(worst)}, {min_eval}")


def random_movie_catalog(movie_catalog):
	"""Select and display a random movie from the active user's catalog."""
	if not movie_catalog:
		print(cr.Fore.RED + "No movies in database.")
		return
	random_movie = rm.choice(list(movie_catalog))
	print(f"Your movie for tonight: {random_movie} ({movie_catalog[random_movie]['release_year']})")


def search_movie_catalog(movie_catalog):
	"""Fuzzy matching search query."""
	user_search = input(cr.Fore.LIGHTBLUE_EX + "Enter part of movie name: ").strip().lower()
	if not user_search:
		return
	close_matches = difflib.get_close_matches(user_search, [t.lower() for t in movie_catalog], cutoff=0.4)
	for match in close_matches:
		for title in movie_catalog:
			if match == title.lower():
				print(f"{title} ({movie_catalog[title]['release_year']}): {movie_catalog[title]['rating']}")


def user_choice_sorted_rotation():
	"""Asks sorting direction preference."""
	while True:
		choice = input(cr.Fore.LIGHTBLUE_EX + "Start from highest value? (Y/N): ").strip().lower()
		if choice in ['y', 'n']:
			return choice == 'y'


def sorted_movie_catalog_rating():
	"""Sorted rating print block."""
	data = ms.get_movie_one_data(ACTIVE_USER_ID, "rating")
	if not data:
		return
	items = list(data.items())
	items.sort(key=lambda x: x[1], reverse=user_choice_sorted_rotation())
	for title, grade in items:
		print(f"{title}: {grade}")


def sorted_movie_catalog_year():
	"""Sorted release year print block."""
	data = ms.get_movie_one_data(ACTIVE_USER_ID, "release_year")
	if not data:
		return
	items = list(data.items())
	items.sort(key=lambda x: x[1], reverse=user_choice_sorted_rotation())
	for title, year in items:
		print(f"{title}: {year}")


def histo_movie_catalog_rating():
	"""Histogram processing logic."""
	data = ms.get_movie_one_data(ACTIVE_USER_ID, "rating")
	if not data:
		return
	plt.figure(figsize=(8, 6))
	plt.hist(list(data.values()), bins=range(0, 11), edgecolor="black")
	plt.title(f"Rating Distribution for {ACTIVE_USERNAME}")
	plt.show()


def histo_movie_catalog_year():
	"""Histogram processing logic for years."""
	data = ms.get_movie_one_data(ACTIVE_USER_ID, "release_year")
	if not data:
		return
	vals = list(data.values())
	plt.figure(figsize=(12, 6))
	plt.hist(vals, bins=range(min(vals), max(vals) + 2), edgecolor="black")
	plt.title(f"Year Distribution for {ACTIVE_USERNAME}")
	plt.show()


def filter_movie_catalog_user(movie_catalog):
	"""Filters results via terminal parameters."""
	raw_rating = input(cr.Fore.LIGHTBLUE_EX + "Enter minimum rating (blank for 0): ").strip()
	filter_rating = float(raw_rating) if raw_rating else 0.0
	print("\nFiltered Results:")
	for movie, data in movie_catalog.items():
		if data["rating"] >= filter_rating:
			print(f"{movie} ({data['release_year']}): {data['rating']}")


def generate_website(movie_catalog):
	"""Generates user-specific static website with notes, scores, links and flags."""
	current_dir = os.path.dirname(os.path.abspath(__file__))
	template_path = os.path.join(current_dir, "_static", "index_template.html")
	# Generiert dateisystemfreundliche Pfade wie z.B. "_static/John.html"
	output_path = os.path.join(current_dir, "_static", f"{ACTIVE_USERNAME}.html")

	if not os.path.exists(template_path) or not movie_catalog:
		print(cr.Fore.RED + "Error: Template missing or collection empty.")
		return

	print(cr.Fore.YELLOW + f"Generating website for {ACTIVE_USERNAME}...")

	movie_grid_html = ""
	for title, data in movie_catalog.items():
		poster = data.get("poster_url")
		if not poster or poster == "N/A":
			poster = "https://via.placeholder.com/128x193?text=No+Poster"

		imdb_link = f"https://www.imdb.com/title/{data['imdb_id']}/" if data.get('imdb_id') else "#"
		country_code = data.get("country", "US")
		# Externe Open-Source Flaggen-Vektorgrafiken API verwenden
		flag_url = f"https://purecatamphetamine.github.io/country-flag-icons/3x2/{country_code}.svg"

		note_tooltip = data.get("notes", "").replace('"', '&quot;')
		note_class = "has-note" if note_tooltip else ""

		movie_grid_html += f"""
        <li>
            <div class="movie {note_class}" data-note="{note_tooltip}">
                <a href="{imdb_link}" target="_blank">
                    <img class="movie-poster" src="{poster}" alt="{title} Poster">
                </a>
                <div class="movie-badge">
                    <img class="country-flag" src="{flag_url}" alt="{country_code}">
                    <span class="movie-rating">★ {data['rating']}</span>
                </div>
                <div class="movie-title">{title}</div>
                <div class="movie-year">{data['release_year']}</div>
            </div>
        </li>
        """

	try:
		with open(template_path, "r", encoding="utf-8") as file:
			template_content = file.read()

		html_content = template_content.replace("__TEMPLATE_TITLE__", f"{ACTIVE_USERNAME}'s Movie Room")
		html_content = html_content.replace("__TEMPLATE_MOVIE_GRID__", movie_grid_html)

		with open(output_path, "w", encoding="utf-8") as file:
			file.write(html_content)

		print(cr.Fore.GREEN + f"Website successfully generated at: {output_path}")
	except Exception as e:
		print(cr.Fore.RED + f"Error generating file system object: {e}")


def main():
	"""Core runtime engine routing block loop."""
	user_login_screen()
	while True:
		movie_catalog = ms.list_movies(ACTIVE_USER_ID)
		print_menu_movie_catalog()
		user_choice = get_user_menu_number()

		match user_choice:
			case 0:
				print(cr.Fore.MAGENTA + "Goodbye!"); return
			case 1:
				show_movie_catalog(movie_catalog)
			case 2:
				add_movie_catalog(movie_catalog)
			case 3:
				delete_movie_catalog(movie_catalog)
			case 4:
				update_movie_catalog(movie_catalog)
			case 5:
				stat_movie_catalog()
			case 6:
				random_movie_catalog(movie_catalog)
			case 7:
				search_movie_catalog(movie_catalog)
			case 8:
				sorted_movie_catalog_rating()
			case 9:
				sorted_movie_catalog_year()
			case 10:
				filter_movie_catalog_user(movie_catalog)
			case 11:
				histo_movie_catalog_rating()
			case 12:
				histo_movie_catalog_year()
			case 13:
				generate_website(movie_catalog)
			case 14:
				user_login_screen()

		input(cr.Fore.MAGENTA + "\nPress enter to continue")


if __name__ == "__main__":
	main()