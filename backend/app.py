from flask import Flask, jsonify
from flask_cors import CORS
from routes import register_blueprints
from config import get_config

def create_app():
    app = Flask(__name__)
    CORS(app) 
    
    config = get_config()
    
    register_blueprints(app)
    
    @app.route("/")
    def home():
        return jsonify({"welcome": "Welcome to the Suggestify API!"})
    
    return app

if __name__ == "__main__":
    print("Starting Flask server...")
    app = create_app()
    app.run(debug=True, port=5000)