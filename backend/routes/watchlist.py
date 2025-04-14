from flask import Blueprint, jsonify, request
from database import get_db_connection
from utils.auth_utils import token_required
from utils.movie_utils import fetch_movie, parse_list_from_db
import ast

watchlist_bp = Blueprint('watchlist', __name__)

@watchlist_bp.route("/watchlist", methods=["GET"])
@token_required
def get_watchlist(current_user):
    """Get the user's watchlist """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True) 

    try:
        # Gets user's id from email 
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()

        if not user_result:
            return jsonify({"error": "User does not exist"}), 404
        
        user_id = user_result['id']

        # Get watchlist data
        cursor.execute("""
            SELECT id, movie_id, status, date_added, user_rating, notes
            FROM user_watchlist
            WHERE user_id = %s
            ORDER BY date_added DESC
        """, (user_id,))

        watchlist_items = cursor.fetchall()
        
        # Fetch movie details for each watchlist item
        for item in watchlist_items:
            # Look at the stored recommendations (prevents unnecessary API calls)
            cursor.execute("""
                SELECT movie_title, poster_path, overview, genres, release_date, vote_average
                FROM user_recommendations 
                WHERE movie_id = %s AND user_id = %s
            """, (item['movie_id'], user_id))
            
            movie_details = cursor.fetchone()
            
            # If not in recommendations then fetch from TMDB API
            if not movie_details:
                movie_info = fetch_movie(item['movie_id'])
                if movie_info:
                    item['movie_title'] = movie_info.get('title', '')
                    item['poster_path'] = movie_info.get('poster_path', '')
                    item['overview'] = movie_info.get('overview', '')
                    item['genres'] = [genre["name"] for genre in movie_info.get("genres", [])]
                    item['release_date'] = movie_info.get('release_date', '')
                    item['vote_average'] = movie_info.get('vote_average', 0)
            else:
                item['movie_title'] = movie_details['movie_title']
                item['poster_path'] = movie_details['poster_path']
                item['overview'] = movie_details['overview']
                
                # Parse genres from string to list
                try:
                    if movie_details['genres']:
                        item['genres'] = parse_list_from_db(movie_details['genres'])
                    else:
                        item['genres'] = []
                except Exception:
                    item['genres'] = []
                    
                item['release_date'] = movie_details['release_date']
                item['vote_average'] = movie_details['vote_average']
                
        return jsonify({"watchlist": watchlist_items})
    except Exception as e:
        print(f"An error occurred when fetching the watchlist: {str(e)}")
        return jsonify({"error": "Failed to fetch watchlist"}), 500
    finally:
        cursor.close()
        connection.close()

@watchlist_bp.route("/watchlist", methods=['POST'])
@token_required
def add_to_watchlist(current_user):
    """Add a movie to the user's watchlist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    data = request.json
    movie_id = data.get("movie_id")
    status = data.get("status", "want_to_watch")
    notes = data.get("notes", "")

    if not movie_id:
        return jsonify({"error": "Movie ID is needed"}), 400
    
    try:
        # Gets user's id from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()

        if not user_result:
            return jsonify({"error": "User does not exist"}), 404
        
        user_id = user_result[0]

        # Adds movie and users input to database    
        cursor.execute("""
            INSERT INTO user_watchlist (user_id, movie_id, status, notes) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status = %s, notes = %s
        """, (user_id, movie_id, status, notes, status, notes))   
        connection.commit()
        return jsonify({"success": "Movie has been successfully added to watchlist"}), 201
    except Exception as e:
        connection.rollback()
        print(f"An error occurred when adding to watchlist: {str(e)}")
        return jsonify({"error": "Failed to add movie to watchlist"}), 500
    finally:
        cursor.close()
        connection.close()

@watchlist_bp.route("/watchlist/<int:movie_id>", methods=["PUT"])
@token_required
def update_watchlist(current_user, movie_id):
    """Update a movie in the user's watchlist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    data = request.json
    status = data.get("status")
    user_rating = data.get("user_rating")
    notes = data.get("notes")

    try:
        # Gets user's id from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"error": "User does not exist"}), 404
        
        user_id = user_result[0]
 
        # Verifies if movie exist in watchlist
        cursor.execute("SELECT id FROM user_watchlist WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        if not cursor.fetchone():
            return jsonify({"error": "Movie not found in watchlist"}), 404
        
        # List variables for the users input and parameters to be stored in database
        update_parts = []
        parameters = []

        # Updates status
        if status is not None:
            update_parts.append("status = %s")
            parameters.append(status)
        
        # Updates user ratings
        if user_rating is not None:
            if not (0 <= float(user_rating) <= 10):
                return jsonify({"error": "Rating needs to be between 0 and 10"}), 400
            update_parts.append("user_rating = %s")
            parameters.append(user_rating)
        
        # Updates notes
        if notes is not None:
            update_parts.append("notes = %s")
            parameters.append(notes)
        
        # Prevents empty values being added to databse 
        if not update_parts:
            return jsonify({"error": "All input fields are empty"}), 400
        
        # Updates database based on user input
        query = f"UPDATE user_watchlist SET {', '.join(update_parts)} WHERE user_id = %s AND movie_id = %s"
        parameters.extend([user_id, movie_id])
        
        cursor.execute(query, parameters)
        connection.commit()

        return jsonify({"success": "Watchlist has been updated successfully"}), 200
    except Exception as e:
        connection.rollback()
        print(f"Failed to update watchlist: {str(e)}")
        return jsonify({"error": "An error occurred when updating the watchlist"}), 500
    finally:
        cursor.close()
        connection.close()

@watchlist_bp.route("/watchlist/<int:movie_id>", methods=["DELETE"])
@token_required
def delete_from_watchlist(current_user, movie_id):
    """Remove a movie from the user's watchlist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Gets id from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"error": "User does not exist"}), 404
        
        user_id = user_result[0]

        # Deletes movies based on movie id  
        cursor.execute("DELETE FROM user_watchlist WHERE user_id = %s AND movie_id = %s", 
                     (user_id, movie_id))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "No movies found in watchlist"}), 404
        
        connection.commit()
        return jsonify({"success": "Movie was removed from watchlist"}), 200
    except Exception as e:
        connection.rollback()
        print(f"An error occurred when removing movie from watchlist: {str(e)}")
        return jsonify({"error": "Failed to remove movie from watchlist"}), 500
    finally:
        cursor.close()
        connection.close()