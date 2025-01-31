from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection
from functools import wraps
from dotenv import load_dotenv
import bcrypt 
import re 
import jwt
import os 
import datetime

# import uuid 

app = Flask(__name__)
CORS(app)  # Allow React to access this API

load_dotenv()  
SECRET_KEY = str(os.getenv("JWT_SECRET_KEY"))

def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        # Checks if the token exist 
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 403
        try:
            # Exractes the token and gather the payload which is the email
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
            return jsonify({"Success": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": "An error occurred while registering the user"}), 500
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
               {"email": email, "exp": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)).timestamp()},
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
        exists_in_table = cursor.fetchone() # user_id from from queestionnaire
        print(exists_in_table)

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

# Forgot password fucntionlity implement it later 
# @app.route("/forgot-password", methods=["POST"])
# def forgot_password():
#     data = response.json
#     email = data.get("email")

#     if not email:
#         return jsonify({"error": "Email is required"}), 400
    
#     connection = get_db_connection()
#     cursor = connection.cursor()

#     try: 
#         cursor.execute("SELECT id FROM users WHERE email = %s", (email),)
#         user = cursor.fetchone()

#         if not user:
#             return jsonify({"error": "Email does not exist "})
        
#         token = str(uuid.uuid4())
#         link = f"http://127.0.0.1:3000/reset-password?token={token}"

#         cursor.execute("UPDATE users SET token = %s WHERE email = %s", (token, email))
#         cursor.commit()

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
