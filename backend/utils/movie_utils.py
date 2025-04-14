import requests
import ast
from config import get_config

config = get_config()
TMDB_KEY = config.TMDB_API_KEY

def fetch_genre_mapping():
    """Fetch the mapping of genre IDs to names from TMDB."""
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    genre_dict = {}
    
    if response.status_code == 200:
        genres = response.json().get("genres", [])
        for genre in genres:
            genre_id = genre["id"]
            genre_name = genre["name"]
            genre_dict[genre_id] = genre_name
        return genre_dict
    else:
        print("Failed to fetch genre mapping")
        return {}

def get_actors(movie_id):
    """Get the top 5 cast members for a movie."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    actors = []

    if response.status_code == 200:
        credits = response.json()
        cast_list = credits.get("cast", [])[:5]  
        for cast_member in cast_list:
            actor_name = cast_member["name"]
            actors.append(actor_name)
        return actors
    return []

def fetch_movie_details(movie_id):
    """Fetch basic details about a movie."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    genre_list = []

    if response.status_code == 200:
        data = response.json()
        for genre in data.get("genres", []):
            genre_name = genre["name"]
            genre_list.append(genre_name)
        return {
            "title": data.get("title", ""),
            "overview": data.get("overview", ""),
            "poster_path": data.get("poster_path", ""),
            "release_date": data.get("release_date", ""),
            "vote_average": data.get("vote_average", 0),
            "genres": genre_list
        }
    else:
        print(f"Failed to retrieve data for {movie_id}")
        return None

def fetch_keywords_for_movies(movie_id):
    """Fetch keywords for a movie."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={TMDB_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "keywords": [keyword["name"] for keyword in data.get("keywords", [])]
        }
    else:
        print(f"Failed to retrieve keywords for {movie_id}")
        return {"keywords": []}

def build_movie_profile(movie_id):
    """Build a text profile of a movie for similarity comparison."""
    actors = get_actors(movie_id)
    movie_details = fetch_movie_details(movie_id)
    
    if not movie_details:
        return None
    
    keywords_data = fetch_keywords_for_movies(movie_id)
    keywords = keywords_data.get("keywords", [])

    profile = f"{movie_details['title']} {movie_details['overview']} {' '.join(movie_details['genres'])} {' '.join(actors)} {' '.join(keywords)}"

    return profile, movie_details

def parse_list_from_db(list_str):
    """Safely parse a list string from the database."""
    if not list_str:
        return []
        
    if isinstance(list_str, str):
        try:
            return ast.literal_eval(list_str)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing list: {e}")
            return []
    return list_str

def fetch_movie(movie_id):
    """Fetch a single movie by ID."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None