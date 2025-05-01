import re
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta, timezone
from config import get_config

config = get_config()
SECRET_KEY = config.SECRET_KEY

def token_required(function):
    """ Function to verify JWT request """
    @wraps(function)
    def decorated(*args, **kwargs):
        # Check if the token exists
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
            return jsonify({"error": "Token is invalid"}), 403
        # Returns the email to the original function
        return function(current_user, *args, **kwargs)
    return decorated

def generate_token(email, expire_hours=None):
    """Generate a JWT token for a user."""
    if expire_hours is None:
        expire_hours = config.JWT_EXPIRATION_HOURS
        
    expiration = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    
    token = jwt.encode(
        {"email": email, "exp": expiration.timestamp()},
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

def is_valid_email(email):
    """Check if the provided email has a valid format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None