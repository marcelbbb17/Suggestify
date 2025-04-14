from flask import Blueprint, jsonify, request
from database import get_db_connection
from utils.auth_utils import token_required
from utils.movie_utils import parse_list_from_db, build_movie_profile, fetch_movie_details
import requests
import ast
import time
from threading import Lock
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from config import get_config

recommendations_bp = Blueprint('recommendations', __name__)
config = get_config()
TMDB_KEY = config.TMDB_API_KEY

# Used to track ongoing recommendation generations
user_recommendation_locks = {}
lock_mutex = Lock()

# Function to check and set locks for users 
def check_and_set_lock(user_id):
    """Check if a user has a lock and set one if not."""
    with lock_mutex:
        # Check if user already has a lock
        if user_id in user_recommendation_locks:
            # Check if the lock is stale (older than 5 minutes)
            current_time = time.time()
            lock_time = user_recommendation_locks[user_id]
            if current_time - lock_time > 300:  # 5 minutes timeout
                print(f"Found stale lock for user {user_id}, resetting")
                user_recommendation_locks[user_id] = current_time
                return True
            return False
        else:
            # Set a new lock with current timestamp
            user_recommendation_locks[user_id] = time.time()
            return True

# Function to release a lock
def release_lock(user_id):
    """Release a user's lock."""
    with lock_mutex:
        if user_id in user_recommendation_locks:
            del user_recommendation_locks[user_id]

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

def should_refresh_recommendations(user_id):
    """Check if recommendations need to be refreshed."""
    print(f"Checking if recs need to be refreshed for user {user_id}")

    try: 
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM user_recommendations WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result or result['count'] == 0:
            print("No recommendations exist so refresh")
            return True
        
        # If they do exist continue
        print(f"Recommendations do exist: {result['count']}")

        # Get the timestamps for when recommendation were generated 
        cursor.execute("""
            SELECT 
                rm.last_updated AS recs_updated
            FROM user_recommendations_metadata rm
            WHERE rm.user_id = %s
        """, (user_id,))
        metadata_result = cursor.fetchone()
        
        # Gets the questionnaire timestamp for when they were last updated
        cursor.execute("""
            SELECT 
                last_updated AS prefs_updated
            FROM questionnaire
            WHERE user_id = %s
        """, (user_id,))
        questionnaire_result = cursor.fetchone()

        if not metadata_result:
            print("No metadata found so we need to refresh")
            return True 

        if not questionnaire_result:
            # This should never happen but just in case
            print("No questionnaire date found but they have recommendations which is interesting")
            return True 
        
        recs_updated = metadata_result['recs_updated']
        prefs_updated = questionnaire_result['prefs_updated']
        print(f"Timestamps for rec_updated: {recs_updated} and prefs_updated: {prefs_updated}")

        # If preferences were updated after recommendations (Generate new content for user)
        if prefs_updated > recs_updated:
            print("Preferences were updated after recommendations so refresh them")
            return True
        
        # Else update recs if they are older than 24 hours 
        refresh_threshold = datetime.now() - timedelta(hours=24)
        should_refresh = recs_updated < refresh_threshold
        
        if should_refresh:
            print("Recommendations are older than 24 hours so refresh")
        else:
            print("Recommendations are up to date")
            
        return should_refresh
    except Exception as e:
        print(f"Error occurred in the refresh function: {e}")
        return True 
    finally:
        cursor.close()
        connection.close()

def get_stored_recommendations(user_id):
    """Get stored recommendations for a user."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.id, r.user_id, r.movie_id, 
            r.movie_title AS title,  
            r.poster_path, r.overview,
            r.recommendation_score, r.genres, r.actors,
            r.release_date, r.vote_average,
            m.last_updated 
        FROM user_recommendations r 
        JOIN user_recommendations_metadata m ON r.user_id = m.user_id 
        WHERE r.user_id = %s 
        ORDER BY r.recommendation_score DESC
    """, (user_id,))

    recommendations = cursor.fetchall()
    cursor.close()
    connection.close()

    return recommendations

def compute_tfidf_similarity(movie_profiles, favourite_profiles, user_preferences):
    """Compute similarity between movie profiles and user's favorite profiles."""
    # Prevent empty profiles from being processed
    if not movie_profiles or not favourite_profiles:
        print("Error: No valid movie profiles found!")
        return np.zeros((len(favourite_profiles), len(movie_profiles)))
    
    vectorizer = TfidfVectorizer(
        stop_words="english",
        sublinear_tf=True,
        norm="l2",
        max_df=0.85,
        min_df=2
    )

    # Gets the users preferred actors and genres from database
    favourite_genres = user_preferences.get("genres", [])
    favourite_actors = user_preferences.get("favourite_actors", [])

    # Parse the user preferences
    favourite_genres = parse_list_from_db(favourite_genres)
    favourite_actors = parse_list_from_db(favourite_actors)

    # Boost the weighting of user's favorite actors and genres
    boost_genres = (" ".join(favourite_genres) + " ") * 2
    boost_actors = (" ".join(favourite_actors) + " ") * 2

    # Add the boosted genres/actors to the profile to improve recommendations
    boosted_favourite_profiles = []
    for profile in favourite_profiles:
        boosted_profile = f"{profile} {boost_genres}{boost_actors}"
        boosted_favourite_profiles.append(boosted_profile)

    # Transform into TF-IDF matrices
    tfidf_matrix = vectorizer.fit_transform(movie_profiles)
    favourite_tfidf_matrix = vectorizer.transform(boosted_favourite_profiles)
    
    # Compare the two matrices based on similarity
    similarity_scores = cosine_similarity(favourite_tfidf_matrix, tfidf_matrix)
    return similarity_scores

def get_top_recommendations(similarity_scores, all_movies, favorite_titles=None, top_n=20, min_similarity=0.05):
    """Get top recommendations based on similarity scores."""
    import re
    
    # Function to normalize titles for comparison
    def normalize_title(title):
        return re.sub(r'[^\w\s]', '', title).lower().strip()

    def is_same_movie(candidate_title, favourite_title, threshold=0.9):
        candidate_words = set(normalize_title(candidate_title).split())
        favourite_words = set(normalize_title(favourite_title).split())
        # If both sets are empty return false (not same movie)
        if not candidate_words or not favourite_words:
            return False
        # Checks if the two titles are the same or not 
        common = candidate_words.intersection(favourite_words)
        ratio = len(common) / min(len(candidate_words), len(favourite_words))
        return ratio >= threshold

    if similarity_scores is None or similarity_scores.size == 0:
        print("No similarities found returning general movies")
        return all_movies[:top_n]
    
    # Get the max similarity score and sort in descending order
    max_scores = np.max(similarity_scores, axis=0)
    sorted_indices = np.argsort(max_scores)[::-1]
    
    recommendations = []
    seen_movie_ids = set()
    
    for idx in sorted_indices:
        movie = all_movies[idx]
        
        # Skip any movies missing details 
        if "id" not in movie or "title" not in movie or "profile" not in movie:
            print(f"Skipping {movie}")
            continue
        
        # Skip movies that are below min_similarity threshold
        if max_scores[idx] < min_similarity:
            continue
        
        # Final check to prevent recommending movies the user has already seen (based on questionnaire results for now)
        candidate_title = movie["title"]
        skip = False
        if favorite_titles:
            for fav in favorite_titles:
                if is_same_movie(candidate_title, fav):
                    skip = True
                    break
        if skip:
            continue
        
        # Store the recommendations until they reach top_n
        if movie["id"] not in seen_movie_ids:
            recommendations.append(movie)
            seen_movie_ids.add(movie["id"])
            if len(recommendations) >= top_n:
                break
    return recommendations[:top_n]

def fetch_movies_for_user(current_user, user_preferences):
    """Fetch candidate movies for recommendations."""
    from flask import current_app
    
    # Use the movies endpoint to get candidate movies
    response = requests.get(
        "http://127.0.0.1:5000/movies",
        headers={"Authorization": request.headers.get("Authorization")}
    )

    if response.status_code == 200:
        all_movies = response.json().get("movies", [])

        filtered_movies = []
        for movie in all_movies:
            # Count the number of matches between movie and user preferences
            genres = parse_list_from_db(user_preferences["genres"])
            actors = parse_list_from_db(user_preferences["favourite_actors"])
            
            genre_match_count = sum(1 for genre in movie["genres"] if genre in genres)
            actor_match_count = sum(1 for actor in movie["actors"] if actor in actors)
   
            if genre_match_count >= 1 or actor_match_count >= 1:
                filtered_movies.append(movie)

        print(f"Filtered Movies: {len(filtered_movies)}")
        return filtered_movies
    else:
        print(f"Failed to fetch movies: {response.status_code}")
        return []

def save_recommendations(user_id, recommendations):
    """Save recommendations to the database."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # First, delete all existing recommendations
        cursor.execute("DELETE FROM user_recommendations WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} old recommendations")
        
        # Add a set to track which movies we've already inserted
        inserted_movie_ids = set()
        
        # Process each movie individually
        successful_inserts = 0
        for i, movie in enumerate(recommendations):
            try:
                movie_id = int(movie.get("id", 0))
                
                # Skip if we've already inserted this movie
                if movie_id in inserted_movie_ids:
                    print(f"Skipping duplicate movie ID: {movie_id}")
                    continue
                
                inserted_movie_ids.add(movie_id)
                
                # Convert lists to strings for storage
                genres_str = str(movie.get("genres", []))
                actors_str = str(movie.get("actors", []))
                
                cursor.execute("""
                    INSERT INTO user_recommendations 
                    (user_id, movie_id, movie_title, poster_path, overview, 
                     recommendation_score, genres, actors, release_date, vote_average) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    int(user_id), 
                    movie_id,
                    str(movie.get("title", "")),
                    str(movie.get("poster_path", "")),
                    str(movie.get("overview", "")),
                    float(0.0),  
                    genres_str,
                    actors_str,
                    str(movie.get("release_date", "")),
                    float(movie.get("vote_average", 0.0))
                ))
                successful_inserts += 1
            except Exception as e:
                print(f"Error inserting movie #{i}: {e}")
        
        print(f"Successfully inserted {successful_inserts} movies")
        
        # Get current timestamp for metadata
        current_time = datetime.now()
        
        # Update metadata table
        cursor.execute("""
            INSERT INTO user_recommendations_metadata (user_id, last_updated) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE last_updated = %s
        """, (int(user_id), current_time, current_time))
        
        connection.commit()
        return True
    except Exception as e:
        print(f"Fatal error in save_recommendations: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def search_for_movie_by_title(title):
    """Search for a movie by title."""
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={title}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("results", [])
        if data:
            movie_id = data[0]["id"]
            profile_result = build_movie_profile(movie_id)
            if profile_result and len(profile_result) == 2:
                profile, details = profile_result
                if profile and len(profile.split()) >= 5:
                    return profile
    return None

@recommendations_bp.route("/recommend", methods=["GET"])
@token_required
def recommend_movies(current_user):
    """Generate movie recommendations for a user."""
    print(f"Recommendation process has begun for {current_user}")

    connection = get_db_connection()
    cursor = connection.cursor()
    user_id = None

    try: 
        # Get the user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            cursor.close()
            connection.close()
            return jsonify({"error": "User not found"}), 404
    
        user_id = user_result[0]
        cursor.close()
        connection.close()

        # Check if recommendations are already being generated for this user
        if not check_and_set_lock(user_id):
            print(f"Recommendations generation in progress for user {user_id}")
            
            # If recommendations are already being generated, return the stored recommendations with a status
            stored_recs = get_stored_recommendations(user_id)
            if stored_recs:
                for rec in stored_recs:
                    try:
                        rec['genres'] = ast.literal_eval(rec['genres'])
                        rec['actors'] = ast.literal_eval(rec['actors'])
                    except:
                        rec['genres'] = []
                        rec['actors'] = [] 
                print(f"Returning {len(stored_recs)} stored movies while generation is in progress")    
                return jsonify({
                    "recommended_movies": stored_recs, 
                    "status": "generating"
                })
            else:
                return jsonify({
                    "recommended_movies": [], 
                    "status": "generating"
                })

        try:
            # Check if we need to refresh recommendations
            need_to_refresh = should_refresh_recommendations(user_id)

            if not need_to_refresh:
                print("No need to refresh recommendation. Returning stored recommendations")
                release_lock(user_id)  # Release the lock since we're returning stored recommendations
                stored_recs = get_stored_recommendations(user_id)
                if stored_recs:
                    for rec in stored_recs:
                        try:
                            rec['genres'] = ast.literal_eval(rec['genres'])
                            rec['actors'] = ast.literal_eval(rec['actors'])
                        except:
                            rec['genres'] = []
                            rec['actors'] = [] 
                    print(f"Returning {len(stored_recs)} stored movies")    
                    return jsonify({"recommended_movies": stored_recs}) 
            
            # If 24 hours passed or the user hasn't generated recommendations
            print("Generating new recommendations") 
            user_preferences = get_user_preferences(current_user)
            
            # Converts favourite movies from database into a list
            favorite_movies = user_preferences.get("favourite_movies", [])
            favorite_movies = parse_list_from_db(favorite_movies)
            
            # Get movies that match user preferences
            candidate_movies = fetch_movies_for_user(current_user, user_preferences)
            
            if not favorite_movies:
                release_lock(user_id)  # Release lock before returning error
                return jsonify({"error": "No favorite movies found in your preferences"}), 404

            valid_favorite_profiles = []
            for fav_movie in favorite_movies:
                movie_profile = None
                
                # Try to find the movie in candidate movies first
                for movie in candidate_movies:
                    if movie.get("title", "").lower() == fav_movie.lower():
                        movie_profile = movie.get("profile")
                        break
                
                # If not found, search the movie by title
                if not movie_profile:
                    movie_profile = search_for_movie_by_title(fav_movie)
                
                if movie_profile:
                    valid_favorite_profiles.append(movie_profile)
                else:
                    print(f"'{fav_movie}' did not return a valid profile.")

            if not valid_favorite_profiles:
                release_lock(user_id)  # Release lock before returning error
                return jsonify({"error": "No valid favorite movie profiles found"}), 404

            candidate_profiles = [movie["profile"] for movie in candidate_movies if "profile" in movie]
            similarity_scores = compute_tfidf_similarity(candidate_profiles, valid_favorite_profiles, user_preferences)
            
            # Pass favorite_movies to exclude already-watched movies
            recommended_movies = get_top_recommendations(
                similarity_scores, candidate_movies, 
                favorite_titles=favorite_movies, top_n=20
            )

            # Save the recommendations to database
            saved = save_recommendations(user_id, recommended_movies)
            if not saved:
                print("Failed to save recommendations")
                
            # Release the lock after successful completion
            release_lock(user_id)
            
            print(f"Successfully generated {len(recommended_movies)} recommendations")
            return jsonify({"recommended_movies": recommended_movies})
        except Exception as e:
            print(f"Error during recommendation generation: {e}")
            # Make sure to release the lock in case of error
            release_lock(user_id)
            raise e
    except Exception as e:
        # If we have a user_id, make sure to release any lock
        if user_id:
            release_lock(user_id)
        print(f"Error in recommend_movies: {e}")
        return jsonify({"error": "An error occurred gathering recommendations"}), 500