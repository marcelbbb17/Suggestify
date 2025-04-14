from flask import Blueprint, jsonify, request
from database import get_db_connection
from utils.auth_utils import token_required

preferences_bp = Blueprint('preferences', __name__)

@preferences_bp.route("/save_questionnaire", methods=["POST"])
@token_required
def save_questionnaire(current_user):
    """Save user preferences from the questionnaire."""
    data = request.json
    email = current_user 

    favourite_movies = data.get("favouriteMovies", [])
    genres = data.get("genres", [])
    age = data.get("age")
    gender = data.get("gender")
    watch_frequency = data.get("watchFrequency")
    favourite_actors = data.get("favouriteActors", [])

    # Checks if all input fields are entered 
    if not age or not gender or not watch_frequency:
        return jsonify({"error": "Please input all fields"}), 400 
    if len(favourite_actors) == 0 or len(favourite_movies) == 0 or len(genres) == 0:
        return jsonify({"error": "Please add a favorite movie, actor and genre"}), 400
    
    connection = get_db_connection()
    cursor = connection.cursor()

    try: 
        # Get user_id from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user[0]

        # Check if user already has preferences
        cursor.execute("SELECT user_id FROM questionnaire WHERE user_id = %s", (user_id,))
        exists_in_table = cursor.fetchone()

        if exists_in_table:
            # Update existing preferences
            cursor.execute("""
                UPDATE questionnaire 
                SET favourite_movies = %s, genres = %s, age = %s, gender = %s, 
                    watch_frequency = %s, favourite_actors = %s, last_updated = NOW() 
                WHERE user_id = %s
            """, (
                str(favourite_movies), str(genres), age, gender, 
                watch_frequency, str(favourite_actors), user_id
            ))
            connection.commit()
            return jsonify({"success": "We have updated your preferences"}), 200
        else:
            # Add new preferences
            cursor.execute("""
                INSERT INTO questionnaire 
                (user_id, favourite_movies, genres, age, gender, watch_frequency, favourite_actors, last_updated) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                user_id, str(favourite_movies), str(genres), age, 
                gender, watch_frequency, str(favourite_actors)
            ))
            connection.commit()
            return jsonify({"success": "Data was saved successfully"}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@preferences_bp.route("/recommendation-feedback", methods=["POST"])
@token_required
def save_recommendation_feedback(current_user):
    """Save user feedback on recommendations."""
    data = request.json
    feedback = data.get("feedback")

    if not feedback:
        return jsonify({"error": "No feedback provided"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Get user ID from email
        cursor.execute("SELECT id FROM users WHERE email = %s", (current_user,))
        user_result = cursor.fetchone()

        if not user_result:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user_result[0]

        # Check if user already has a feedback 
        cursor.execute("""
            SELECT id FROM recommendation_feedback 
            WHERE user_id = %s
        """, (user_id,))

        user_current_feedback = cursor.fetchone()

        if user_current_feedback:
            # Update feedback
            cursor.execute("""
                UPDATE recommendation_feedback 
                SET feedback_value = %s, feedback_date = NOW() 
                WHERE user_id = %s
            """, (feedback, user_id))
        else:
            # Save feedback
            cursor.execute("""
                INSERT INTO recommendation_feedback 
                (user_id, feedback_value, feedback_date) 
                VALUES (%s, %s, NOW())
            """, (user_id, feedback)) 
            
        connection.commit()
        return jsonify({"success": "Feedback saved successfully"}), 200
    except Exception as e:
        connection.rollback()
        print(f"Error saving recommendation feedback {str(e)}")
        return jsonify({"error": "Failed to save feedback"}), 500
    finally:
        cursor.close()
        connection.close()

@preferences_bp.route("/refresh-recommendations", methods=["POST"])
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