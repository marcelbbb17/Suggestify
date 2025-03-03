from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection
from functools import wraps
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta, timezone
import requests
import bcrypt 
import re 
import jwt
import os 
import numpy as np
import ast

app = Flask(__name__)
CORS(app)  
load_dotenv()  
SECRET_KEY = str(os.getenv("SECRET_KEY"))

load_dotenv()
TMBD_KEY = os.getenv("TMBD_API_KEY")

def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        # Checks if the token exist 
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 403
        try:
            # Gets the token and decodes it 
            token = token.split("Bearer ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['email']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session Expired. Please log in again"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error":"Token is invalid"}), 403
        # returns the email to the original function 
        return function(current_user, *args, **kwargs)
    return decorated

@app.route("/movies", methods=["GET"])
@token_required 
def movies(current_user):
    total_pages = 5
    all_movies = []
    
    # Call genre mapping function
    genre_mapping = fetch_genre_mapping()

    # Gets users preferneces from database 
    user_preferences = get_user_preferences(current_user)
    if not user_preferences:
        return jsonify({"error": "User preferences not found"}), 404
    
    if len(user_preferences["genres"]) > 5:  
        total_pages = 8 
    
    # Converts the string into an actual list
    favorite_genres = ast.literal_eval(user_preferences["genres"])
    favorite_actors = ast.literal_eval(user_preferences["favourite_actors"])  
    
    # fetches movies from these 3 categories to ensure a decently good movie pull
    categories = {
        "popular": f"https://api.themoviedb.org/3/movie/popular?api_key={TMBD_KEY}&language=en-US&page=",
        "top_rated": f"https://api.themoviedb.org/3/movie/top_rated?api_key={TMBD_KEY}&language=en-US&page=",
        "trending": f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMBD_KEY}&language=en-US&page="
    }

    for category, base_url in categories.items():
        for page in range(1, total_pages + 1): 
            url = f"{base_url}{page}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                movies = data.get("results", [])
                for movie in movies:
                    # Gets genre ids for the movie
                    genre_ids = movie.get("genre_ids", []) 
                    movie_genres = []
                
                    # Gets movie id and creates movie profile
                    movie_id = movie["id"]     
                    profile = movie_profile(movie_id)
                    if not profile:
                        continue # skips movies without profile

                    # Converts the genre_ids provided by TMBD into actual genres     
                    for genre_id in genre_ids:
                        genre_name = genre_mapping.get(genre_id, "Unknown")
                        movie_genres.append(genre_name)
                    
                    # Checks if the movies genre matches users preferenced genres at least one of them 
                    matches_favorite_genres = False
                    for genre in movie_genres:
                        if genre in favorite_genres:
                            matches_favorite_genres = True 
                            break 

                    # Checks if movies has at least one of the actors         
                    actors = get_actors(movie_id)
                    matches_favorite_actors = False 
                    for actor in actors:
                        if actor in favorite_actors:
                            matches_favorite_actors = True 
                            break
                    
                    # If it matches favourite genre or movie then add movie to the list
                    if matches_favorite_genres or matches_favorite_actors:
                        movie["genres"] = movie_genres
                        movie["actors"] = actors
                        movie["profile"] = profile
                        movie.pop("genre_ids", None)
                        all_movies.append(movie)
    print(len(all_movies))    
    return jsonify({"movies" : all_movies})

@app.route("/recommend", methods=["GET"])
@token_required
def recommend_movies(current_user):
    print(f"Recommendation process has begun for {current_user}")

    connection = get_db_connection()
    cursor = connection.cursor()

    try: 
        # gets the user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            cursor.close()
            connection.close()
            return jsonify({"error": "User not found"}), 404
    
        user_id = user_result[0]
        cursor.close()
        connection.close()

        # Check if we need to refresh recommendation 
        need_to_refresh = should_refresh_recommendations(user_id)

        if not need_to_refresh:
            print("No need to refresh recommendation. Returning Stored recommendations")
            stored_recs = get_stored_recommendations(user_id)
            if stored_recs:
                for rec in stored_recs:
                    try:
                        rec['genres'] = ast.literal_eval(rec['genres'])
                        rec['actors'] = ast.literal_eval(rec['actors'])
                    except:
                        rec['genres'] = []
                        rec['actors'] = [] 
                print(f"returning {len(stored_recs)} stored movies")    
                return jsonify({"recommended_movies" : stored_recs}) 
        
        # If 24 hours passed or the user hasnt generated recs
        print("Generating New Recommendations") 
        user_preferences = get_user_preferences(current_user)
    
        # Converts favourite movies from database into a list
        favorite_movies = user_preferences.get("favourite_movies", [])
        if isinstance(favorite_movies, str):
            try:
                favorite_movies = ast.literal_eval(favorite_movies)
            except Exception as e:
                print("Error converting preferences", e)
                favorite_movies = []
    
        # Get movies that match user preferences
        candidate_movies = fetch_movies_for_user(current_user, user_preferences)
    
        if not favorite_movies:
            return jsonify({"error": "No movies match user preference :( )"}), 404

        valid_favorite_profiles = []
        for fav_movie in favorite_movies:
            match = next((m["profile"] for m in candidate_movies if m["title"].lower() == fav_movie.lower()), None)
            if match:
                valid_favorite_profiles.append(match)
            else:
                fetched_profile = fecth_missing_movie(fav_movie)
                if fetched_profile:
                    valid_favorite_profiles.append(fetched_profile)
                else:
                    print(f"'{fav_movie}' did not return a valid profile.")

        if not valid_favorite_profiles:
            return jsonify({"error": "No valid favorite movie profiles found"}), 404

        candidate_profiles = [movie["profile"] for movie in candidate_movies]
        similarity_scores = compute_tfidf_similarity(candidate_profiles, valid_favorite_profiles, user_preferences)
    
        # Pass favorite_movies to exclude already-watched movies.
        recommended_movies = get_top_recommendations(similarity_scores, candidate_movies, favorite_titles=favorite_movies, top_n=20)

        # Save the recs to database
        saved = save_recommendations(user_id, recommended_movies)
        if not saved:
            print("Fauled to save recommendations")
        print([movie["original_title"] for movie in recommended_movies])
        return jsonify({"recommended_movies": recommended_movies})
    except Exception as e:
        print(f"Error in recommend_movies: {e}")
        return jsonify({"error": "An error occured gathering recommendations"}), 500



def isValidEmail(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

@app.route("/")
def home():
    return jsonify({"welcome" : "Welcome to the Suggestify API!"})

@app.route("/signup", methods=["POST"])
def signup():
    # Gets the input data from the request made by the client
    data = request.json 
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Checks if any of the input fields are empty
    if not username or not email or not password:
        return jsonify({"error": "Please provide all fields"}), 400
    
    # Hashes the password using bcrypt
    hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Sets ups the connection to the database
    connection = get_db_connection()
    cursor = connection.cursor()

    try: 
        # Checks if email is regsitered in the database already
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "email is already registered with us"}), 400
        # Checks if the email is valid
        if not isValidEmail(email):
            return jsonify({"error": "Please provide a valid email address"}), 400
        # Checks if username is registered in the database already
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "username is already taken"}), 400
        # Checks if the password is at least 8 characters long
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        else: 
            # Adds the new user to the database
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, hash_password))
            connection.commit()
            token = jwt.encode(
               {"email": email, "exp": (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()},
               SECRET_KEY,
               algorithm = "HS256"
           )
            return jsonify({f"Success": "User registered successfully!", "token" : token, "username": username}), 201
    except Exception as e:
        return jsonify({"error": f"An error occurred while registering the user: {str(e)}"}), 500
    finally:
        connection.close()
        cursor.close()

@app.route("/login", methods=["POST"]) 
def login():
   data = request.json
   email = data.get("email")
   password = data.get("password")
   
   # Check if username and password was provided 
   if not email or not password:
       return jsonify({"error" : "Please provide an email or password"}), 400
   
   connection = get_db_connection()
   cursor = connection.cursor()
   try: 
       # Check if email is in the databae
       cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
       if not cursor.fetchone(): 
           return jsonify({"error": "This email does not exist"}), 404
       
       # Retreives password from database based on provided email
       cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
       stored_password = cursor.fetchone()

       # Check if the entered password is correct
       if not bcrypt.checkpw(password.encode("utf-8"), stored_password[0].encode("utf-8")):
           return jsonify({"error": "Password is incorrect"}), 401 

       cursor.execute("SELECT username FROM users WHERE email = %s", (email,))
       username = cursor.fetchone()[0]
       if username:
           token = jwt.encode(
               {"email": email, "exp": (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()},
               SECRET_KEY,
               algorithm = "HS256"
           )
           return jsonify({"success": f"Welcome back {username}", "token" : token, "username": username}), 200 
   except Exception as e:
       return jsonify({"error": f"An error occured: {str(e)}"}), 500
   finally:
       cursor.close()
       connection.close()
   

@app.route("/save_questionnaire", methods=["POST"])
@token_required
def save_questionnaire(current_user):
    data = request.json
    email = current_user 

    favourite_movies = data.get("favouriteMovies", [])
    genres = data.get("genres", [])
    age = data.get("age")
    gender = data.get("gender")
    watch_frequency = data.get("watchFrequency")
    favourite_actors = data.get("favouriteActors", [])

    if not age or not gender or not watch_frequency:
        return jsonify({"error": "Please input all fields"}), 400
    
    if len(favourite_actors) == 0 or len(favourite_movies) == 0 or len(genres) == 0:
        return jsonify({"error": "Please add a favorite movie, actor and genre"}), 400
    
    connection = get_db_connection()
    cursor = connection.cursor()

    try: 
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user[0] # Users id from users table 

        cursor.execute("SELECT user_id FROM questionnaire WHERE user_id = %s", (user_id,))
        exists_in_table = cursor.fetchone() # user_id from from queestionnaire table

        if exists_in_table:
            # If user is already in questionnaire table then it updates their preference
            cursor.execute("UPDATE questionnaire SET favourite_movies = %s, genres = %s, age = %s, gender = %s, watch_frequency = %s, favourite_actors = %s WHERE user_id = %s", (str(favourite_movies), str(genres), age, gender, watch_frequency, str(favourite_actors), user_id))
            connection.commit()
            return jsonify({"success": "We have updated your preferences"}), 200
        else:
            # If not then add their preference
            cursor.execute("INSERT INTO questionnaire (user_id, favourite_movies, genres, age, gender, watch_frequency, favourite_actors) VALUES (%s, %s, %s, %s, %s, %s, %s)", (user_id, str(favourite_movies), str(genres), age, gender, watch_frequency, str(favourite_actors)),)
            connection.commit()
            return jsonify({"success": "Data was Saved successfuly"}), 201
    except Exception as e:
        return jsonify({"error": f"An error occured: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

def get_user_preferences(email):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT favourite_movies, genres, favourite_actors FROM questionnaire WHERE user_id = (SELECT id FROM users WHERE email = %s)", (email,))
    user_data = cursor.fetchone()

    cursor.close() 
    connection.close()

    return user_data

def fetch_genre_mapping():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMBD_KEY}&language=en-US"
    response = requests.get(url)
    genre_dict = {}
    
    # Gets the list of all genres and add them to genre dict with id and name
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
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMBD_KEY}&language=en-US"
    response = requests.get(url)
    actors = []

    if response.status_code == 200:
        credits = response.json()
        cast_list = credits.get("cast", [])[:5] # Limits to top 5 cast members 
        for cast_member in cast_list:
            actor_name = cast_member["name"]
            actors.append(actor_name)
        return actors 
    return []


def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMBD_KEY}&language=en-US"
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
            "genres": genre_list
        }    
    else:
        print(f"Failed to retreive data for {movie_id}")
        return None 

def fetch_keywords_for_movies(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={TMBD_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "keywords": [keyword["name"] for keyword in data.get("keywords", [])]
        }
    else:
        print(f"failed to retrieve keywords for {movie_id}")
        return {"keywords" : []}
    
def movie_profile(movie_id):
    actors = get_actors(movie_id)
    movie_details = fetch_movie_details(movie_id)
    keywords_data = fetch_keywords_for_movies(movie_id)

    if not movie_details: 
        return None 
    
    keywords_data = fetch_keywords_for_movies(movie_id)
    keywords = keywords_data.get("keywords", [])

    profile = f"{movie_details['title']} {movie_details['overview']} {' '.join(movie_details['genres'])} {' '.join(actors)} {' '.join(keywords)}"

    return profile

def fecth_missing_movie(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMBD_KEY}&query={title}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("results", [])
        if data:
            movie_id = data[0]["id"]
            profile = movie_profile(movie_id)
            if profile and len(profile.split()) >= 5:
                return profile
    return None

def compute_tfidf_similarity(movie_profiles, favourite_profiles, user_preferences):
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

    # Gets the users prefered actors and genres from database
    favourite_genres = user_preferences.get("genres", [])
    favourite_actors = user_preferences.get("favourite_actors", [])

    # Converts the user preferences into a list
    if isinstance(favourite_genres, str):
        try:
            favourite_genres = ast.literal_eval(favourite_genres)
        except Exception as e:
            print("A problem occurred when converting:", e)
            favourite_genres = []
    if isinstance(favourite_actors, str):
        try:
            favourite_actors = ast.literal_eval(favourite_actors)
        except Exception as e:
            print("A problem occurred when converting:", e)
            favourite_actors = []

    # increases the weighting of users favourtite actors and genres 
    boost_genres = (" ".join(favourite_genres) + " ") * 2
    boost_actors = (" ".join(favourite_actors) + " ") * 2

    # Adds the boosted genres/actors to the profile to improve recs
    boosted_favourite_profiles = []
    for profile in favourite_profiles:
        boosted_profile = f"{profile} {boost_genres}{boost_actors}"
        boosted_favourite_profiles.append(boosted_profile)

    # Turns them into a matrix
    tfidf_matrix = vectorizer.fit_transform(movie_profiles)
    favourite_tfidf_matrix = vectorizer.transform(boosted_favourite_profiles)
    
    # compare the two matrices based on similarity
    similarity_scores = cosine_similarity(favourite_tfidf_matrix, tfidf_matrix)
    return similarity_scores


def get_similar_movies(movie_index, similarity_matrix, top_n=20):
    # Gets similarity score of  movies
    similar_movies_score = list(enumerate(similarity_matrix[movie_index])) 
    # Sorts movie in descending order ignoring the first movie based on similarity
    sorted_movies = sorted(similar_movies_score, key=lambda x: x[1], reverse=True) # Sorts by similarity
    # return the movies
    similar_movies_indices = []
    for movie in sorted_movies[1:top_n+1]:
        i = movie[0]
        similar_movies_indices.append(i)
    print(similar_movies_indices)
    return similar_movies_indices

def get_top_recommendations(similarity_scores, all_movies, favorite_titles=None, top_n=20, min_similarity=0.05):
    # Removes punctiation and turns them into lower case 
    def normalize_title(title):
        return re.sub(r'[^\w\s]', '', title).lower().strip()

    def is_same_movie(candidate_title, favourite_title, threshold=0.9):
        candidate_words = set(normalize_title(candidate_title).split())
        favourite_words = set(normalize_title(favourite_title).split())
        # If both sets are empty return false (not same movie)
        if not candidate_words or not favourite_words:
            return False
        # Checks if the two title are the same or not 
        common = candidate_words.intersection(favourite_words)
        ratio = len(common) / min(len(candidate_words), len(favourite_words))
        return ratio >= threshold


    if similarity_scores is None or similarity_scores.size == 0:
        print("No similarities found returning general movies")
        return all_movies[:top_n]
    
    # Get the max sim score and sorts it in descending order
    max_scores = np.max(similarity_scores, axis=0)
    sorted_indices = np.argsort(max_scores)[::-1]
    
    recommendations = []
    seen_movie_ids = set()
    
    for idx in sorted_indices:
        movie = all_movies[idx]
        
        # Skips any movies missing any details 
        if "id" not in movie or "title" not in movie or "profile" not in movie:
            print(f"Skkipping {movie}")
            continue
        
        # Skip movies that are below min_similarity threhold
        if max_scores[idx] < min_similarity:
            continue
        
        # Final check to prevent recommending movie the user has already seen
        candidate_title = movie["title"]
        skip = False
        if favorite_titles:
            for fav in favorite_titles:
                if is_same_movie(candidate_title, fav):
                    skip = True
                    break
        if skip:
            continue
        
        # Stores the recs until they reach top_n which is 20 in this case
        if movie["id"] not in seen_movie_ids:
            recommendations.append(movie)
            seen_movie_ids.add(movie["id"])
            if len(recommendations) >= top_n:
                break
    return recommendations[:top_n]

def fetch_movies_for_user(current_user, user_preferences):
    url = "http://127.0.0.1:5000/movies"
    
    # Checks if user is authenticated via the token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        print("Token not found")
        return []
    
    # Retrieves movies from /movie endpoint
    headers = {"Authorization": auth_header}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        all_movies = response.json().get("movies", [])

        filtered_movies = []
        for movie in all_movies:
            # Counts the amount of matches between movie and user preferences
            genre_match_count = sum(1 for genre in movie["genres"] if genre in user_preferences["genres"])
            actor_match_count = sum(1 for actor in movie["actors"] if actor in user_preferences["favourite_actors"])
   
            if genre_match_count >= 1 or actor_match_count >= 1:
                filtered_movies.append(movie)

        print(f"Filtered Movies: {len(filtered_movies)}")
        return filtered_movies

    else:
        print(f"Failed to fetch movies: {response.status_code}")
        print(f"Response: {response.text}")
        return []
    
def get_stored_recommendations(user_id):
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

def save_recommendations(user_id, recommendations):    
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # First, ensure we delete ALL existing recommendations
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

def should_refresh_recommendations(user_id):
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

        # Get the timestamps
        cursor.execute("""
            SELECT 
                rm.last_updated AS recs_updated
            FROM user_recommendations_metadata rm
            WHERE rm.user_id = %s
        """, (user_id,))
        metadata_result = cursor.fetchone()
        
        # Gets the questionnaire timestamp
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
            print("No questionnaire date found but they have recommendations which is interesting")
            return True 
        
        recs_updated = metadata_result['recs_updated']
        prefs_updated = questionnaire_result['prefs_updated']
        print(f"Timestamps for rec_updated: {recs_updated} and prefs_updated: {prefs_updated}")

        # If preferences were updated after recommendations 
        if prefs_updated > recs_updated:
            print("Preferences were updated after recommendations so refresh them")
            return True
        
        # Else update recs if they are older than 24 hours 
        refresh_threshold = datetime.now() - timedelta(hours=24)
        should_refresh = recs_updated < refresh_threshold
        
        if should_refresh:
            print("Recommendations are older than 24 hours so  refresh")
        else:
            print("Recommendations are up to date")
        
        # This is to prevent the deadlock 
        wait_period = datetime.now() - timedelta(seconds=10)
        if recs_updated and recs_updated > wait_period:
            print("Recommendations were updated in the last 10 seconds so no more pls")
            return False 
            
        return should_refresh
    except Exception as e:
        print(f"Error occured in the refresh function: {e}")
        return True 
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
