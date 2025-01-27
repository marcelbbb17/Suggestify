from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection
import bcrypt 
import re 
import uuid 

app = Flask(__name__)
CORS(app)  # Allow React to access this API

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

@app.route("/login", methods={"POST"}) 
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
           return jsonify({"success": f"Welcome back {username}", "username": username}), 200
   except Exception as e:
       return jsonify({"error": f"An error occured: {str(e)}"}), 500
   finally:
       connection.close()
       cursor.close()

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
