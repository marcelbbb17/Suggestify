from flask import Blueprint, request, jsonify
import bcrypt
from database import get_db_connection
from utils.auth_utils import is_valid_email, generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user."""
    # Gets inputs data from frontend 
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Checks if any input field is empty 
    if not username or not email or not password:
        return jsonify({"error": "Please provide all fields"}), 400
    
    # Hashes the password using bcrypt
    hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Database Connection
    connection = get_db_connection()
    cursor = connection.cursor()

    try: 
        # Checks if email is registered in the database already
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email is already exist"}), 400
        
        # Checks if the email is valid
        if not is_valid_email(email):
            return jsonify({"error": "Please provide a valid email address"}), 400
        
        # Checks if username is registered in the database already
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username is already taken"}), 400
        
        # Checks if the password is at least 8 characters long
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        else: 
            # Adds the new user to the database
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, hash_password))
            connection.commit()
            
            # Generate token
            token = generate_token(email)            
            return jsonify({
                "success": "User registered successfully!", 
                "token": token, 
                "username": username
            }), 201
    except Exception as e:
        connection.rollback()
        return jsonify({"error": f"An error occurred while registering the user: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@auth_bp.route("/login", methods=["POST"]) 
def login():
    """Log in user"""
    data = request.json
    email = data.get("email")
    password = data.get("password")
   
    # Checks if any input field is empty 
    if not email or not password:
        return jsonify({"error": "Please provide an email and password"}), 400
   
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try: 
        # Check if email is in the database
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if not cursor.fetchone(): 
            return jsonify({"error": "This email does not exist"}), 404
       
        # Gets password from database based on email
        cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
        stored_password = cursor.fetchone()

        # Check if password is correct
        if not bcrypt.checkpw(password.encode("utf-8"), stored_password[0].encode("utf-8")):
            return jsonify({"error": "Password is incorrect"}), 401 

        cursor.execute("SELECT username FROM users WHERE email = %s", (email,))
        username = cursor.fetchone()[0]
        
        if username:
            # Generate token
            token = generate_token(email)
            
            return jsonify({
                "success": f"Welcome back {username}", 
                "token": token, 
                "username": username
            }), 200 
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()