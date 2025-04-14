from flask import Blueprint, jsonify, request
from utils.auth_utils import token_required
from utils.movie_utils import fetch_genre_mapping, get_actors, build_movie_profile, parse_list_from_db
from database import get_db_connection
import requests
import ast
from config import get_config

movies_bp = Blueprint('movies', __name__)
config = get_config()
TMDB_KEY = config.TMDB_API_KEY

def get_user_preferences(email):
    """Get user preferences from the database."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT favourite_movies, genres, favourite_actors 
        FROM questionnaire 
        WHERE user_id = (SELECT id FROM users WHERE email = %s)
    """, (email,))
    user_data = cursor.fetchone()

    cursor.close() 
    connection.close()

    return user_data

@movies_bp.route("/movies", methods=["GET"])
@token_required
def get_movies(current_user):
    """Get movies based on user preferences."""
    total_pages = 5
    all_movies = []
    
    # Get genre mapping
    genre_mapping = fetch_genre_mapping()

    # Get user preferences from database 
    user_preferences = get_user_preferences(current_user)
    if not user_preferences:
        return jsonify({"error": "User preferences not found"}), 404
    
    if len(user_preferences["genres"]) > 5:  
        total_pages = 8 
    
    # Parse the user's preferred genres and actors
    favorite_genres = parse_list_from_db(user_preferences["genres"])
    favorite_actors = parse_list_from_db(user_preferences["favourite_actors"])
    
    # Fetch movies from these 3 categories for now
    categories = {
        "popular": f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_KEY}&language=en-US&page=",
        "top_rated": f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_KEY}&language=en-US&page=",
        "trending": f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_KEY}&language=en-US&page="
    }

    for category, base_url in categories.items():
        for page in range(1, total_pages + 1): 
            url = f"{base_url}{page}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                movies = data.get("results", [])
                for movie in movies:
                    # Get genre ids for the movie
                    genre_ids = movie.get("genre_ids", []) 
                    movie_genres = []
                
                    # Get movie id and create movie profile
                    movie_id = movie["id"]
                    profile_result = build_movie_profile(movie_id)
                    if not profile_result or len(profile_result) != 2:
                        continue  # Skip movies without profile
                    
                    profile, movie_details = profile_result

                    # Convert the genre_ids into actual genres     
                    for genre_id in genre_ids:
                        genre_name = genre_mapping.get(genre_id, "Unknown")
                        movie_genres.append(genre_name)
                    
                    # Check if the movie's genre matches user's preferred genres (at least one of them)
                    matches_favorite_genres = False
                    for genre in movie_genres:
                        if genre in favorite_genres:
                            matches_favorite_genres = True 
                            break 

                    # Check if movie has at least one of the preferred actors
                    actors = get_actors(movie_id)
                    matches_favorite_actors = False 
                    for actor in actors:
                        if actor in favorite_actors:
                            matches_favorite_actors = True 
                            break
                    
                    # If it matches favorite genre or actor, add movie to the list
                    if matches_favorite_genres or matches_favorite_actors:
                        movie["genres"] = movie_genres
                        movie["actors"] = actors
                        movie["profile"] = profile
                        movie.pop("genre_ids", None)
                        all_movies.append(movie)
    
    return jsonify({"movies": all_movies})

@movies_bp.route("/proxy", methods=["GET"])
@token_required
def proxy_api_request(current_user):
    """ Function used to fetch for raw TMBD data """
    try:
        base_url = request.args.get('url')
        if not base_url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        url = f"{base_url}?api_key={TMDB_KEY}&language=en-US"
        
        append_to_response = request.args.get('append_to_response')
        if append_to_response:
            url += f"&append_to_response={append_to_response}"
            
        page = request.args.get('page')
        if page:
            url += f"&page={page}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                genre_mapping = fetch_genre_mapping()
                
                for movie in data['results']:
                    if 'genre_ids' in movie:
                        movie_genres = []
                        for genre_id in movie['genre_ids']:
                            genre_name = genre_mapping.get(genre_id, "Unknown")
                            movie_genres.append(genre_name)
                        
                        movie['genres'] = movie_genres
                        movie.pop('genre_ids', None)
            
            return jsonify(data), 200
        else:
            return jsonify({"error": f"API request failed with status: {response.status_code}"}), response.status_code
            
    except Exception as e:
        print(f"Error in proxy endpoint: {str(e)}")
        return jsonify({"error": "Failed to process API request"}), 500