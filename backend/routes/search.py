from flask import Blueprint, jsonify, request
from utils.auth_utils import token_required
from utils.movie_utils import fetch_genre_mapping, get_actors
import requests
from config import get_config

search_bp = Blueprint('search', __name__)
config = get_config()
TMDB_KEY = config.TMDB_API_KEY

@search_bp.route("/search", methods=["GET"])
@token_required
def search_movies(current_user):
    """Search for movies based on user search input."""
    query = request.args.get('query', "")

    if not query:
        return jsonify({"error": "Search query is too short"}), 400
    
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&language=en-US&query={query}&page=1&include_adult=false"

    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            # Get the names of the genres     
            genre_mapping = fetch_genre_mapping()

            for movie in results:
                genre_ids = movie.get("genre_ids", [])
                movie_genre = []

                for genre_id in genre_ids:
                    genre_name = genre_mapping.get(genre_id, "unknown")
                    movie_genre.append(genre_name)
                
                movie["genres"] = movie_genre
                movie.pop("genre_ids", None)

                # Get actors of each movie 
                movie["actors"] = get_actors(movie["id"])
            
            return jsonify({"results": results}), 200
        else:
            return jsonify({"error": "Failed to get movies"}), 500
    except Exception as e:
        print(f"An error occurred when fetching movies: {str(e)}")
        return jsonify({"error": "An error occurred when fetching movies"}), 500