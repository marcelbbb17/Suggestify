from flask import Blueprint, jsonify, request
from database import get_db_connection
from utils.auth_utils import token_required
from utils.movie_utils import (
    parse_list_from_db, 
    build_enhanced_movie_profile,
    fetch_movie, 
    fetch_movie_by_title, 
    fetch_movies_by_genre, 
    fetch_movies_by_keyword,
    is_same_movie
)
from routes.watchlist import get_user_watchlist_preferences
from utils.cache_utils import cache_decorator
from models.user_preference_model import UserPreferenceModel, build_user_preference_model
import requests
import ast
import json
import time
from threading import Lock
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from config import get_config
import os

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
    """ Check if recommendations need to be refreshed """
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

        # Get the timestamps for when recommendations were generated 
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
        
        # Handle null timestamps
        if recs_updated is None:
            print("No recommendation timestamp, need to refresh")
            return True    
        
        if prefs_updated is None:
            print("No preferences timestamp, using current time")
            prefs_updated = datetime.now()

        # If preferences were updated after recommendations (Generate new content for user)
        if prefs_updated > recs_updated:
            print("Preferences were updated after recommendations so refresh them")
            return True
        
        # Check if we received any new feedback that should trigger a refresh
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM recommendation_feedback
            WHERE user_id = %s AND feedback_date > %s
        """, (user_id, recs_updated))
        
        feedback_result = cursor.fetchone()
        if feedback_result and feedback_result['count'] > 0:
            print(f"Found {feedback_result['count']} new feedback items since last update")
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
    """ Get stored recommendations for a user """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
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
        return recommendations
    except Exception as e:
        print(f"Error fetching stored recommendations: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_profiles_for_favorite_movies(favorite_movies, candidate_movies=None):
    """ Get profiles for favorite movies """
    valid_profiles = []
    
    print(f"DEBUG: Starting get_profiles_for_favorite_movies with {len(favorite_movies)} favorite movies")
    
    for i, fav_movie in enumerate(favorite_movies):
        try:
            print(f"DEBUG: Processing favorite movie {i+1}/{len(favorite_movies)}: {fav_movie}")
            
            # Try to find in candidate movies first
            if candidate_movies:
                for movie in candidate_movies:
                    if is_same_movie(movie.get("title", ""), fav_movie):
                        if "profile" in movie:
                            valid_profiles.append(movie.get("profile"))
                            print(f"DEBUG: Found profile in candidate movies for {fav_movie}")
                            continue
            
            # If not found, search directly
            movie_details = fetch_movie_by_title(fav_movie)
            if movie_details:
                movie_id = movie_details.get("id")
                if movie_id:
                    profile_result = build_enhanced_movie_profile(movie_id)
                    if profile_result:
                        profile_text = profile_result[0]
                        valid_profiles.append(profile_text)
                        continue
            
            # Fallback to simplified profile
            simplified_profile = f"{fav_movie} {fav_movie} movie film cinema"
            valid_profiles.append(simplified_profile)            
        except Exception as e:
            print(f"Error building profile for {fav_movie}: {e}")
            minimal_profile = f"{fav_movie} movie"
            valid_profiles.append(minimal_profile)
    
    print(f"DEBUG: Completed get_profiles_for_favorite_movies with {len(valid_profiles)} profiles")
    return valid_profiles

def get_fallback_recommendations(user_preferences):
    """ Provide fallback recommendations when normal process fails """
    try:
        print("Generating fallback recommendations")
        recommendations = []
        
        # Use user's favourite genres to fetch recommendations
        favorite_genres = parse_list_from_db(user_preferences.get("genres", []))
        
        # Fetch popular movies for each genre
        for genre in favorite_genres:
            try:
                genre_movies = fetch_movies_by_genre(genre, limit=5)
                recommendations.extend(genre_movies)
            except Exception as e:
                print(f"Error fetching movies for genre {genre}: {e}")
        
        # If still no recommendations, just get popular movies
        if not recommendations:
            try:
                url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_KEY}&language=en-US&page=1"
                response = requests.get(url)
                if response.status_code == 200:
                    popular_movies = response.json().get("results", [])
                    recommendations.extend(popular_movies[:20])
                    print(f"Added {len(popular_movies[:20])} popular movies as fallback")
            except Exception as e:
                print(f"Error fetching popular movies: {e}")
        
        # Process and return fallback recommendations
        processed_recommendations = []
        for movie in recommendations:
            movie["recommendation_score"] = 0.5  # Neutral score
            processed_recommendations.append(movie)
        
        return processed_recommendations[:20]  
    except Exception as e:
        print(f"Error generating fallback recommendations: {e}")
        return []


def save_enhanced_recommendations(user_id, recommendations):
    """ Save enhanced recommendations to the database """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Delete all existing recommendations
        cursor.execute("DELETE FROM user_recommendations WHERE user_id = %s", (user_id,))
        print(f"Deleted {cursor.rowcount} old recommendations")
        
        # Add a set to track which movies we've already inserted
        inserted_movie_ids = set()
        
        # Process each movie individually
        successful_inserts = 0
        for i, movie in enumerate(recommendations):
            try:
                movie_id = int(movie.get("id", 0))
                if not movie_id:
                    continue
                
                # Skip if we've already inserted this movie
                if movie_id in inserted_movie_ids:
                    continue
                
                inserted_movie_ids.add(movie_id)
                
                # Convert lists to strings for storage
                genres_str = str(movie.get("genres", []))
                actors_str = str(movie.get("actors", []))
                
                # Get recommendation score
                try:
                    rec_score = float(movie.get("recommendation_score", 0.0))
                except (TypeError, ValueError):
                    rec_score = 0.0
                
                # Adds results to the database
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
                    rec_score,  
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

def save_recommendation_explanations(user_id, recommendations):
    """ Save explanations for why movies were recommended to a user """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Clear previous explanations
        cursor.execute("DELETE FROM recommendation_explanations WHERE user_id = %s", (user_id,))
        
        for movie in recommendations:
            movie_id = movie.get('id')
            score_breakdown = movie.get('_score_breakdown', {})
            
            # Generate explanation
            explanation = generate_recommendation_explanation(movie)
            
            # Insert explanation into database
            cursor.execute("""
                INSERT INTO recommendation_explanations 
                (user_id, movie_id, explanation, aspects, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (
                user_id,
                movie_id,
                explanation,
                json.dumps(score_breakdown)
            ))
        
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Error saving recommendation explanations: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def generate_recommendation_explanation(movie):
    """ Generate explanation for why this movie was recommended """
    score_breakdown = movie.get("_score_breakdown", {})
    explanation = f"We recommended {movie.get('title', 'this movie')} because "
    
    reasons = []
    
    # Add genre-based explanation if it's a significant factor
    if score_breakdown.get("genre_boost", 0) > 0.05:
        genres = movie.get("genres", [])
        if genres:
            genres_text = ", ".join(genres[:3])
            reasons.append(f"it's in the {genres_text} genre(s) that you seem to enjoy")
    
    # Add theme-based explanation
    if score_breakdown.get("theme_score", 0) > 0.05:
        themes = movie.get("themes", [])
        if themes:
            themes_text = ", ".join(themes[:2])
            reasons.append(f"it explores themes like {themes_text} that appear in other movies you like")
    
    # Add franchise-based explanation
    if score_breakdown.get("franchise_score", 0) > 0.1:
        franchises = movie.get("franchises", [])
        if franchises:
            franchise = franchises[0].replace("_", " ").title()
            reasons.append(f"it's part of the {franchise} universe that you seem to enjoy")
    
    # Add actor-based explanation
    if score_breakdown.get("actor_boost", 0) > 0.03:
        actors = movie.get("actors", [])
        if actors:
            actors_text = ", ".join(actors[:2])
            reasons.append(f"it stars {actors_text} who appear in other movies you like")
    
    # Add rating explanation if it's highly rated
    if movie.get("vote_average", 0) >= 7.5:
        reasons.append(f"it's highly rated with a score of {movie.get('vote_average')}")
    
    # Add recency explanation for new movies
    if movie.get("release_date", ""):
        try:
            release_year = int(movie.get("release_date", "").split("-")[0])
            current_year = datetime.now().year
            if current_year - release_year <= 1:
                reasons.append("it's a recent release")
        except:
            pass
    
    # Combine all reasons
    if not reasons:
        explanation += "it matches your overall taste in movies."
    else:
        explanation += ", ".join(reasons[:-1])
        if len(reasons) > 1:
            explanation += f", and {reasons[-1]}."
        else:
            explanation += f"{reasons[0]}."
    
    return explanation

@cache_decorator(ttl=3600)  # Cache for 1 hour    
def fetch_movies_for_user(current_user, user_preferences):
    """ Fetch candidate movies for recommendations """
    from flask import current_app, request
    from config import is_production
    
    # Auto-detect environment and set appropriate base URL
    if is_production():
        # Production environment (Render)
        BASE_URL = os.getenv('API_BASE_URL', 'https://suggestify-backend-cuvb.onrender.com')
    else:
        # Local development
        BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    
    movies_url = f"{BASE_URL}/movies"
    
    print(f"DEBUG: About to make request to {movies_url}")
    print(f"DEBUG: Authorization header: {request.headers.get('Authorization')[:20] if request.headers.get('Authorization') else 'None'}...")
    
    try:
        response = requests.get(
            movies_url,
            headers={"Authorization": request.headers.get("Authorization")},
        )
        print(f"DEBUG: Response status code: {response.status_code}")
        
        if response.status_code == 200:
            all_movies = response.json().get("movies", [])
            print(f"DEBUG: Successfully got {len(all_movies)} movies")
            return all_movies
        else:
            print(f"DEBUG: Failed to fetch movies: {response.status_code}")
            print(f"DEBUG: Response content: {response.text[:200]}...")
            return []
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: Connection error to /movies: {e}")
        return []
    except Exception as e:
        print(f"DEBUG: Unexpected error in fetch_movies_for_user: {e}")
        return []

def add_enhanced_profile_to_movie(movie):
    """Add enhanced profile data to a movie object."""
    if not movie or "id" not in movie:
        return movie
    
    # Check if we already have enhanced profile info
    if "profile" in movie and "themes" in movie:
        return movie
        
    movie_id = movie.get("id")
    
    # Try to get enhanced profile from the database first
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM movie_enhanced_profiles
            WHERE movie_id = %s
        """, (movie_id,))
        
        profile_data = cursor.fetchone()
        
        if profile_data:
            # Add profile data to the movie
            movie["profile"] = profile_data.get("profile_text")
            movie["themes"] = json.loads(profile_data.get("themes", "[]"))
            movie["tones"] = json.loads(profile_data.get("tones", "[]"))
            movie["target_audience"] = profile_data.get("target_audience")
            movie["franchises"] = json.loads(profile_data.get("franchises", "[]"))
            movie["core_concepts"] = json.loads(profile_data.get("core_concepts", "[]"))
            
            return movie
            
        # If not in database, generate and store
        try:
            profile_result = build_enhanced_movie_profile(movie_id)
            
            if profile_result and len(profile_result) >= 3:
                profile_text, enhanced_elements, movie_details = profile_result
                
                # Update the movie with enhanced data
                movie["profile"] = profile_text
                movie["themes"] = enhanced_elements.get("themes", [])
                movie["tones"] = enhanced_elements.get("tones", [])
                movie["target_audience"] = enhanced_elements.get("target_audience", "general")
                movie["franchises"] = enhanced_elements.get("franchises", [])
                movie["core_concepts"] = enhanced_elements.get("core_concepts", [])
                
                # Add additional details if not present
                if "genres" not in movie:
                    movie["genres"] = enhanced_elements.get("genres", [])
                if "actors" not in movie:
                    movie["actors"] = enhanced_elements.get("actors", [])
                
                # Store in database for future use
                cursor.execute("""
                    INSERT INTO movie_enhanced_profiles
                    (movie_id, profile_text, themes, tones, target_audience, franchises, core_concepts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    profile_text = VALUES(profile_text),
                    themes = VALUES(themes),
                    tones = VALUES(tones),
                    target_audience = VALUES(target_audience),
                    franchises = VALUES(franchises),
                    core_concepts = VALUES(core_concepts)
                """, (
                    movie_id,
                    profile_text,
                    json.dumps(enhanced_elements.get("themes", [])),
                    json.dumps(enhanced_elements.get("tones", [])),
                    enhanced_elements.get("target_audience", "general"),
                    json.dumps(enhanced_elements.get("franchises", [])),
                    json.dumps(enhanced_elements.get("core_concepts", []))
                ))
                
                connection.commit()
        except Exception as e:
            print(f"Error generating enhanced profile for movie {movie_id}: {e}")
    except Exception as e:
        print(f"Database error in add_enhanced_profile_to_movie: {e}")
    finally:
        cursor.close()
        connection.close()
    
    return movie

def compute_enhanced_recommendations(user_id, candidate_movies, user_preferences, favourite_profiles, user_preference_model=None, top_n=20):
    """ Compute movie recommendations with user preference model """
    print("DEBUG: Inside compute_enhanced_recommendations")
    print(f"DEBUG: Received {len(candidate_movies)} candidate movies")
    print(f"DEBUG: Received {len(favourite_profiles)} favorite profiles")
    
    if not candidate_movies or not favourite_profiles:
        return []
    
    filtered_candidates = exclude_disliked_movies(user_id, candidate_movies)
    print(f"DEBUG: After disliked filtering: {len(filtered_candidates)} candidates remain (filtered out {len(candidate_movies) - len(filtered_candidates)} movies)")
    
    # If no preference model provided, use current weights
    weights = None
    if user_preference_model:
        weights = user_preference_model.get_preference_weights()
    
    # Get watchlist preferences 
    try:
        watchlist_preferences = get_user_watchlist_preferences(user_id)
        watchlist_movie_ids = watchlist_preferences.get('all_watchlist_movie_ids', [])
        print(f"Found {len(watchlist_movie_ids)} watchlist items")
    except Exception as e:
        print(f"Error getting watchlist preferences: {e}")
        watchlist_preferences = {"all_watchlist_movie_ids": [], "liked_genres": [], "liked_actors": []}
        watchlist_movie_ids = []
    
    # Get user's favorite movies and convert to lowercase for comparison
    try:
        favorite_movies = parse_list_from_db(user_preferences.get("favourite_movies", []))
        favorite_movies_lower = [movie.lower() for movie in favorite_movies]
    except Exception as e:
        print(f"Error processing favorite movies: {e}")
        favorite_movies = []
        favorite_movies_lower = []
    
    # Remove movies already in watchlist or favorites
    filtered_candidates_final = []
    skipped_watchlist = 0
    skipped_favorites = 0
    
    for i, movie in enumerate(filtered_candidates):
        try:
            # Skip if missing required fields
            if not movie.get("id") or not movie.get("title"):
                continue
            
            # Add enhanced profile data if not already present
            if "profile" not in movie or "themes" not in movie:
                movie = add_enhanced_profile_to_movie(movie)
            
            # Skip if in watchlist
            movie_id = str(movie["id"]) if movie["id"] is not None else None
            if movie_id and any(str(movie_id) == str(wl_id) for wl_id in watchlist_movie_ids):
                skipped_watchlist += 1
                continue
                
            # Skip if it's a favorite movie
            is_favorite = False
            movie_title = movie.get("title", "").lower()
            for fav in favorite_movies_lower:
                if is_same_movie(movie_title, fav):
                    is_favorite = True
                    break
            if is_favorite:
                skipped_favorites += 1
                continue
                
            filtered_candidates_final.append(movie)
        except Exception as e:
            print(f"DEBUG: Error filtering movie {i}: {e}")
    
    # Combine genre preferences from questionnaire and highly rated movies 
    try:
        questionnaire_genres = parse_list_from_db(user_preferences.get("genres", []))
        liked_genres = watchlist_preferences.get('liked_genres', [])
        combined_genres = list(set(questionnaire_genres + liked_genres))
    except Exception as e:
        print(f"Error combining genres: {e}")
        combined_genres = parse_list_from_db(user_preferences.get("genres", []))
    
    # Combine actors 
    try:
        questionnaire_actors = parse_list_from_db(user_preferences.get('favourite_actors', []))
        liked_actors = watchlist_preferences.get('liked_actors', [])
        combined_actors = list(set(questionnaire_actors + liked_actors))
    except Exception as e:
        print(f"Error combining actors: {e}")
        combined_actors = parse_list_from_db(user_preferences.get('favourite_actors', []))
    
    # Get movie profiles for TF-IDF 
    movie_profiles = []
    movie_indices = []
    
    for i, movie in enumerate(filtered_candidates_final):
        try:
            if "profile" in movie and movie["profile"]:
                movie_profiles.append(movie["profile"])
                movie_indices.append(i)
        except Exception as e:
            print(f"DEBUG: Error accessing movie profile: {e}")
    
    # Boosted profiles for user preferences
    try:
        boosted_genres = (" ".join(combined_genres) + " ") * 2
        boosted_actors = (" ".join(combined_actors) + " ") * 2

        boosted_profiles = []
        for profile in favourite_profiles:
            boosted_profile = f"{profile} {boosted_genres} {boosted_actors}"
            boosted_profiles.append(boosted_profile)
    except Exception as e:
        print(f"DEBUG: Error creating boosted profiles: {e}")
        boosted_profiles = favourite_profiles.copy()

    # Compute TF-IDF similarity 
    vectorizer = TfidfVectorizer(
        stop_words="english",
        sublinear_tf=True,
        norm="l2",
        max_df=0.85,
        min_df=2
    )

    # Compute similarity if we have valid profiles
    similarity_scores = None
    if movie_profiles and boosted_profiles:
        try:
            tfidf_matrix = vectorizer.fit_transform(movie_profiles)
            favorite_tfidf_matrix = vectorizer.transform(boosted_profiles)
            similarity_scores = cosine_similarity(favorite_tfidf_matrix, tfidf_matrix)
            print("Successfully computed similarity scores")
        except Exception as e:
            print(f"Error computing similarity: {e}")
            similarity_scores = None
    else:
        print("Not enough profiles for similarity computation")
    
    # Get similarity scores 
    if similarity_scores is not None and similarity_scores.size > 0:
        max_scores = np.max(similarity_scores, axis=0)
    else:
        # If similarity comparison fails
        max_scores = np.ones(len(movie_indices)) * 0.5

    # Score and rank movies 
    scored_movies = []
    
    # Define default weights if none provided
    if not weights:
        weights = {
            "base_similarity": 0.2,
            "genre_match": 0.3,
            "actor_match": 0.15,
            "theme_match": 0.15,
            "tone_match": 0.05,
            "franchise_match": 0.05,
            "audience_match": 0.05,
            "rating_boost": 0.05
        }
    
    for idx, i in enumerate(movie_indices):
        try:
            movie = filtered_candidates_final[i]
            
            # Base similarity score (from TF-IDF)
            base_score = max_scores[idx] if idx < len(max_scores) else 0.5
            base_score = base_score * weights.get("base_similarity", 0.2)

            # Genre match boost
            movie_genres = movie.get("genres", [])
            if not isinstance(movie_genres, list):
                movie_genres = []
                
            matching_genres = sum(1 for genre in movie_genres if genre in combined_genres)
            if combined_genres:
                genre_boost = min(matching_genres / len(combined_genres), 1.0) * weights.get("genre_match", 0.3)
            else:
                genre_boost = 0

            # Actor match boost
            movie_actors = movie.get("actors", [])
            if not isinstance(movie_actors, list):
                movie_actors = []
                
            matching_actors = sum(1 for actor in movie_actors if actor in combined_actors)
            if matching_actors > 0:
                actor_boost = min(matching_actors / 3, 1.0) * weights.get("actor_match", 0.15)
            else:
                actor_boost = 0
            
            # Theme match boost
            movie_themes = movie.get("themes", [])
            if not isinstance(movie_themes, list):
                movie_themes = []
            
            # Get user's liked themes from successful recommendations if we have a preference model
            liked_themes = []
            if user_preference_model:
                liked_themes = list(user_preference_model.theme_ratings.keys())
            
            matching_themes = sum(1 for theme in movie_themes if theme in liked_themes)
            if liked_themes:
                theme_boost = min(matching_themes / len(liked_themes), 1.0) * weights.get("theme_match", 0.15)
            else:
                theme_boost = 0
            
            # Tone match boost
            movie_tones = movie.get("tones", [])
            if not isinstance(movie_tones, list):
                movie_tones = []
            
            # Get user's liked tones from successful recommendations if we have a preference model
            liked_tones = []
            if user_preference_model:
                liked_tones = list(user_preference_model.tone_ratings.keys())
            
            matching_tones = sum(1 for tone in movie_tones if tone in liked_tones)
            if liked_tones:
                tone_boost = min(matching_tones / len(liked_tones), 1.0) * weights.get("tone_match", 0.05)
            else:
                tone_boost = 0
            
            # Franchise match boost
            movie_franchises = movie.get("franchises", [])
            if not isinstance(movie_franchises, list):
                movie_franchises = []
            
            # Get user's liked franchises from successful recommendations if we have a preference model
            liked_franchises = []
            if user_preference_model:
                liked_franchises = list(user_preference_model.franchise_ratings.keys())

            franchise_boost = 0

            matching_franchises = sum(1 for franchise in movie_franchises if franchise in liked_franchises)
            if liked_franchises:
                if matching_franchises > 0:
                    franchise_boost = min(matching_franchises / len(liked_franchises), 1.0) * weights.get("franchise_match", 0.3) * 3.0
                else:
                    franchise_boost = 0
            
            # Target audience match
            target_audience = movie.get("target_audience", "general")
            audience_boost = 0
            
            # If we have a preference model, check for target audience match
            if user_preference_model:
                # Get the audience preferences from database
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                
                try:
                    cursor.execute("""
                        SELECT target_age FROM user_style_preferences
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    pref_result = cursor.fetchone()
                    if pref_result and pref_result.get('target_age'):
                        preferred_audience = pref_result.get('target_age')
                        if preferred_audience == target_audience:
                            audience_boost = weights.get("audience_match", 0.05)
                        elif target_audience == "general":
                            audience_boost = weights.get("audience_match", 0.05) * 0.5
                except Exception as e:
                    print(f"Error getting audience preference: {e}")
                finally:
                    cursor.close()
                    connection.close()
            
            # Rating boost
            rating_boost = 0
            vote_average = movie.get("vote_average")
            vote_count = movie.get("vote_count", 0)
            
            if vote_average is not None and vote_count is not None and vote_count > 50:
                try:
                    avg_rating = float(vote_average)
                    rating_boost = min(avg_rating / 10, 1.0) * weights.get("rating_boost", 0.05)
                except (TypeError, ValueError) as e:
                    print(f"DEBUG: Error processing rating: {e}")

            # Calculate final score
            final_score = base_score + genre_boost + actor_boost + theme_boost + tone_boost + franchise_boost + audience_boost + rating_boost
            
            # Add the scored movie to our list with score breakdown
            scored_movie = dict(movie)
            scored_movie["recommendation_score"] = round(final_score, 3)
            
            # Add score breakdown
            scored_movie["_score_breakdown"] = {
                "base_score": round(base_score, 3),
                "genre_boost": round(genre_boost, 3),
                "actor_boost": round(actor_boost, 3),
                "theme_score": round(theme_boost, 3),
                "tone_score": round(tone_boost, 3),
                "franchise_score": round(franchise_boost, 3),
                "audience_score": round(audience_boost, 3),
                "rating_boost": round(rating_boost, 3)
            }          
            scored_movies.append(scored_movie)
        except Exception as e:
            print(f"DEBUG: Error scoring movie: {e}")
    
    # Sort by final score
    print("DEBUG: Sorting recommendations")
    try:
        scored_movies.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
    except Exception as e:
        print(f"DEBUG: Error sorting recommendations: {e}")
    
    # Ensure diversity in recommendations
    diverse_recommendations = ensure_diversity(scored_movies, max_per_genre=5, top_n=20)
      
    return diverse_recommendations[:top_n]

def ensure_diversity(scored_movies, max_per_genre=5, top_n=20):
    """ Diversity filter with balance between relevance and variety."""
    genres_count = {}
    diverse_results = []
    
    # Safety check for empty input
    if not scored_movies:
        print("WARNING: No scored movies provided to diversity filter")
        return []
    
    # Include top 5 movies regardless of genre 
    top_count = min(5, len(scored_movies))
    for idx in range(top_count):
        movie = scored_movies[idx]
        diverse_results.append(movie)
        
        # Track genres for these movies
        movie_genres = movie.get("genres", ["Unknown"])
        if not isinstance(movie_genres, list):
            movie_genres = ["Unknown"]
            
        for genre in movie_genres[:2]:
            genre_str = str(genre)
            if genre_str not in genres_count:
                genres_count[genre_str] = 0
            genres_count[genre_str] += 1
    
    # Apply diversity filter for remaining slots
    for movie in scored_movies:
        # Skip movies we've already added
        if movie in diverse_results:
            continue
            
        movie_genres = movie.get("genres", ["Unknown"])
        if not isinstance(movie_genres, list):
            movie_genres = ["Unknown"]
        elif len(movie_genres) == 0:
            movie_genres = ["Unknown"]
        
        # Check if this movie would exceed genre caps
        exceeds_cap = False
        for genre in movie_genres[:2]:
            genre_str = str(genre)
            if genre_str in genres_count and genres_count[genre_str] >= max_per_genre:
                exceeds_cap = True
                break
        
        # If very high score, add despite genre cap
        max_score = scored_movies[0].get("recommendation_score", 0) if scored_movies else 0
        high_score_threshold = max_score * 0.8
        movie_score = movie.get("recommendation_score", 0)
        is_high_score = movie_score >= high_score_threshold if high_score_threshold > 0 else False
        
        if not exceeds_cap or is_high_score:
            diverse_results.append(movie)
            
            # Update genre counts
            for genre in movie_genres[:2]:
                genre_str = str(genre)
                if genre_str not in genres_count:
                    genres_count[genre_str] = 0
                genres_count[genre_str] += 1
        
        # Stop once we have enough recommendations
        if len(diverse_results) >= top_n:
            break
    
    # If we still need more, add remaining movies
    if len(diverse_results) < top_n:
        for movie in scored_movies:
            if movie not in diverse_results and len(diverse_results) < top_n:
                diverse_results.append(movie)
    
    return diverse_results[:top_n]

@recommendations_bp.route("/recommend", methods=["GET"])
@token_required
def recommend_movies(current_user):
    """ Generate movie recommendations """
    print(f"Recommendation process has begun for {current_user}")

    connection = get_db_connection()
    cursor = connection.cursor()
    user_id = None
    user_preferences = None

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

        # Check if already generating recommendations
        if not check_and_set_lock(user_id):
            print(f"Recommendations generation in progress for user {user_id}")
            
            # Return stored recommendations with status
            stored_recs = get_stored_recommendations(user_id)
            if stored_recs:
                for rec in stored_recs:
                    try:
                        rec['genres'] = parse_list_from_db(rec['genres'])
                        rec['actors'] = parse_list_from_db(rec['actors'])
                    except:
                        if 'genres' not in rec:
                            rec['genres'] = []
                        if 'actors' not in rec:
                            rec['actors'] = []
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
                print("No need to refresh recommendations. Returning stored recommendations")
                release_lock(user_id)
                stored_recs = get_stored_recommendations(user_id)
                if stored_recs:
                    for rec in stored_recs:
                        try:
                            rec['genres'] = parse_list_from_db(rec['genres'])
                            rec['actors'] = parse_list_from_db(rec['actors'])
                        except:
                            if 'genres' not in rec:
                                rec['genres'] = []
                            if 'actors' not in rec:
                                rec['actors'] = []
                    return jsonify({"recommended_movies": stored_recs}) 
                
            # Generate new recommendations
            print("Generating new recommendations") 
            user_preferences = get_user_preferences(current_user)
            if not user_preferences:
                release_lock(user_id)
                return jsonify({"error": "User preferences not found"}), 404
            
            print("user preferences", user_preferences) 
            # Get watchlist data for the user preference model
            watchlist_prefs = get_user_watchlist_preferences(user_id)
            watchlist_items = watchlist_prefs.get('all_watchlist_items', [])
            
            print("Received watchlist preferences", watchlist_prefs)
            # Build the enhanced user preference model
            try:
                user_model = build_user_preference_model(user_id, watchlist_items, user_preferences)
            except Exception as e:
                print(f"Error building user model: {e}")
                user_model = None
            
            # Get favourite movies
            favorite_movies = user_preferences.get("favourite_movies", [])
            favorite_movies = parse_list_from_db(favorite_movies)
            print("favorite movies", favorite_movies)

            if not favorite_movies:
                print("Warning: No favorite movies in preferences")
                favorite_movies = ["action", "comedy", "romance", "adventure"] # Generic movie genre incase all fails
            
            print("Now sending data to movies route")
            # Get candidate movies
            candidate_movies = fetch_movies_for_user(current_user, user_preferences)
            
            # Check if we have candidates
            if not candidate_movies:
                candidate_movies = get_fallback_recommendations(user_preferences)
            
            # Get valid favorite profiles
            valid_favorite_profiles = get_profiles_for_favorite_movies(favorite_movies, candidate_movies)
            
            # Check if we have profiles
            if not valid_favorite_profiles:
                print("Warning: No valid favorite profiles, creating generic profiles")
                valid_favorite_profiles = [
                    "movie action adventure thriller exciting",
                    "movie comedy funny entertaining lighthearted",
                    "movie drama emotional moving powerful"
                ]
            
            # Compute recommendations
            recommendations = compute_enhanced_recommendations(
                user_id=user_id,
                candidate_movies=candidate_movies,
                user_preferences=user_preferences,
                favourite_profiles=valid_favorite_profiles,
                user_preference_model=user_model,
                top_n=20
            )
            
            # Check if we have recommendations
            if not recommendations:
                print("Warning: No recommendations generated, using fallback")
                recommendations = get_fallback_recommendations(user_preferences)
            
            # Save recommendations
            if recommendations:
                saved = save_enhanced_recommendations(user_id, recommendations)
                save_recommendation_explanations(user_id, recommendations)
                if not saved:
                    print("Warning: Failed to save recommendations")
            
            # Release the lock
            release_lock(user_id)
            
            # Clean up recommendations for output
            for rec in recommendations:
                if '_score_breakdown' in rec:
                    rec.pop('_score_breakdown')
            
            print(f"Successfully generated {len(recommendations)} recommendations")
            for i, movie in enumerate(recommendations, 1):
                print(f"{i}. {movie['title']}")
            return jsonify({"recommended_movies": recommendations})
        except Exception as e:
            print(f"Error during recommendation generation: {e}")
            # Make sure to release the lock in case of error
            release_lock(user_id)
            
            # Try to return something useful
            try:
                if not stored_recs:
                    fallback_recs = get_fallback_recommendations(user_preferences)
                    print("Returning fallback recommendations")
                    return jsonify({"recommended_movies": fallback_recs, "status": "fallback"})
                else:
                    print("Returning stored recomendations")
                    return jsonify({"recommend_movies": stored_recs, "status": "stored recommendations"})
            except:
                return jsonify({"error": "Failed to generate recommendations"}), 500
    except Exception as e:
        # If we have a user_id, make sure to release any lock
        if user_id:
            release_lock(user_id)
        print(f"Error in recommend_movies: {e}")
        return jsonify({"error": "An error occurred gathering recommendations"}), 500

@recommendations_bp.route("/recommendation-explanations", methods=["GET"])
@token_required
def get_recommendation_explanations(current_user):
    """ Get explanations for why movies were recommended """
    movie_id = request.args.get('movie_id')
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get user id
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user_result['id']
        
        # Get explanation for a specific movie
        if movie_id:
            cursor.execute("""
                SELECT explanation, aspects, created_at
                FROM recommendation_explanations
                WHERE user_id = %s AND movie_id = %s
            """, (user_id, movie_id))
            
            explanation = cursor.fetchone()
            
            if not explanation:
                return jsonify({"error": "No explanation found for this movie"}), 404
            
            return jsonify({
                "movie_id": movie_id,
                "explanation": explanation.get("explanation"),
                "aspects": json.loads(explanation.get("aspects", "{}")),
                "created_at": explanation.get("created_at").isoformat() if explanation.get("created_at") else None
            })
        
        # Get explanations for all movies
        cursor.execute("""
            SELECT e.movie_id, e.explanation, e.aspects, e.created_at, 
                   r.movie_title, r.recommendation_score
            FROM recommendation_explanations e
            JOIN user_recommendations r ON e.movie_id = r.movie_id AND e.user_id = r.user_id
            WHERE e.user_id = %s
            ORDER BY r.recommendation_score DESC
        """, (user_id,))
        
        explanations = cursor.fetchall()
        
        if not explanations:
            return jsonify({"explanations": []}), 200
        
        result = []
        for exp in explanations:
            result.append({
                "movie_id": exp.get("movie_id"),
                "movie_title": exp.get("movie_title"),
                "explanation": exp.get("explanation"),
                "score": exp.get("recommendation_score"),
                "aspects": json.loads(exp.get("aspects", "{}")),
                "created_at": exp.get("created_at").isoformat() if exp.get("created_at") else None
            })      
        return jsonify({"explanations": result})
    except Exception as e:
        print(f"Error getting recommendation explanations: {e}")
        return jsonify({"error": "Failed to retrieve recommendation explanations"}), 500
    finally:
        cursor.close()
        connection.close()

@recommendations_bp.route("/recommendation-feedback", methods=["POST"])
@token_required
def save_recommendation_feedback(current_user):
    """ Save recommnedation feedback in database """
    data = request.json
    feedback = data.get("feedback")
    movie_id = data.get("movie_id")
    rating = data.get("rating")
    is_overall = data.get("overall", False)  
    
    if not feedback:
        return jsonify({"error": "Feedback value is required"}), 400
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user_result[0]
        
        if is_overall or movie_id is None:
            # Save overall feedback in database
            cursor.execute("""
                INSERT INTO overall_recommendation_feedback 
                (user_id, feedback_value, feedback_date) 
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                feedback_value = VALUES(feedback_value),
                feedback_date = NOW()
            """, (user_id, feedback))
            print(f"Saved overall feedback '{feedback}' for user {user_id}")
            
        else:
            # Save movie specifc feedback in database
            print(f"Saving movie-specific feedback for movie {movie_id}: {feedback}, rating: {rating}")
            cursor.execute("""
                INSERT INTO recommendation_feedback 
                (user_id, movie_id, feedback_value, rating, feedback_date) 
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                feedback_value = VALUES(feedback_value),
                rating = VALUES(rating),
                feedback_date = NOW()
            """, (user_id, movie_id, feedback, rating))
        
        # Force recommendation refresh for negative feedback
        if feedback == "bad":
            cursor.execute("""
                UPDATE user_recommendations_metadata 
                SET last_updated = DATE_SUB(NOW(), INTERVAL 25 HOUR) 
                WHERE user_id = %s
            """, (user_id,))
        
        connection.commit()
        return jsonify({"success": "Feedback saved successfully"}), 200       
    except Exception as e:
        connection.rollback()
        print(f"Error saving recommendation feedback: {str(e)}")
        return jsonify({"error": "Failed to save feedback"}), 500
    finally:
        cursor.close()
        connection.close()

@recommendations_bp.route("/disliked-recommendations", methods=["GET"])
@token_required
def get_disliked_recommendations(current_user):
    """ Get a list of movies a user has disliked """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user_result["id"]
        
        # Get all movies the user gave negative feedback
        cursor.execute("""
            SELECT rf.movie_id, rf.feedback_date, r.movie_title, r.genres
            FROM recommendation_feedback rf
            JOIN user_recommendations r ON rf.movie_id = r.movie_id AND rf.user_id = r.user_id
            WHERE rf.user_id = %s AND rf.feedback_value = 'bad'
            ORDER BY rf.feedback_date DESC
        """, (user_id,))
        
        disliked_movies = cursor.fetchall()
        
        # Process the results
        result = []
        for movie in disliked_movies:
            try:
                # Parse genres from string
                genres = ast.literal_eval(movie['genres']) if movie['genres'] else []
            except:
                genres = []
                
            result.append({
                "movie_id": movie['movie_id'],
                "title": movie['movie_title'],
                "feedback_date": movie['feedback_date'].isoformat() if movie['feedback_date'] else None,
                "genres": genres
            })
        
        return jsonify({"disliked_movies": result})
    except Exception as e:
        print(f"Error getting disliked recommendations: {str(e)}")
        return jsonify({"error": "Failed to get disliked recommendations"}), 500
    finally:
        cursor.close()
        connection.close()

def exclude_disliked_movies(user_id, candidate_movies):
    """ Filter out movies similar to ones the user has disliked """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get disliked movie IDs
        cursor.execute("""
            SELECT movie_id 
            FROM recommendation_feedback 
            WHERE user_id = %s AND feedback_value = 'bad'
        """, (user_id,))
        
        disliked_movie_ids = [str(row['movie_id']) for row in cursor.fetchall()]
        
        if not disliked_movie_ids:
            return candidate_movies
        
        # Get disliked movies' details to analyse patterns
        disliked_genres = set()
        disliked_actors = set()
        
        # For each disliked movie, get its details
        for movie_id in disliked_movie_ids:
            cursor.execute("""
                SELECT genres, actors 
                FROM user_recommendations 
                WHERE user_id = %s AND movie_id = %s
            """, (user_id, movie_id))
            
            movie = cursor.fetchone()
            if movie:
                try:
                    # Parse genres and actors from strings
                    genres = ast.literal_eval(movie['genres']) if movie['genres'] else []
                    actors = ast.literal_eval(movie['actors']) if movie['actors'] else []
                    
                    disliked_genres.update(genres)
                    disliked_actors.update(actors)
                except:
                    pass
        
        # Filter candidate movies
        filtered_candidates = []
        for movie in candidate_movies:
            # Skip exact disliked movies
            if str(movie.get('id')) in disliked_movie_ids:
                continue
                
            # Count matching disliked features
            genre_matches = 0
            actor_matches = 0
            
            # Check genres
            movie_genres = movie.get('genres', [])
            for genre in movie_genres:
                if genre in disliked_genres:
                    genre_matches += 1
            
            # Check actors  
            movie_actors = movie.get('actors', [])
            for actor in movie_actors:
                if actor in disliked_actors:
                    actor_matches += 1
            
            # Only exclude movies with significant similarity to disliked movies
            if genre_matches >= 3 or actor_matches >= 2:
                continue                
            filtered_candidates.append(movie)
        
        return filtered_candidates
    except Exception as e:
        print(f"Error excluding disliked movies: {str(e)}")
        return candidate_movies
    finally:
        cursor.close()
        connection.close()

@recommendations_bp.route("/refresh-recommendations", methods=["POST"])
@token_required
def refresh_recommendations(current_user):
    """Force refresh of user recommendations."""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user_result[0]
        
        # Force recommendations to refresh by setting last_updated to more than 24 hours ago
        cursor.execute("""
            UPDATE user_recommendations_metadata 
            SET last_updated = DATE_SUB(NOW(), INTERVAL 25 HOUR) 
            WHERE user_id = %s
        """, (user_id,))
        
        connection.commit()
        
        return jsonify({"success": "Recommendations will be refreshed on next request"}), 200
    except Exception as e:
        connection.rollback()
        print(f"Error refreshing recommendations: {str(e)}")
        return jsonify({"error": "Failed to refresh recommendations"}), 500
    finally:
        cursor.close()
        connection.close()