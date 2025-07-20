from flask import Blueprint, jsonify, request
from utils.auth_utils import token_required
from utils.movie_utils import fetch_genre_mapping, get_actors, build_enhanced_movie_profile, parse_list_from_db
from utils.cache_utils import get_cached_data, set_cached_data
from database import get_db_connection
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import ast
from config import get_config
import os

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

    print("Now we are in movies route")
    # Uses caching to avoid repeated API calls 
    cache_key = f"movie_data_{current_user}"
    cached_data = get_cached_data(cache_key)

    if cached_data:
        return jsonify({"movies": cached_data})
    
    # genre mapping
    genre_mapping = fetch_genre_mapping()

    # Gets user prefernce from questionnaire form database 
    user_preferences = get_user_preferences(current_user)
    if not user_preferences:
        return jsonify({"error": "User preferences not found"}), 404
    
    favourite_genres = parse_list_from_db(user_preferences["genres"])
    favourite_actors = parse_list_from_db(user_preferences["favourite_actors"])

    print(f"User preferences loaded: genres={favourite_genres}, actors={favourite_actors}")

    all_movies = [] 
    movie_tasks = []

    categories = {
        "popular": f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_KEY}&language=en-US&page=",
        "top_rated": f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMDB_KEY}&language=en-US&page=",
        "trending": f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_KEY}&language=en-US&page=",
        "now_playing": f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_KEY}&language=en-US&page=",
        "upcoming": f"https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_KEY}&language=en-US&page="        
    }   

    # Auto-detect environment and adjust pages accordingly
    from config import is_production
    
    if is_production():
        pages_per_category = int(os.getenv('PAGES_PER_CATEGORY', '1'))
    else:
        pages_per_category = int(os.getenv('PAGES_PER_CATEGORY', '2'))

    with ThreadPoolExecutor(max_workers=10) as executor:
        for category, base_url in categories.items():
            for page in range(1, pages_per_category + 1):
                url = f"{base_url}{page}"
                movie_tasks.append(executor.submit(fetch_movie_data, url, favourite_genres, favourite_actors, genre_mapping))
        
        for future in as_completed(movie_tasks):
            try:
                movies = future.result()
                if movies:
                    all_movies.extend(movies)
            except Exception as e:
                print(f"Error occured when fecthing movies {e}")
    
    # Duplicate movies by ID
    seen_ids = set()
    unique_movies = []
    for movie in all_movies:
        if movie['id'] not in seen_ids:
            seen_ids.add(movie['id'])
            unique_movies.append(movie)
    
    # cache the results for future requests
    set_cached_data(cache_key, unique_movies, ttl=3600) # cache for 1 hour

    return jsonify({"movies": unique_movies})

def fetch_movie_data(url, favourite_genres, favourite_actors, genre_mapping):
    """Fetch movie data from TMDB API with better error handling."""
    try:
        response = requests.get(url, timeout=10) 
        if response.status_code != 200:
            print(f"Error: Status code {response.status_code} for TMDB API call")
            return []
        
        data = response.json()
        movies = data.get("results", [])
        
        if not movies:
            print("No results found in the response")
            return []
            
        processed_movies = []
        
        # Auto-detect environment and adjust features accordingly
        from config import is_production
        
        if is_production():
            ENABLE_ACTORS = os.getenv('ENABLE_ACTORS', 'false').lower() == 'true'
            ENABLE_ENHANCED_PROFILES = os.getenv('ENABLE_ENHANCED_PROFILES', 'false').lower() == 'true'
        else:
            ENABLE_ACTORS = os.getenv('ENABLE_ACTORS', 'true').lower() == 'true'
            ENABLE_ENHANCED_PROFILES = os.getenv('ENABLE_ENHANCED_PROFILES', 'true').lower() == 'true'
        
        for i, movie in enumerate(movies):
            try:
                if not isinstance(movie, dict):
                    continue
                
                # Process genre info
                movie_genres = []
                genre_ids = movie.get("genre_ids", [])
                if genre_ids:
                    for genre_id in genre_ids:
                        genre_name = genre_mapping.get(genre_id, "unknown")
                        movie_genres.append(genre_name)
                
                # Get actors (configurable)
                movie_id = movie.get("id")
                if not movie_id:
                    continue
                    
                if ENABLE_ACTORS:
                    try:
                        actors = get_actors(movie_id)
                    except Exception as e:
                        print(f"Error getting actors for movie {movie_id}: {e}")
                        actors = []
                else:
                    actors = []
                
                # Get enhanced profile (configurable)
                if ENABLE_ENHANCED_PROFILES:
                    try:
                        profile_result = build_enhanced_movie_profile(movie_id)
                        if profile_result:
                            profile, enhanced_elements, details = profile_result
                            movie["genres"] = movie_genres
                            movie["actors"] = actors
                            movie["profile"] = profile
                            movie["themes"] = enhanced_elements.get("themes", [])
                            movie["tones"] = enhanced_elements.get("tones", [])
                            movie["franchises"] = enhanced_elements.get("franchises", [])
                            movie.pop("genre_ids", None)
                            processed_movies.append(movie)
                    except Exception as e:
                        print(f"Error building profile for movie {movie_id}: {e}")
                        # Fallback to basic info
                        movie["genres"] = movie_genres
                        movie["actors"] = actors
                        movie.pop("genre_ids", None)
                        processed_movies.append(movie)
                else:
                    # Basic processing only
                    movie["genres"] = movie_genres
                    movie["actors"] = actors
                    movie.pop("genre_ids", None)
                    processed_movies.append(movie)
                    
            except Exception as e:
                print(f"Error processing movie {i}: {e}")
                continue
        print(f"Successfully processed {len(processed_movies)} out of {len(movies)} movies")     
        return processed_movies
    except Exception as e:
        print(f"An error occurred in fetch_movie_data: {e}")
        return []
    
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
            print(f"Error: Status code {response.status_code} for TMDB API call ")
            return jsonify({"error": "Failed to fetch from TMDB"}), 500
            
    except Exception as e:
        print(f"Error in proxy endpoint: {str(e)}")
        return jsonify({"error": "Failed to process API request"}), 500