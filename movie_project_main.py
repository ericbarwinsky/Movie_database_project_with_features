import os
import statistics as stat
import random as rm
import difflib

import colorama as cr
import matplotlib.pyplot as plt

from storage import movie_storage_sql as ms


def print_menu_movie_catalog():
    """Shows menu on terminal."""
    print(cr.Fore.MAGENTA + "\nMenu:")
    print("0. Exit")
    print("1. List movies")
    print("2. Add movie")
    print("3. Delete movie")
    print("4. Stats")
    print("5. Random movie")
    print("6. Search movie")
    print("7. Movie sorted by rating")
    print("8. Movie sorted by year")
    print("9. Movie filter")
    print("10. Create rating histogramm")
    print("11. Create year histogramm")
    print("12. Generate Website\n")


def get_user_menu_number():
    """Returns a valid user input from the menu options."""
    while True:
        try:
            user_choice = int(input(cr.Fore.LIGHTBLUE_EX + "Enter choice (0-12)   "))
        except ValueError:
            print(cr.Fore.RED + "Invalid input, choose a number from 0 to 12")
        else:
            if 0 <= user_choice <= 12:
                return user_choice
            else:
                print(cr.Fore.RED + "Invalid input, choose a number from 0 to 12")


def show_movie_catalog(movie_catalog):
    """Displays the date entry from the database."""
    counter = len(movie_catalog)
    print(f"{counter} movies in total")
    for movie, data in movie_catalog.items():
        rating = data["rating"]
        release_year = data["release_year"]
        print(f"{movie} ({release_year}): {rating}")


def add_movie_catalog(movie_catalog):
    """Queries the OMDb API for a movie title and adds the fetched details to the database."""
    movie_title = input(cr.Fore.LIGHTBLUE_EX + "Please enter the movie title to search and add: ").strip()

    if len(movie_title) < 1:
        print(cr.Fore.RED + "Movie name must not be empty.")
        return

    print(cr.Fore.YELLOW + f"Searching for '{movie_title}' on OMDb...")

    try:
        movie_data = ms.fetch_movie_from_api(movie_title)

        if movie_data is None:
            print(cr.Fore.RED + f"Movie '{movie_title}' not found in the OMDb database.")
            return

        if movie_data["title"] in movie_catalog:
            print(cr.Fore.RED + f"'{movie_data['title']}' already exists in your local database.")
            return

        success = ms.add_movie(
            movie_data["title"],
            movie_data["year"],
            movie_data["rating"],
            movie_data["poster_url"]
        )

        if success:
            print(cr.Fore.GREEN + f"\nMovie successfully added!")
            print(f"Title: {movie_data['title']}")
            print(f"Year:  {movie_data['year']}")
            print(f"Grade: {movie_data['rating']}")
            print(f"Poster: {movie_data['poster_url']}")

    except ConnectionError as ce:
        print(cr.Fore.RED + f"Network Error: {ce}")
    except ValueError as ve:
        print(cr.Fore.RED + f"Configuration Error: {ve}")


def delete_movie_catalog(movie_catalog):
    """Delete a movie from the database by title."""
    delete_title = input(cr.Fore.LIGHTBLUE_EX + "Please enter the title to be deleted: ").strip()
    if delete_title in movie_catalog:
        ms.delete_movie(delete_title)
        print(cr.Fore.MAGENTA + f"The movie '{delete_title}' was deleted.")
    else:
        print(cr.Fore.RED + f"The title '{delete_title}' does not exist!")


def stat_movie_catalog():
    """Display statistics: average, median, best and worst movies."""
    movie_catalog_data = ms.get_movie_one_data("rating")

    if not movie_catalog_data:
        print(cr.Fore.RED + "No movies in database.")
        return

    evaluations = list(movie_catalog_data.values())
    average_movies = stat.mean(evaluations)
    median_movies = stat.median(evaluations)
    print(f"Average rating: {average_movies:.1f}")
    print(f"Median of movies: {median_movies} ")

    max_evaluation = max(evaluations)
    min_evaluation = min(evaluations)
    best_movie = [title for title, evalu in movie_catalog_data.items() if evalu == max_evaluation]
    worst_movie = [title for title, evalu in movie_catalog_data.items() if evalu == min_evaluation]
    print(f"Best movie(s): {', '.join(best_movie)}, {max_evaluation}")
    print(f"Worst movie(s): {', '.join(worst_movie)}, {min_evaluation}")


def random_movie_catalog(movie_catalog):
    """Select and display a random movie from the catalog."""
    if not movie_catalog:
        print(cr.Fore.RED + "No movies in database.")
        return

    random_movie = rm.choice(list(movie_catalog))
    rating = movie_catalog[random_movie]["rating"]
    release_year = movie_catalog[random_movie]["release_year"]
    print(f"Your movie for tonight from the year"
          f" {release_year}: {random_movie}, it's rated {rating}")


def search_movie_catalog(movie_catalog):
    """Search for movies by partial title match using fuzzy matching."""
    user_search = input(cr.Fore.LIGHTBLUE_EX + "Enter part of movie name: ").strip().lower()
    if not user_search:
        print(cr.Fore.RED + "Search query cannot be empty.")
        return

    search_list = []
    close_matches = difflib.get_close_matches(user_search,
                                              [title.lower() for title in movie_catalog],
                                              n=len(movie_catalog), cutoff=0.4)

    for match in close_matches:
        for title in movie_catalog:
            if match == title.lower():
                search_list.append(f"{title} ({movie_catalog[title]['release_year']}):"
                                   f" {movie_catalog[title]['rating']}")

    if search_list:
        for searching in search_list:
            print(searching)
    else:
        print(cr.Fore.RED + "No suitable film title found")


def user_choice_sorted_rotation():
    """Ask user if sorted list should start from 'highest' value (Y/N)."""
    while True:
        user_choice = input(cr.Fore.LIGHTBLUE_EX +
                            "Do you want to start from the highest value? (Y)Yes (N)No   ").strip().lower()
        match user_choice:
            case "y":
                return True
            case "n":
                return False
            case _:
                print(cr.Fore.RED + "Invalid input")
                continue


def sorted_movie_catalog_rating():
    """Display movies sorted by rating."""
    movie_catalog_data = ms.get_movie_one_data("rating")
    if not movie_catalog_data:
        print(cr.Fore.RED + "No movies in database.")
        return

    list_tupel_movie_catalog = list(movie_catalog_data.items())
    rotation_choice = user_choice_sorted_rotation()
    list_tupel_movie_catalog.sort(key=lambda x: x[1], reverse=rotation_choice)
    for title, grade in list_tupel_movie_catalog:
        print(f"{title}: {grade}")


def histo_movie_catalog_rating():
    """Create and display histogram of movie ratings (0-10)."""
    movie_catalog_data = ms.get_movie_one_data("rating")
    if not movie_catalog_data:
        print(cr.Fore.RED + "No movies in database to create a histogram.")
        return

    movie_catalog_value = list(movie_catalog_data.values())
    plt.figure(figsize=(8, 6))
    plt.hist(movie_catalog_value, bins=range(0, 11), edgecolor="black")
    plt.title("Distribution of movie ratings")
    plt.xlabel("Grade (1-10)")
    plt.ylabel("Number of movies")
    plt.xticks(range(1, 11))
    plt.grid(axis="y")
    plt.show()


def sorted_movie_catalog_year():
    """Display movies sorted by release year."""
    movie_catalog_data = ms.get_movie_one_data("release_year")
    if not movie_catalog_data:
        print(cr.Fore.RED + "No movies in database.")
        return

    list_tupel_movie_catalog = list(movie_catalog_data.items())
    rotation_choice = user_choice_sorted_rotation()
    list_tupel_movie_catalog.sort(key=lambda x: x[1], reverse=rotation_choice)
    for title, grade in list_tupel_movie_catalog:
        print(f"{title}: {grade}")


def histo_movie_catalog_year():
    """Create and display histogram of movie release years."""
    movie_catalog_data = ms.get_movie_one_data("release_year")
    if not movie_catalog_data:
        print(cr.Fore.RED + "No movies in database.")
        return

    value_movie_catalog = list(movie_catalog_data.values())
    highest_year = max(value_movie_catalog)
    lowest_year = min(value_movie_catalog)

    plt.figure(figsize=(18, 6))
    plt.hist(value_movie_catalog,
             bins=range(lowest_year, highest_year + 2),
             edgecolor="black")

    plt.title("Distribution of movie years")
    plt.xlabel("Years 19XX-20XX")
    plt.ylabel("Number of movies")
    years = list(range(lowest_year, highest_year + 1))
    labels = [str(y)[-2:] for y in years]
    plt.xticks(years, labels)
    plt.grid(axis="y")
    plt.show()


def filter_movie_catalog_user(movie_catalog):
    """Filter movies by minimum rating and year range."""
    raw_rating = input(cr.Fore.LIGHTBLUE_EX + "Enter minimum rating (leave blank for 0): ").strip()
    try:
        filter_rating = float(raw_rating) if raw_rating else 0.0
    except ValueError:
        print(cr.Fore.RED + "Invalid rating input. Using 0.")
        filter_rating = 0.0

    raw_start = input(cr.Fore.LIGHTBLUE_EX + "Enter start year (leave blank for 0): ").strip()
    try:
        filter_start_year = int(raw_start) if raw_start else 0
    except ValueError:
        print(cr.Fore.RED + "Invalid start year. Using 0.")
        filter_start_year = 0

    raw_end = input(cr.Fore.LIGHTBLUE_EX + "Enter end year (leave blank for 3000): ").strip()
    try:
        filter_end_year = int(raw_end) if raw_end else 3000
    except ValueError:
        print(cr.Fore.RED + "Invalid end year. Using 3000.")
        filter_end_year = 3000

    print("\nFiltered Movies:")
    found = False
    for movie, data in movie_catalog.items():
        if data["rating"] >= filter_rating:
            if filter_start_year <= data["release_year"] <= filter_end_year:
                print(f'{movie} ({data["release_year"]}): {data["rating"]}')
                found = True

    if not found:
        print(cr.Fore.YELLOW + "No movies matched your filter criteria.")


def generate_website(movie_catalog):
    """Generates a static HTML website from the current movie database using a template."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    template_path = os.path.join(current_dir, "_static", "index_template.html")
    output_path = os.path.join(current_dir, "_static", "index.html")

    if not os.path.exists(template_path):
        print(cr.Fore.RED + f"Error: Template file not found at {template_path}")
        return

    if not movie_catalog:
        print(cr.Fore.RED + "No movies in database to generate a website.")
        return

    print(cr.Fore.YELLOW + "Generating website...")

    movie_grid_html = ""
    for title, data in movie_catalog.items():
        poster_url = data.get("poster_url")

        if not poster_url or poster_url == "N/A":
            poster_url = "https://via.placeholder.com/128x193?text=No+Poster"

        year = data.get("release_year", "N/A")

        movie_grid_html += f"""
        <li>
            <div class="movie">
                <img class="movie-poster" src="{poster_url}" alt="{title} Poster">
                <div class="movie-title">{title}</div>
                <div class="movie-year">{year}</div>
            </div>
        </li>
        """

    try:
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        html_content = template_content.replace("__TEMPLATE_TITLE__", "My Movie Database")
        html_content = html_content.replace("__TEMPLATE_MOVIE_GRID__", movie_grid_html)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        print(cr.Fore.GREEN + f"Website successfully generated at: {output_path}")

    except Exception as e:
        print(cr.Fore.RED + f"An error occurred while generating the website: {e}")


def main():
    """Main program loop: display menu and handle user choices."""
    print("********** My Movies Database **********")
    while True:
        movie_catalog = ms.list_movies()

        print_menu_movie_catalog()
        user_choice = get_user_menu_number()
        match user_choice:
            case 0: print(cr.Fore.MAGENTA + "Bye!"); break
            case 1: show_movie_catalog(movie_catalog)
            case 2: add_movie_catalog(movie_catalog)
            case 3: delete_movie_catalog(movie_catalog)
            case 4: stat_movie_catalog()
            case 5: random_movie_catalog(movie_catalog)
            case 6: search_movie_catalog(movie_catalog)
            case 7: sorted_movie_catalog_rating()
            case 8: sorted_movie_catalog_year()
            case 9: filter_movie_catalog_user(movie_catalog)
            case 10: histo_movie_catalog_rating()
            case 11: histo_movie_catalog_year()
            case 12: generate_website(movie_catalog)
            case _: print(cr.Fore.RED + "Invalid enter")
        input(cr.Fore.MAGENTA + "\nPress enter to continue")


if __name__ == "__main__":
    main()